"""API key generation, hashing, and validation."""

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_key import APIKey
from app.models.user import User

API_KEY_PREFIX = "omni_"
API_KEY_RANDOM_BYTES = 32


def generate_api_key() -> str:
    """Generate a secure random API key prefixed with omni_."""
    token = secrets.token_urlsafe(API_KEY_RANDOM_BYTES)
    return f"{API_KEY_PREFIX}{token}"


def hash_api_key(key: str) -> str:
    """SHA-256 hash for storage (never store raw keys)."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def validate_api_key(raw_key: str, db: Session) -> User:
    """
    Look up API key by hash, verify active status, return associated user.

    Raises HTTPException 401 if invalid or inactive.
    """
    if not raw_key or not raw_key.startswith(API_KEY_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    key_hash = hash_api_key(raw_key)
    stmt = (
        select(APIKey)
        .where(APIKey.key_hash == key_hash, APIKey.is_active.is_(True))
    )
    api_key = db.scalar(stmt)

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if api_key.expires_at is not None:
        expires_at = api_key.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
            )

    user = db.get(User, api_key.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    api_key.last_used_at = datetime.now(timezone.utc)
    db.commit()

    return user
