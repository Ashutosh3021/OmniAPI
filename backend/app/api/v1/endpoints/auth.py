"""Authentication endpoints: register, login, refresh, me."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserTier
from app.schemas.auth import Token, TokenRefresh, UserLogin, UserRegister, UserResponse
from app.services import auth_service
from app.utils.decorators import require_auth
from app.utils.exceptions import AuthenticationError, DuplicateResourceError
from app.utils.user_helpers import split_full_name, user_to_response

router = APIRouter()


def _issue_tokens(user: User) -> Token:
    tier = user.tier.value if hasattr(user.tier, "value") else str(user.tier)
    claims = auth_service.build_token_claims(user.id, user.email, tier)
    return Token(
        access_token=auth_service.create_access_token(claims),
        refresh_token=auth_service.create_refresh_token(claims),
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, db: Session = Depends(get_db)) -> UserResponse:
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
def login(body: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Validate credentials and return JWT token pair."""
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not auth_service.verify_password(body.password, user.password_hash):
        raise AuthenticationError("Incorrect email or password")

    if not user.is_active:
        raise AuthenticationError("User account is inactive")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return _issue_tokens(user)


@router.post("/refresh", response_model=Token)
def refresh(body: TokenRefresh, db: Session = Depends(get_db)) -> Token:
    """Issue a new token pair from a valid refresh token."""
    payload = auth_service.decode_token(body.refresh_token)

    if payload.get("type") != auth_service.TOKEN_TYPE_REFRESH:
        raise AuthenticationError("Invalid refresh token")

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError()

    try:
        user_pk = int(user_id)
    except (TypeError, ValueError) as exc:
        raise AuthenticationError() from exc

    user = db.get(User, user_pk)
    if user is None or not user.is_active:
        raise AuthenticationError()

    return _issue_tokens(user)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(require_auth)) -> UserResponse:
    """Return the currently authenticated user."""
    return user_to_response(current_user)
