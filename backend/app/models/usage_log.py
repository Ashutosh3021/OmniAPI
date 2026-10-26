"""API usage log for analytics and billing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.parsing import parse_bool, parse_datetime


@dataclass
class UsageLog:
    """Record of a single orchestrated API call."""

    id: int
    user_id: int
    endpoint: str
    response_time_ms: int
    status_code: int
    cache_hit: bool
    created_at: datetime
    service_id: int | None = None
    api_key_id: int | None = None
    request_size_bytes: int | None = None
    response_size_bytes: int | None = None
    error_message: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "UsageLog":
        """Build a usage log from a database row."""
        return cls(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            endpoint=row["endpoint"],
            response_time_ms=int(row["response_time_ms"]),
            status_code=int(row["status_code"]),
            cache_hit=parse_bool(row.get("cache_hit")),
            created_at=parse_datetime(row["created_at"]),  # type: ignore[arg-type]
            service_id=int(row["service_id"]) if row.get("service_id") is not None else None,
            api_key_id=int(row["api_key_id"]) if row.get("api_key_id") is not None else None,
            request_size_bytes=(
                int(row["request_size_bytes"])
                if row.get("request_size_bytes") is not None
                else None
            ),
            response_size_bytes=(
                int(row["response_size_bytes"])
                if row.get("response_size_bytes") is not None
                else None
            ),
            error_message=row.get("error_message"),
        )

    def __repr__(self) -> str:
        return (
            f"<UsageLog(id={self.id}, user_id={self.user_id}, "
            f"endpoint={self.endpoint!r}, status_code={self.status_code})>"
        )
