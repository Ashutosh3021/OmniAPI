"""API key request and response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class APIKeyCreate(BaseModel):
    """Create a new OmniAPI key."""

    name: str = Field(..., min_length=1, max_length=100)
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API key metadata (raw key never included)."""

    model_config = ConfigDict(from_attributes=True)

    key_id: int
    name: str
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime


class APIKeyCreatedResponse(APIKeyResponse):
    """API key creation response including the raw key (shown once)."""

    raw_key: str
