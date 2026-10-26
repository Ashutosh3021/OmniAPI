"""Global exception handlers for FastAPI."""

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db.client import DatabaseError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(DatabaseError)
    async def database_exception_handler(request: Request, exc: DatabaseError) -> JSONResponse:
        """A data-store failure is a 503, not a 500.

        The data store is a remote service: it can be unreachable or reject a
        statement. Either way the request could not be served, and the caller
        should be told to retry rather than that the application is broken.
        """
        logger.exception("Data store error on %s", request.url.path)
        return JSONResponse(
            status_code=503,
            content={"detail": "Database service unavailable"},
            headers={"Retry-After": "5"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
