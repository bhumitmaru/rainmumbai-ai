from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    contact_number: Mapped[str] = mapped_column(String(10), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(back_populates="user")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="reset_tokens")


class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MeteoObservation(Base):
    __tablename__ = "meteo_observations"
    __table_args__ = (
        UniqueConstraint(
            "station", "observed_at", "source", "is_forecast", name="uq_obs_station_time_source"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    rainfall_mm: Mapped[float | None] = mapped_column(Float)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    humidity_pct: Mapped[float | None] = mapped_column(Float)
    pressure_hpa: Mapped[float | None] = mapped_column(Float)
    wind_kmh: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(60), default="open-meteo", nullable=False)
    is_forecast: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(80))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DailyLPA(Base):
    __tablename__ = "daily_lpa"
    __table_args__ = (UniqueConstraint("month_day", "station", name="uq_lpa_day_station"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month_day: Mapped[str] = mapped_column(String(5), nullable=False)  # MM-DD
    station: Mapped[str] = mapped_column(String(40), nullable=False)
    lpa_mm: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(80), default="climatology-seed")


class DailyRainfall(Base):
    """IMD-day (08:30–08:30 IST) aggregated rainfall, used for CDR spot."""

    __tablename__ = "daily_rainfall"
    __table_args__ = (UniqueConstraint("station", "imd_date", name="uq_daily_rain_station_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    imd_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    rainfall_mm: Mapped[float] = mapped_column(Float, nullable=False)
    is_forecast: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(60), default="open-meteo")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)  # index_formula | calibration
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    config_json: Mapped[dict | None] = mapped_column(JSON)
    metrics_json: Mapped[dict | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    predictions: Mapped[list["Prediction"]] = relationship(back_populates="model_version")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    target_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    current_index: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_index: Mapped[float] = mapped_column(Float, nullable=False)
    expected_deviation: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    p_increase: Mapped[float] = mapped_column(Float, nullable=False)
    p_no_change: Mapped[float] = mapped_column(Float, nullable=False)
    p_decrease: Mapped[float] = mapped_column(Float, nullable=False)
    category_current: Mapped[str] = mapped_column(String(20), nullable=False)
    category_predicted: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_overall: Mapped[float] = mapped_column(Float, nullable=False)
    data_quality: Mapped[float] = mapped_column(Float, nullable=False)
    model_performance: Mapped[float] = mapped_column(Float, nullable=False)
    stability_score: Mapped[float] = mapped_column(Float, nullable=False)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"), nullable=False)
    inputs_json: Mapped[dict | None] = mapped_column(JSON)
    is_current_cache: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    model_version: Mapped[ModelVersion] = relationship(back_populates="predictions")
    outcome: Mapped["Outcome | None"] = relationship(back_populates="prediction", uselist=False)


class Outcome(Base):
    __tablename__ = "outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), unique=True)
    actual_index: Mapped[float] = mapped_column(Float, nullable=False)
    actual_direction: Mapped[str] = mapped_column(String(20), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prediction: Mapped[Prediction] = relationship(back_populates="outcome")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="running")
    mae: Mapped[float | None] = mapped_column(Float)
    rmse: Mapped[float | None] = mapped_column(Float)
    direction_accuracy: Mapped[float | None] = mapped_column(Float)
    direction_f1: Mapped[float | None] = mapped_column(Float)
    promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    candidate_version: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)
    metrics_json: Mapped[dict | None] = mapped_column(JSON)


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_name: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="running")
    message: Mapped[str | None] = mapped_column(Text)


class IngestionStatus(Base):
    __tablename__ = "ingestion_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    last_source: Mapped[str | None] = mapped_column(String(80))
    records_last_run: Mapped[int] = mapped_column(Integer, default=0)
