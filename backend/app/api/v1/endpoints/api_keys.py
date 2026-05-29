"""API key management endpoints (JWT-authenticated, tenant-scoped)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.tenant_middleware import get_tenant_id
from app.models.api_key import APIKey
from app.models.user import User
from app.schemas.api_key import APIKeyCreate, APIKeyCreatedResponse, APIKeyResponse
from app.services import api_key_service
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> APIKeyCreatedResponse:
    """Create a new API key; raw key is returned only in this response."""
    _ = tenant_id  # enforce tenant context from JWT, not client input

    raw_key = api_key_service.generate_api_key()
    api_key = APIKey(
        user_id=current_user.id,
        key_hash=api_key_service.hash_api_key(raw_key),
        name=body.name,
        expires_at=body.expires_at,
        is_active=True,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    response = _to_response(api_key)
    return APIKeyCreatedResponse(**response.model_dump(), raw_key=raw_key)


@router.get("", response_model=list[APIKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> list[APIKeyResponse]:
    """List all API keys for the current tenant (no raw keys)."""
    _ = tenant_id
    stmt = (
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
    )
    keys = db.scalars(stmt).all()
    return [_to_response(key) for key in keys]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> None:
    """Soft-delete an API key by setting is_active to False."""
    _ = tenant_id
    api_key = db.scalar(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    if api_key is None:
        raise ResourceNotFoundError("API key not found")

    api_key.is_active = False
    db.commit()
