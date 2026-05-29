"""Health check endpoint."""

from fastapi import APIRouter

from app.config import get_settings
from app.db.session import check_database_connection
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return service health including database connectivity for load balancers."""
    settings = get_settings()
    db_ok = check_database_connection()

    if db_ok:
        status = "healthy"
        db_status = "connected"
    else:
        status = "degraded"
        db_status = "disconnected"

    return HealthResponse(
        status=status,
        version=settings.api_version,
        environment=settings.environment,
        database=db_status,
        redis="skipped",
    )
