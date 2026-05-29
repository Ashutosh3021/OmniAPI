"""User model helpers for auth flows."""

from app.models.user import User
from app.schemas.auth import UserResponse


def split_full_name(full_name: str) -> tuple[str | None, str | None]:
    """Split a display name into first and last name parts."""
    parts = full_name.strip().split(maxsplit=1)
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]


def user_to_response(user: User) -> UserResponse:
    """Map a User ORM instance to UserResponse."""
    tier = user.tier.value if hasattr(user.tier, "value") else str(user.tier)
    return UserResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        tier=tier,
        created_at=user.created_at,
    )
