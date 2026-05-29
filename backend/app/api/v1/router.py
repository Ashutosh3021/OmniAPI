"""API v1 router aggregating all endpoint modules."""

from fastapi import APIRouter

from app.api.v1.endpoints import api_keys, auth, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
