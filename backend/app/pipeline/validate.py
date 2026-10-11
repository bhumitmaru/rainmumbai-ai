from app.core.config import load_index_config
from app.providers.base import HourlyPoint


def in_range(value: float | None, lo: float, hi: float) -> float | None:
    if value is None:
        return None
    if lo <= value <= hi:
        return value
    return None


def sanitize_point(point: HourlyPoint) -> HourlyPoint:
    ranges = load_index_config()["confidence"]["physical_ranges"]
    return HourlyPoint(
        time=point.time,
        rainfall_mm=in_range(point.rainfall_mm, *ranges["rainfall_mm"]),
        temperature_c=in_range(point.temperature_c, *ranges["temperature_c"]),
        humidity_pct=in_range(point.humidity_pct, *ranges["humidity_pct"]),
        pressure_hpa=in_range(point.pressure_hpa, *ranges["pressure_hpa"]),
        wind_kmh=in_range(point.wind_kmh, *ranges["wind_kmh"]),
        model_name=point.model_name,
    )
