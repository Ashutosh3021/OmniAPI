"""Authentication endpoints: register, login, refresh, logout, profile, password."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.rate_limit import (
    enforce_login_rate_limit,
    enforce_register_rate_limit,
)
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User, UserTier
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    Token,
    TokenRefresh,
    UserLogin,
    UserProfileUpdate,
    UserRegister,
    UserResponse,
)
from app.services import auth_service, session_service
from app.utils.decorators import require_auth
from app.utils.exceptions import AuthenticationError, DuplicateResourceError
from app.utils.user_helpers import split_full_name, user_to_response

logger = logging.getLogger(__name__)

router = APIRouter()

PASSWORD_RESET_TTL_MINUTES = 60


def _issue_tokens(user: User, db: Session) -> Token:
    tier = user.tier.value if hasattr(user.tier, "value") else str(user.tier)
    claims = auth_service.build_token_claims(user.id, user.email, tier)
    refresh_token = session_service.issue_refresh_token(db, user)
    return Token(
        access_token=auth_service.create_access_token(claims),
        refresh_token=refresh_token,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: UserRegister,
    db: Session = Depends(get_db),
    _throttle: None = Depends(enforce_register_rate_limit),
) -> UserResponse:
    """Register a new user with free tier by default."""
    existing = db.scalar(select(User).where(User.email == body.email))
    if existing is not None:
        raise DuplicateResourceError("Email already registered")

    first_name, last_name = split_full_name(body.full_name)
    user = User(
        email=body.email,
        password_hash=auth_service.hash_password(body.password),
        first_name=first_name,
        last_name=last_name,
        tier=UserTier.FREE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_response(user)


@router.post("/login", response_model=Token)
def login(
    body: UserLogin,
    db: Session = Depends(get_db),
    _throttle: None = Depends(enforce_login_rate_limit),
) -> Token:
    """Validate credentials and return a token pair."""
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not auth_service.verify_password(body.password, user.password_hash):
        raise AuthenticationError("Incorrect email or password")

    if not user.is_active:
        raise AuthenticationError("User account is inactive")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return _issue_tokens(user, db)


@router.post("/refresh", response_model=Token)
def refresh(body: TokenRefresh, db: Session = Depends(get_db)) -> Token:
    """Exchange a refresh token for a new token pair.

    The presented token is revoked and replaced. Presenting a token that was
    already used revokes every token in the family.
    """
    user, new_refresh_token = session_service.rotate_refresh_token(db, body.refresh_token)
    tier = user.tier.value if hasattr(user.tier, "value") else str(user.tier)
    claims = auth_service.build_token_claims(user.id, user.email, tier)
    return Token(
        access_token=auth_service.create_access_token(claims),
        refresh_token=new_refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: TokenRefresh, db: Session = Depends(get_db)) -> None:
    """Revoke a refresh token. Signing out on the client is not enough."""
    session_service.revoke_refresh_token(db, body.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(require_auth)) -> UserResponse:
    """Return the currently authenticated user."""
    return user_to_response(current_user)


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
) -> UserResponse:
    """Update the authenticated user's profile."""
    first_name, last_name = split_full_name(body.full_name)
    current_user.first_name = first_name
    current_user.last_name = last_name
    db.commit()
    db.refresh(current_user)
    return user_to_response(current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
) -> None:
    """Change the authenticated user's password.

    Every existing session is revoked — a password change is how a user
    responds to a suspected compromise.
    """
    if not auth_service.verify_password(body.current_password, current_user.password_hash):
        raise AuthenticationError("Current password is incorrect")

    if body.current_password == body.new_password:
        raise AuthenticationError("New password must be different from the current one")

    current_user.password_hash = auth_service.hash_password(body.new_password)
    db.commit()

    session_service.revoke_all_for_user(db, current_user.id)


@router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=status.HTTP_202_ACCEPTED)
def forgot_password(
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> ForgotPasswordResponse:
    """Start a password reset.

    The response is identical whether or not the address has an account, so
    the endpoint cannot be used to enumerate users.
    """
    from app.config import get_settings

    settings = get_settings()
    user = db.scalar(select(User).where(User.email == body.email))

    reset_token: Optional[str] = None
    if user is not None and user.is_active:
        raw = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=PASSWORD_RESET_TTL_MINUTES
        )
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=session_service.hash_token(raw),
                expires_at=expires_at,
            )
        )
        db.commit()
        logger.info("Password reset requested for user %s", user.id)
        if not settings.is_production:
            # No email provider is wired up yet. Outside production the token
            # is returned so the flow can be exercised end to end.
            reset_token = raw

    return ForgotPasswordResponse(status="accepted", reset_token=reset_token)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)) -> None:
    """Complete a password reset using a single-use token."""
    record = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == session_service.hash_token(body.token)
        )
    )
    if record is None or not record.is_usable:
        raise AuthenticationError("This reset link is invalid or has expired")

    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("This reset link is invalid or has expired")

    user.password_hash = auth_service.hash_password(body.new_password)
    record.used_at = datetime.now(timezone.utc)
    db.commit()

    # A reset is a compromise response: kill every existing session.
    session_service.revoke_all_for_user(db, user.id)
