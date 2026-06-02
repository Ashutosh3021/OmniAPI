"""Health check response schema."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthChecks(BaseModel):
    """Per-dependency health probe results."""

    database: str = Field(..., description="PostgreSQL connectivity")
    redis: str = Field(..., description="Redis connectivity")
    celery: str = Field(..., description="Celery worker availability")


class HealthResponse(BaseModel):
    """Service health status returned by GET /health."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Overall service health"
    )
    checks: HealthChecks
    version: str = Field(..., description="API version")
