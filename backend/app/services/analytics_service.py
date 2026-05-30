"""Usage analytics computed from UsageLog aggregates."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.external_service import ExternalService
from app.models.usage_log import UsageLog
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse, ServiceBreakdown, UsageMetrics

# Proxy cost per millisecond of upstream compute avoided by cache hits.
# Formula: estimated_cost_saved = cache_hits * avg_upstream_response_time_ms * COST_PER_UPSTREAM_MS_USD
COST_PER_UPSTREAM_MS_USD = 0.000001
VALID_PERIODS = {"last_24h", "last_7d", "last_30d"}


class AnalyticsService:
    """Tenant-scoped analytics from UsageLog rows."""

    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user

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

    def iter_usage_rows(self, days: int = 30):
        """Yield UsageLog rows with service names for CSV export."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(
                UsageLog.created_at,
                ExternalService.service_name,
                UsageLog.response_time_ms,
                UsageLog.cache_hit,
                UsageLog.status_code,
            )
            .outerjoin(ExternalService, UsageLog.service_id == ExternalService.id)
            .where(
                UsageLog.user_id == self.user.id,
                UsageLog.created_at >= cutoff,
            )
            .order_by(UsageLog.created_at.desc())
        )
        for row in self.db.execute(stmt).yield_per(500):
            service_name = row.service_name if row.service_name is not None else "deleted"
            yield type(
                "UsageRow",
                (),
                {
                    "created_at": row.created_at,
                    "service_name": service_name,
                    "response_time_ms": row.response_time_ms,
                    "cache_hit": row.cache_hit,
                    "status_code": row.status_code,
                },
            )()

    def _period_to_timedelta(self, period: str) -> timedelta:
        mapping = {
            "last_24h": timedelta(hours=24),
            "last_7d": timedelta(days=7),
            "last_30d": timedelta(days=30),
        }
        return mapping.get(period, timedelta(hours=24))

    def _aggregate_metrics(self, cutoff: datetime) -> UsageMetrics:
        stmt = select(
            func.count(UsageLog.id).label("total"),
            func.sum(case((UsageLog.status_code < 400, 1), else_=0)).label("success"),
            func.sum(case((UsageLog.status_code >= 400, 1), else_=0)).label("failed"),
            func.sum(case((UsageLog.cache_hit.is_(True), 1), else_=0)).label("cache_hits"),
            func.avg(UsageLog.response_time_ms).label("avg_ms"),
        ).where(
            UsageLog.user_id == self.user.id,
            UsageLog.created_at >= cutoff,
        )
        row = self.db.execute(stmt).one()
        total = int(row.total or 0)
        cache_hits = int(row.cache_hits or 0)
        avg_ms = float(row.avg_ms or 0.0)

        return UsageMetrics(
            total_calls=total,
            successful_calls=int(row.success or 0),
            failed_calls=int(row.failed or 0),
            cache_hits=cache_hits,
            cache_hit_rate=(cache_hits / total) if total else 0.0,
            avg_response_time_ms=avg_ms,
            estimated_cost_saved=self._compute_cost_saved(cache_hits, avg_ms),
        )

    def _service_breakdown(self, cutoff: datetime) -> list[ServiceBreakdown]:
        stmt = (
            select(
                ExternalService.service_name,
                func.count(UsageLog.id).label("call_count"),
                func.sum(case((UsageLog.cache_hit.is_(True), 1), else_=0)).label(
                    "cache_hits"
                ),
                func.avg(UsageLog.response_time_ms).label("avg_ms"),
                func.sum(case((UsageLog.status_code >= 400, 1), else_=0)).label(
                    "error_count"
                ),
            )
            .join(ExternalService, UsageLog.service_id == ExternalService.id)
            .where(
                UsageLog.user_id == self.user.id,
                UsageLog.created_at >= cutoff,
            )
            .group_by(ExternalService.service_name)
            .order_by(func.count(UsageLog.id).desc())
        )
        rows = self.db.execute(stmt).all()
        return [
            ServiceBreakdown(
                service_name=row.service_name,
                call_count=int(row.call_count or 0),
                cache_hits=int(row.cache_hits or 0),
                avg_response_time_ms=float(row.avg_ms or 0.0),
                error_count=int(row.error_count or 0),
            )
            for row in rows
        ]

    def _compute_cost_saved(self, cache_hits: int, avg_upstream_ms: float) -> float:
        """USD estimate for avoided upstream compute (see COST_PER_UPSTREAM_MS_USD)."""
        return round(cache_hits * avg_upstream_ms * COST_PER_UPSTREAM_MS_USD, 4)
