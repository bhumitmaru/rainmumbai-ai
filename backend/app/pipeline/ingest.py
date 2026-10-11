"""Hourly data acquisition: Open-Meteo -> validated observations -> daily rainfall.

Stores sanitized hourly observations in ``meteo_observations`` (D3), aggregates
them into IMD-day rainfall in ``daily_rainfall``, backfills season history from
the archive API, and reconciles matured predictions into outcomes.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.datetime_utils import from_utc_naive, utcnow
from app.db.models import (
    DailyRainfall,
    IngestionStatus,
    MeteoObservation,
    Outcome,
    Prediction,
)
from app.index.service import (
    IST,
    direction_from_delta,
    latest_completed_imd_date,
    next_imd_date,
)
from app.pipeline.preprocess import daily_rainfall_for_series
from app.pipeline.state import reconstruct_observed_spot
from app.pipeline.validate import sanitize_point
from app.providers.base import HourlyPoint, StationSeries
from app.providers.cached import CachedFallbackProvider
from app.providers.open_meteo import OpenMeteoProvider

logger = logging.getLogger(__name__)

STATIONS = ("colaba", "santacruz", "mumbai")


def _upsert_observation(
    db: Session,
    station: str,
    point: HourlyPoint,
    source: str,
    is_forecast: bool,
) -> None:
    row = db.scalar(
        select(MeteoObservation).where(
            MeteoObservation.station == station,
            MeteoObservation.observed_at == point.time,
            MeteoObservation.source == source,
            MeteoObservation.is_forecast == is_forecast,
        )
    )
    values = {
        "rainfall_mm": point.rainfall_mm,
        "temperature_c": point.temperature_c,
        "humidity_pct": point.humidity_pct,
        "pressure_hpa": point.pressure_hpa,
        "wind_kmh": point.wind_kmh,
        "model_name": point.model_name,
    }
    if row is None:
        db.add(
            MeteoObservation(
                station=station,
                observed_at=point.time,
                source=source,
                is_forecast=is_forecast,
                **values,
            )
        )
    else:
        for key, value in values.items():
            setattr(row, key, value)


def _upsert_daily_rainfall(
    db: Session,
    station: str,
    imd_date: date,
    mm: float,
    is_forecast: bool,
    source: str,
) -> None:
    row = db.scalar(
        select(DailyRainfall).where(
            DailyRainfall.station == station,
            DailyRainfall.imd_date == imd_date,
        )
    )
    if row is None:
        db.add(
            DailyRainfall(
                station=station,
                imd_date=imd_date,
                rainfall_mm=mm,
                is_forecast=is_forecast,
                source=source,
            )
        )
    else:
        row.rainfall_mm = mm
        row.is_forecast = is_forecast
        row.source = source


def _backfill_archive(db: Session, live: OpenMeteoProvider, latest_completed: date) -> None:
    settings = get_settings()
    existing = db.scalar(
        select(func.count())
        .select_from(DailyRainfall)
        .where(
            DailyRainfall.station == "colaba",
            DailyRainfall.is_forecast == False,  # noqa: E712
            DailyRainfall.imd_date <= latest_completed,
        )
    )
    if (existing or 0) >= settings.season_backfill_days - 10:
        return
    end = latest_completed - timedelta(days=8)
    start = latest_completed - timedelta(days=settings.season_backfill_days)
    if end <= start:
        return
    for station in ("colaba", "santacruz"):
        try:
            series = live.fetch_archive(station, start.isoformat(), end.isoformat())
            daily = daily_rainfall_for_series(series, start, end)
            for d, mm in daily.items():
                _upsert_daily_rainfall(db, station, d, mm, False, "open-meteo-archive")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Archive backfill failed for %s: %s", station, exc)


def _record_ingestion_status(db: Session, source: str, degraded: bool, warning: str | None, records: int) -> None:
    status = db.scalar(select(IngestionStatus).where(IngestionStatus.provider == "open-meteo"))
    now = utcnow()
    if status is None:
        status = IngestionStatus(provider="open-meteo")
        db.add(status)
    status.last_success_at = now
    status.last_source = source
    status.records_last_run = records
    if degraded:
        status.last_error_at = now
        status.last_error = warning
    else:
        status.last_error_at = None
        status.last_error = None


def reconcile_outcomes(db: Session) -> int:
    """Attach observed outcomes to predictions whose target window has closed."""
    now = utcnow()
    pending = [
        p
        for p in db.scalars(
            select(Prediction)
            .outerjoin(Outcome, Outcome.prediction_id == Prediction.id)
            .where(Outcome.id.is_(None))
            .order_by(Prediction.target_timestamp.asc())
        ).all()
        if p.target_timestamp <= now
    ]
    if not pending:
        return 0

    count = 0
    spot_cache: dict[date, dict[date, float]] = {}
    for pred in pending:
        target_date = from_utc_naive(pred.target_timestamp).astimezone(IST).date()
        if target_date not in spot_cache:
            spot_cache[target_date] = reconstruct_observed_spot(db, target_date)
        spots = spot_cache[target_date]
        if target_date not in spots:
            continue
        actual = float(spots[target_date])
        actual_dir = direction_from_delta(round(actual - pred.current_index, 4))
        db.add(
            Outcome(
                prediction_id=pred.id,
                actual_index=actual,
                actual_direction=actual_dir,
                observed_at=now,
            )
        )
        count += 1
    return count


def run_ingest(db: Session) -> dict:
    live = OpenMeteoProvider()
    provider = CachedFallbackProvider(live, db)
    bundle = provider.fetch()
    now = utcnow()

    observed: dict[str, list[HourlyPoint]] = {s: [] for s in STATIONS}
    forecast: dict[str, list[HourlyPoint]] = {s: [] for s in STATIONS}
    saved = 0

    for series in bundle.stations:
        if series.station not in STATIONS:
            continue
        for raw in series.points:
            point = sanitize_point(raw)
            is_fc = point.time > from_utc_naive(now)
            _upsert_observation(db, series.station, point, series.source, is_fc)
            saved += 1
            (forecast if is_fc else observed)[series.station].append(point)

    for series in bundle.ensemble_members:
        for raw in series.points:
            point = sanitize_point(raw)
            _upsert_observation(db, "mumbai", point, series.source, True)
            saved += 1

    latest = latest_completed_imd_date(from_utc_naive(now))
    obs_start = latest - timedelta(days=8)
    for station in ("colaba", "santacruz"):
        daily = daily_rainfall_for_series(
            StationSeries(
                station=station,
                latitude=0.0,
                longitude=0.0,
                points=observed[station],
                source=bundle.source,
                is_forecast=False,
            ),
            obs_start,
            latest,
        )
        for d, mm in daily.items():
            _upsert_daily_rainfall(db, station, d, mm, False, "open-meteo")

    _backfill_archive(db, live, latest)

    target = next_imd_date(from_utc_naive(now))
    for station in ("colaba", "santacruz"):
        daily = daily_rainfall_for_series(
            StationSeries(
                station=station,
                latitude=0.0,
                longitude=0.0,
                points=forecast[station],
                source=bundle.source,
                is_forecast=True,
            ),
            target,
            target,
        )
        for d, mm in daily.items():
            _upsert_daily_rainfall(db, station, d, mm, True, "open-meteo")

    reconciled = reconcile_outcomes(db)
    _record_ingestion_status(db, bundle.source, bundle.degraded, bundle.warning, saved)
    db.commit()

    return {
        "records": saved,
        "reconciled_outcomes": reconciled,
        "source": bundle.source,
        "degraded": bundle.degraded,
        "warning": bundle.warning,
    }
