"""External service credential management endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.tenant_middleware import get_tenant_id
from app.models.external_service import ExternalService, ExternalServiceStatus
from app.models.user import User
from app.schemas.external_service import (
    ExternalServiceCreate,
    ExternalServiceResponse,
    ExternalServiceUpdate,
)
from app.utils import encryption
from app.utils.decorators import require_auth
from app.utils.exceptions import DuplicateResourceError, ResourceNotFoundError

router = APIRouter()


def _to_response(service: ExternalService) -> ExternalServiceResponse:
    status_value = (
        service.status.value if hasattr(service.status, "value") else str(service.status)
    )
    return ExternalServiceResponse(
        service_id=service.id,
        service_name=service.service_name,
        max_calls_per_hour=service.max_calls_per_hour,
        status=status_value,
        created_at=service.created_at,
    )


@router.post(
    "",
    response_model=ExternalServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_external_service(
    body: ExternalServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> ExternalServiceResponse:
    _ = tenant_id
    service_name = body.service_name.value

    existing = db.scalar(
        select(ExternalService).where(
            ExternalService.user_id == current_user.id,
            ExternalService.service_name == service_name,
        )
    )
    if existing is not None:
        raise DuplicateResourceError(
            f"External service '{service_name}' is already configured"
        )

    service = ExternalService(
        user_id=current_user.id,
        service_name=service_name,
        api_key_encrypted=encryption.encrypt(body.api_key),
        max_calls_per_hour=body.max_calls_per_hour,
        status=ExternalServiceStatus.ACTIVE,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return _to_response(service)


@router.get("", response_model=list[ExternalServiceResponse])
def list_external_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> list[ExternalServiceResponse]:
    _ = tenant_id
    stmt = (
        select(ExternalService)
        .where(ExternalService.user_id == current_user.id)
        .order_by(ExternalService.created_at.desc())
    )
    services = db.scalars(stmt).all()
    return [_to_response(service) for service in services]


@router.get("/{service_id}", response_model=ExternalServiceResponse)
def get_external_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> ExternalServiceResponse:
    _ = tenant_id
    service = db.scalar(
        select(ExternalService).where(
            ExternalService.id == service_id,
            ExternalService.user_id == current_user.id,
        )
    )
    if service is None:
        raise ResourceNotFoundError("External service not found")
    return _to_response(service)


@router.patch("/{service_id}", response_model=ExternalServiceResponse)
def update_external_service(
    service_id: int,
    body: ExternalServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> ExternalServiceResponse:
    _ = tenant_id
    service = db.scalar(
        select(ExternalService).where(
            ExternalService.id == service_id,
            ExternalService.user_id == current_user.id,
        )
    )
    if service is None:
        raise ResourceNotFoundError("External service not found")

    if body.api_key is not None:
        service.api_key_encrypted = encryption.encrypt(body.api_key)
    if body.max_calls_per_hour is not None:
        service.max_calls_per_hour = body.max_calls_per_hour
    if body.status is not None:
        try:
            service.status = ExternalServiceStatus(body.status)
        except ValueError as exc:
            raise ResourceNotFoundError("Invalid status value") from exc

    db.commit()
    db.refresh(service)
    return _to_response(service)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_external_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> None:
    _ = tenant_id
    service = db.scalar(
        select(ExternalService).where(
            ExternalService.id == service_id,
            ExternalService.user_id == current_user.id,
        )
    )
    if service is None:
        raise ResourceNotFoundError("External service not found")

    db.delete(service)
    db.commit()
