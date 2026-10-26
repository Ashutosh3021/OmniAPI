"""External service credential management endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status

from app.db.database import Database, get_db
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
    status_value = service.status.value if hasattr(service.status, "value") else str(service.status)
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
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> ExternalServiceResponse:
    _ = tenant_id
    service_name = body.service_name.value

    existing = db.external_services.list_for_user_named(current_user.id, [service_name])
    if existing:
        raise DuplicateResourceError(
            f"Service '{service_name}' is already configured. "
            f"Update it instead of adding a second one."
        )

    service = db.external_services.create(
        user_id=current_user.id,
        service_name=service_name,
        api_key_encrypted=encryption.encrypt(body.api_key),
        max_calls_per_hour=body.max_calls_per_hour,
        status=ExternalServiceStatus.ACTIVE.value,
        created_at=datetime.now(timezone.utc),
    )
    return _to_response(service)


@router.get("", response_model=list[ExternalServiceResponse])
def list_external_services(
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> list[ExternalServiceResponse]:
    _ = tenant_id
    services = db.external_services.list_for_user(current_user.id)
    return [_to_response(service) for service in services]


@router.get("/{service_id}", response_model=ExternalServiceResponse)
def get_external_service(
    service_id: int,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> ExternalServiceResponse:
    _ = tenant_id
    service = db.external_services.get_for_user(service_id, current_user.id)
    if service is None:
        raise ResourceNotFoundError("External service not found")
    return _to_response(service)


@router.post("/{service_id}/test", response_model=ExternalServiceTestResponse)
async def test_external_service(
    service_id: int,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> ExternalServiceTestResponse:
    """Verify the stored provider credential with one real provider call.

    Always returns 200 — the verdict (and the provider's own error message)
    is in the body, so the dashboard can show it inline.
    """
    _ = tenant_id
    service = db.external_services.get_for_user(service_id, current_user.id)
    if service is None:
        raise ResourceNotFoundError("External service not found")

    definition = SERVICE_CATALOG.get(service.service_name)
    if definition is None:
        raise ResourceNotFoundError(
            f"Service '{service.service_name}' is not supported by this platform."
        )

    success, message = await probe_service(definition, service.api_key_encrypted)

    now = datetime.now(timezone.utc)
    if success:
        service = db.external_services.update(
            service.id,
            status=ExternalServiceStatus.ACTIVE.value,
            clear_error=True,
            last_tested_at=now,
            updated_at=now,
        )
    else:
        # A rejected credential is an error state; other failures (rate
        # limits, upstream outages) leave the configured status alone.
        rejected = (
            "returned 401" in message or "returned 403" in message or "rejected" in message.lower()
        )
        service = db.external_services.update(
            service.id,
            error_message=message[:500],
            status=ExternalServiceStatus.ERROR.value if rejected else None,
            last_tested_at=now,
            updated_at=now,
        )

    if service is None:
        raise ResourceNotFoundError("External service not found")

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
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> ExternalServiceResponse:
    _ = tenant_id
    if db.external_services.get_for_user(service_id, current_user.id) is None:
        raise ResourceNotFoundError("External service not found")

    # A new credential invalidates whatever the old one told us.
    new_key = body.api_key is not None
    service = db.external_services.update(
        service_id,
        api_key_encrypted=encryption.encrypt(body.api_key) if new_key else None,
        max_calls_per_hour=body.max_calls_per_hour,
        status=body.status,
        clear_error=new_key,
        clear_last_tested=new_key,
        updated_at=datetime.now(timezone.utc),
    )
    if service is None:
        raise ResourceNotFoundError("External service not found")

    return _to_response(service)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_external_service(
    service_id: int,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> None:
    _ = tenant_id
    if db.external_services.get_for_user(service_id, current_user.id) is None:
        raise ResourceNotFoundError("External service not found")

    db.external_services.delete(service_id)
