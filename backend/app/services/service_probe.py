"""Verify a stored provider credential against the upstream API.

Users paste a third-party key into the dashboard and need to know it works
before they wire it into their application. This performs one minimal call
against the provider and reports the verdict.
"""

import logging
from datetime import datetime, timezone

from app.external_apis.base import BaseAPIClient
from app.services.service_catalog import ServiceDefinition
from app.utils.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)


async def probe_service(
    definition: ServiceDefinition,
    encrypted_api_key: str,
) -> tuple[bool, str]:
    """
    Call the provider once with a minimal valid request.

    Returns ``(success, message)`` where the message is safe to show to the
    end user.
    """
    client: BaseAPIClient = definition.client_cls(encrypted_api_key)
    try:
        await client.fetch(definition.example)
    except ExternalAPIError as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return False, detail
    except Exception as exc:  # noqa: BLE001 - surfaced to the user as a message
        logger.exception("Provider probe failed for %s", definition.service_name)
        return False, f"{definition.label} probe failed: {exc}"

    return True, "Connection successful"


def now_utc() -> datetime:
    """Current UTC timestamp (timezone-aware)."""
    return datetime.now(timezone.utc)
