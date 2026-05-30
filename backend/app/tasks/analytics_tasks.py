"""Scheduled analytics aggregation tasks."""

import json
import logging
from datetime import datetime, timedelta, timezone

import redis
from sqlalchemy import case, func, select

from app.config import get_settings
from app.db.session import SessionLocal
from app.models.usage_log import UsageLog
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
STATS_TTL_SECONDS = 7200


@celery_app.task(name="tasks.compute_hourly_stats")
def compute_hourly_stats() -> dict:
    """
    Aggregate the last hour of UsageLog data per tenant into Redis snapshots.

    Key: omniapi:stats:{tenant_id}:hourly
  TTL: 2 hours
    """
    db = SessionLocal()
    settings = get_settings()
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    tenants_processed = 0

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

        tenant_stmt = (
            select(UsageLog.user_id)
            .where(UsageLog.created_at >= cutoff)
            .group_by(UsageLog.user_id)
        )
        tenant_ids = [row[0] for row in db.execute(tenant_stmt).all()]

        if not tenant_ids:
            return {"tenants_processed": 0}

        for user_id in tenant_ids:
            agg = db.execute(
                select(
                    func.count(UsageLog.id).label("total"),
                    func.sum(case((UsageLog.status_code < 400, 1), else_=0)).label(
                        "success"
                    ),
                    func.sum(case((UsageLog.cache_hit.is_(True), 1), else_=0)).label(
                        "cache_hits"
                    ),
                    func.avg(UsageLog.response_time_ms).label("avg_ms"),
                ).where(
                    UsageLog.user_id == user_id,
                    UsageLog.created_at >= cutoff,
                )
            ).one()

            total = int(agg.total or 0)
            snapshot = {
                "tenant_id": user_id,
                "period": "last_hour",
                "total_calls": total,
                "successful_calls": int(agg.success or 0),
                "cache_hits": int(agg.cache_hits or 0),
                "avg_response_time_ms": float(agg.avg_ms or 0.0),
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
            key = f"omniapi:stats:{user_id}:hourly"
            redis_client.set(key, json.dumps(snapshot), ex=STATS_TTL_SECONDS)

        tenants_processed = len(tenant_ids)
        return {"tenants_processed": tenants_processed}
    except Exception:
        logger.exception("compute_hourly_stats failed")
        return {"tenants_processed": tenants_processed}
    finally:
        db.close()
        redis_client.close()
