from functools import lru_cache
import secrets
from pathlib import Path

import yaml
from pydantic import Field, field_validator
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
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
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
    open_meteo_historical_forecast_url: str = "https://historical-forecast-api.open-meteo.com/v1/forecast"
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
    admin_password: str = Field(default_factory=lambda: secrets.token_urlsafe(24))

    season_backfill_days: int = 220
    frontend_url: str = "http://localhost:5173"

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        cleaned = [origin.strip() for origin in value.split(",") if origin.strip()]
        if not cleaned:
            raise ValueError("CORS_ORIGINS must contain at least one explicit origin.")
        if any(origin == "*" for origin in cleaned):
            raise ValueError("CORS_ORIGINS must not contain a wildcard origin.")
        return ",".join(cleaned)

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        weak_defaults = {
            "change-me-to-a-long-random-string",
            "secret",
            "dev-secret",
            "test-secret",
            "default-secret-key",
        }
        if value.lower() in weak_defaults:
            raise ValueError("SECRET_KEY must be set to a strong random value in production.")
        if len(value) < 32:
            raise ValueError("SECRET_KEY must contain at least 32 characters.")
        return value

    @field_validator("admin_password")
    @classmethod
    def validate_admin_password(cls, value: str) -> str:
        weak_defaults = {"change-me-admin", "admin", "password", "admin123"}
        if value.lower() in weak_defaults:
            raise ValueError("ADMIN_PASSWORD must be set to a strong password in production.")
        if len(value) < 12:
            raise ValueError("ADMIN_PASSWORD must contain at least 12 characters.")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

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
