"""Reusable FastAPI authentication dependencies."""

from typing import Optional

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services import api_key_service, auth_service
from app.utils.exceptions import AuthenticationError

_bearer_optional = HTTPBearer(auto_error=False)


async def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """Require a valid JWT access token."""
    return current_user


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    """Require a valid X-API-Key header."""
    if not x_api_key:
        raise AuthenticationError("X-API-Key header required")
    return api_key_service.validate_api_key(x_api_key, db)


async def require_auth_or_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_optional),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    """Accept JWT Bearer token or X-API-Key header."""
    if x_api_key:
        return api_key_service.validate_api_key(x_api_key, db)

    if credentials and credentials.credentials:
        payload = auth_service.decode_token(credentials.credentials)
        if payload.get("type") != auth_service.TOKEN_TYPE_ACCESS:
            raise AuthenticationError("Invalid access token")

        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError()

        from sqlalchemy import select

        from app.models.user import User as UserModel

        try:
            user_pk = int(user_id)
        except (TypeError, ValueError) as exc:
            raise AuthenticationError() from exc

        user = db.scalar(select(UserModel).where(UserModel.id == user_pk))
        if user is None:
            raise AuthenticationError("User not found")
        if not user.is_active:
            from app.utils.exceptions import AuthorizationError

            raise AuthorizationError("User account is inactive")
        return user

    raise AuthenticationError("Authentication required")
