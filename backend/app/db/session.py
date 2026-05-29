"""SQLAlchemy engine and session management for Supabase PostgreSQL."""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

try:
    engine = create_engine(
        settings.sqlalchemy_database_url,
        **settings.sqlalchemy_engine_kwargs,
    )
except SQLAlchemyError as exc:
    logger.exception("Failed to create database engine")
    raise RuntimeError("Database engine initialization failed") from exc

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.

    Rolls back on error and always closes the session.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database session error")
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """Verify database connectivity (used by health checks)."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logger.exception("Database connection check failed")
        return False
