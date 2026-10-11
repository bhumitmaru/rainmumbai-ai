"""Performance analytics (MAE/RMSE/accuracy/F1)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.datetime_utils import from_utc_naive
from app.db.models import EvaluationRun
from app.db.seed import get_active_model_version
from app.pipeline.state import load_outcome_pairs
from app.schemas.performance import PerformanceOut
from app.services.metrics import direction_accuracy, direction_f1, mae, rmse


def get_performance(db: Session) -> PerformanceOut:
    settings = get_settings()
    pairs = load_outcome_pairs(db)
    value_pairs = [(p.predicted_index, p.outcome.actual_index) for p in pairs]
    direction_pairs = [(p.direction, p.outcome.actual_direction) for p in pairs]

    last_run = db.scalar(select(EvaluationRun).order_by(EvaluationRun.id.desc()).limit(1))
    version = get_active_model_version(db, "index_formula")

    return PerformanceOut(
        mae=mae(value_pairs),
        rmse=rmse(value_pairs),
        direction_accuracy=direction_accuracy(direction_pairs),
        direction_f1=direction_f1(direction_pairs),
        sample_count=len(pairs),
        last_evaluated_at=from_utc_naive(last_run.finished_at) if last_run is not None else None,
        model_version=version.version if version is not None else None,
        disclaimer=settings.disclaimer,
    )
