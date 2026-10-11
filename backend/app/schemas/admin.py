from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class IngestionStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error: str | None
    last_source: str | None
    records_last_run: int


class JobRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_name: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    message: str | None


class UserAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    contact_number: str
    role: str
    status: str
    created_at: datetime


class AdminOverviewOut(BaseModel):
    ingestion: list[IngestionStatusOut]
    recent_jobs: list[JobRunOut]
    user_count: int
    prediction_count: int


class JobTriggerOut(BaseModel):
    message: str
    job_run_id: int


class BackfillRequest(BaseModel):
    start: str
    end: str
    seasons: str | None = None
    dry_run: bool = False


class BackfillTriggerOut(BaseModel):
    message: str
    job_run_id: int
    summary: dict
