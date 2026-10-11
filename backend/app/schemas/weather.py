from datetime import datetime

from pydantic import BaseModel


class WeatherCurrentOut(BaseModel):
    station: str
    observed_at: datetime | None
    rainfall_mm: float | None
    temperature_c: float | None
    humidity_pct: float | None
    pressure_hpa: float | None
    wind_kmh: float | None
    source: str
    degraded: bool
    warning: str | None


class HourlyWeather(BaseModel):
    time: datetime
    rainfall_mm: float | None
    temperature_c: float | None
    humidity_pct: float | None
    pressure_hpa: float | None
    wind_kmh: float | None


class RainfallPoint(BaseModel):
    time: datetime
    rainfall_mm: float | None


class WeatherForecastOut(BaseModel):
    current: WeatherCurrentOut
    hourly_rainfall_24h: list[RainfallPoint]
    hourly: list[HourlyWeather]
    generated_at: datetime
    source: str
    degraded: bool
    warning: str | None
