"""Performance analytics (MAE/RMSE/accuracy/F1)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.datetime_utils import from_utc_naive
from app.db.models import EvaluationRun
from app.db.seed import get_active_model_version
from app.pipeline.state import load_outcome_pairs
from app.schemas.performance import EvaluationSnapshot, PerformanceOut, PerformanceSample
from app.services.metrics import direction_accuracy, direction_f1, mae, rmse


def _sample_count(run: EvaluationRun) -> int | None:
    if isinstance(run.metrics_json, dict) and run.metrics_json.get("sample_count") is not None:
        return int(run.metrics_json["sample_count"])
    return None


def get_performance(db: Session) -> PerformanceOut:
    settings = get_settings()
    pairs = load_outcome_pairs(db)
    value_pairs = [(p.predicted_index, p.outcome.actual_index) for p in pairs]
    direction_pairs = [(p.direction, p.outcome.actual_direction) for p in pairs]

    runs = db.scalars(select(EvaluationRun).order_by(EvaluationRun.id.asc())).all()
    last_run = runs[-1] if runs else None
    version = get_active_model_version(db, "index_formula")

    samples = [
        PerformanceSample(
            target_timestamp=from_utc_naive(p.target_timestamp),
            predicted_index=p.predicted_index,
            actual_index=p.outcome.actual_index,
            error=round(p.predicted_index - p.outcome.actual_index, 4),
            abs_error=round(abs(p.predicted_index - p.outcome.actual_index), 4),
            direction=p.direction,
            actual_direction=p.outcome.actual_direction,
            direction_correct=p.direction == p.outcome.actual_direction,
        )
        for p in pairs
        if p.outcome is not None
    ]

    return PerformanceOut(
        mae=mae(value_pairs),
        rmse=rmse(value_pairs),
        direction_accuracy=direction_accuracy(direction_pairs),
        direction_f1=direction_f1(direction_pairs),
        sample_count=len(pairs),
        last_evaluated_at=from_utc_naive(last_run.finished_at) if last_run is not None else None,
        model_version=version.version if version is not None else None,
        disclaimer=settings.disclaimer,
        evaluation_runs=[
            EvaluationSnapshot(
                id=run.id,
                finished_at=from_utc_naive(run.finished_at),
                status=run.status,
                mae=run.mae,
                rmse=run.rmse,
                direction_accuracy=run.direction_accuracy,
                direction_f1=run.direction_f1,
                sample_count=_sample_count(run),
                promoted=run.promoted,
                notes=run.notes,
            )
            for run in runs
        ],
        samples=samples,
    )
