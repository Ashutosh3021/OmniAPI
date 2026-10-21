"""External service credential schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ExternalServiceName(str, Enum):
    """Supported external API integrations.

    Kept in lockstep with ``app.services.service_catalog.SERVICE_CATALOG``;
    the startup assertion in ``app.main`` enforces that.
    """

    WEATHER = "weather"
    NEWS = "news"
    STOCK = "stock"


class ExternalServiceCreate(BaseModel):
    """Register credentials for an external API."""

    service_name: ExternalServiceName
    api_key: str = Field(..., min_length=1)
    max_calls_per_hour: int = Field(default=100, ge=1, le=100_000)


class ExternalServiceUpdate(BaseModel):
    """Update external service settings.

    ``service_name`` is intentionally immutable — it is the upstream routing
    key and the response-cache namespace for the tenant.
    """

    api_key: Optional[str] = Field(default=None, min_length=1)
    max_calls_per_hour: Optional[int] = Field(default=None, ge=1, le=100_000)
    status: Optional[str] = Field(default=None, pattern="^(active|inactive)$")


class ExternalServiceResponse(BaseModel):
    """External service metadata (no API keys)."""

    model_config = ConfigDict(from_attributes=True)

    service_id: int
    service_name: str
    max_calls_per_hour: int
    status: str
    error_message: Optional[str] = None
    last_tested_at: Optional[datetime] = None
    created_at: datetime


class SupportedServiceParam(BaseModel):
    """Description of a single parameter accepted by a service."""

    type: str = Field(..., description="string | number | boolean")
    required: bool
    example: Optional[Any] = None
    default: Optional[Any] = None
    description: Optional[str] = None


class SupportedService(BaseModel):
    """A service the platform knows how to orchestrate."""

    service_name: str
    label: str
    description: str
    signup_url: str
    docs_url: str
    required_params: str
    example: dict[str, Any]
    params: dict[str, SupportedServiceParam]


class SupportedServicesResponse(BaseModel):
    """The full catalogue of supported services."""

    services: list[SupportedService]


class ExternalServiceTestResponse(BaseModel):
    """Result of testing a stored provider credential."""

    success: bool
    service_name: str
    message: str
    checked_at: datetime
