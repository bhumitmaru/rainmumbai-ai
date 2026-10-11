from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import HourlyPoint, StationSeries, WeatherBundle, WeatherProvider

HOURLY = ",".join(
    [
        "precipitation",
        "temperature_2m",
        "relative_humidity_2m",
        "surface_pressure",
        "wind_speed_10m",
    ]
)
MODELS = ["ecmwf_ifs025", "gfs_seamless", "icon_seamless"]


class OpenMeteoProvider(WeatherProvider):
    name = "open-meteo"

    def __init__(self) -> None:
        self.settings = get_settings()

    def _station_coords(self) -> dict[str, tuple[float, float]]:
        return {
            "colaba": (self.settings.colaba_lat, self.settings.colaba_lon),
            "santacruz": (self.settings.santacruz_lat, self.settings.santacruz_lon),
            "mumbai": (self.settings.mumbai_lat, self.settings.mumbai_lon),
        }

    def fetch_archive(self, station: str, start: str, end: str) -> StationSeries:
        """Hourly rainfall history for a station over an inclusive date range."""
        lat, lon = self._station_coords()[station]
        payload = self._get(
            self.settings.open_meteo_archive_url,
            {
                "latitude": lat,
                "longitude": lon,
                "start_date": start,
                "end_date": end,
                "hourly": "precipitation",
                "timezone": "UTC",
            },
        )
        return self._parse_hourly(
            station, lat, lon, payload, "open-meteo-archive", rainfall_only=True
        )

    def fetch(self) -> WeatherBundle:
        stations: list[StationSeries] = []
        ensemble: list[StationSeries] = []
        coords = self._station_coords()
        for station, (lat, lon) in coords.items():
            payload = self._get(
                self.settings.open_meteo_forecast_url,
                {
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": HOURLY,
                    "forecast_days": 3,
                    "past_days": 7,
                    "timezone": "UTC",
                    "wind_speed_unit": "kmh",
                },
            )
            stations.append(self._parse_hourly(station, lat, lon, payload, "open-meteo-forecast"))

        # Multi-model rainfall at Mumbai for stability (forecast only).
        for model in MODELS:
            try:
                payload = self._get(
                    self.settings.open_meteo_forecast_url,
                    {
                        "latitude": self.settings.mumbai_lat,
                        "longitude": self.settings.mumbai_lon,
                        "hourly": "precipitation",
                        "forecast_days": 3,
                        "timezone": "UTC",
                        "models": model,
                    },
                )
                series = self._parse_hourly(
                    "mumbai",
                    self.settings.mumbai_lat,
                    self.settings.mumbai_lon,
                    payload,
                    f"open-meteo-{model}",
                    model_name=model,
                    rainfall_only=True,
                )
                series.is_forecast = True
                ensemble.append(series)
            except Exception:
                continue

        try:
            ens_payload = self._get(
                self.settings.open_meteo_ensemble_url,
                {
                    "latitude": self.settings.mumbai_lat,
                    "longitude": self.settings.mumbai_lon,
                    "hourly": "precipitation",
                    "forecast_days": 2,
                    "timezone": "UTC",
                },
            )
            ensemble.extend(self._parse_ensemble(ens_payload))
        except Exception:
            pass

        return WeatherBundle(
            stations=stations,
            ensemble_members=ensemble,
            fetched_at=datetime.now(timezone.utc),
            source=self.name,
        )

    def _get(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        timeout = self.settings.open_meteo_timeout_seconds
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def _parse_hourly(
        self,
        station: str,
        lat: float,
        lon: float,
        payload: dict[str, Any],
        source: str,
        model_name: str | None = None,
        rainfall_only: bool = False,
    ) -> StationSeries:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        rain = hourly.get("precipitation") or [None] * len(times)
        temp = hourly.get("temperature_2m") or [None] * len(times)
        hum = hourly.get("relative_humidity_2m") or [None] * len(times)
        pres = hourly.get("surface_pressure") or [None] * len(times)
        wind = hourly.get("wind_speed_10m") or [None] * len(times)
        points: list[HourlyPoint] = []
        for i, stamp in enumerate(times):
            dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            points.append(
                HourlyPoint(
                    time=dt,
                    rainfall_mm=_num(rain[i] if i < len(rain) else None),
                    temperature_c=None if rainfall_only else _num(temp[i] if i < len(temp) else None),
                    humidity_pct=None if rainfall_only else _num(hum[i] if i < len(hum) else None),
                    pressure_hpa=None if rainfall_only else _num(pres[i] if i < len(pres) else None),
                    wind_kmh=None if rainfall_only else _num(wind[i] if i < len(wind) else None),
                    model_name=model_name,
                )
            )
        past_hours = sum(1 for p in points if p.time <= datetime.now(timezone.utc))
        is_forecast = past_hours < len(points)
        return StationSeries(
            station=station,
            latitude=lat,
            longitude=lon,
            points=points,
            source=source,
            is_forecast=is_forecast,
        )

    def _parse_ensemble(self, payload: dict[str, Any]) -> list[StationSeries]:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        series_list: list[StationSeries] = []
        for key, values in hourly.items():
            if not key.startswith("precipitation"):
                continue
            member = "ensemble" if key == "precipitation" else key.replace("precipitation_", "")
            points = []
            for i, stamp in enumerate(times):
                dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                points.append(
                    HourlyPoint(
                        time=dt,
                        rainfall_mm=_num(values[i] if i < len(values) else None),
                        temperature_c=None,
                        humidity_pct=None,
                        pressure_hpa=None,
                        wind_kmh=None,
                        model_name=member,
                    )
                )
            series_list.append(
                StationSeries(
                    station="mumbai",
                    latitude=self.settings.mumbai_lat,
                    longitude=self.settings.mumbai_lon,
                    points=points,
                    source=f"open-meteo-ensemble-{member}",
                    is_forecast=True,
                )
            )
        return series_list


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
