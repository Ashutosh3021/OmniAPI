"""API key generation, hashing, and validation."""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import HTTPException, status

from app.db.database import Database
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


def lookup_api_key(raw_key: str, db: Database) -> Optional[APIKey]:
    """Find an active, unexpired API key by its raw value."""
    if not raw_key or not raw_key.startswith(API_KEY_PREFIX):
        return None
    found = db.api_keys.find_active_by_hash(hash_api_key(raw_key))
    if found is None:
        return None
    api_key, _owner = found
    if _is_expired(api_key):
        return None
    return api_key


def validate_api_key(raw_key: str, db: Database) -> User:
    """
    Look up an API key, verify it, and return the owning user.

    Raises HTTPException 401 if the key is invalid or expired.
    """
    user, _ = validate_api_key_with_record(raw_key, db)
    return user


def validate_api_key_with_record(raw_key: str, db: Database) -> Tuple[User, Optional[APIKey]]:
    """
    Look up an API key, verify it, and return the owning user and the key.

    The owner is joined in the same statement, so authenticating a request
    costs a single round trip to the data store. Returning the key record
    lets the caller reuse it instead of querying for it again.
    """
    if not raw_key or not raw_key.startswith(API_KEY_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    found = db.api_keys.find_active_by_hash(hash_api_key(raw_key))
    if found is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    api_key, user = found
    if _is_expired(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    _touch_last_used(api_key, db)
    return user, api_key


def _touch_last_used(api_key: APIKey, db: Database) -> None:
    """Record usage of a key without putting a write on every request."""
    now = datetime.now(timezone.utc)
    db.api_keys.touch_last_used(api_key.id, now)
    api_key.last_used_at = now
