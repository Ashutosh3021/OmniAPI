"""Reusable FastAPI authentication dependencies."""

from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services import api_key_service


async def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """Require a valid JWT access token."""
    return current_user


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    """Require a valid X-API-Key header."""
    if not x_api_key:
        from app.utils.exceptions import AuthenticationError

        raise AuthenticationError("X-API-Key header required")
    return api_key_service.validate_api_key(x_api_key, db)
