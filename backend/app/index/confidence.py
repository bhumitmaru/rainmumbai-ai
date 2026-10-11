from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import load_index_config
from app.index.service import direction_from_delta
from app.providers.base import HourlyPoint, StationSeries


def clip(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def data_quality_score(
    points: list[HourlyPoint],
    now: datetime | None = None,
) -> float:
    cfg = load_index_config()["confidence"]
    ranges = cfg["physical_ranges"]
    now = now or datetime.now(timezone.utc)
    if not points:
        return 20.0

    expected = 24
    recent = [
        p
        for p in points
        if now - timedelta(hours=36) <= p.time <= now + timedelta(hours=1)
    ]
    completeness = 100.0 * min(len(recent), expected) / expected if expected else 0.0

    latest = max((p.time for p in points), default=None)
    if latest is None:
        freshness = 0.0
    else:
        age_h = (now - latest.astimezone(timezone.utc)).total_seconds() / 3600.0
        ok = float(cfg["freshness_hours_ok"])
        stale = float(cfg["freshness_hours_stale"])
        if age_h <= ok:
            freshness = 100.0
        elif age_h >= stale:
            freshness = 25.0
        else:
            freshness = 100.0 - 75.0 * (age_h - ok) / (stale - ok)

    checks = 0
    valid = 0
    mapping = [
        ("rainfall_mm", "rainfall_mm"),
        ("temperature_c", "temperature_c"),
        ("humidity_pct", "humidity_pct"),
        ("pressure_hpa", "pressure_hpa"),
        ("wind_kmh", "wind_kmh"),
    ]
    for point in recent or points[-24:]:
        for attr, key in mapping:
            value = getattr(point, attr)
            if value is None:
                checks += 1
                continue
            lo, hi = ranges[key]
            checks += 1
            if lo <= value <= hi:
                valid += 1
    validity = 100.0 * valid / checks if checks else 50.0
    return round(clip(0.4 * completeness + 0.35 * freshness + 0.25 * validity), 2)


def model_performance_score(mae: float | None, direction_accuracy: float | None) -> float:
    if mae is None and direction_accuracy is None:
        return 55.0
    mae_score = 100.0 if mae is None else clip(100.0 - 2.0 * mae)
    acc_score = 55.0 if direction_accuracy is None else clip(100.0 * direction_accuracy)
    return round(clip(0.5 * mae_score + 0.5 * acc_score), 2)


def stability_score(
    member_predictions: list[float],
    previous_prediction: float | None,
    current_prediction: float,
) -> float:
    if len(member_predictions) >= 2:
        mean = sum(member_predictions) / len(member_predictions)
        var = sum((x - mean) ** 2 for x in member_predictions) / len(member_predictions)
        spread = var**0.5
        spread_score = clip(100.0 - 4.0 * spread)
    else:
        spread_score = 50.0
    if previous_prediction is None:
        change_score = 70.0
    else:
        change = abs(current_prediction - previous_prediction)
        change_score = clip(100.0 - 5.0 * change)
    return round(clip(0.6 * spread_score + 0.4 * change_score), 2)


def overall_confidence(dq: float, mp: float, st: float) -> float:
    w = load_index_config()["confidence"]["overall_weights"]
    return round(
        clip(w["data_quality"] * dq + w["model_performance"] * mp + w["stability"] * st),
        2,
    )


def direction_probabilities(member_deltas: list[float]) -> dict[str, float]:
    if not member_deltas:
        return {"Increase": 33.34, "No Change": 33.33, "Decrease": 33.33}
    counts = {"Increase": 0, "No Change": 0, "Decrease": 0}
    for delta in member_deltas:
        counts[direction_from_delta(delta)] += 1
    n = len(member_deltas)
    raw = {k: 100.0 * v / n for k, v in counts.items()}
    # Snap to 100.00
    total = sum(raw.values())
    if total <= 0:
        return {"Increase": 33.34, "No Change": 33.33, "Decrease": 33.33}
    scaled = {k: round(v * 100.0 / total, 2) for k, v in raw.items()}
    drift = round(100.0 - sum(scaled.values()), 2)
    scaled["No Change"] = round(scaled["No Change"] + drift, 2)
    return scaled


def mumbai_points(stations: list[StationSeries]) -> list[HourlyPoint]:
    for series in stations:
        if series.station == "mumbai" and series.points:
            return series.points
    merged: list[HourlyPoint] = []
    for series in stations:
        merged.extend(series.points)
    return merged
