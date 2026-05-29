"""Custom application exceptions."""


class OmniAPIException(Exception):
    """Base exception for OmniAPI errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(OmniAPIException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class ValidationError(OmniAPIException):
    """Request validation failed."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message, status_code=422)


class AuthenticationError(OmniAPIException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, status_code=401)


class AuthorizationError(OmniAPIException):
    """Insufficient permissions."""

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status_code=403)


class DatabaseError(OmniAPIException):
    """Database operation failed."""

    def __init__(self, message: str = "Database error") -> None:
        super().__init__(message, status_code=503)
