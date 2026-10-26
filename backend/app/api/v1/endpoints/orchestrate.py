"""Orchestration endpoint."""

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response

from app.db.database import Database, get_db
from app.middleware.rate_limit import get_tier_limit
from app.models.user import User
from app.schemas.orchestrate import OrchestrateRequest, OrchestrateResponse
from app.services.orchestrator_service import OrchestratorService
from app.utils.decorators import require_auth_or_api_key

router = APIRouter()


def _cache_state(results: list) -> str:
    """Summarise the cache state of the response as HIT / MISS / PARTIAL."""
    if not results:
        return "MISS"
    hits = sum(1 for r in results if r.cache_hit)
    if hits == len(results):
        return "HIT"
    if hits == 0:
        return "MISS"
    return "PARTIAL"


def _attach_rate_limit_headers(request: Request, response: Response, user: User) -> None:
    limit = getattr(request.state, "rate_limit_limit", None)
    remaining = getattr(request.state, "rate_limit_remaining", None)
    if limit is None:
        limit = str(get_tier_limit(user))
    if remaining is None:
        remaining = limit
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)


@router.post("", response_model=OrchestrateResponse)
async def orchestrate(
    body: OrchestrateRequest,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth_or_api_key),
) -> OrchestrateResponse:
    """Orchestrate calls to one or more configured external services."""
    orchestrator = OrchestratorService(
        db=db,
        user=current_user,
        api_key_id=getattr(request.state, "api_key_id", None),
    )
    result = await orchestrator.orchestrate(body)

    # Record usage after the response has been sent, so the caller is not
    # held up by the write.
    usage_rows = orchestrator.usage_rows
    background_tasks.add_task(orchestrator.flush_usage, usage_rows)

    _attach_rate_limit_headers(request, response, current_user)
    response.headers["X-Cache"] = _cache_state(result.results)
    return result
