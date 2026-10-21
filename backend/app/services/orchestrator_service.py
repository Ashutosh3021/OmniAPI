"""Core orchestration engine with Redis cache and parallel provider fan-out."""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.external_service import ExternalService, ExternalServiceStatus
from app.models.usage_log import UsageLog
from app.models.user import User
from app.schemas.orchestrate import OrchestrateRequest, OrchestrateResponse, ServiceResult
from app.services.cache_service import SERVICE_TTL, CacheService
from app.services.provider_caller import call_provider
from app.services.rate_limiter import RateLimiter
from app.services.service_catalog import (
    SERVICE_CATALOG,
    ServiceDefinition,
    supported_service_names,
)
from app.services.webhook_service import WebhookService
from app.utils.exceptions import (
    RateLimitExceededError,
    ServiceNotConfiguredError,
    ValidationFailedError,
)

logger = logging.getLogger(__name__)

ORCHESTRATE_ENDPOINT = "/orchestrate"

# Upper bound on the serialized request parameters. Keeps a hostile client
# from pushing megabytes into the cache key, the broker and the provider.
MAX_PARAMS_BYTES = 8 * 1024


@dataclass
class _WorkItem:
    service_name: str
    definition: ServiceDefinition
    external_service: ExternalService
    cache_key: str
    params: dict[str, Any]
    cached_payload: Optional[dict[str, Any]] = None


