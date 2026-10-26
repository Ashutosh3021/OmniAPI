"""Short-lived cache for user rows.

The data store is a remote service: reading a user costs a network round trip
on every authenticated request. Caching the row in Redis for a short window
keeps that cost off the hot path.

The cache is an optimisation, never a source of truth. A Redis outage
degrades the application to reading the user from the data store, and the
entries are short-lived so a change to an account takes effect quickly even
if an explicit invalidation is missed.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from starlette.concurrency import run_in_threadpool

from app.db.database import Database
from app.models.parsing import parse_bool, parse_datetime
from app.models.user import User
from app.services.redis_client import get_redis

logger = logging.getLogger(__name__)

# The user row changes rarely. A short window is enough to absorb the read
# traffic of a session without letting a stale tier or a deactivated account
# linger.
USER_CACHE_TTL_SECONDS = 30


def _key(user_id: int) -> str:
    return f"omniapi:user:{user_id}"


def _serialize(user: User) -> str:
    return json.dumps(
        {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "tier": user.tier,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }
    )


def _deserialize(raw: str) -> User | None:
    try:
        data: dict[str, Any] = json.loads(raw)
    except (TypeError, ValueError):
        return None
    try:
        return User(
            id=int(data["id"]),
            email=data["email"],
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            tier=str(data.get("tier") or "free"),
            is_active=parse_bool(data.get("is_active")),
            created_at=parse_datetime(data["created_at"]),  # type: ignore[arg-type]
            updated_at=parse_datetime(data.get("updated_at")),
            last_login=parse_datetime(data.get("last_login")),
        )
    except (KeyError, TypeError, ValueError):
        return None


async def cached_user(db: Database, user_id: int) -> User | None:
    """Return a user, preferring the cache over the data store."""
    try:
        raw = await get_redis().get(_key(user_id))
        if raw:
            user = _deserialize(raw)
            if user is not None:
                return user
    except Exception:  # noqa: BLE001 - the cache must never fail a request
        logger.warning("User cache read failed", exc_info=True)

    user = await run_in_threadpool(db.users.get_by_id, user_id)
    if user is not None:
        await store_user(user)
    return user


async def store_user(user: User) -> None:
    """Put a user into the cache."""
    try:
        await get_redis().set(_key(user.id), _serialize(user), ex=USER_CACHE_TTL_SECONDS)
    except Exception:  # noqa: BLE001 - the cache must never fail a request
        logger.warning("User cache write failed", exc_info=True)


async def invalidate_user(user_id: int) -> None:
    """Drop a user from the cache after a change to their account."""
    try:
        await get_redis().delete(_key(user_id))
    except Exception:  # noqa: BLE001 - the cache must never fail a request
        logger.warning("User cache invalidation failed", exc_info=True)


async def touch_last_login(db: Database, user: User) -> None:
    """Record a sign-in and refresh the cached copy of the account."""
    now = datetime.now(timezone.utc)
    try:
        await run_in_threadpool(db.users.touch_last_login, user.id, now)
    except Exception:  # noqa: BLE001 - a missed timestamp must not fail a sign-in
        logger.warning("Could not record the sign-in time", exc_info=True)
    user.last_login = now
    await invalidate_user(user.id)
