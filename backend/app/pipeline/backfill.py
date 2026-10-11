"""Historical backfill of predictions/outcomes using archive + historical forecasts."""

from __future__ import annotations

import argparse
import json
import logging
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.datetime_utils import to_utc_naive
from app.db.models import Prediction
from app.db.seed import ensure_model_versions, get_active_model_version
from app.db.session import SessionLocal
from app.index.confidence import direction_probabilities
from app.index.service import IST, category_for, direction_from_delta, imd_window_end, next_spot, season_start_for
from app.pipeline.evaluate import run_evaluation
from app.pipeline.ingest import _upsert_daily_rainfall, reconcile_outcomes
from app.pipeline.preprocess import daily_rainfall_for_series, lpa_lookup
from app.pipeline.state import load_daily_lpa, reconstruct_observed_spot
from app.providers.base import HourlyPoint, StationSeries
from app.providers.open_meteo import OpenMeteoProvider
from app.services.calibration import active_calibration

logger = logging.getLogger(__name__)


@dataclass
class BackfillSummary:
    attempted: int = 0
    backfilled: int = 0
    skipped: int = 0
    dry_run_updates: int = 0
    skip_reasons: Counter[str] = Counter()
    skipped_dates: dict[str, list[str]] | None = None

    def __post_init__(self) -> None:
        if self.skipped_dates is None:
            self.skipped_dates = defaultdict(list)

    def skip(self, d: date, reason: str) -> None:
        self.skipped += 1
        self.skip_reasons[reason] += 1
        self.skipped_dates[reason].append(d.isoformat())

    def as_dict(self) -> dict[str, Any]:
        return {
            "attempted": self.attempted,
            "backfilled": self.backfilled,
            "skipped": self.skipped,
            "dry_run_updates": self.dry_run_updates,
            "skip_reasons": dict(self.skip_reasons),
            "skipped_dates": dict(self.skipped_dates or {}),
        }


def _iter_days(start: date, end: date) -> list[date]:
    out: list[date] = []
    d = start
    while d <= end:
        out.append(d)
        d += timedelta(days=1)
    return out


def _parse_seasons(raw: str | None) -> set[int] | None:
    if not raw:
        return None
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def _season_allowed(d: date, seasons: set[int] | None) -> bool:
    if not seasons:
        return True
    return season_start_for(d).year in seasons


def _request_json(
    client: httpx.Client,
    url: str,
    params: dict[str, Any],
    cache: dict[str, dict[str, Any]],
    retries: int = 4,
) -> dict[str, Any]:
    key = f"{url}?{json.dumps(params, sort_keys=True)}"
    if key in cache:
        return cache[key]
    wait = 0.75
    for attempt in range(1, retries + 1):
        try:
            res = client.get(url, params=params)
            res.raise_for_status()
            payload = res.json()
            cache[key] = payload
            return payload
        except Exception:  # noqa: BLE001
            if attempt == retries:
                raise
            time.sleep(wait)
            wait *= 2
    raise RuntimeError("unreachable")


def _coords(station: str) -> tuple[float, float]:
    settings = get_settings()
    if station == "colaba":
        return settings.colaba_lat, settings.colaba_lon
    if station == "santacruz":
        return settings.santacruz_lat, settings.santacruz_lon
    return settings.mumbai_lat, settings.mumbai_lon


def _historical_forecast_rain(
    client: httpx.Client,
    station: str,
    issue_date: date,
    target_date: date,
    cache: dict[str, dict[str, Any]],
) -> float | None:
    settings = get_settings()
    lat, lon = _coords(station)
    url = settings.open_meteo_historical_forecast_url
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": issue_date.isoformat(),
        "end_date": target_date.isoformat(),
        "hourly": "precipitation",
        "timezone": "UTC",
    }
    payload = _request_json(client, url, params, cache)
    hourly = payload.get("hourly") or {}
    stamps = hourly.get("time") or []
    rain = hourly.get("precipitation") or []
    points: list[HourlyPoint] = []
    for i, stamp in enumerate(stamps):
        dt = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        mm = rain[i] if i < len(rain) else None
        points.append(
            HourlyPoint(
                time=dt,
                rainfall_mm=float(mm) if mm is not None else None,
                temperature_c=None,
                humidity_pct=None,
                pressure_hpa=None,
                wind_kmh=None,
            )
        )
    daily = daily_rainfall_for_series(
        StationSeries(station=station, latitude=lat, longitude=lon, points=points, source="open-meteo-historical"),
        target_date,
        target_date,
    )
    return daily.get(target_date)


def _upsert_backfill_prediction(
    db: Session,
    *,
    target_date: date,
    current_index: float,
    predicted_index: float,
    direction: str,
    probs: dict[str, float],
    version_id: int,
    inputs_json: dict[str, Any],
    dry_run: bool,
) -> bool:
    target_ts = to_utc_naive(imd_window_end(target_date))
    issued_at = to_utc_naive(imd_window_end(target_date - timedelta(days=1)))
    expected_deviation = round(predicted_index - current_index, 4)
    existing = db.scalar(
        select(Prediction).where(
            Prediction.model_version_id == version_id,
            Prediction.target_timestamp == target_ts,
            Prediction.source == "backfill",
        )
    )
    if dry_run:
        return existing is None
    if existing is None:
        row = Prediction(
            generated_at=issued_at,
            target_timestamp=target_ts,
            current_index=current_index,
            predicted_index=predicted_index,
            expected_deviation=expected_deviation,
            direction=direction,
            p_increase=probs["Increase"],
            p_no_change=probs["No Change"],
            p_decrease=probs["Decrease"],
            category_current=category_for(current_index),
            category_predicted=category_for(predicted_index),
            confidence_overall=0.0,
            data_quality=0.0,
            model_performance=0.0,
            stability_score=0.0,
            model_version_id=version_id,
            inputs_json=inputs_json,
            is_current_cache=False,
            source="backfill",
        )
        db.add(row)
        return True
    existing.generated_at = issued_at
    existing.current_index = current_index
    existing.predicted_index = predicted_index
    existing.expected_deviation = expected_deviation
    existing.direction = direction
    existing.p_increase = probs["Increase"]
    existing.p_no_change = probs["No Change"]
    existing.p_decrease = probs["Decrease"]
    existing.category_current = category_for(current_index)
    existing.category_predicted = category_for(predicted_index)
    existing.inputs_json = inputs_json
    existing.is_current_cache = False
    existing.source = "backfill"
    return False


