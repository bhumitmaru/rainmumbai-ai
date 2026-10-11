from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.performance import PerformanceOut
from app.services.performance import get_performance

router = APIRouter()


@router.get("", response_model=PerformanceOut)
def performance(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    from_timestamp: datetime | None = Query(None, alias="from"),
    to_timestamp: datetime | None = Query(None, alias="to"),
    source: Literal["live", "backfill", "all"] = Query("all"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> PerformanceOut:
    return get_performance(
        db,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
        source=source,
        limit=limit,
        offset=offset,
    )
