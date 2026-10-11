import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MeteoObservation
from app.providers.base import HourlyPoint, StationSeries, WeatherBundle, WeatherProvider

logger = logging.getLogger(__name__)


class CachedFallbackProvider(WeatherProvider):
    """Live provider with database fallback when the weather API is down."""

    name = "cached-fallback"

    def __init__(self, live: WeatherProvider, db: Session) -> None:
        self.live = live
        self.db = db

    def fetch(self) -> WeatherBundle:
        try:
            bundle = self.live.fetch()
            if bundle.stations and any(s.points for s in bundle.stations):
                return bundle
            raise RuntimeError("Empty weather payload")
        except Exception as exc:
            logger.warning("Weather provider failed (%s); using cached observations", exc)
            return self._from_db(str(exc))

    def _from_db(self, reason: str) -> WeatherBundle:
        stations: list[StationSeries] = []
        for station in ("colaba", "santacruz", "mumbai"):
            rows = self.db.scalars(
                select(MeteoObservation)
                .where(MeteoObservation.station == station)
                .order_by(MeteoObservation.observed_at.desc())
                .limit(240)
            ).all()
            points = [
                HourlyPoint(
                    time=row.observed_at,
                    rainfall_mm=row.rainfall_mm,
                    temperature_c=row.temperature_c,
                    humidity_pct=row.humidity_pct,
                    pressure_hpa=row.pressure_hpa,
                    wind_kmh=row.wind_kmh,
                    model_name=row.model_name,
                )
                for row in reversed(rows)
            ]
            stations.append(
                StationSeries(
                    station=station,
                    latitude=0,
                    longitude=0,
                    points=points,
                    source="database-cache",
                    is_forecast=False,
                )
            )
        return WeatherBundle(
            stations=stations,
            ensemble_members=[],
            fetched_at=datetime.now(timezone.utc),
            source="database-cache",
            degraded=True,
            warning=f"Live weather API unavailable ({reason}). Showing cached observations.",
        )
