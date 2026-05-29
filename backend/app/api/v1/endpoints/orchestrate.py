"""Orchestration endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.orchestrate import OrchestrateRequest, OrchestrateResponse
from app.services.orchestrator_service import OrchestratorService
from app.utils.decorators import require_auth_or_api_key

router = APIRouter()


@router.post("", response_model=OrchestrateResponse)
async def orchestrate(
    body: OrchestrateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth_or_api_key),
) -> OrchestrateResponse:
    """Orchestrate calls to one or more configured external services."""
    orchestrator = OrchestratorService(db=db, user=current_user)
    return await orchestrator.orchestrate(body)