class OrchestratorService:
    """Parallel orchestration with Redis cache and in-process provider calls."""

    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user
        self.settings = get_settings()

    async def orchestrate(self, request: OrchestrateRequest) -> OrchestrateResponse:
        self._validate_services(request.services)
        validated_params = self._validate_params(request)
        external_services = self._load_configured_services(request.services)

        await self._enforce_service_quotas(external_services)

        cache = CacheService()
        work_items = await self._build_work_items(
            request.services, external_services, validated_params, cache
        )

        total_start = time.monotonic()
        results = await self._collect_results(work_items, cache)
        total_time_ms = int((time.monotonic() - total_start) * 1000)

        self._log_usage(external_services, results)

        request_id = str(uuid.uuid4())
        response = OrchestrateResponse(
            request_id=request_id,
            results=results,
            total_time_ms=total_time_ms,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        all_succeeded = all(r.success for r in results)
        event_type = "orchestrate.complete" if all_succeeded else "orchestrate.failed"
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

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_services(self, service_names: list[str]) -> None:
        unknown = [s for s in service_names if s not in SERVICE_CATALOG]
        if unknown:
            raise ServiceNotConfiguredError(
                f"Unsupported service(s): {', '.join(sorted(unknown))}. "
                f"Supported services are: {', '.join(supported_service_names())}."
            )

    def _validate_params(self, request: OrchestrateRequest) -> dict[str, dict[str, Any]]:
        """Validate each service's parameters against its published schema."""
        validated: dict[str, dict[str, Any]] = {}
        errors: list[dict] = []

        for service_name in request.services:
            definition = SERVICE_CATALOG[service_name]
            raw = request.params.get(service_name, {})

            if not isinstance(raw, dict):
                errors.append(
                    {
                        "loc": ["body", "params", service_name],
                        "msg": "Parameters must be an object",
                        "type": "type_error.dict",
                    }
                )
                continue

            try:
                model = definition.params_model(**raw)
            except Exception as exc:  # pydantic ValidationError
                for error in _pydantic_errors(exc, service_name):
                    errors.append(error)
                continue

            validated[service_name] = model.model_dump(exclude_none=True)

        if errors:
            raise ValidationFailedError(errors)

        total = sum(len(json_bytes(p)) for p in validated.values())
        if total > MAX_PARAMS_BYTES:
            raise ValidationFailedError(
                [
                    {
                        "loc": ["body", "params"],
                        "msg": (
                            f"Parameters total {total} bytes, which exceeds the "
                            f"{MAX_PARAMS_BYTES} byte limit."
                        ),
                        "type": "value_error.too_large",
                    }
                ]
            )

        return validated

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def _load_configured_services(self, service_names: list[str]) -> dict[str, ExternalService]:
        stmt = select(ExternalService).where(
            ExternalService.user_id == self.user.id,
            ExternalService.service_name.in_(service_names),
        )
        records = {svc.service_name: svc for svc in self.db.scalars(stmt).all()}

        missing = [name for name in service_names if name not in records]
        if missing:
            raise ServiceNotConfiguredError(
                f"Service(s) not configured: {', '.join(missing)}. "
                f"Add your provider API key under External Services first."
            )

        inactive = [
            name
            for name, svc in records.items()
            if svc.status != ExternalServiceStatus.ACTIVE
        ]
        if inactive:
            raise ServiceNotConfiguredError(
                f"Service(s) not active: {', '.join(inactive)}. "
                f"Activate them under External Services first."
            )

        return records

    async def _enforce_service_quotas(
        self, external_services: dict[str, ExternalService]
    ) -> None:
        """Enforce each configured service's own calls-per-hour quota."""
        limiter = RateLimiter()
        for name, service in external_services.items():
            limit = service.max_calls_per_hour
            if limit <= 0:
                continue
            allowed, _ = await limiter.is_allowed_service(
                tenant_id=str(self.user.id),
                service_id=service.id,
                limit=limit,
            )
            if not allowed:
                retry_after = await limiter.retry_after_seconds(
                    tenant_id=str(self.user.id),
                    api_key_id=limiter.service_key(str(self.user.id), service.id),
                )
                minutes = max(1, round(retry_after / 60))
                raise RateLimitExceededError(
                    detail=(
                        f"Service '{name}' reached its limit of {limit} calls/hour. "
                        f"Raise the limit under External Services or try again in about "
                        f"{minutes} minute{'s' if minutes != 1 else ''}."
                    ),
                    retry_after=retry_after or 3600,
                )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def _build_work_items(
        self,
        service_names: list[str],
        external_services: dict[str, ExternalService],
        validated_params: dict[str, dict[str, Any]],
        cache: CacheService,
    ) -> list[_WorkItem]:
        work_items: list[_WorkItem] = []
        for service_name in service_names:
            external_service = external_services[service_name]
            params = validated_params.get(service_name, {})
            cache_key = CacheService.build_key(self.user.id, service_name, params)
            cached = await cache.get(cache_key)

            work_items.append(
                _WorkItem(
                    service_name=service_name,
                    definition=SERVICE_CATALOG[service_name],
                    external_service=external_service,
                    cache_key=cache_key,
                    params=params,
                    cached_payload=cached,
                )
            )
        return work_items

    async def _collect_results(
        self,
        work_items: list[_WorkItem],
        cache: CacheService,
    ) -> list[ServiceResult]:
        """Run every service concurrently and collect the results in order."""

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
            return await self._resolve_provider(item, cache)

        return list(await asyncio.gather(*(resolve(item) for item in work_items)))

    async def _resolve_provider(
        self,
        item: _WorkItem,
        cache: CacheService,
    ) -> ServiceResult:
        start = time.monotonic()
        payload = await call_provider(
            item.definition,
            item.external_service.api_key_encrypted,
            item.params,
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
            try:
                await cache.set(item.cache_key, cache_payload, ttl)
            except Exception:  # noqa: BLE001 - a cache write must not fail the request
                logger.warning("Cache write failed for %s", item.service_name, exc_info=True)

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

    # ------------------------------------------------------------------
    # Usage recording
    # ------------------------------------------------------------------

    def _log_usage(
        self,
        external_services: dict[str, ExternalService],
        results: list[ServiceResult],
    ) -> None:
        """Record one usage row per service call.

        The rows are flushed to the database by the caller (see
        ``flush_usage``) so the response is not held up by the write.
        """
        for result in results:
            external_service = external_services.get(result.service)
            if external_service is None:
                continue
            error_message = result.error[:500] if result.error else None
            self.db.add(
                UsageLog(
                    user_id=self.user.id,
                    service_id=external_service.id,
                    endpoint=f"{ORCHESTRATE_ENDPOINT}/{result.service}",
                    response_time_ms=result.response_time_ms,
                    status_code=200 if result.success else 500,
                    cache_hit=result.cache_hit,
                    error_message=error_message,
                    created_at=datetime.now(timezone.utc),
                )
            )

    def flush_usage(self) -> None:
        """Commit the pending usage rows."""
        try:
            self.db.commit()
        except Exception:  # noqa: BLE001 - never fail a served request
            logger.exception("Failed to record usage")
            self.db.rollback()


def json_bytes(value: Any) -> bytes:
    """Serialize a value to bytes for size accounting."""
    import json

    return json.dumps(value, default=str).encode("utf-8")


def _pydantic_errors(exc: Exception, service_name: str) -> list[dict]:
    """Convert a pydantic validation error into FastAPI's error shape."""
    errors = getattr(exc, "errors", None)
    if not callable(errors):
        return [
            {
                "loc": ["body", "params", service_name],
                "msg": str(exc),
                "type": "value_error",
            }
        ]

    formatted: list[dict] = []
    for error in errors():
        loc = list(error.get("loc", ()))
        # Drop the model name pydantic prepends.
        if loc and loc[0] in ("params", "body"):
            loc = loc[1:]
        formatted.append(
            {
                "loc": ["body", "params", service_name, *loc],
                "msg": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error"),
            }
        )
    return formatted
