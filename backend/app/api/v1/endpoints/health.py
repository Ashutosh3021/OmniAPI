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


async def _check_redis(redis_url: str) -> str:
    client = aioredis.from_url(redis_url, decode_responses=True)
    try:
        await client.ping()
        return "ok"
    except Exception:
        logger.exception("Redis health check failed")
        return "unreachable"
    finally:
        await client.aclose()


def _check_celery() -> str:
    try:
        inspect = celery_app.control.inspect(timeout=2)
        active = inspect.active()
        if active:
            return "ok"
        return "no_workers"
    except Exception:
        logger.exception("Celery health check failed")
        return "unreachable"


@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> JSONResponse:
    """Return service health including database, Redis, and Celery worker status."""
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

    overall = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    status_code = 200 if overall == "healthy" else 503

    body = HealthResponse(
        status=overall,
        checks=HealthChecks(**checks),
        version=settings.api_version,
    )

    return JSONResponse(status_code=status_code, content=body.model_dump())
