from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.weather import WeatherCurrentOut, WeatherForecastOut
from app.services.weather import get_current_weather, get_forecast

router = APIRouter()


@router.get("/current", response_model=WeatherCurrentOut)
def current(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> WeatherCurrentOut:
    return get_current_weather(db)


@router.get("/forecast", response_model=WeatherForecastOut)
def forecast(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> WeatherForecastOut:
    return get_forecast(db)
