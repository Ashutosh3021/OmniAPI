"""Health check endpoints with dependency probes."""

import asyncio
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.schemas.health import HealthChecks, HealthResponse
from app.services.redis_client import get_redis
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

# Dependencies that must be healthy for the service to accept traffic.
# Celery is deliberately not critical: after the orchestrator stopped routing
# provider calls through the broker, the request path (auth, orchestrate,
# analytics) has no Celery dependency. Celery only carries fire-and-forget
# webhook delivery, so a missing worker degrades webhooks, not the API.
CRITICAL_CHECKS = {"database", "redis"}


async def _check_redis() -> str:
    try:
        client = get_redis()
        await client.ping()
        return "ok"
    except Exception as exc:  # noqa: BLE001 - reported, not raised
        logger.warning("Redis health check failed: %s", exc)
        return "unreachable"


def _check_celery() -> str:
    try:
        # ping() returns a dict of {worker_name: {"ok": "pong"}} for each
        # live worker. active() only returns workers currently processing a
        # task — an idle worker returns None, which is NOT an error.
        inspect = celery_app.control.inspect(timeout=2)
        pong = inspect.ping()
        if pong:
            return "ok"
        return "no_workers"
    except Exception as exc:  # noqa: BLE001 - reported, not raised
        logger.warning("Celery health check failed: %s", exc)
        return "unreachable"


def _check_database(db: Session) -> str:
    try:
        db.execute(text("SELECT 1"))
        return "ok"
    except Exception:  # noqa: BLE001 - reported, not raised
        logger.exception("Database health check failed")
        return "unreachable"


@router.get("/health/live", tags=["health"])
async def liveness_check() -> JSONResponse:
    """Process liveness. Performs no I/O, so it can never block the event loop.

    This is the endpoint a load balancer should poll.
    """
    settings = get_settings()
    body = HealthResponse(
        status="healthy",
        checks=HealthChecks(database="ok", redis="ok", celery="ok"),
        version=settings.api_version,
    )
    return JSONResponse(status_code=200, content=body.model_dump())


@router.get("/health/ready", tags=["health"])
async def readiness_check(db: Session = Depends(get_db)) -> JSONResponse:
    """Readiness: verifies the dependencies the request path actually needs.

    HTTP 503 is returned only when a critical dependency is unreachable.
    """
    settings = get_settings()
    checks: dict[str, str] = {
        "database": _check_database(db),
        "redis": await _check_redis(),
    }
    # Blocking broker call — run it off the event loop.
    checks["celery"] = await asyncio.to_thread(_check_celery)

    critical_ok = all(checks.get(k) == "ok" for k in CRITICAL_CHECKS)
    all_ok = all(v == "ok" for v in checks.values())

    if all_ok:
        overall = "healthy"
    elif critical_ok:
        overall = "degraded"
    else:
        overall = "unhealthy"

    status_code = 503 if not critical_ok else 200

    body = HealthResponse(
        status=overall,
        checks=HealthChecks(**checks),
        version=settings.api_version,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


@router.get("/health", tags=["health"])
async def health_check(db: Session = Depends(get_db)) -> JSONResponse:
    """Alias of :func:`readiness_check`, kept for backwards compatibility."""
    return await readiness_check(db)
