"""Orchestration request and response schemas."""

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class OrchestrateRequest(BaseModel):
    """Request to orchestrate one or more external services."""

    services: list[str] = Field(..., min_length=1)
    params: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def params_keys_match_services(self) -> "OrchestrateRequest":
        """Reject param keys that do not correspond to a requested service."""
        extra = set(self.params.keys()) - set(self.services)
        if extra:
            raise ValueError(
                f"params contains keys not listed in services: {', '.join(sorted(extra))}"
            )
        return self


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
