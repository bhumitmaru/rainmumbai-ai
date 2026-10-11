"""Idempotent seed data: LPA climatology, model versions, and admin user.

The RainMumbai Index formula (NCDEX CDR) needs a daily Long-Period Average
(LPA) rainfall for Colaba and Santacruz for every calendar day. IMD daily LPA
normals are not bundled here, so a deterministic climatological curve is
generated and clearly labelled ``source=climatology-seed``. The daily LPA is
scaled so the monsoon season (1 Jun - 30 Sep) sums to the configured season
LPA anchor (2206.7 mm). See README for the assumption.
"""

import math
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings, load_index_config
from app.core.security import hash_password
from app.db.models import DailyLPA, ModelVersion, User

STATIONS = ("colaba", "santacruz", "mumbai")


def _build_city_daily_lpa() -> dict[str, float]:
    """Return {month-day: mm} daily LPA for the city (used for all stations)."""
    cfg = load_index_config()
    anchor = float(cfg["season_lpa_anchor_mm"])
    season_start = date(2001, 6, 1)
    season_end = date(2001, 9, 30)

    weights: dict[int, float] = {}
    total = 0.0
    d = date(2001, 1, 1)
    while d <= date(2001, 12, 31):
        doy = d.timetuple().tm_yday
        w = math.exp(-((doy - 195) ** 2) / (2 * 38.0**2))
        if season_start <= d <= season_end:
            weights[doy] = w
            total += w
        else:
            weights[doy] = 0.0
        d += timedelta(days=1)

    out: dict[str, float] = {}
    d = date(2001, 1, 1)
    while d <= date(2001, 12, 31):
        doy = d.timetuple().tm_yday
        mm = round(anchor * weights[doy] / total, 2) if weights[doy] > 0 else 0.0
        out[f"{d.month:02d}-{d.day:02d}"] = mm
        d += timedelta(days=1)
    out["02-29"] = out["02-28"]
    return out


def seed_daily_lpa(db: Session) -> int:
    if db.scalar(select(DailyLPA.id).limit(1)) is not None:
        return 0
    daily = _build_city_daily_lpa()
    count = 0
    for month_day, mm in daily.items():
        for station in STATIONS:
            db.add(
                DailyLPA(
                    month_day=month_day,
                    station=station,
                    lpa_mm=mm,
                    source="climatology-seed",
                )
            )
            count += 1
    db.commit()
    return count


def get_active_model_version(db: Session, kind: str) -> ModelVersion | None:
    return db.scalar(
        select(ModelVersion)
        .where(ModelVersion.kind == kind, ModelVersion.status == "active")
        .order_by(ModelVersion.id.desc())
    )


def ensure_model_versions(db: Session) -> None:
    cfg = load_index_config()
    formula_id = str(cfg.get("formula_id", "ncdex_cdr_v1"))
    if db.scalar(select(ModelVersion).where(ModelVersion.version == formula_id)) is None:
        db.add(
            ModelVersion(
                version=formula_id,
                kind="index_formula",
                status="active",
                config_json=cfg,
                notes="NCDEX RAINMUMBAI cumulative-deviation-rainfall formula",
            )
        )
    cal = cfg.get("calibration", {}) or {}
    if cal.get("enabled"):
        cal_id = f"calibration_v1"
        if db.scalar(select(ModelVersion).where(ModelVersion.version == cal_id)) is None:
            db.add(
                ModelVersion(
                    version=cal_id,
                    kind="calibration",
                    status="active",
                    config_json={
                        "slope": float(cal.get("slope", 1.0)),
                        "intercept": float(cal.get("intercept", 0.0)),
                    },
                    notes="Optional linear calibration (slope/intercept)",
                )
            )
    db.commit()


def ensure_admin_user(db: Session) -> None:
    settings = get_settings()
    if db.scalar(select(User).where(User.email == settings.admin_email)) is not None:
        return
    db.add(
        User(
            full_name="Administrator",
            email=settings.admin_email,
            contact_number="0000000000",
            password_hash=hash_password(settings.admin_password),
            role="admin",
            status="active",
        )
    )
    db.commit()


def ensure_seed(db: Session) -> None:
    seed_daily_lpa(db)
    ensure_model_versions(db)
    ensure_admin_user(db)
