"""Datetime helpers.

Convention: the database stores *naive UTC* timestamps. This keeps SQLite
(local dev) and PostgreSQL interchangeable. Convert to aware UTC only when
doing zone-aware math (e.g. the IST rainfall day window).
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC now."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def from_utc_naive(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
