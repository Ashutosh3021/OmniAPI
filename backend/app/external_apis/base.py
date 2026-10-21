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

