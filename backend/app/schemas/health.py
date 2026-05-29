"""Health check response schema."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Service health status returned by GET /health."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Overall service health"
    )
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Deployment environment")
    database: Literal["connected", "disconnected"] = Field(
        ..., description="Supabase PostgreSQL connectivity"
    )
    redis: Optional[Literal["connected", "disconnected", "skipped"]] = Field(
        default="skipped",
        description="Redis connectivity (optional in phase 1)",
    )
