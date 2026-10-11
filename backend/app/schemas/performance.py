from datetime import datetime

from pydantic import BaseModel


class EvaluationSnapshot(BaseModel):
    id: int
    finished_at: datetime | None
    status: str
    mae: float | None
    rmse: float | None
    direction_accuracy: float | None
    direction_f1: float | None
    sample_count: int | None
    promoted: bool
    notes: str | None


class PerformanceSample(BaseModel):
    target_timestamp: datetime
    predicted_index: float
    actual_index: float
    error: float
    abs_error: float
    direction: str
    actual_direction: str
    direction_correct: bool


class PerformanceOut(BaseModel):
    mae: float | None
    rmse: float | None
    direction_accuracy: float | None
    direction_f1: float | None
    sample_count: int
    last_evaluated_at: datetime | None
    model_version: str | None
    disclaimer: str
    evaluation_runs: list[EvaluationSnapshot]
    samples: list[PerformanceSample]
