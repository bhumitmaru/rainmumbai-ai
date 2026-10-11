"""RainMumbai AI FastAPI application entrypoint."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import (
    admin,
    auth,
    health,
    performance,
    predictions,
    profitability,
    weather,
)
from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    app_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.core.logging import setup_logging
from app.db import seed
from app.db.models import Base
from app.db.session import SessionLocal, engine
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.pipeline import predict

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed.ensure_seed(db)
        try:
            predict.run_predict(db)
        except Exception:  # noqa: BLE001
            logger.exception("Initial prediction failed")
    scheduler = None
    if settings.scheduler_enabled and settings.env != "test":
        scheduler = start_scheduler()
    yield
    if scheduler is not None:
        stop_scheduler(scheduler)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000
        logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, duration)
        return response


app = FastAPI(
    title="RainMumbai AI",
    version="1.0.0",
    description="Predictive modeling of the RainMumbai Index using meteorological data.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(StarletteHTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])
app.include_router(performance.router, prefix="/api/performance", tags=["performance"])
app.include_router(profitability.router, prefix="/api/profitability", tags=["profitability"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(health.router, prefix="/api", tags=["health"])
