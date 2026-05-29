"""Shared FastAPI dependencies."""

from app.db.session import get_db
from app.middleware.auth_middleware import get_current_user, oauth2_scheme
from app.middleware.tenant_middleware import get_tenant_id
from app.utils.decorators import require_api_key, require_auth, require_auth_or_api_key

__all__ = [
    "get_db",
    "get_current_user",
    "get_tenant_id",
    "oauth2_scheme",
    "require_auth",
    "require_api_key",
    "require_auth_or_api_key",
]
