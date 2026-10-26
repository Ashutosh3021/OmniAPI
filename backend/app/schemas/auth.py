"""Authentication request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Token(BaseModel):
    """JWT access and opaque refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Refresh token request body."""

    refresh_token: str = Field(..., min_length=1)


class UserProfileUpdate(BaseModel):
    """Profile fields the user may change."""

    full_name: str = Field(..., min_length=1, max_length=200)


class OAuthProviderInfo(BaseModel):
    """A sign-in provider the platform offers."""

    id: str
    name: str
    configured: bool


class OAuthProvidersResponse(BaseModel):
    """The providers the client may render a button for."""

    providers: list[OAuthProviderInfo]


class OAuthStartResponse(BaseModel):
    """Where the browser must be sent to begin a provider sign-in."""

    authorization_url: str
    state: str


class OAuthExchangeRequest(BaseModel):
    """Exchange a one-time sign-in code for a token pair."""

    code: str = Field(..., min_length=1, max_length=512)


class UserResponse(BaseModel):
    """Public user profile."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: str
    full_name: str
    tier: str
    created_at: datetime
