from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class HourlyPoint:
    time: datetime
    rainfall_mm: float | None
    temperature_c: float | None
    humidity_pct: float | None
    pressure_hpa: float | None
    wind_kmh: float | None
    model_name: str | None = None


@dataclass
class StationSeries:
    station: str
    latitude: float
    longitude: float
    points: list[HourlyPoint] = field(default_factory=list)
    source: str = "open-meteo"
    is_forecast: bool = True


@dataclass
class WeatherBundle:
    stations: list[StationSeries]
    ensemble_members: list[StationSeries]
    fetched_at: datetime
    source: str
    degraded: bool = False
    warning: str | None = None


class WeatherProvider(ABC):
    """Swap-in weather source. Implementations must not train a model."""

    name: str

    @abstractmethod
    def fetch(self) -> WeatherBundle:
        raise NotImplementedError
