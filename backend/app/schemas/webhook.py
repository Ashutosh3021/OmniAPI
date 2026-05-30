"""Webhook subscription and delivery payload schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WebhookEventType(str, Enum):
    """Supported webhook event types."""

    ORCHESTRATE_COMPLETE = "orchestrate.complete"
    ORCHESTRATE_FAILED = "orchestrate.failed"
    API_KEY_CREATED = "api_key.created"


class WebhookCreate(BaseModel):
    """Register a new outbound webhook."""

    url: str = Field(..., max_length=500)
    event_type: WebhookEventType

    @field_validator("url")
    @classmethod
    def validate_https_url(cls, value: str) -> str:
        if not value.lower().startswith("https://"):
            raise ValueError("Webhook URL must use HTTPS")
        return value


class WebhookUpdate(BaseModel):
    """Update webhook URL or active status."""

    url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None

    @field_validator("url")
    @classmethod
    def validate_https_url(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.lower().startswith("https://"):
            raise ValueError("Webhook URL must use HTTPS")
        return value


class WebhookResponse(BaseModel):
    """Webhook subscription metadata."""

    model_config = ConfigDict(from_attributes=True)

    webhook_id: int
    url: str
    event_type: str
    is_active: bool
    retry_count: int
    created_at: datetime


class WebhookCreatedResponse(WebhookResponse):
    """Webhook created; signing secret is returned only once."""

    secret: str


class WebhookEventDelivery(BaseModel):
    """Single webhook delivery attempt."""

    model_config = ConfigDict(from_attributes=True)

    event_id: int
    event_type: str
    status: str
    http_status_code: Optional[int] = None
    attempt_count: int
    delivered_at: Optional[datetime] = None
    created_at: datetime


class WebhookDetailResponse(WebhookResponse):
    """Webhook with recent delivery history."""

    recent_events: list[WebhookEventDelivery] = Field(default_factory=list)


class WebhookEventPayload(BaseModel):
    """JSON body POSTed to the user's webhook endpoint."""

    event_id: str
    event_type: str
    tenant_id: str
    timestamp: str
    data: dict[str, Any]
