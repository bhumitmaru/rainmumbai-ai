"""Monthly evaluation job (replaces the PDF's monthly retraining).

Reconciles matured predictions, recomputes MAE/RMSE/direction-accuracy/F1,
stores a versioned EvaluationRun, and — only when the calibration layer is
enabled — refits the linear calibration and promotes it only if it beats the
currently active version.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import load_index_config
from app.core.datetime_utils import utcnow
from app.db.models import EvaluationRun, ModelVersion
from app.db.seed import get_active_model_version
from app.pipeline.ingest import reconcile_outcomes
from app.pipeline.state import load_outcome_pairs
from app.services.calibration import active_calibration, fit_line, next_calibration_version
from app.services.metrics import direction_accuracy, direction_f1, mae, rmse

logger = logging.getLogger(__name__)


def _raw_predicted(p) -> float:
    if isinstance(p.inputs_json, dict):
        raw = p.inputs_json.get("raw_predicted_index")
        if raw is not None:
            return float(raw)
    return float(p.predicted_index)


def _calibrated_mae(pairs: list[tuple[float, float]], slope: float, intercept: float) -> float:
    if not pairs:
        return float("inf")
    return round(sum(abs((slope * x + intercept) - y) for x, y in pairs) / len(pairs), 4)


def run_evaluation(db: Session) -> dict:
    now = utcnow()
    reconciled = reconcile_outcomes(db)
    db.commit()

    pairs = load_outcome_pairs(db)
    value_pairs = [(p.predicted_index, p.outcome.actual_index) for p in pairs]
    direction_pairs = [(p.direction, p.outcome.actual_direction) for p in pairs]

    mae_val = mae(value_pairs)
    rmse_val = rmse(value_pairs)
    acc = direction_accuracy(direction_pairs)
    f1 = direction_f1(direction_pairs)

    run = EvaluationRun(status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    promoted = False
    candidate_version: str | None = None
    cfg = load_index_config()
    cal_cfg = cfg.get("calibration", {}) or {}

    if cal_cfg.get("enabled") and len(pairs) >= 2:
        raw_pairs = [(_raw_predicted(p), p.outcome.actual_index) for p in pairs]
        slope, intercept = fit_line(raw_pairs)
        candidate_mae = _calibrated_mae(raw_pairs, slope, intercept)
        active = active_calibration(db)
        active_mae = _calibrated_mae(raw_pairs, active["slope"], active["intercept"])
        if candidate_mae < active_mae - 1e-6:
            old = get_active_model_version(db, "calibration")
            if old is not None:
                old.status = "inactive"
            candidate_version = next_calibration_version(db)
            db.add(
                ModelVersion(
                    version=candidate_version,
                    kind="calibration",
                    status="active",
                    config_json={"slope": round(slope, 6), "intercept": round(intercept, 6)},
                    metrics_json={"mae": candidate_mae, "active_mae": active_mae},
                    notes="Promoted by monthly evaluation (beats active calibration)",
                )
            )
            promoted = True
            logger.info(
                "Promoted %s (MAE %.4f vs active %.4f)",
                candidate_version,
                candidate_mae,
                active_mae,
            )

    run.finished_at = now
    run.status = "success"
    run.mae = mae_val
    run.rmse = rmse_val
    run.direction_accuracy = acc
    run.direction_f1 = f1
    run.promoted = promoted
    run.candidate_version = candidate_version
    run.metrics_json = {
        "mae": mae_val,
        "rmse": rmse_val,
        "direction_accuracy": acc,
        "direction_f1": f1,
        "sample_count": len(pairs),
    }
    run.notes = f"Reconciled {reconciled} outcomes; {len(pairs)} evaluated samples."
    db.commit()

    return {
        "reconciled": reconciled,
        "samples": len(pairs),
        "mae": mae_val,
        "rmse": rmse_val,
        "direction_accuracy": acc,
        "direction_f1": f1,
        "promoted": promoted,
        "candidate_version": candidate_version,
    }
