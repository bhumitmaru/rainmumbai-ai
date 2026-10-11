from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.profitability import ProfitabilityOut
from app.services.profitability import get_profitability

router = APIRouter()


@router.get("", response_model=ProfitabilityOut)
def profitability(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    source: Literal["live", "backfill", "all"] = Query("all"),
    from_timestamp: datetime | None = Query(None, alias="from"),
    to_timestamp: datetime | None = Query(None, alias="to"),
) -> ProfitabilityOut:
    return get_profitability(db, source=source, from_timestamp=from_timestamp, to_timestamp=to_timestamp)
