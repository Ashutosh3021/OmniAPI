"""Custom HTTP exceptions with consistent JSON error shapes."""

from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Authentication failed (401)."""

    def __init__(self, detail: str = "Could not validate credentials") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(HTTPException):
    """Insufficient permissions (403)."""

    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class DuplicateResourceError(HTTPException):
    """Resource already exists (400)."""

    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ResourceNotFoundError(HTTPException):
    """Resource not found (404)."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
