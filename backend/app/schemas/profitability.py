from datetime import datetime

from pydantic import BaseModel


class TradeOut(BaseModel):
    target_timestamp: datetime
    direction: str
    current_index: float
    actual_index: float
    realized_delta: float
    pnl_inr: float
    source: str


class ProfitabilityOut(BaseModel):
    decision_rule: str
    lots: int
    inr_per_mm: float
    trades: list[TradeOut]
    total_pnl_inr: float
    trade_count: int
    win_rate_pct: float
    disclaimer: str
