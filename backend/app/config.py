"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List, Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with Pyronites and Redis configuration."""

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

    # Database — Pyronites
    pyronites_url: str = Field(..., description="Base URL of the Pyronites backend")
    pyronites_key: str = Field(..., description="Pyronites API key for the app's project")
    pyronites_project_id: str = Field(..., description="Pyronites project the app reads and writes")
    pyronites_timeout: float = Field(30.0, description="Per-request timeout, in seconds")

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Rate limiting (requests per hour)
    rate_limit_free: int = 100
    rate_limit_pro: int = 1000
    rate_limit_enterprise: int = 10000

    # Authentication throttling. The OAuth entry points are the only
    # unauthenticated write endpoints, so they carry their own limit.
    rate_limit_oauth_per_ip: int = 20
    rate_limit_auth_window_seconds: int = 900

    # Honour X-Forwarded-For only when a trusted proxy sits in front of the
    # app. Leave off when the app is directly exposed.
    trust_proxy_header: bool = False

    # Celery
    celery_task_timeout: int = 10

    # Data retention
    usage_log_retention_days: int = 90
    webhook_event_retention_days: int = 30

    # Security
    secret_key: str = Field(..., min_length=16)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    encryption_key: str = Field(
        ...,
        description="Fernet key (32-byte base64) for encrypting external API credentials",
    )

    # OAuth (Google / GitHub)
    # The provider applications live in the Google and GitHub consoles; their
    # redirect URI must point at {oauth_redirect_base_url}/api/v1/auth/oauth/{provider}/callback
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    oauth_redirect_base_url: str = Field(
        "http://localhost:8000",
        description="Public base URL of this API, used to build the provider callback URL",
    )
    oauth_success_redirect_url: str = Field(
        "http://localhost:3000/auth/callback",
        description="Frontend page the browser returns to after a successful sign-in",
    )
    oauth_failure_redirect_url: str = Field(
        "http://localhost:3000/login?error=oauth_failed",
        description="Frontend page the browser returns to after a failed sign-in",
    )
    oauth_state_ttl_seconds: int = 600
    oauth_code_ttl_seconds: int = 300

    # CORS
    allowed_origins: str = "http://localhost:3000"

    @field_validator("allowed_origins")
    @classmethod
    def validate_cors_origins(cls, value: str, info) -> str:
        """Prevent wildcard CORS in production."""
        if info.data.get("environment") == "production" and "*" in value:
            raise ValueError("Wildcard CORS (*) is not allowed in production")
        return value

    @field_validator("pyronites_url")
    @classmethod
    def validate_pyronites_url(cls, value: str) -> str:
        """Ensure the Pyronites base URL is an absolute http(s) URL."""
        if not value:
            raise ValueError("PYRONITES_URL is required")
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("PYRONITES_URL must be an absolute http(s) URL")
        return value.rstrip("/")

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def oauth_providers(self) -> List[str]:
        """Providers that are configured well enough to be offered."""
        available = []
        if self.google_client_id and self.google_client_secret:
            available.append("google")
        if self.github_client_id and self.github_client_secret:
            available.append("github")
        return available

    def oauth_callback_url(self, provider: str) -> str:
        """The callback URL registered with a provider application."""
        return (
            f"{self.oauth_redirect_base_url.rstrip('/')}" f"/api/v1/auth/oauth/{provider}/callback"
        )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance for dependency injection."""
    return Settings()
