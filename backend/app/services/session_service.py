"""Refresh token issuance, rotation and revocation.

Refresh tokens are opaque random strings, not JWTs. The server keeps a
SHA-256 hash of each token, which makes three things possible that a purely
stateless JWT cannot do:

* **Rotation** — every refresh issues a new token and revokes the old one.
* **Revocation** — logging out or changing a password kills the session
  server-side instead of waiting for the token to expire.
* **Reuse detection** — presenting an already-revoked token means it leaked,
  so the whole rotation family is revoked.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.utils.exceptions import AuthenticationError

REFRESH_TOKEN_BYTES = 32


def hash_token(raw: str) -> str:
    """Hash a raw token for storage. The raw value is never persisted."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _create_record(
    db: Session,
    user_id: int,
    family_id: str,
    expires_at: datetime,
) -> Tuple[str, RefreshToken]:
    """Create a refresh token row and return the raw token and the record."""
    raw = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    record = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(raw),
        family_id=family_id,
        expires_at=expires_at,
    )
    db.add(record)
    db.flush()  # assign the id without committing
    return raw, record


def issue_refresh_token(db: Session, user: User) -> str:
    """Issue a brand new refresh token in its own rotation family."""
    settings = get_settings()
    expires_at = _now() + timedelta(days=settings.refresh_token_expire_days)
    raw, _ = _create_record(db, user.id, str(uuid.uuid4()), expires_at)
    db.commit()
    return raw


def rotate_refresh_token(db: Session, raw: str) -> Tuple[User, str]:
    """
    Exchange a valid refresh token for a new one.

    The presented token is revoked. Presenting an already-revoked token is
    treated as a leak: the entire family is revoked and the request fails.
    """
    settings = get_settings()
    record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw))
    )
    if record is None:
        raise AuthenticationError("Invalid refresh token. Sign in again.")

    if record.is_revoked:
        revoke_family(db, record.family_id)
        raise AuthenticationError(
            "This refresh token was already used. All sessions have been revoked "
            "for safety. Sign in again."
        )

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= _now():
        raise AuthenticationError("Refresh token has expired. Sign in again.")

    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Account is not active.")

    new_expires_at = _now() + timedelta(days=settings.refresh_token_expire_days)
    new_raw, new_record = _create_record(
        db, user.id, record.family_id, new_expires_at
    )
    record.revoked_at = _now()
    record.replaced_by_id = new_record.id
    db.commit()

    return user, new_raw


def revoke_refresh_token(db: Session, raw: str) -> None:
    """Revoke a single refresh token. Unknown tokens are ignored."""
    if not raw:
        return
    record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw))
    )
    if record is None or record.is_revoked:
        return
    record.revoked_at = _now()
    db.commit()


def revoke_family(db: Session, family_id: str) -> None:
    """Revoke every token in a rotation family."""
    records = db.scalars(
        select(RefreshToken).where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
    ).all()
    for record in records:
        record.revoked_at = _now()
    db.commit()


def revoke_all_for_user(db: Session, user_id: int) -> None:
    """Revoke every live refresh token for a user (password change, etc.)."""
    records = db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    ).all()
    for record in records:
        record.revoked_at = _now()
    db.commit()


def purge_expired(db: Session) -> int:
    """Delete refresh tokens that expired more than a day ago."""
    cutoff = _now() - timedelta(days=1)
    records = db.scalars(
        select(RefreshToken).where(RefreshToken.expires_at < cutoff)
    ).all()
    for record in records:
        db.delete(record)
    db.commit()
    return len(records)


def find_live_token(db: Session, raw: str) -> Optional[RefreshToken]:
    """Return the live record for a raw token, if there is one."""
    return db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(raw),
            RefreshToken.revoked_at.is_(None),
        )
    )
