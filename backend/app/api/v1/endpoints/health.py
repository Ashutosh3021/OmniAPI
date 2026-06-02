"""Health check endpoint with dependency probes."""

import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.schemas.health import HealthChecks, HealthResponse
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

# Dependencies that must be healthy for the service to be considered available.
CRITICAL_CHECKS = {"database"}


async def _check_redis(redis_url: str) -> str:
    client = aioredis.from_url(redis_url, decode_responses=True)
    try:
        await client.ping()
        return "ok"
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        return "unreachable"
    finally:
        await client.aclose()


def _check_celery() -> str:
    try:
        # ping() returns a dict of {worker_name: {"ok": "pong"}} for each
        # live worker. active() only returns workers currently processing a
        # task — an idle worker returns None, which is NOT an error.
        inspect = celery_app.control.inspect(timeout=5)
        pong = inspect.ping()
        if pong:
            return "ok"
        return "no_workers"
    except Exception as exc:
        logger.warning("Celery health check failed: %s", exc)
        return "unreachable"


@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> JSONResponse:
    """Return service health including database, Redis, and Celery worker status.

    HTTP 200 is returned when all *critical* dependencies (database) are healthy.
    Non-critical dependencies (Redis, Celery) being unavailable results in a
    ``degraded`` status but still returns HTTP 200 so load-balancer health probes
    do not take the service out of rotation when background workers are offline.
    HTTP 503 is only returned when a critical dependency is unreachable.
    """
    settings = get_settings()
    checks: dict[str, str] = {}

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        logger.exception("Database health check failed")
        checks["database"] = "unreachable"

    checks["redis"] = await _check_redis(settings.redis_url)
    checks["celery"] = _check_celery()

    critical_ok = all(checks.get(k) == "ok" for k in CRITICAL_CHECKS)
    all_ok = all(v == "ok" for v in checks.values())

    if all_ok:
        overall = "healthy"
    elif critical_ok:
        overall = "degraded"
    else:
        overall = "unhealthy"

    # 503 only when a critical dependency is down
    status_code = 503 if not critical_ok else 200

    body = HealthResponse(
        status=overall,
        checks=HealthChecks(**checks),
        version=settings.api_version,
    )

    return JSONResponse(status_code=status_code, content=body.model_dump())
