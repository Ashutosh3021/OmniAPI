"""Authentication request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """New user registration payload."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=200)


class UserLogin(BaseModel):
    """User login credentials."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Refresh token request body."""

    refresh_token: str


class UserResponse(BaseModel):
    """Public user profile (no password)."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: str
    full_name: str
    tier: str
    created_at: datetime
