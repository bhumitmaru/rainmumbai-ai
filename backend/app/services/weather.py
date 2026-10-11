"""Read-side weather services (current conditions + forecast)."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import from_utc_naive, utcnow
from app.db.models import IngestionStatus, MeteoObservation
from app.schemas.weather import (
    HourlyWeather,
    RainfallPoint,
    WeatherCurrentOut,
    WeatherForecastOut,
)

MAIN_SOURCE = "open-meteo-forecast"


def _ingestion_degraded(db: Session) -> tuple[bool, str | None]:
    status = db.scalar(select(IngestionStatus).where(IngestionStatus.provider == "open-meteo"))
    if status is not None and status.last_error_at is not None:
        return True, status.last_error or "Live weather unavailable; showing stored data."
    return False, None


def get_current_weather(db: Session) -> WeatherCurrentOut:
    row = db.scalar(
        select(MeteoObservation)
        .where(
            MeteoObservation.station == "mumbai",
            MeteoObservation.is_forecast == False,  # noqa: E712
        )
        .order_by(MeteoObservation.observed_at.desc())
        .limit(1)
    )
    if row is None:
        row = db.scalar(
            select(MeteoObservation)
            .where(MeteoObservation.station == "mumbai")
            .order_by(MeteoObservation.observed_at.desc())
            .limit(1)
        )
    degraded, warning = _ingestion_degraded(db)
    return WeatherCurrentOut(
        station="mumbai",
        observed_at=from_utc_naive(row.observed_at) if row is not None else None,
        rainfall_mm=row.rainfall_mm if row is not None else None,
        temperature_c=row.temperature_c if row is not None else None,
        humidity_pct=row.humidity_pct if row is not None else None,
        pressure_hpa=row.pressure_hpa if row is not None else None,
        wind_kmh=row.wind_kmh if row is not None else None,
        source=row.source if row is not None else "none",
        degraded=degraded,
        warning=warning,
    )


def get_forecast(db: Session) -> WeatherForecastOut:
    now = utcnow()
    rows = db.scalars(
        select(MeteoObservation)
        .where(
            MeteoObservation.station == "mumbai",
            MeteoObservation.source == MAIN_SOURCE,
            MeteoObservation.is_forecast == True,  # noqa: E712
            MeteoObservation.observed_at >= now - timedelta(hours=1),
        )
        .order_by(MeteoObservation.observed_at.asc())
        .limit(48)
    ).all()

    hourly = [
        HourlyWeather(
            time=from_utc_naive(r.observed_at),
            rainfall_mm=r.rainfall_mm,
            temperature_c=r.temperature_c,
            humidity_pct=r.humidity_pct,
            pressure_hpa=r.pressure_hpa,
            wind_kmh=r.wind_kmh,
        )
        for r in rows
    ]
    cutoff = now + timedelta(hours=24)
    rain24 = [
        RainfallPoint(time=from_utc_naive(r.observed_at), rainfall_mm=r.rainfall_mm)
        for r in rows
        if r.observed_at < cutoff
    ]

    current = get_current_weather(db)
    return WeatherForecastOut(
        current=current,
        hourly_rainfall_24h=rain24,
        hourly=hourly,
        generated_at=from_utc_naive(now),
        source=rows[0].source if rows else "none",
        degraded=current.degraded,
        warning=current.warning,
    )
