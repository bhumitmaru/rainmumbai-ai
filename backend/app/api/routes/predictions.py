from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.prediction import PredictionHistoryOut, PredictionOut
from app.services.predictions import get_latest_prediction, list_predictions, serialize_prediction

router = APIRouter()


@router.get("/latest", response_model=PredictionOut)
def latest(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> PredictionOut:
    pred = get_latest_prediction(db)
    if pred is None:
        raise HTTPException(
            status_code=404,
            detail="No prediction available yet. Please wait for the next scheduled run.",
        )
    return serialize_prediction(pred)


@router.get("/history", response_model=PredictionHistoryOut)
def history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    from_timestamp: datetime | None = Query(None, alias="from"),
    to_timestamp: datetime | None = Query(None, alias="to"),
    source: Literal["live", "backfill", "all"] = Query("all"),
) -> PredictionHistoryOut:
    return list_predictions(
        db,
        limit=limit,
        offset=offset,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
        source=source,
    )
