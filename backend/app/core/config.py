from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "RainMumbai AI"
    env: str = "development"
    secret_key: str = "change-me-to-a-long-random-string"
    access_token_expire_minutes: int = 60
    refresh_remember_minutes: int = 10080
    database_url: str = "sqlite:///./rainmumbai.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    mumbai_lat: float = 19.0760
    mumbai_lon: float = 72.8777
    colaba_lat: float = 18.9067
    colaba_lon: float = 72.8147
    santacruz_lat: float = 19.0896
    santacruz_lon: float = 72.8656

    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_ensemble_url: str = "https://ensemble-api.open-meteo.com/v1/ensemble"
    open_meteo_archive_url: str = "https://archive-api.open-meteo.com/v1/archive"
    open_meteo_timeout_seconds: int = 20

    index_config_path: str = "config/index.yaml"
    disclaimer: str = (
        "Predictions are probabilistic and based on historical data and current "
        "meteorological conditions. They do not guarantee future outcomes."
    )
    smtp_enabled: bool = False
    reset_token_expire_minutes: int = 30
    scheduler_enabled: bool = True
    hourly_ingest_cron: str = "0 * * * *"
    monthly_eval_cron: str = "0 3 1 * *"

    admin_email: str = "admin@rainmumbai.ai"
    admin_password: str = "change-me-admin"

    season_backfill_days: int = 220
    frontend_url: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def project_root(self) -> Path:
        return ROOT

    @property
    def resolved_index_config(self) -> Path:
        path = Path(self.index_config_path)
        if not path.is_absolute():
            path = ROOT / path
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def load_index_config() -> dict:
    settings = get_settings()
    with settings.resolved_index_config.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)
