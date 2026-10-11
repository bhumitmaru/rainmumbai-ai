from datetime import datetime

from pydantic import BaseModel


class PerformanceOut(BaseModel):
    mae: float | None
    rmse: float | None
    direction_accuracy: float | None
    direction_f1: float | None
    sample_count: int
    last_evaluated_at: datetime | None
    model_version: str | None
    disclaimer: str
