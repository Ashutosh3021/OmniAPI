"""JWT authentication dependency."""

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer


from app.db.database import Database, get_db
from app.middleware.rate_limit import apply_rate_limit
from app.models.user import User
from app.services import auth_service, user_cache
from app.utils.exceptions import AuthenticationError, AuthorizationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/oauth/exchange")


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Database = Depends(get_db),
) -> User:
    """
    Decode JWT, load user from database, enforce active status and rate limits.

    The user row is read through a short-lived cache, so the data store is
    only consulted on a miss. The lookup is dispatched to a worker thread
    either way: it is blocking I/O, and running it on the event loop would
    stall every concurrent request for the duration of the round trip.

    Raises 401 for invalid tokens or missing users; 403 for inactive users.
    """
    payload = auth_service.decode_token(token)

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
