from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.db.models import Outcome, Prediction
from app.db.session import SessionLocal
from app.pipeline.backfill import run_backfill
from app.index.service import direction_from_delta
from app.providers.base import HourlyPoint, StationSeries


def _series(station: str, start: date, end: date, hourly_mm: float) -> StationSeries:
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    points = []
    t = start_dt
    while t < end_dt:
        points.append(
            HourlyPoint(
                time=t,
                rainfall_mm=hourly_mm,
                temperature_c=None,
                humidity_pct=None,
                pressure_hpa=None,
                wind_kmh=None,
            )
        )
        t += timedelta(hours=1)
    return StationSeries(station=station, latitude=0, longitude=0, points=points, source="test")


def test_backfill_idempotent(monkeypatch):
    monkeypatch.setattr(
        "app.pipeline.backfill.OpenMeteoProvider.fetch_archive",
        lambda _self, station, start, end: _series(station, date.fromisoformat(start), date.fromisoformat(end), 1.0),
    )
    monkeypatch.setattr(
        "app.pipeline.backfill._historical_forecast_rain",
        lambda *_args, **_kwargs: 12.0,
    )

    with SessionLocal() as db:
        start = date(2025, 6, 2)
        end = date(2025, 6, 2)
        first = run_backfill(db, start=start, end=end)
        assert first["backfilled"] == 1
        second = run_backfill(db, start=start, end=end)
        assert second["backfilled"] == 0

        rows = db.scalars(select(Prediction).where(Prediction.source == "backfill")).all()
        assert len(rows) == 1
        outcomes = db.scalars(
            select(Outcome).join(Prediction, Prediction.id == Outcome.prediction_id).where(Prediction.source == "backfill")
        ).all()
        assert len(outcomes) == 1


def test_backfill_prediction_outcome_matching(monkeypatch):
    monkeypatch.setattr(
        "app.pipeline.backfill.OpenMeteoProvider.fetch_archive",
        lambda _self, station, start, end: _series(station, date.fromisoformat(start), date.fromisoformat(end), 2.0),
    )
    monkeypatch.setattr(
        "app.pipeline.backfill._historical_forecast_rain",
        lambda *_args, **_kwargs: 20.0,
    )

    with SessionLocal() as db:
        summary = run_backfill(db, start=date(2025, 6, 4), end=date(2025, 6, 4))
        assert summary["attempted"] == 1
        pred = db.scalar(
            select(Prediction)
            .where(Prediction.source == "backfill")
            .order_by(Prediction.target_timestamp.desc())
            .limit(1)
        )
        assert pred is not None
        assert pred.outcome is not None
        expected = direction_from_delta(round(pred.outcome.actual_index - pred.current_index, 4))
        assert pred.outcome.actual_direction == expected
