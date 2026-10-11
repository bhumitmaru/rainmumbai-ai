from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.performance import PerformanceOut
from app.services.performance import get_performance

router = APIRouter()


@router.get("", response_model=PerformanceOut)
def performance(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> PerformanceOut:
    return get_performance(db)
