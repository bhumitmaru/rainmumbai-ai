"""Rule-based historical profitability.

Decision rule (documented in config/index.yaml): a directional position is
taken for each matured prediction — Increase -> long, Decrease -> short,
No Change -> flat. P&L = position * lots * inr_per_mm * realized index change.
Past performance is explicitly not a guarantee of future results.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings, load_index_config
from app.core.datetime_utils import from_utc_naive
from app.pipeline.state import load_outcome_pairs
from app.schemas.profitability import ProfitabilityOut, TradeOut

_POSITION = {"Increase": 1, "Decrease": -1, "No Change": 0}


def get_profitability(db: Session) -> ProfitabilityOut:
    settings = get_settings()
    cfg = load_index_config()
    profit_cfg = cfg.get("profit", {}) or {}
    lots = int(profit_cfg.get("lots", 1))
    inr_per_mm = float(profit_cfg.get("inr_per_mm", 50.0))
    decision = str(profit_cfg.get("decision", "directional"))

    pairs = load_outcome_pairs(db)
    trades: list[TradeOut] = []
    total = 0.0
    wins = 0
    for pred in pairs:
        pos = _POSITION.get(pred.direction, 0)
        realized = round(pred.outcome.actual_index - pred.current_index, 4)
        pnl = round(pos * lots * inr_per_mm * realized, 2)
        total += pnl
        if pnl > 0:
            wins += 1
        trades.append(
            TradeOut(
                target_timestamp=from_utc_naive(pred.target_timestamp),
                direction=pred.direction,
                current_index=pred.current_index,
                actual_index=pred.outcome.actual_index,
                realized_delta=realized,
                pnl_inr=pnl,
            )
        )

    trade_count = len(trades)
    win_rate = round(100.0 * wins / trade_count, 2) if trade_count else 0.0
    return ProfitabilityOut(
        decision_rule=decision,
        lots=lots,
        inr_per_mm=inr_per_mm,
        trades=trades,
        total_pnl_inr=round(total, 2),
        trade_count=trade_count,
        win_rate_pct=win_rate,
        disclaimer=settings.disclaimer,
    )
