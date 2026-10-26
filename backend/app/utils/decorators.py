"""Reusable FastAPI authentication dependencies."""

from typing import Optional

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.concurrency import run_in_threadpool

from app.db.database import Database, get_db
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit import apply_rate_limit
from app.models.api_key import APIKey
from app.models.user import User
from app.services import api_key_service, auth_service, user_cache
from app.utils.exceptions import AuthenticationError, AuthorizationError

_bearer_optional = HTTPBearer(auto_error=False)


async def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """Require a valid JWT access token."""
    return current_user


def _validate_api_key_sync(raw_key: str, db: Database) -> tuple[User, Optional[APIKey]]:
    """Blocking API key validation. Runs in a worker thread."""
    return api_key_service.validate_api_key_with_record(raw_key, db)


async def require_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Database = Depends(get_db),
) -> User:
    """Require a valid X-API-Key header."""
    if not x_api_key:
        raise AuthenticationError("X-API-Key header required")

    # The key is looked up once and reused for the rate-limit bucket.
    user, api_key = await run_in_threadpool(_validate_api_key_sync, x_api_key, db)
    api_key_id = str(api_key.id) if api_key else "api_key"
    # Recorded so usage rows can be attributed to the key that made the call.
    request.state.api_key_id = api_key.id if api_key else None
    await apply_rate_limit(request, user, api_key_id=api_key_id)
    return user


async def require_auth_or_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_optional),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Database = Depends(get_db),
) -> User:
    """Accept JWT Bearer token or X-API-Key header with rate limiting."""
    if x_api_key:
        user, api_key = await run_in_threadpool(_validate_api_key_sync, x_api_key, db)
        api_key_id = str(api_key.id) if api_key else "api_key"
        request.state.api_key_id = api_key.id if api_key else None
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

        user = await user_cache.cached_user(db, user_pk)
        if user is None:
            raise AuthenticationError("User not found")
        if not user.is_active:
            raise AuthorizationError("User account is inactive")

        await apply_rate_limit(request, user, api_key_id="jwt")
        return user

    raise AuthenticationError("Authentication required")
