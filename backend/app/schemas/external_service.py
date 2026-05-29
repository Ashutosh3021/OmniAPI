"""External service credential schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ExternalServiceName(str, Enum):
    """Supported external API integrations."""

    WEATHER = "weather"
    NEWS = "news"
    STOCK = "stock"


class ExternalServiceCreate(BaseModel):
    """Register credentials for an external API."""

    service_name: ExternalServiceName
    api_key: str = Field(..., min_length=1)
    max_calls_per_hour: int = Field(default=100, ge=1)


class ExternalServiceUpdate(BaseModel):
    """Update external service settings."""

    api_key: Optional[str] = Field(default=None, min_length=1)
    max_calls_per_hour: Optional[int] = Field(default=None, ge=1)
    status: Optional[str] = None


class ExternalServiceResponse(BaseModel):
    """External service metadata (no API keys)."""

    model_config = ConfigDict(from_attributes=True)

    service_id: int
    service_name: str
    max_calls_per_hour: int
    status: str
    created_at: datetime
