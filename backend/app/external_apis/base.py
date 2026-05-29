"""Abstract base class for external API clients."""

from abc import ABC, abstractmethod


class BaseAPIClient(ABC):
    """Base interface for OmniAPI external service clients."""

    service_name: str

    @abstractmethod
    async def fetch(self, params: dict) -> dict:
        """Fetch data from the external API. Returns normalized response dict."""

    @abstractmethod
    def validate_params(self, params: dict) -> bool:
        """Validate required params before making the call."""
