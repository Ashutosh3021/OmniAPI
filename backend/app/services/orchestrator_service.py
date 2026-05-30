"""Core orchestration engine with Redis cache and Celery workers."""

import asyncio
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from celery.result import AsyncResult
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.external_service import ExternalService, ExternalServiceStatus
from app.models.usage_log import UsageLog
from app.models.user import User
from app.schemas.orchestrate import OrchestrateRequest, OrchestrateResponse, ServiceResult
from app.services.cache_service import SERVICE_TTL, CacheService
from app.services.webhook_service import WebhookService
from app.tasks.external_api_tasks import call_news_api, call_stock_api, call_weather_api
from app.utils.exceptions import ServiceNotConfiguredError

TASK_REGISTRY = {
    "weather": call_weather_api,
    "news": call_news_api,
    "stock": call_stock_api,
}

ORCHESTRATE_ENDPOINT = "/orchestrate"


@dataclass
class _WorkItem:
    service_name: str
    external_service: ExternalService
    cache_key: str
    params: dict[str, Any]
    cached_payload: Optional[dict[str, Any]] = None
    async_result: Optional[AsyncResult] = None


class OrchestratorService:
    """Parallel orchestration with Redis cache and Celery task offload."""

    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user
        self.settings = get_settings()

    async def orchestrate(self, request: OrchestrateRequest) -> OrchestrateResponse:
        unknown = [s for s in request.services if s not in TASK_REGISTRY]
        if unknown:
            raise ServiceNotConfiguredError(
                f"Unknown service(s): {', '.join(unknown)}"
            )

        external_services = self._load_configured_services(request.services)
        cache = CacheService()
        work_items: list[_WorkItem] = []

        try:
            for service_name in request.services:
                external_service = external_services[service_name]
                params = request.params.get(service_name, {})
                cache_key = CacheService.build_key(self.user.id, service_name, params)
                cached = await cache.get(cache_key)

                if cached is not None:
                    work_items.append(
                        _WorkItem(
                            service_name=service_name,
                            external_service=external_service,
                            cache_key=cache_key,
                            params=params,
                            cached_payload=cached,
                        )
                    )
                else:
                    task_fn = TASK_REGISTRY[service_name]
                    async_result = task_fn.delay(
                        tenant_id=str(self.user.id),
                        encrypted_key=external_service.api_key_encrypted,
                        params=params,
                    )
                    work_items.append(
                        _WorkItem(
                            service_name=service_name,
                            external_service=external_service,
                            cache_key=cache_key,
                            params=params,
                            async_result=async_result,
                        )
                    )

            total_start = time.monotonic()
            results = await self._collect_results(work_items, cache)
            total_time_ms = int((time.monotonic() - total_start) * 1000)

            for item, result in zip(work_items, results, strict=True):
                self._log_usage(item.external_service, result)

            self.db.commit()

            request_id = str(uuid.uuid4())
            response = OrchestrateResponse(
                request_id=request_id,
                results=results,
                total_time_ms=total_time_ms,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            all_succeeded = all(r.success for r in results)
            event_type = (
                "orchestrate.complete" if all_succeeded else "orchestrate.failed"
            )
            WebhookService(self.db).dispatch_event(
                tenant_id=str(self.user.id),
                event_type=event_type,
                data={
                    "request_id": request_id,
                    "services": request.services,
                    "total_time_ms": total_time_ms,
                    "results_summary": [
                        {
                            "service": r.service,
                            "success": r.success,
                            "cache_hit": r.cache_hit,
                        }
                        for r in results
                    ],
                },
            )

            return response
        finally:
            await cache.close()

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

    async def _collect_results(
        self,
        work_items: list[_WorkItem],
        cache: CacheService,
    ) -> list[ServiceResult]:
        async def resolve(item: _WorkItem) -> ServiceResult:
            if item.cached_payload is not None:
                return ServiceResult(
                    service=item.service_name,
                    success=True,
                    data=item.cached_payload.get("data"),
                    error=None,
                    response_time_ms=0,
                    cache_hit=True,
                )
            return await self._resolve_task_result(item, cache)

        return list(await asyncio.gather(*(resolve(item) for item in work_items)))

    async def _resolve_task_result(
        self,
        item: _WorkItem,
        cache: CacheService,
    ) -> ServiceResult:
        start = time.monotonic()
        assert item.async_result is not None

        try:
            payload = await asyncio.to_thread(
                item.async_result.get,
                timeout=self.settings.celery_task_timeout,
            )
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            error = "Timeout" if "Timeout" in type(exc).__name__ else str(exc)
            return ServiceResult(
                service=item.service_name,
                success=False,
                data=None,
                error=error,
                response_time_ms=elapsed_ms,
                cache_hit=False,
            )

        elapsed_ms = int((time.monotonic() - start) * 1000)
        success = bool(payload.get("success"))

        if success:
            cache_payload = {
                "service": item.service_name,
                "data": payload.get("data"),
                "fetched_at": payload.get("fetched_at"),
            }
            ttl = SERVICE_TTL.get(item.service_name, 300)
            await cache.set(item.cache_key, cache_payload, ttl)

            return ServiceResult(
                service=item.service_name,
                success=True,
                data=payload.get("data"),
                error=None,
                response_time_ms=elapsed_ms,
                cache_hit=False,
            )

        return ServiceResult(
            service=item.service_name,
            success=False,
            data=None,
            error=payload.get("error") or "External API request failed",
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
            cache_hit=result.cache_hit,
            error_message=error_message,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
