"""External service credential management endpoints."""

import logging
from datetime import datetime, timezone

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
    ExternalServiceTestResponse,
    ExternalServiceUpdate,
    SupportedService,
    SupportedServicesResponse,
)
from app.services.service_catalog import SERVICE_CATALOG, describe_all_services
from app.services.service_probe import probe_service
from app.utils import encryption
from app.utils.decorators import require_auth
from app.utils.exceptions import DuplicateResourceError, ResourceNotFoundError

logger = logging.getLogger(__name__)

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
        error_message=service.error_message,
        last_tested_at=service.last_tested_at,
        created_at=service.created_at,
    )


@router.get("/supported", response_model=SupportedServicesResponse)
def list_supported_services(
    current_user: User = Depends(require_auth),
) -> SupportedServicesResponse:
    """Return the catalogue of external APIs this platform can orchestrate.

    The dashboard renders its provider picker from this response, so the list
    of supported services is never hardcoded on the client.
    """
    described = describe_all_services()
    services = [
        SupportedService(
            service_name=item["service_name"],
            label=item["label"],
            description=item["description"],
            signup_url=item["signup_url"],
            docs_url=item["docs_url"],
            required_params=item["required_params"],
            example=item["example"],
            params=item["params"],
        )
        for item in described
    ]
    return SupportedServicesResponse(services=services)


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
            f"Service '{service_name}' is already configured. "
            f"Update it instead of adding a second one."
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


@router.post("/{service_id}/test", response_model=ExternalServiceTestResponse)
async def test_external_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> ExternalServiceTestResponse:
    """Verify the stored provider credential with one real provider call.

    Always returns 200 — the verdict (and the provider's own error message)
    is in the body, so the dashboard can show it inline.
    """
    _ = tenant_id
    service = db.scalar(
        select(ExternalService).where(
            ExternalService.id == service_id,
            ExternalService.user_id == current_user.id,
        )
    )
    if service is None:
        raise ResourceNotFoundError("External service not found")

    definition = SERVICE_CATALOG.get(service.service_name)
    if definition is None:
        raise ResourceNotFoundError(
            f"Service '{service.service_name}' is not supported by this platform."
        )

    success, message = await probe_service(definition, service.api_key_encrypted)

    now = datetime.now(timezone.utc)
    service.last_tested_at = now
    if success:
        service.status = ExternalServiceStatus.ACTIVE
        service.error_message = None
    else:
        service.error_message = message[:500]
        # A rejected credential is an error state; other failures (rate
        # limits, upstream outages) leave the configured status alone.
        if "returned 401" in message or "returned 403" in message or "rejected" in message.lower():
            service.status = ExternalServiceStatus.ERROR
    db.commit()
    db.refresh(service)

    return ExternalServiceTestResponse(
        success=success,
        service_name=service.service_name,
        message=message,
        checked_at=now,
    )


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
        # A new credential invalidates whatever the old one told us.
        service.error_message = None
        service.last_tested_at = None
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
