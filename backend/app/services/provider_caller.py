"""Call an upstream provider directly, with in-process retries.

The provider call used to be dispatched to a Celery worker and then awaited
through the result backend, which turned an "async" orchestration into a
synchronous round trip: a broker publish, a worker pickup, a result write and
a poll — all while the request held a database session and a thread. Calling
the provider directly lets the orchestrator fan out with ``asyncio.gather``,
so the total latency is the slowest single upstream call rather than the sum
of all of them.
"""

import asyncio
import logging
from typing import Any, Optional

from app.services.service_catalog import ServiceDefinition
from app.utils.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
RETRY_DELAYS_SECONDS = (1.0, 2.0)


async def call_provider(
    definition: ServiceDefinition,
    encrypted_api_key: str,
    params: dict[str, Any],
    max_attempts: int = MAX_ATTEMPTS,
) -> dict[str, Any]:
    """
    Call the upstream provider, retrying transient failures.

    Returns a payload dict with ``success``, ``data``, ``fetched_at`` and
    ``error`` keys. Never raises for an upstream failure — the orchestrator
    reports the error per service.
    """
    last_error: Optional[str] = None

    for attempt in range(max_attempts):
        try:
            client = definition.client_cls(encrypted_api_key)
            payload = await client.fetch(params)
            return {
                "success": True,
                "service": definition.service_name,
                "data": payload.get("data"),
                "fetched_at": payload.get("fetched_at"),
                "error": None,
            }
        except ExternalAPIError as exc:
            last_error = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            if not exc.retryable:
                break
        except Exception as exc:  # noqa: BLE001 - reported per service
            last_error = f"{definition.label} request failed: {exc}"
            logger.warning(
                "Provider %s failed (attempt %s/%s): %s",
                definition.service_name,
                attempt + 1,
                max_attempts,
                exc,
            )

        if attempt < max_attempts - 1:
            await asyncio.sleep(RETRY_DELAYS_SECONDS[min(attempt, len(RETRY_DELAYS_SECONDS) - 1)])

    return {
        "success": False,
        "service": definition.service_name,
        "data": None,
        "fetched_at": None,
        "error": last_error or f"{definition.label} request failed",
    }
