"""API key generation, hashing, and validation."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.api_key import APIKey
from app.models.user import User

API_KEY_PREFIX = "omni_"
API_KEY_RANDOM_BYTES = 32

# How stale ``last_used_at`` is allowed to get before it is written again.
# Writing it on every request put a write transaction on the hot path.
LAST_USED_WRITE_INTERVAL_SECONDS = 60


def generate_api_key() -> str:
    """Generate a secure random API key prefixed with omni_."""
    token = secrets.token_urlsafe(API_KEY_RANDOM_BYTES)
    return f"{API_KEY_PREFIX}{token}"


def hash_api_key(key: str) -> str:
    """SHA-256 hash for storage (never store raw keys)."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _is_expired(api_key: APIKey) -> bool:
    if api_key.expires_at is None:
        return False
    expires_at = api_key.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < datetime.now(timezone.utc)


def lookup_api_key(raw_key: str, db: Session) -> Optional[APIKey]:
    """Find an active, unexpired API key by its raw value."""
    if not raw_key or not raw_key.startswith(API_KEY_PREFIX):
        return None
    api_key = db.scalar(
        select(APIKey).where(
            APIKey.key_hash == hash_api_key(raw_key),
            APIKey.is_active.is_(True),
        )
    )
    if api_key is None or _is_expired(api_key):
        return None
    return api_key


def validate_api_key(raw_key: str, db: Session) -> User:
    """
    Look up an API key, verify it, and return the owning user.

    Raises HTTPException 401 if the key is invalid or expired.
    """
    user, _ = validate_api_key_with_record(raw_key, db)
    return user


def validate_api_key_with_record(
    raw_key: str, db: Session
) -> Tuple[User, Optional[APIKey]]:
    """
    Look up an API key, verify it, and return the owning user and the key.

    Returning the key record lets the caller reuse it (for the rate-limit
    bucket) instead of querying for it a second time.

    Raises HTTPException 401 if the key is invalid or expired.
    """
    api_key = lookup_api_key(raw_key, db)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    user = db.get(User, api_key.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    _touch_last_used(api_key, db)
    return user, api_key


def _touch_last_used(api_key: APIKey, db: Session) -> None:
    """Record usage of a key without putting a write on every request."""
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(seconds=LAST_USED_WRITE_INTERVAL_SECONDS)

    last_used = api_key.last_used_at
    if last_used is not None:
        if last_used.tzinfo is None:
            last_used = last_used.replace(tzinfo=timezone.utc)
        if last_used >= threshold:
            return

    # A single conditional UPDATE: no read, no row lock, and concurrent
    # requests cannot pile up writes for the same key.
    db.execute(
        text(
            "UPDATE api_keys SET last_used_at = :now "
            "WHERE id = :id AND (last_used_at IS NULL OR last_used_at < :threshold)"
        ),
        {"now": now, "id": api_key.id, "threshold": threshold},
    )
    api_key.last_used_at = now
    db.commit()
