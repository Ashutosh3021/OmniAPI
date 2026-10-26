"""Usage analytics computed from UsageLog aggregates."""

from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from app.db.database import Database
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsResponse,
    AnalyticsSummaryResponse,
    ServiceBreakdown,
    UsageMetrics,
)

# Proxy cost per millisecond of upstream compute avoided by cache hits.
# Formula: estimated_cost_saved = cache_hits * avg_upstream_response_time_ms * COST_PER_UPSTREAM_MS_USD
COST_PER_UPSTREAM_MS_USD = 0.000001
VALID_PERIODS = {"last_24h", "last_7d", "last_30d"}


class AnalyticsService:
    """Tenant-scoped analytics from UsageLog rows."""

    def __init__(self, db: Database, user: User) -> None:
        self.db = db
        self.user = user

    def get_summary(self) -> AnalyticsSummaryResponse:
        """Compute the lightweight summary metrics used on the dashboard home page.

        'Calls today' vs 'calls yesterday' is used to derive the change percentage.
        'avg_response_ms change' compares today vs yesterday as well.
        """
        now = datetime.now(timezone.utc)
        today_start = now - timedelta(hours=24)
        yesterday_start = today_start - timedelta(hours=24)

        metrics = self.db.usage_logs.metrics_for(
            self.user.id,
            since=yesterday_start,
            today_start=today_start,
            yesterday_start=yesterday_start,
        )

        calls_today = metrics.calls_today
        calls_yesterday = metrics.calls_yesterday
        calls_change = (
            round((calls_today - calls_yesterday) / calls_yesterday * 100, 1)
            if calls_yesterday
            else 0.0
        )

        avg_today = metrics.avg_response_time_ms_today
        avg_yesterday = metrics.avg_response_time_ms_yesterday
        response_change_ms = round(avg_today - avg_yesterday, 1)

        cache_hit_percent = round(metrics.cache_hit_rate * 100, 1)

        return AnalyticsSummaryResponse(
            calls_today=calls_today,
            calls_change=calls_change,
            cache_hit_percent=cache_hit_percent,
            avg_response_ms=round(avg_today, 1),
            response_change_ms=response_change_ms,
        )

    def get_metrics(self, period: str) -> AnalyticsResponse:
        """Compute metrics and per-service breakdown for the given period."""
        if period not in VALID_PERIODS:
            period = "last_24h"

        cutoff = datetime.now(timezone.utc) - self._period_to_timedelta(period)

        metrics = self._aggregate_metrics(cutoff)
        by_service = self._service_breakdown(cutoff)

        return AnalyticsResponse(
            period=period,
            metrics=metrics,
            by_service=by_service,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def iter_usage_rows(self, days: int = 30) -> Iterator[dict[str, Any]]:
        """Yield UsageLog rows with service names for CSV export."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        for row in self.db.usage_logs.iter_rows_with_service(self.user.id, cutoff):
            service_name = row.get("service_name") or "deleted"
            yield {
                "created_at": row.get("created_at"),
                "service_name": service_name,
                "response_time_ms": row.get("response_time_ms"),
                "cache_hit": bool(row.get("cache_hit")),
                "status_code": row.get("status_code"),
            }

    def _period_to_timedelta(self, period: str) -> timedelta:
        mapping = {
            "last_24h": timedelta(hours=24),
            "last_7d": timedelta(days=7),
            "last_30d": timedelta(days=30),
        }
        return mapping.get(period, timedelta(hours=24))

    def _aggregate_metrics(self, cutoff: datetime) -> UsageMetrics:
        now = datetime.now(timezone.utc)
        metrics = self.db.usage_logs.metrics_for(
            self.user.id,
            since=cutoff,
            today_start=now,
            yesterday_start=now,
        )

        total = metrics.total
        cache_hits = metrics.cache_hits
        avg_ms = metrics.avg_response_time_ms

        return UsageMetrics(
            total_calls=total,
            successful_calls=metrics.successful,
            failed_calls=metrics.failed,
            cache_hits=cache_hits,
            cache_hit_rate=(cache_hits / total) if total else 0.0,
            avg_response_time_ms=avg_ms,
            estimated_cost_saved=self._compute_cost_saved(cache_hits, avg_ms),
        )

    def _service_breakdown(self, cutoff: datetime) -> list[ServiceBreakdown]:
        rows = self.db.usage_logs.breakdown_by_service(self.user.id, cutoff)
        return [
            ServiceBreakdown(
                service_name=row.get("service_name") or "deleted",
                call_count=int(row.get("call_count") or 0),
                cache_hits=int(row.get("cache_hits") or 0),
                avg_response_time_ms=float(row.get("avg_ms") or 0.0),
                error_count=int(row.get("error_count") or 0),
            )
            for row in rows
        ]

    def _compute_cost_saved(self, cache_hits: int, avg_upstream_ms: float) -> float:
        """USD estimate for avoided upstream compute (see COST_PER_UPSTREAM_MS_USD)."""
        return round(cache_hits * avg_upstream_ms * COST_PER_UPSTREAM_MS_USD, 4)
