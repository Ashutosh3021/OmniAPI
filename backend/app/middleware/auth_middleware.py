"""JWT authentication dependency."""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services import auth_service
from app.utils.exceptions import AuthenticationError, AuthorizationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode JWT, load user from database, enforce active status.

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

    user = db.scalar(select(User).where(User.id == user_pk))
    if user is None:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthorizationError("User account is inactive")

    return user
