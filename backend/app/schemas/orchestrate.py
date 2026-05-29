"""Orchestration request and response schemas."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class OrchestrateRequest(BaseModel):
    """Request to orchestrate one or more external services."""

    services: list[str] = Field(..., min_length=1)
    params: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ServiceResult(BaseModel):
    """Result for a single orchestrated service call."""

    service: str
    success: bool
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    response_time_ms: int
    cache_hit: bool = False


class OrchestrateResponse(BaseModel):
    """Aggregated orchestration response."""

    request_id: str
    results: list[ServiceResult]
    total_time_ms: int
    timestamp: str
