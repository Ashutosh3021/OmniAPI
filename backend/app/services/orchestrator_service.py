"""Core orchestration engine for external API calls."""

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Type

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.external_apis.base import BaseAPIClient
from app.external_apis.news_api import NewsAPIClient
from app.external_apis.stock_api import StockAPIClient
from app.external_apis.weather_api import WeatherAPIClient
from app.models.external_service import ExternalService, ExternalServiceStatus
from app.models.usage_log import UsageLog
from app.models.user import User
from app.schemas.orchestrate import OrchestrateRequest, OrchestrateResponse, ServiceResult
from app.utils.exceptions import ExternalAPIError, ServiceNotConfiguredError

CLIENT_REGISTRY: dict[str, Type[BaseAPIClient]] = {
    "weather": WeatherAPIClient,
    "news": NewsAPIClient,
    "stock": StockAPIClient,
}

ORCHESTRATE_ENDPOINT = "/orchestrate"


class OrchestratorService:
    """Sequential orchestration of external API calls for a tenant."""

    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user

    async def orchestrate(self, request: OrchestrateRequest) -> OrchestrateResponse:
        unknown = [s for s in request.services if s not in CLIENT_REGISTRY]
        if unknown:
            raise ServiceNotConfiguredError(
                f"Unknown service(s): {', '.join(unknown)}"
            )

        external_services = self._load_configured_services(request.services)
        total_start = time.monotonic()
        results: list[ServiceResult] = []

        for service_name in request.services:
            external_service = external_services[service_name]
            service_params = request.params.get(service_name, {})
            result = await self._call_service(
                service_name=service_name,
                external_service=external_service,
                params=service_params,
            )
            results.append(result)
            self._log_usage(external_service, result)

        self.db.commit()

        total_time_ms = int((time.monotonic() - total_start) * 1000)
        return OrchestrateResponse(
            request_id=str(uuid.uuid4()),
            results=results,
            total_time_ms=total_time_ms,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _load_configured_services(self, service_names: list[str]) -> dict[str, ExternalService]:
        stmt = select(ExternalService).where(
            ExternalService.user_id == self.user.id,
            ExternalService.service_name.in_(service_names),
        )
        records = {svc.service_name: svc for svc in self.db.scalars(stmt).all()}

        missing = [name for name in service_names if name not in records]
        if missing:
            raise ServiceNotConfiguredError(
                f"Service(s) not configured: {', '.join(missing)}"
            )

        inactive = [
            name
            for name, svc in records.items()
            if svc.status != ExternalServiceStatus.ACTIVE
        ]
        if inactive:
            raise ServiceNotConfiguredError(
                f"Service(s) not active: {', '.join(inactive)}"
            )

        return records

    async def _call_service(
        self,
        service_name: str,
        external_service: ExternalService,
        params: dict[str, Any],
    ) -> ServiceResult:
        client_cls = CLIENT_REGISTRY[service_name]
        client = client_cls(external_service.api_key_encrypted)

        start = time.monotonic()
        try:
            payload = await client.fetch(params)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return ServiceResult(
                service=service_name,
                success=True,
                data=payload.get("data"),
                error=None,
                response_time_ms=elapsed_ms,
                cache_hit=False,
            )
        except ExternalAPIError as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            return ServiceResult(
                service=service_name,
                success=False,
                data=None,
                error=detail,
                response_time_ms=elapsed_ms,
                cache_hit=False,
            )
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return ServiceResult(
                service=service_name,
                success=False,
                data=None,
                error=str(exc),
                response_time_ms=elapsed_ms,
                cache_hit=False,
            )

    def _log_usage(self, external_service: ExternalService, result: ServiceResult) -> None:
        error_message = result.error[:500] if result.error else None
        log = UsageLog(
            user_id=self.user.id,
            service_id=external_service.id,
            endpoint=f"{ORCHESTRATE_ENDPOINT}/{result.service}",
            response_time_ms=result.response_time_ms,
            status_code=200 if result.success else 500,
            cache_hit=False,
            error_message=error_message,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
