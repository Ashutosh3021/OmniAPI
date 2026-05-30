"""Analytics and usage reporting schemas."""

from pydantic import BaseModel, Field


class UsageMetrics(BaseModel):
    """Aggregated usage metrics for a time period."""

    total_calls: int
    successful_calls: int
    failed_calls: int
    cache_hits: int
    cache_hit_rate: float = Field(ge=0.0, le=1.0)
    avg_response_time_ms: float
    estimated_cost_saved: float


class ServiceBreakdown(BaseModel):
    """Per-service usage breakdown."""

    service_name: str
    call_count: int
    cache_hits: int
    avg_response_time_ms: float
    error_count: int


class AnalyticsResponse(BaseModel):
    """Full analytics response for a dashboard period."""

    period: str
    metrics: UsageMetrics
    by_service: list[ServiceBreakdown]
    generated_at: str
