"""Authentication: JWT token management.

There is no password here. Accounts are identified by a Google or GitHub
identity, and the tokens below are what the application issues once such an
identity has been verified.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt

from app.config import get_settings

settings = get_settings()

TOKEN_TYPE_ACCESS = "access"


def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload["exp"] = expire
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(data: dict[str, Any]) -> str:
    """Create a short-lived JWT access token."""
    expires = timedelta(minutes=settings.access_token_expire_minutes)
    token_data = {**data, "type": TOKEN_TYPE_ACCESS}
    return _create_token(token_data, expires)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises HTTPException 401 on invalid or expired tokens.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return payload
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc


def build_token_claims(user_id: int, email: str, tier: str) -> dict[str, Any]:
    """Build standard JWT claims for a user."""
    user_id_str = str(user_id)
    return {
        "sub": user_id_str,
        "tenant_id": user_id_str,
        "email": email,
        "tier": tier,
    }
