from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.datetime_utils import utcnow
from app.db.models import IngestionStatus, JobRun, Prediction, User
from app.db.session import get_db
from app.pipeline import evaluate, ingest, predict
from app.schemas.admin import (
    AdminOverviewOut,
    IngestionStatusOut,
    JobRunOut,
    JobTriggerOut,
    UserAdminOut,
)

router = APIRouter()


@router.get("/overview", response_model=AdminOverviewOut)
def overview(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)) -> AdminOverviewOut:
    ingestion = db.scalars(select(IngestionStatus).order_by(IngestionStatus.provider.asc())).all()
    recent = db.scalars(select(JobRun).order_by(JobRun.id.desc()).limit(10)).all()
    user_count = db.scalar(select(func.count()).select_from(User)) or 0
    prediction_count = db.scalar(select(func.count()).select_from(Prediction)) or 0
    return AdminOverviewOut(
        ingestion=[IngestionStatusOut.model_validate(i) for i in ingestion],
        recent_jobs=[JobRunOut.model_validate(j) for j in recent],
        user_count=user_count,
        prediction_count=prediction_count,
    )


@router.get("/jobs", response_model=list[JobRunOut])
def jobs(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
    limit: int = Query(50, ge=1, le=200),
) -> list[JobRunOut]:
    rows = db.scalars(select(JobRun).order_by(JobRun.id.desc()).limit(limit)).all()
    return [JobRunOut.model_validate(j) for j in rows]


@router.get("/users", response_model=list[UserAdminOut])
def users(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)) -> list[UserAdminOut]:
    rows = db.scalars(select(User).order_by(User.id.asc())).all()
    return [UserAdminOut.model_validate(u) for u in rows]


@router.post("/ingest", response_model=JobTriggerOut)
def trigger_ingest(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)) -> JobTriggerOut:
    try:
        result = ingest.run_ingest(db)
        predict.run_predict(db)
        job = JobRun(
            job_name="manual_ingest_predict",
            status="success",
            finished_at=utcnow(),
            message=str(result),
        )
        db.add(job)
        db.commit()
        return JobTriggerOut(message="success", job_run_id=job.id)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        job = JobRun(
            job_name="manual_ingest_predict",
            status="failed",
            finished_at=utcnow(),
            message=str(exc),
        )
        db.add(job)
        db.commit()
        return JobTriggerOut(message="failed", job_run_id=job.id)


@router.post("/evaluate", response_model=JobTriggerOut)
def trigger_evaluate(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)) -> JobTriggerOut:
    try:
        result = evaluate.run_evaluation(db)
        job = JobRun(
            job_name="manual_evaluation",
            status="success",
            finished_at=utcnow(),
            message=str(result),
        )
        db.add(job)
        db.commit()
        return JobTriggerOut(message="success", job_run_id=job.id)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        job = JobRun(
            job_name="manual_evaluation",
            status="failed",
            finished_at=utcnow(),
            message=str(exc),
        )
        db.add(job)
        db.commit()
        return JobTriggerOut(message="failed", job_run_id=job.id)
