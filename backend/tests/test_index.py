from datetime import date

from app.index.service import (
    category_for,
    direction_from_delta,
    next_spot,
    reconstruct_spot_series,
    season_start_for,
)


def test_direction_from_delta():
    assert direction_from_delta(5.0) == "Increase"
    assert direction_from_delta(-5.0) == "Decrease"
    assert direction_from_delta(0.5) == "No Change"


def test_category_for():
    # anchor 2206.7, +/- 50 => Moderate between 2156.7 and 2256.7
    assert category_for(2100.0) == "Low"
    assert category_for(2200.0) == "Moderate"
    assert category_for(2300.0) == "High"


def test_next_spot_reset():
    # On reset date, base becomes the season anchor regardless of previous.
    spot = next_spot(3000.0, 10.0, 5.0, date(2026, 6, 1))
    assert spot == round(2206.7 + (10.0 - 5.0), 4)


def test_next_spot_accumulates():
    prev = next_spot(2206.7, 10.0, 5.0, date(2026, 6, 2))
    assert prev == round(2206.7 + 5.0, 4)
    nxt = next_spot(prev, 8.0, 5.0, date(2026, 6, 3))
    assert nxt == round(prev + 3.0, 4)


def test_season_start_for():
    assert season_start_for(date(2026, 10, 5)) == date(2026, 6, 1)
    assert season_start_for(date(2026, 1, 15)) == date(2025, 6, 1)


def test_reconstruct_spot_series_missing_uses_lpa():
    daily_rain = {date(2026, 6, 1): 20.0}
    daily_lpa = {date(2026, 6, 1): 5.0, date(2026, 6, 2): 5.0}
    spots = reconstruct_spot_series(daily_rain, daily_lpa, date(2026, 6, 1), date(2026, 6, 2))
    assert spots[date(2026, 6, 1)] == round(2206.7 + 15.0, 4)
    # June 2 has no rain -> uses LPA (zero deviation), spot unchanged.
    assert spots[date(2026, 6, 2)] == spots[date(2026, 6, 1)]


def test_reconstruct_spot_series_june_reset_sequence():
    start = date(2026, 5, 31)
    end = date(2026, 6, 2)
    daily_rain = {
        date(2026, 5, 31): 12.0,  # +2 on prior season path
        date(2026, 6, 1): 30.0,  # reset day: anchor + (30-10)
        date(2026, 6, 2): 7.0,  # next day: prior + (7-10)
    }
    daily_lpa = {
        date(2026, 5, 31): 10.0,
        date(2026, 6, 1): 10.0,
        date(2026, 6, 2): 10.0,
    }
    spots = reconstruct_spot_series(daily_rain, daily_lpa, start, end)
    assert spots[date(2026, 5, 31)] == 2208.7
    assert spots[date(2026, 6, 1)] == 2226.7
    assert spots[date(2026, 6, 2)] == 2223.7
