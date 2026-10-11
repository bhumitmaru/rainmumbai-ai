from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.profitability import ProfitabilityOut
from app.services.profitability import get_profitability

router = APIRouter()


@router.get("", response_model=ProfitabilityOut)
def profitability(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ProfitabilityOut:
    return get_profitability(db)
