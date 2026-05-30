"""Reusable FastAPI authentication dependencies."""

from typing import Optional

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit import apply_rate_limit
from app.models.api_key import APIKey
from app.models.user import User
from app.services import api_key_service, auth_service
from app.utils.exceptions import AuthenticationError, AuthorizationError

_bearer_optional = HTTPBearer(auto_error=False)


async def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """Require a valid JWT access token."""
    return current_user


async def require_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    """Require a valid X-API-Key header."""
    if not x_api_key:
        raise AuthenticationError("X-API-Key header required")

    key_hash = api_key_service.hash_api_key(x_api_key)
    api_key = db.scalar(select(APIKey).where(APIKey.key_hash == key_hash))
    user = api_key_service.validate_api_key(x_api_key, db)

    api_key_id = str(api_key.id) if api_key else "api_key"
    await apply_rate_limit(request, user, api_key_id=api_key_id)
    return user


async def require_auth_or_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_optional),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    """Accept JWT Bearer token or X-API-Key header with rate limiting."""
    if x_api_key:
        key_hash = api_key_service.hash_api_key(x_api_key)
        api_key = db.scalar(select(APIKey).where(APIKey.key_hash == key_hash))
        user = api_key_service.validate_api_key(x_api_key, db)
        api_key_id = str(api_key.id) if api_key else "api_key"
        await apply_rate_limit(request, user, api_key_id=api_key_id)
        return user

    if credentials and credentials.credentials:
        payload = auth_service.decode_token(credentials.credentials)
        if payload.get("type") != auth_service.TOKEN_TYPE_ACCESS:
            raise AuthenticationError("Invalid access token")

        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError()

        try:
            user_pk = int(user_id)
        except (TypeError, ValueError) as exc:
            raise AuthenticationError() from exc

        user = db.scalar(select(User).where(User.id == user_pk))
        if user is None:
            raise AuthenticationError("User not found")
        if not user.is_active:
            raise AuthorizationError("User account is inactive")

        await apply_rate_limit(request, user, api_key_id="jwt")
        return user

    raise AuthenticationError("Authentication required")
