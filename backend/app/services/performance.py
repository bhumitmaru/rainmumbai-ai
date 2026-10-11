"""Performance analytics (MAE/RMSE/accuracy/F1)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.datetime_utils import from_utc_naive, to_utc_naive
from app.db.models import EvaluationRun
from app.db.seed import get_active_model_version
from app.pipeline.state import load_outcome_pairs
from app.schemas.performance import (
    BaselineMetrics,
    EvaluationSnapshot,
    PerformanceOut,
    PerformanceSample,
    PerformanceSeriesPoint,
)
from app.services.metrics import direction_accuracy, direction_f1, mae, rmse


def _sample_count(run: EvaluationRun) -> int | None:
    if isinstance(run.metrics_json, dict) and run.metrics_json.get("sample_count") is not None:
        return int(run.metrics_json["sample_count"])
    return None


def get_performance(
    db: Session,
    *,
    from_timestamp: datetime | None = None,
    to_timestamp: datetime | None = None,
    source: str = "all",
    limit: int = 200,
    offset: int = 0,
) -> PerformanceOut:
    settings = get_settings()
    pairs = load_outcome_pairs(
        db,
        source=source,
        from_timestamp=to_utc_naive(from_timestamp) if from_timestamp is not None else None,
        to_timestamp=to_utc_naive(to_timestamp) if to_timestamp is not None else None,
    )
    value_pairs = [(p.predicted_index, p.outcome.actual_index) for p in pairs if p.outcome is not None]
    direction_pairs = [(p.direction, p.outcome.actual_direction) for p in pairs if p.outcome is not None]
    baseline_value_pairs = [(p.current_index, p.outcome.actual_index) for p in pairs if p.outcome is not None]
    baseline_direction_pairs = [("No Change", p.outcome.actual_direction) for p in pairs if p.outcome is not None]

    runs = db.scalars(select(EvaluationRun).order_by(EvaluationRun.id.asc())).all()
    last_run = runs[-1] if runs else None
    version = get_active_model_version(db, "index_formula")

    all_samples = [
        PerformanceSample(
            prediction_id=p.id,
            target_timestamp=from_utc_naive(p.target_timestamp),
            predicted_index=p.predicted_index,
            actual_index=p.outcome.actual_index,
            error=round(p.predicted_index - p.outcome.actual_index, 4),
            abs_error=round(abs(p.predicted_index - p.outcome.actual_index), 4),
            direction=p.direction,
            actual_direction=p.outcome.actual_direction,
            direction_correct=p.direction == p.outcome.actual_direction,
            source=p.source,
        )
        for p in pairs
        if p.outcome is not None
    ]
    samples = all_samples[offset : offset + limit]

    error_series = [
        PerformanceSeriesPoint(target_timestamp=s.target_timestamp, value=s.error) for s in all_samples
    ]
    cum: list[PerformanceSeriesPoint] = []
    hits = 0
    for idx, s in enumerate(all_samples):
        if s.direction_correct:
            hits += 1
        cum.append(
            PerformanceSeriesPoint(
                target_timestamp=s.target_timestamp,
                value=round((hits / (idx + 1)) * 100.0, 2),
            )
        )

    return PerformanceOut(
        mae=mae(value_pairs),
        rmse=rmse(value_pairs),
        direction_accuracy=direction_accuracy(direction_pairs),
        direction_f1=direction_f1(direction_pairs),
        sample_count=len(all_samples),
        sample_total=len(all_samples),
        last_evaluated_at=from_utc_naive(last_run.finished_at) if last_run is not None else None,
        model_version=version.version if version is not None else None,
        disclaimer=settings.disclaimer,
        baseline=BaselineMetrics(
            label="Persistence (No Change / predicted deviation = 0)",
            mae=mae(baseline_value_pairs),
            direction_accuracy=direction_accuracy(baseline_direction_pairs),
        ),
        evaluated_from=all_samples[0].target_timestamp if all_samples else None,
        evaluated_to=all_samples[-1].target_timestamp if all_samples else None,
        error_series=error_series,
        cumulative_accuracy_series=cum,
        limit=limit,
        offset=offset,
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
