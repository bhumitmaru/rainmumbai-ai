"""Shared DB-state loaders for reproducible index reconstruction.

The RainMumbai Index is a cumulative-deviation-rainfall (CDR) spot that must be
reconstructed from daily IMD rainfall and daily LPA. These helpers are the single
source of truth for reading that state so ingest, predict, and evaluate agree.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DailyLPA, DailyRainfall, Outcome, Prediction
from app.index.service import reconstruct_spot_series, season_start_for
from app.pipeline.preprocess import average_station_daily, lpa_lookup


def load_daily_lpa(db: Session) -> dict[tuple[str, str], float]:
    rows = db.scalars(select(DailyLPA)).all()
    return {(r.station, r.month_day): float(r.lpa_mm) for r in rows}


def load_city_daily_rain(
    db: Session,
    up_to: date | None = None,
    include_forecast: bool = False,
) -> dict[date, float]:
    stmt = select(DailyRainfall)
    if not include_forecast:
        stmt = stmt.where(DailyRainfall.is_forecast == False)  # noqa: E712
    if up_to is not None:
        stmt = stmt.where(DailyRainfall.imd_date <= up_to)
    rows = db.scalars(stmt).all()
    colaba = {r.imd_date: float(r.rainfall_mm) for r in rows if r.station == "colaba"}
    santacruz = {r.imd_date: float(r.rainfall_mm) for r in rows if r.station == "santacruz"}
    return average_station_daily(colaba, santacruz)


def city_lpa_between(
    lpa_rows: dict[tuple[str, str], float], start: date, end: date
) -> dict[date, float]:
    out: dict[date, float] = {}
    d = start
    while d <= end:
        out[d] = float(lpa_lookup(lpa_rows, "mumbai", d))
        d += timedelta(days=1)
    return out


def reconstruct_observed_spot(db: Session, up_to: date) -> dict[date, float]:
    """Observed CDR spot series from the season start through ``up_to``."""
    rain = load_city_daily_rain(db, up_to=up_to)
    lpa_rows = load_daily_lpa(db)
    start = season_start_for(up_to)
    lpa = city_lpa_between(lpa_rows, start, up_to)
    return reconstruct_spot_series(rain, lpa, start, up_to)


def load_outcome_pairs(
    db: Session,
    *,
    source: str = "all",
    from_timestamp: datetime | None = None,
    to_timestamp: datetime | None = None,
) -> list[Prediction]:
    """Predictions that have a matched observed outcome, oldest first."""
    stmt = select(Prediction).join(Outcome, Outcome.prediction_id == Prediction.id)
    if source in {"live", "backfill"}:
        stmt = stmt.where(Prediction.source == source)
    if from_timestamp is not None:
        stmt = stmt.where(Prediction.target_timestamp >= from_timestamp)
    if to_timestamp is not None:
        stmt = stmt.where(Prediction.target_timestamp <= to_timestamp)
    return list(db.scalars(stmt.order_by(Prediction.target_timestamp.asc())).all())
