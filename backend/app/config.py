"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List, Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with Supabase and Redis configuration."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # FastAPI
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "info"
    api_title: str = "OmniAPI"
    api_version: str = "1.0.0"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_db_password: str = ""

    # Database
    database_url: str = Field(..., description="PostgreSQL connection string (Supabase)")
    db_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Rate limiting (requests per hour)
    rate_limit_free: int = 100
    rate_limit_pro: int = 1000
    rate_limit_enterprise: int = 10000

    # Celery
    celery_task_timeout: int = 10

    # Security
    secret_key: str = Field(..., min_length=16)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    encryption_key: str = Field(
        ...,
        description="Fernet key (32-byte base64) for encrypting external API credentials",
    )

    # CORS
    allowed_origins: str = "http://localhost:3000"

    @field_validator("allowed_origins")
    @classmethod
    def validate_cors_origins(cls, value: str, info) -> str:
        """Prevent wildcard CORS in production."""
        if info.data.get("environment") == "production" and "*" in value:
            raise ValueError("Wildcard CORS (*) is not allowed in production")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """Ensure DATABASE_URL is a valid PostgreSQL/Supabase connection string."""
        if not value:
            raise ValueError("DATABASE_URL is required")

        normalized = value.replace("postgresql+psycopg2://", "postgresql://")
        parsed = urlparse(normalized)

        if parsed.scheme == "sqlite":
            return value

        if parsed.scheme not in ("postgresql", "postgres"):
            raise ValueError(
                "DATABASE_URL must use postgresql:// scheme (Supabase PostgreSQL)"
            )
        if not parsed.hostname:
            raise ValueError("DATABASE_URL must include a hostname")
        if not parsed.path or parsed.path == "/":
            raise ValueError("DATABASE_URL must include a database name")

        return value

    @property
    def sqlalchemy_database_url(self) -> str:
        """Connection URL for SQLAlchemy with psycopg2 driver."""
        url = self.database_url
        if url.startswith("sqlite"):
            return url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg2://", 1)
        return url

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def sqlalchemy_engine_kwargs(self) -> dict:
        """SQLAlchemy engine options including connection pooling."""
        kwargs: dict = {"echo": self.db_echo}
        if not self.database_url.startswith("sqlite"):
            kwargs.update(
                {
                    "pool_pre_ping": True,
                    "pool_size": 10,
                    "max_overflow": 20,
                }
            )
        return kwargs


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance for dependency injection."""
    return Settings()
