"""API key management endpoints (JWT-authenticated, tenant-scoped)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status

from app.db.database import Database, get_db
from app.middleware.tenant_middleware import get_tenant_id
from app.models.api_key import APIKey
from app.models.user import User
from app.schemas.api_key import APIKeyCreate, APIKeyCreatedResponse, APIKeyResponse, APIKeyUpdate
from app.services import api_key_service
from app.services.webhook_service import WebhookService
from app.utils.decorators import require_auth
from app.utils.exceptions import ResourceNotFoundError

router = APIRouter()


def _to_response(api_key: APIKey) -> APIKeyResponse:
    return APIKeyResponse(
        key_id=api_key.id,
        name=api_key.name,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.post("", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    body: APIKeyCreate,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> APIKeyCreatedResponse:
    """Create a new API key; raw key is returned only in this response."""
    _ = tenant_id  # enforce tenant context from JWT, not client input

    raw_key = api_key_service.generate_api_key()
    api_key = db.api_keys.create(
        user_id=current_user.id,
        key_hash=api_key_service.hash_api_key(raw_key),
        name=body.name,
        expires_at=body.expires_at,
        created_at=datetime.now(timezone.utc),
    )

    WebhookService(db).dispatch_event(
        tenant_id=str(current_user.id),
        event_type="api_key.created",
        data={"key_id": api_key.id, "name": api_key.name},
    )

    response = _to_response(api_key)
    return APIKeyCreatedResponse(**response.model_dump(), raw_key=raw_key)


@router.get("", response_model=list[APIKeyResponse])
def list_api_keys(
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> list[APIKeyResponse]:
    """List all API keys for the current tenant (no raw keys)."""
    _ = tenant_id
    keys = db.api_keys.list_for_user(current_user.id)
    return [_to_response(key) for key in keys]


@router.get("/{key_id}", response_model=APIKeyResponse)
def get_api_key(
    key_id: int,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> APIKeyResponse:
    """Get a specific API key by ID for the current tenant (no raw key)."""
    _ = tenant_id
    api_key = db.api_keys.get_for_user(key_id, current_user.id)
    if api_key is None:
        raise ResourceNotFoundError("API key not found")

    return _to_response(api_key)


@router.patch("/{key_id}", response_model=APIKeyResponse)
def update_api_key(
    key_id: int,
    body: APIKeyUpdate,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> APIKeyResponse:
    """Update the name, expiry or active state of an existing API key.

    Revoking (``is_active: false``) keeps the record so the traffic the key
    produced remains attributable; deleting removes it entirely.
    """
    _ = tenant_id
    if db.api_keys.get_for_user(key_id, current_user.id) is None:
        raise ResourceNotFoundError("API key not found")

    api_key = db.api_keys.update(
        key_id,
        name=body.name,
        expires_at=body.expires_at,
        is_active=body.is_active,
        updated_at=datetime.now(timezone.utc),
    )
    if api_key is None:
        raise ResourceNotFoundError("API key not found")

    return _to_response(api_key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(
    key_id: int,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> None:
    """Permanently delete an API key for the current tenant."""
    _ = tenant_id
    if db.api_keys.get_for_user(key_id, current_user.id) is None:
        raise ResourceNotFoundError("API key not found")

    db.api_keys.delete(key_id)
