"""Authentication request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """New user registration payload."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=200)


class UserLogin(BaseModel):
    """User login credentials."""

    email: EmailStr
    password: str


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


class ChangePasswordRequest(BaseModel):
    """Password change request."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    """Password reset request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Password reset completion."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class ForgotPasswordResponse(BaseModel):
    """Result of a password reset request.

    Always reports "accepted" so the endpoint cannot be used to discover
    which email addresses have accounts. Outside production the reset token
    is included so the flow is testable without an email provider.
    """

    status: str = "accepted"
    reset_token: str | None = None


class UserResponse(BaseModel):
    """Public user profile (no password)."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: str
    full_name: str
    tier: str
    created_at: datetime
