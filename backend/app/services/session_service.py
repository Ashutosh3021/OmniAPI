"""Refresh token issuance, rotation and revocation.

Refresh tokens are opaque random strings, not JWTs. The server keeps a
SHA-256 hash of each token, which makes three things possible that a purely
stateless JWT cannot do:

* **Rotation** — every refresh issues a new token and revokes the old one.
* **Revocation** — signing out kills the session server-side instead of
  waiting for the token to expire.
* **Reuse detection** — presenting an already-revoked token means it leaked,
  so the whole rotation family is revoked.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from app.config import get_settings
from app.db.database import Database
from app.models.user import User
from app.utils.exceptions import AuthenticationError

REFRESH_TOKEN_BYTES = 32

# Rows that are not sessions carry this family prefix. Only refresh tokens
# are issued now, but rows minted by the retired password-reset flow are
# still live in existing databases, and the prefix keeps them unusable as
# refresh tokens.
RESET_FAMILY_PREFIX = "reset:"


def hash_token(raw: str) -> str:
    """Hash a raw token for storage. The raw value is never persisted."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def issue_refresh_token(db: Database, user: User) -> str:
    """Issue a brand new refresh token in its own rotation family."""
    settings = get_settings()
    expires_at = _now() + timedelta(days=settings.refresh_token_expire_days)
    raw = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    db.refresh_tokens.create(
        user_id=user.id,
        token_hash=hash_token(raw),
        family_id=str(uuid.uuid4()),
        expires_at=expires_at,
        created_at=_now(),
    )
    return raw


def rotate_refresh_token(db: Database, raw: str) -> Tuple[User, str]:
    """
    Exchange a valid refresh token for a new one.

    The presented token is revoked. Presenting an already-revoked token is
    treated as a leak: the entire family is revoked and the request fails.
    """
    settings = get_settings()
    record = db.refresh_tokens.get_by_hash(hash_token(raw))
    if record is None:
        raise AuthenticationError("Invalid refresh token. Sign in again.")

    if record.revoked_at is not None:
        db.refresh_tokens.revoke_family(record.family_id, _now())
        raise AuthenticationError(
            "This refresh token was already used. All sessions have been revoked "
            "for safety. Sign in again."
        )

    # Password-reset tokens live in the same table so they can be revoked
    # the same way, but they are not sessions and must never be exchanged
    # for one.
    if record.family_id.startswith(RESET_FAMILY_PREFIX):
        raise AuthenticationError("Invalid refresh token. Sign in again.")

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= _now():
        raise AuthenticationError("Refresh token has expired. Sign in again.")

    user = db.users.get_by_id(record.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Account is not active.")

    new_expires_at = _now() + timedelta(days=settings.refresh_token_expire_days)
    new_raw = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    replacement = db.refresh_tokens.create(
        user_id=user.id,
        token_hash=hash_token(new_raw),
        family_id=record.family_id,
        expires_at=new_expires_at,
        created_at=_now(),
    )
    db.refresh_tokens.replace(record.id, replacement.id, _now())

    return user, new_raw


def revoke_refresh_token(db: Database, raw: str) -> None:
    """Revoke a single refresh token. Unknown tokens are ignored."""
    if not raw:
        return
    record = db.refresh_tokens.get_by_hash(hash_token(raw))
    if record is None or record.revoked_at is not None:
        return
    db.refresh_tokens.revoke(record.id, _now())


def revoke_family(db: Database, family_id: str) -> None:
    """Revoke every token in a rotation family."""
    db.refresh_tokens.revoke_family(family_id, _now())


def revoke_all_for_user(db: Database, user_id: int) -> None:
    """Revoke every live refresh token for a user (sign the user out everywhere)."""
    db.refresh_tokens.revoke_all_for_user(user_id, _now())


def purge_expired(db: Database) -> int:
    """Delete refresh tokens that expired more than a day ago."""
    return db.refresh_tokens.delete_older_than(_now() - timedelta(days=1))


def find_live_token(db: Database, raw: str) -> Optional[object]:
    """Return the live record for a raw token, if there is one."""
    record = db.refresh_tokens.get_by_hash(hash_token(raw))
    if record is None or record.revoked_at is not None:
        return None
    return record
