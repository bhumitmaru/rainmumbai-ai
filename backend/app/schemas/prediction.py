from datetime import datetime

from pydantic import BaseModel


class DirectionProbabilities(BaseModel):
    increase: float
    no_change: float
    decrease: float


class ConfidenceBreakdown(BaseModel):
    overall: float
    data_quality: float
    model_performance: float
    stability: float


class PredictionOut(BaseModel):
    id: int
    generated_at: datetime
    target_timestamp: datetime
    current_index: float
    predicted_index: float
    expected_deviation: float
    direction: str
    probabilities: DirectionProbabilities
    category_current: str
    category_predicted: str
    confidence: ConfidenceBreakdown
    model_version: str
    disclaimer: str


class HistoryItem(BaseModel):
    id: int
    generated_at: datetime
    target_timestamp: datetime
    current_index: float
    predicted_index: float
    actual_index: float | None
    expected_deviation: float
    direction: str
    actual_direction: str | None
    confidence_overall: float
    model_version: str
    source: str


class PredictionHistoryOut(BaseModel):
    items: list[HistoryItem]
    total: int
    limit: int
    offset: int
