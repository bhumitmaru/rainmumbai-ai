"""NCDEX RAINMUMBAI Cumulative Deviation Rainfall (CDR) spot.

Official recurrence (NCDEX spot methodology):

    Rain_Mumbai(d) = (Rain_Colaba(d) + Rain_Santacruz(d)) / 2
    LPA_Mumbai(d)  = (LPA_Colaba(d)  + LPA_Santacruz(d))  / 2
    DailyDeviation(d) = Rain_Mumbai(d) - LPA_Mumbai(d)
    Anchor (before 1 June) = 2206.7 mm  (Mumbai monsoon season LPA)
    Spot(d) = Spot(d-1) + DailyDeviation(d)
    On 1 June each year Spot is reset to the anchor, then that day's deviation is added.

Rainfall day d is the 24 hours ending 08:30 IST on date d.

This module is the only place the formula lives. Weights/thresholds are in
config/index.yaml. There is no off-season freeze: the same recurrence is applied
every calendar day.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.config import load_index_config

IST = ZoneInfo("Asia/Kolkata")


def index_config() -> dict:
    return load_index_config()


def imd_window_end(imd_date: date) -> datetime:
    cfg = index_config()
    return datetime.combine(
        imd_date,
        time(int(cfg["imd_day_end_hour_ist"]), int(cfg["imd_day_end_minute_ist"])),
        tzinfo=IST,
    )


def imd_window(imd_date: date) -> tuple[datetime, datetime]:
    end = imd_window_end(imd_date)
    return end - timedelta(hours=24), end


def latest_completed_imd_date(now: datetime | None = None) -> date:
    now = now.astimezone(IST) if now else datetime.now(IST)
    end_today = imd_window_end(now.date())
    if now >= end_today:
        return now.date()
    return now.date() - timedelta(days=1)


def next_imd_date(now: datetime | None = None) -> date:
    return latest_completed_imd_date(now) + timedelta(days=1)


def month_day_key(d: date) -> str:
    return f"{d.month:02d}-{d.day:02d}"


def is_reset_date(d: date) -> bool:
    cfg = index_config()
    return d.month == int(cfg["reset_month"]) and d.day == int(cfg["reset_day"])


def season_start_for(d: date) -> date:
    """Most recent 1 June on or before date d (season anchor reset)."""
    cfg = index_config()
    reset = date(d.year, int(cfg["reset_month"]), int(cfg["reset_day"]))
    return reset if d >= reset else reset.replace(year=d.year - 1)


def daily_deviation(rainfall_mm: float, lpa_mm: float) -> float:
    return float(rainfall_mm) - float(lpa_mm)


def next_spot(previous_spot: float | None, rainfall_mm: float, lpa_mm: float, d: date) -> float:
    cfg = index_config()
    anchor = float(cfg["season_lpa_anchor_mm"])
    base = anchor if is_reset_date(d) or previous_spot is None else float(previous_spot)
    return round(base + daily_deviation(rainfall_mm, lpa_mm), 4)


def category_for(index_value: float) -> str:
    cfg = index_config()
    anchor = float(cfg["season_lpa_anchor_mm"])
    low_delta = float(cfg["category"]["low_below_anchor_mm"])
    high_delta = float(cfg["category"]["high_above_anchor_mm"])
    labels = cfg["category"]["labels"]
    if index_value < anchor - low_delta:
        return labels["low"]
    if index_value > anchor + high_delta:
        return labels["high"]
    return labels["moderate"]


def apply_calibration(raw_index: float, slope: float, intercept: float, enabled: bool) -> float:
    if not enabled:
        return raw_index
    return round(slope * raw_index + intercept, 4)


def direction_from_delta(delta: float) -> str:
    thresh = float(index_config()["no_change_threshold_mm"])
    if delta > thresh:
        return "Increase"
    if delta < -thresh:
        return "Decrease"
    return "No Change"


def sum_rainfall(points: list[tuple[datetime, float | None]], start: datetime, end: datetime) -> float | None:
    """Sum rainfall in [start, end). Missing hours => None if nothing present."""
    total = 0.0
    counted = 0
    for ts, value in points:
        ts = ts.astimezone(IST) if ts.tzinfo else ts.replace(tzinfo=IST)
        if start <= ts < end and value is not None:
            total += float(value)
            counted += 1
    if counted == 0:
        return None
    return round(total, 4)


def reconstruct_spot_series(
    daily_rain: dict[date, float],
    daily_lpa: dict[date, float],
    start: date,
    end: date,
) -> dict[date, float]:
    """Inclusive [start, end] CDR path. Missing rain uses LPA (zero deviation)."""
    spots: dict[date, float] = {}
    prev: float | None = None
    d = start
    while d <= end:
        lpa = daily_lpa.get(d, daily_lpa.get(_clamp_leap(d), 0.0))
        rain = daily_rain.get(d, lpa)
        prev = next_spot(prev, rain, lpa, d)
        spots[d] = prev
        d += timedelta(days=1)
    return spots


def _clamp_leap(d: date) -> date:
    if d.month == 2 and d.day == 29:
        return date(d.year, 2, 28)
    return d
