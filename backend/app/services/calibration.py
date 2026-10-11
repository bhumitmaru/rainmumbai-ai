"""Optional linear calibration layer: predicted' = slope * predicted + intercept."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import load_index_config
from app.db.models import ModelVersion
from app.db.seed import get_active_model_version


def active_calibration(db: Session) -> dict:
    """Return {enabled, slope, intercept} for the active calibration version."""
    cfg = load_index_config()
    cal = cfg.get("calibration", {}) or {}
    enabled = bool(cal.get("enabled"))
    version = get_active_model_version(db, "calibration")
    if version is not None and isinstance(version.config_json, dict):
        slope = float(version.config_json.get("slope", cal.get("slope", 1.0)))
        intercept = float(version.config_json.get("intercept", cal.get("intercept", 0.0)))
    else:
        slope = float(cal.get("slope", 1.0))
        intercept = float(cal.get("intercept", 0.0))
    return {"enabled": enabled, "slope": slope, "intercept": intercept}


def fit_line(pairs: list[tuple[float, float]]) -> tuple[float, float]:
    """Ordinary least squares slope/intercept for x -> y."""
    n = len(pairs)
    if n < 2:
        return 1.0, 0.0
    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    xm = sum(xs) / n
    ym = sum(ys) / n
    sxx = sum((x - xm) ** 2 for x in xs)
    sxy = sum((x - xm) * (y - ym) for x, y in pairs)
    if sxx == 0:
        return 1.0, ym - xm
    slope = sxy / sxx
    return slope, ym - slope * xm


def apply(predicted: float, cal: dict) -> float:
    if not cal.get("enabled"):
        return predicted
    return round(cal["slope"] * predicted + cal["intercept"], 4)


def next_calibration_version(db: Session) -> str:
    count = db.scalar(
        select(func.count()).select_from(ModelVersion).where(ModelVersion.kind == "calibration")
    ) or 0
    return f"calibration_v{count + 1}"
