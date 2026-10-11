"""Read-side prediction services (latest + history)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.datetime_utils import from_utc_naive
from app.db.models import Prediction
from app.schemas.prediction import (
    ConfidenceBreakdown,
    DirectionProbabilities,
    HistoryItem,
    PredictionHistoryOut,
    PredictionOut,
)


def _version(pred: Prediction) -> str:
    return pred.model_version.version if pred.model_version is not None else "unknown"


def serialize_prediction(pred: Prediction) -> PredictionOut:
    settings = get_settings()
    return PredictionOut(
        id=pred.id,
        generated_at=from_utc_naive(pred.generated_at),
        target_timestamp=from_utc_naive(pred.target_timestamp),
        current_index=pred.current_index,
        predicted_index=pred.predicted_index,
        expected_deviation=pred.expected_deviation,
        direction=pred.direction,
        probabilities=DirectionProbabilities(
            increase=pred.p_increase,
            no_change=pred.p_no_change,
            decrease=pred.p_decrease,
        ),
        category_current=pred.category_current,
        category_predicted=pred.category_predicted,
        confidence=ConfidenceBreakdown(
            overall=pred.confidence_overall,
            data_quality=pred.data_quality,
            model_performance=pred.model_performance,
            stability=pred.stability_score,
        ),
        model_version=_version(pred),
        disclaimer=settings.disclaimer,
    )


def get_latest_prediction(db: Session) -> Prediction | None:
    pred = db.scalar(
        select(Prediction)
        .where(Prediction.is_current_cache == True)  # noqa: E712
        .order_by(Prediction.id.desc())
        .limit(1)
    )
    if pred is None:
        pred = db.scalar(select(Prediction).order_by(Prediction.id.desc()).limit(1))
    return pred


def _history_item(pred: Prediction) -> HistoryItem:
    outcome = pred.outcome
    return HistoryItem(
        id=pred.id,
        generated_at=from_utc_naive(pred.generated_at),
        target_timestamp=from_utc_naive(pred.target_timestamp),
        current_index=pred.current_index,
        predicted_index=pred.predicted_index,
        actual_index=outcome.actual_index if outcome is not None else None,
        expected_deviation=pred.expected_deviation,
        direction=pred.direction,
        actual_direction=outcome.actual_direction if outcome is not None else None,
        confidence_overall=pred.confidence_overall,
        model_version=_version(pred),
    )


def list_predictions(db: Session, limit: int = 50, offset: int = 0) -> PredictionHistoryOut:
    total = db.scalar(select(func.count()).select_from(Prediction)) or 0
    rows = db.scalars(
        select(Prediction).order_by(Prediction.id.desc()).offset(offset).limit(limit)
    ).all()
    return PredictionHistoryOut(
        items=[_history_item(p) for p in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
