"""API v1 router aggregating all endpoint modules."""

from fastapi import APIRouter

from app.api.v1.endpoints import api_keys, auth, external_services, health, orchestrate

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
api_router.include_router(
    external_services.router,
    prefix="/external-services",
    tags=["External Services"],
)
api_router.include_router(
    orchestrate.router,
    prefix="/orchestrate",
    tags=["Orchestrate"],
)