def run_backfill(
    db: Session,
    *,
    start: date,
    end: date,
    seasons: set[int] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    if end < start:
        raise ValueError("end date must be on/after start date")
    today_ist = datetime.now(IST).date()
    if end >= today_ist:
        raise ValueError("end date must be before today (use yesterday or earlier)")

    settings = get_settings()
    provider = OpenMeteoProvider()
    cache: dict[str, dict[str, Any]] = {}
    summary = BackfillSummary()

    days = [d for d in _iter_days(start, end) if _season_allowed(d, seasons)]
    if not days:
        return summary.as_dict()
    issue_start = min(days) - timedelta(days=1)
    archive_start = min(days) - timedelta(days=1)
    archive_end = max(days)

    for station in ("colaba", "santacruz"):
        series = provider.fetch_archive(station, archive_start.isoformat(), archive_end.isoformat())
        daily = daily_rainfall_for_series(series, issue_start, archive_end)
        for d, mm in daily.items():
            if dry_run:
                continue
            _upsert_daily_rainfall(db, station, d, mm, False, "open-meteo-archive")
    if not dry_run:
        db.flush()

    ensure_model_versions(db)
    version = get_active_model_version(db, "index_formula")
    if version is None:
        raise RuntimeError("No active index formula version found")
    lpa_rows = load_daily_lpa(db)
    cal = active_calibration(db)

    with httpx.Client(timeout=settings.open_meteo_timeout_seconds) as client:
        for d in days:
            summary.attempted += 1
            issue_date = d - timedelta(days=1)
            try:
                colaba_fc = _historical_forecast_rain(client, "colaba", issue_date, d, cache)
                time.sleep(0.05)
                santacruz_fc = _historical_forecast_rain(client, "santacruz", issue_date, d, cache)
            except Exception as exc:  # noqa: BLE001
                summary.skip(d, f"historical forecast fetch failed: {type(exc).__name__}")
                continue

            if colaba_fc is None and santacruz_fc is None:
                summary.skip(d, "historical forecast not available for target IMD window")
                continue
            if colaba_fc is None:
                forecast_rain = float(santacruz_fc)
            elif santacruz_fc is None:
                forecast_rain = float(colaba_fc)
            else:
                forecast_rain = round((float(colaba_fc) + float(santacruz_fc)) / 2.0, 4)

            observed = reconstruct_observed_spot(db, issue_date)
            current = observed.get(issue_date)
            if current is None:
                summary.skip(d, "missing reconstructed observed spot at issue date")
                continue

            lpa_target = float(lpa_lookup(lpa_rows, "mumbai", d))
            raw_predicted = next_spot(float(current), forecast_rain, lpa_target, d)
            predicted = (
                round(cal["slope"] * raw_predicted + cal["intercept"], 4)
                if cal.get("enabled")
                else raw_predicted
            )
            delta = round(predicted - float(current), 4)
            direction = direction_from_delta(delta)
            probs = direction_probabilities([round(forecast_rain - lpa_target, 4)])

            changed = _upsert_backfill_prediction(
                db,
                target_date=d,
                current_index=float(current),
                predicted_index=predicted,
                direction=direction,
                probs=probs,
                version_id=version.id,
                inputs_json={
                    "raw_predicted_index": raw_predicted,
                    "forecast_rain_mm": forecast_rain,
                    "lpa_target_mm": lpa_target,
                    "issue_date": issue_date.isoformat(),
                    "source": "open-meteo-historical-forecast",
                },
                dry_run=dry_run,
            )
            if changed:
                summary.backfilled += 1
            elif dry_run:
                summary.dry_run_updates += 1
            logger.info("Backfill %s target=%s source=historical-forecast", "dry-run" if dry_run else "write", d)

    if not dry_run:
        reconciled = reconcile_outcomes(db)
        db.commit()
        evaluation = run_evaluation(db)
    else:
        reconciled = 0
        evaluation = {"samples": None, "mae": None, "rmse": None, "direction_accuracy": None, "direction_f1": None}

    result = summary.as_dict()
    result["reconciled_outcomes"] = reconciled
    result["evaluation"] = evaluation
    return result


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Backfill RainMumbai historical predictions/outcomes.")
    p.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    p.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    p.add_argument("--seasons", required=False, help="Comma-separated season years, e.g. 2024,2025")
    p.add_argument("--dry-run", action="store_true", help="Compute and log without database writes")
    return p


def _parse_date(raw: str) -> date:
    return date.fromisoformat(raw)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = _build_parser().parse_args()
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    seasons = _parse_seasons(args.seasons)
    with SessionLocal() as db:
        summary = run_backfill(db, start=start, end=end, seasons=seasons, dry_run=args.dry_run)
    print(json.dumps(summary, indent=2, sort_keys=True))  # noqa: T201


if __name__ == "__main__":
    main()
