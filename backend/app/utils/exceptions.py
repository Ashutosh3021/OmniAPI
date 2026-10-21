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


class ExternalAPIError(HTTPException):
    """Upstream external API failure (502).

    ``retryable`` distinguishes transient upstream problems (timeouts, 429s,
    5xx) from permanent ones (a rejected credential, a bad symbol). Only
    transient failures are worth retrying.
    """

    def __init__(self, detail: str = "External API request failed", retryable: bool = True) -> None:
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
        self.retryable = retryable


class ServiceNotConfiguredError(HTTPException):
    """Requested external service is not configured for the user (404)."""

    def __init__(self, detail: str = "External service not configured") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class RateLimitExceededError(HTTPException):
    """A rate limit or quota was exceeded (429)."""

    def __init__(self, detail: str, retry_after: int = 60) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)},
        )


class ValidationFailedError(HTTPException):
    """Request payload failed validation (422).

    ``detail`` uses FastAPI's list-of-errors shape so the dashboard can
    render the offending field next to the input.
    """

    def __init__(self, errors: list[dict]) -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors)
