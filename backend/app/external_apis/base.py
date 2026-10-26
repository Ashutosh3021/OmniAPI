"""Abstract base class for external API clients."""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.service_params import ServiceParams


class BaseAPIClient(ABC):
    """Base interface for external API clients."""

    service_name: str
    #: Parameter model describing what this service accepts.
    params_model: type[ServiceParams] = ServiceParams

    @abstractmethod
    async def fetch(self, params: dict) -> dict:
        """Fetch data from the external API. Returns normalized response dict."""

    @abstractmethod
    def validate_params(self, params: dict) -> bool:
        """Validate required params before making the call."""

    async def test_credential(self) -> None:
        """Raise ``ExternalAPIError`` if the stored credential is not usable.

        The default implementation performs a minimal real call. Clients whose
        provider has no cheap call may override this.
        """
        from app.utils.exceptions import ExternalAPIError

        try:
            await self.fetch(self.minimal_params())
        except ExternalAPIError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalised to ExternalAPIError
            raise ExternalAPIError(f"Credential check failed: {exc}") from exc

    def minimal_params(self) -> dict[str, Any]:
        """Smallest valid parameter set for this service."""
        from app.services.service_catalog import get_service

        definition = get_service(self.service_name)
        return dict(definition.example) if definition else {}

    @classmethod
    def label(cls) -> str:
        """Human-readable provider name, e.g. "OpenWeatherMap"."""
        from app.services.service_catalog import get_service

        definition = get_service(cls.service_name)
        return definition.label if definition else cls.service_name

    @classmethod
    def upstream_error(cls, status_code: int) -> str:
        """
        Build an actionable message for an upstream HTTP failure.

        The message names the provider, what went wrong, and what the user
        can do about it — a bare status code is useless to someone whose
        provider key was rejected.
        """
        label = cls.label()
        if status_code in (401, 403):
            return (
                f"{label} rejected your API key ({status_code}). "
                f"Update it under External Services."
            )
        if status_code == 429:
            return (
                f"{label} rate limit reached ({status_code}). "
                f"Raise your limit under External Services or try again shortly."
            )
        if status_code >= 500:
            return f"{label} is unavailable ({status_code}). Try again shortly."
        return f"{label} returned {status_code}. Check the request parameters."
