"""Tenant isolation dependency derived from authenticated user."""

from fastapi import Depends

from app.middleware.auth_middleware import get_current_user
from app.models.user import User


async def get_tenant_id(current_user: User = Depends(get_current_user)) -> str:
    """Return tenant_id from the authenticated user (never trust client input)."""
    return str(current_user.user_id)
