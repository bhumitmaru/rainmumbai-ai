from datetime import date, timedelta

from app.index.service import imd_window, month_day_key, sum_rainfall
from app.providers.base import HourlyPoint, StationSeries


def hourly_pairs(points: list[HourlyPoint]) -> list[tuple]:
    return [(p.time, p.rainfall_mm) for p in points]


def daily_rainfall_for_series(series: StationSeries, start: date, end: date) -> dict[date, float]:
    out: dict[date, float] = {}
    pairs = hourly_pairs(series.points)
    d = start
    while d <= end:
        win_start, win_end = imd_window(d)
        total = sum_rainfall(pairs, win_start, win_end)
        if total is not None:
            out[d] = total
        d += timedelta(days=1)
    return out


def average_station_daily(
    colaba: dict[date, float],
    santacruz: dict[date, float],
) -> dict[date, float]:
    keys = set(colaba) | set(santacruz)
    averaged: dict[date, float] = {}
    for d in keys:
        if d in colaba and d in santacruz:
            averaged[d] = round((colaba[d] + santacruz[d]) / 2.0, 4)
        elif d in colaba:
            averaged[d] = colaba[d]
        else:
            averaged[d] = santacruz[d]
    return averaged


def lpa_lookup(lpa_rows: dict[tuple[str, str], float], station: str, d: date) -> float:
    key = (station, month_day_key(d))
    if key in lpa_rows:
        return lpa_rows[key]
    feb28 = (station, "02-28")
    if d.month == 2 and d.day == 29 and feb28 in lpa_rows:
        return lpa_rows[feb28]
    mumbai = ("mumbai", month_day_key(d))
    return lpa_rows.get(mumbai, 0.0)
