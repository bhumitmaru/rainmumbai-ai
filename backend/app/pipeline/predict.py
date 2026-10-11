"""Generate and cache the RainMumbai Index prediction.

Deterministic given the database state (daily rainfall + LPA + forecast rows),
so identical inputs and the same model version produce identical output. The
result is cached as ``is_current_cache`` on the latest Prediction row.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import load_index_config
from app.core.datetime_utils import from_utc_naive, to_utc_naive, utcnow
from app.db.models import DailyRainfall, MeteoObservation, Prediction
from app.db.seed import ensure_model_versions, get_active_model_version
from app.index.confidence import (
    data_quality_score,
    direction_probabilities,
    model_performance_score,
    overall_confidence,
    stability_score,
)
from app.index.service import (
    category_for,
    direction_from_delta,
    imd_window,
    imd_window_end,
    latest_completed_imd_date,
    next_imd_date,
    next_spot,
)
from app.pipeline.preprocess import lpa_lookup
from app.pipeline.state import (
    load_daily_lpa,
    load_outcome_pairs,
    reconstruct_observed_spot,
)
from app.providers.base import HourlyPoint
from app.services.calibration import active_calibration
from app.services.metrics import direction_accuracy, mae

logger = logging.getLogger(__name__)


def _load_forecast_rain(db: Session, target) -> float:
    rows = db.scalars(
        select(DailyRainfall).where(
            DailyRainfall.is_forecast == True,  # noqa: E712
            DailyRainfall.imd_date == target,
        )
    ).all()
    colaba = next((r.rainfall_mm for r in rows if r.station == "colaba"), None)
    santacruz = next((r.rainfall_mm for r in rows if r.station == "santacruz"), None)
    if colaba is not None and santacruz is not None:
        return round((float(colaba) + float(santacruz)) / 2.0, 4)
    if colaba is not None:
        return float(colaba)
    if santacruz is not None:
        return float(santacruz)
    return float(lpa_lookup(load_daily_lpa(db), "mumbai", target))


def _member_deltas(db: Session, target, lpa_target: float) -> list[float]:
    win_start, win_end = imd_window(target)
    rows = db.scalars(
        select(MeteoObservation).where(
            MeteoObservation.station == "mumbai",
            MeteoObservation.is_forecast == True,  # noqa: E712
            MeteoObservation.observed_at >= to_utc_naive(win_start),
            MeteoObservation.observed_at < to_utc_naive(win_end),
        )
    ).all()
    groups: dict[str, float] = {}
    for r in rows:
        groups[r.source] = groups.get(r.source, 0.0) + (r.rainfall_mm or 0.0)
    return [round(v - lpa_target, 4) for v in groups.values()]


def _recent_observed_points(db: Session, hours: int = 36) -> list[HourlyPoint]:
    since = utcnow() - timedelta(hours=hours)
    rows = db.scalars(
        select(MeteoObservation)
        .where(
            MeteoObservation.is_forecast == False,  # noqa: E712
            MeteoObservation.observed_at >= since,
        )
        .order_by(MeteoObservation.observed_at.asc())
    ).all()
    return [
        HourlyPoint(
            time=from_utc_naive(r.observed_at),
            rainfall_mm=r.rainfall_mm,
            temperature_c=r.temperature_c,
            humidity_pct=r.humidity_pct,
            pressure_hpa=r.pressure_hpa,
            wind_kmh=r.wind_kmh,
            model_name=r.model_name,
        )
        for r in rows
    ]


def run_predict(db: Session) -> Prediction:
    cfg = load_index_config()
    now = utcnow()
    aware_now = from_utc_naive(now)
    latest = latest_completed_imd_date(aware_now)
    target = next_imd_date(aware_now)

    spots = reconstruct_observed_spot(db, latest)
    current = float(spots.get(latest, float(cfg["season_lpa_anchor_mm"])))

    lpa_rows = load_daily_lpa(db)
    lpa_target = float(lpa_lookup(lpa_rows, "mumbai", target))
    fc_rain = _load_forecast_rain(db, target)

    raw_predicted = next_spot(current, fc_rain, lpa_target, target)
    cal = active_calibration(db)
    predicted = round(
        cal["slope"] * raw_predicted + cal["intercept"], 4
    ) if cal["enabled"] else raw_predicted

    deviation = round(predicted - current, 4)
    direction = direction_from_delta(deviation)

    member_deltas = _member_deltas(db, target, lpa_target)
    probs = direction_probabilities(member_deltas)

    dq = data_quality_score(_recent_observed_points(db), datetime.now(timezone.utc))
    pairs = load_outcome_pairs(db)
    mae_val = mae([(p.predicted_index, p.outcome.actual_index) for p in pairs])
    acc = direction_accuracy([(p.direction, p.outcome.actual_direction) for p in pairs])
    mp = model_performance_score(mae_val, acc)

    previous = db.scalar(select(Prediction).order_by(Prediction.id.desc()).limit(1))
    prev_predicted = previous.predicted_index if previous is not None else None
    member_predictions = [round(current + d, 4) for d in member_deltas]
    st = stability_score(member_predictions, prev_predicted, predicted)

    overall = overall_confidence(dq, mp, st)

    version = get_active_model_version(db, "index_formula")
    if version is None:
        ensure_model_versions(db)
        version = get_active_model_version(db, "index_formula")

    for p in db.scalars(select(Prediction).where(Prediction.is_current_cache == True)).all():  # noqa: E712
        p.is_current_cache = False

    prediction = Prediction(
        target_timestamp=to_utc_naive(imd_window_end(target)),
        current_index=current,
        predicted_index=predicted,
        expected_deviation=deviation,
        direction=direction,
        p_increase=probs["Increase"],
        p_no_change=probs["No Change"],
        p_decrease=probs["Decrease"],
        category_current=category_for(current),
        category_predicted=category_for(predicted),
        confidence_overall=overall,
        data_quality=dq,
        model_performance=mp,
        stability_score=st,
        model_version_id=version.id,
        inputs_json={
            "raw_predicted_index": raw_predicted,
            "forecast_rain_mm": fc_rain,
            "lpa_target_mm": lpa_target,
            "member_deltas": member_deltas,
        },
        is_current_cache=True,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction
