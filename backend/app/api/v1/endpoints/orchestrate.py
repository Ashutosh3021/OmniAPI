"""Orchestration endpoint."""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.rate_limit import get_tier_limit
from app.models.user import User
from app.schemas.orchestrate import OrchestrateRequest, OrchestrateResponse
from app.services.orchestrator_service import OrchestratorService
from app.utils.decorators import require_auth_or_api_key

router = APIRouter()


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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth_or_api_key),
) -> OrchestrateResponse:
    """Orchestrate calls to one or more configured external services."""
    orchestrator = OrchestratorService(db=db, user=current_user)
    result = await orchestrator.orchestrate(body)
    _attach_rate_limit_headers(request, response, current_user)
    return result
