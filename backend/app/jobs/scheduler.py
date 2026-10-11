"""APScheduler: hourly ingest+prediction and monthly evaluation jobs."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from app.core.config import get_settings
from app.core.datetime_utils import utcnow
from app.db.models import JobRun
from app.db.session import SessionLocal
from app.pipeline import evaluate, ingest, predict

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _ingest_predict(db) -> dict:
    result = ingest.run_ingest(db)
    predict.run_predict(db)
    return result


def _execute_job(name: str, func) -> None:
    with SessionLocal() as db:
        job = JobRun(job_name=name, status="running")
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id
        try:
            result = func(db)
            db.commit()
            job = db.get(JobRun, job_id)
            job.status = "success"
            job.finished_at = utcnow()
            job.message = str(result)
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Job %s failed", name)
            db.rollback()
            job = db.get(JobRun, job_id)
            job.status = "failed"
            job.finished_at = utcnow()
            job.message = str(exc)
            db.commit()


def _hourly() -> None:
    _execute_job("hourly_ingest_predict", _ingest_predict)


def _monthly() -> None:
    _execute_job("monthly_evaluation", evaluate.run_evaluation)


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _hourly,
        CronTrigger.from_crontab(settings.hourly_ingest_cron),
        id="hourly_ingest_predict",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _monthly,
        CronTrigger.from_crontab(settings.monthly_eval_cron),
        id="monthly_evaluation",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    # Immediate first ingestion (background, non-blocking).
    scheduler.add_job(
        _hourly,
        DateTrigger(run_date=datetime.now(timezone.utc) + timedelta(seconds=5)),
        id="initial_ingest",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Scheduler started (hourly=%s, monthly=%s)",
        settings.hourly_ingest_cron,
        settings.monthly_eval_cron,
    )
    return scheduler


def stop_scheduler(scheduler: BackgroundScheduler | None = None) -> None:
    global _scheduler
    s = scheduler or _scheduler
    if s is not None and s.running:
        s.shutdown(wait=False)
    _scheduler = None
