"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.middleware.error_handler import register_exception_handlers

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown hooks."""
    logger.info("Starting %s v%s (%s)", settings.api_title, settings.api_version, settings.environment)
    yield
    logger.info("Shutting down %s", settings.api_title)


def create_app() -> FastAPI:
    """Application factory for FastAPI and tests."""
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Phase 2: allow all origins; restrict in Phase 6
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/", tags=["root"])
    def root() -> dict:
        return {
            "name": settings.api_title,
            "version": settings.api_version,
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    return app


app = create_app()
