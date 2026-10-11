import hashlib
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import bearer_scheme, get_current_user
from app.core.config import get_settings
from app.core.datetime_utils import utcnow
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models import PasswordResetToken, TokenBlocklist, User
from app.db.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
)
from app.schemas.common import Message
from app.services.mailer import send_password_reset

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    user = User(
        full_name=body.full_name,
        email=email,
        contact_number=body.contact_number,
        password_hash=hash_password(body.password),
        role="user",
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id), role=user.role)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    token = create_access_token(str(user.id), role=user.role, remember_me=body.remember_me)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout", response_model=Message)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    if credentials is not None:
        try:
            payload = decode_token(credentials.credentials)
        except ValueError:
            payload = {}
        jti = payload.get("jti")
        if jti and db.scalar(select(TokenBlocklist).where(TokenBlocklist.jti == jti)) is None:
            db.add(TokenBlocklist(jti=jti, expires_at=utcnow()))
            db.commit()
    return Message(message="Logged out")


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)) -> ForgotPasswordResponse:
    settings = get_settings()
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    debug_token: str | None = None
    if user is not None:
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=utcnow() + timedelta(minutes=settings.reset_token_expire_minutes),
            )
        )
        db.commit()
        reset_link = f"{settings.frontend_url.rstrip('/')}/reset-password?token={token}"
        send_password_reset(user.email, reset_link)
        if not settings.smtp_enabled and settings.env == "development":
            debug_token = token
    return ForgotPasswordResponse(
        message="If that email exists, a password reset link has been sent.",
        debug_reset_token=debug_token,
    )


@router.post("/reset-password", response_model=Message)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)) -> Message:
    token_hash = hashlib.sha256(body.token.encode("utf-8")).hexdigest()
    row = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,  # noqa: E712
        )
    )
    if row is None or row.expires_at < utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    row.user.password_hash = hash_password(body.new_password)
    row.used = True
    db.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
