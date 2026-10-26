"""Usage analytics and CSV export endpoints."""

import csv
import io
from datetime import datetime
from typing import Iterator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.db.database import Database, get_db
from app.middleware.tenant_middleware import get_tenant_id
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse, AnalyticsSummaryResponse
from app.services.analytics_service import AnalyticsService
from app.utils.decorators import require_auth

router = APIRouter()


def _csv_row_generator(service: AnalyticsService) -> Iterator[str]:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["timestamp", "service", "response_time_ms", "cache_hit", "status_code"])
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for row in service.iter_usage_rows(days=30):
        created_at = row.get("created_at")
        timestamp = (
            created_at.isoformat() if isinstance(created_at, datetime) else (created_at or "")
        )
        writer.writerow(
            [
                timestamp,
                row.get("service_name"),
                row.get("response_time_ms"),
                row.get("cache_hit"),
                row.get("status_code"),
            ]
        )
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> AnalyticsSummaryResponse:
    """Lightweight 24 h summary for the dashboard home page."""
    _ = tenant_id
    return AnalyticsService(db=db, user=current_user).get_summary()


@router.get("/usage", response_model=AnalyticsResponse)
def get_usage_analytics(
    period: str = Query(default="last_24h", pattern="^(last_24h|last_7d|last_30d)$"),
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> AnalyticsResponse:
    _ = tenant_id
    return AnalyticsService(db=db, user=current_user).get_metrics(period)


@router.get("/reports")
def download_usage_report(
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> StreamingResponse:
    _ = tenant_id
    service = AnalyticsService(db=db, user=current_user)
    return StreamingResponse(
        _csv_row_generator(service),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="usage_report.csv"'},
    )
