"""External third-party API service credentials model."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.parsing import parse_datetime


class ExternalServiceStatus(str, enum.Enum):
    """Operational status of an external service integration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class ExternalService:
    """User-configured external API (e.g. OpenWeatherMap, NewsAPI)."""

    id: int
    user_id: int
    service_name: str
    api_key_encrypted: str
    max_calls_per_hour: int
    status: str
    created_at: datetime
    error_message: str | None = None
    updated_at: datetime | None = None
    last_tested_at: datetime | None = None

    @property
    def service_id(self) -> int:
        """Alias for id used in API responses."""
        return self.id

    @property
    def is_active(self) -> bool:
        """Whether the integration is usable."""
        return self.status == ExternalServiceStatus.ACTIVE.value

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ExternalService":
        """Build an external service from a database row."""
        return cls(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            service_name=row["service_name"],
            api_key_encrypted=row["api_key_encrypted"],
            max_calls_per_hour=int(row["max_calls_per_hour"]),
            status=str(row["status"]),
            created_at=parse_datetime(row["created_at"]),  # type: ignore[arg-type]
            error_message=row.get("error_message"),
            updated_at=parse_datetime(row.get("updated_at")),
            last_tested_at=parse_datetime(row.get("last_tested_at")),
        )

    def __repr__(self) -> str:
        return (
            f"<ExternalService(id={self.id}, user_id={self.user_id}, "
            f"service_name={self.service_name!r})>"
        )
