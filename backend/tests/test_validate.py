from datetime import datetime, timezone

from app.pipeline.validate import sanitize_point
from app.providers.base import HourlyPoint


def test_sanitize_clamps_invalid_values():
    point = HourlyPoint(
        time=datetime.now(timezone.utc),
        rainfall_mm=9999.0,  # out of range -> None
        temperature_c=25.0,
        humidity_pct=120.0,  # out of range -> None
        pressure_hpa=1010.0,
        wind_kmh=20.0,
    )
    out = sanitize_point(point)
    assert out.rainfall_mm is None
    assert out.humidity_pct is None
    assert out.temperature_c == 25.0
    assert out.pressure_hpa == 1010.0
    assert out.wind_kmh == 20.0


def test_sanitize_keeps_valid_values():
    point = HourlyPoint(
        time=datetime.now(timezone.utc),
        rainfall_mm=10.0,
        temperature_c=25.0,
        humidity_pct=70.0,
        pressure_hpa=1010.0,
        wind_kmh=20.0,
    )
    out = sanitize_point(point)
    assert out.rainfall_mm == 10.0
    assert out.humidity_pct == 70.0
