import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    subject: str,
    role: str = "user",
    remember_me: bool = False,
    extra: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    minutes = (
        settings.refresh_remember_minutes
        if remember_me
        else settings.access_token_expire_minutes
    )
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
