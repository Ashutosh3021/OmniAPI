"""Data access for external service credentials."""

from __future__ import annotations

from datetime import datetime

from app.db.client import SqlClient
from app.db.sql import sql_literal
from app.models.external_service import ExternalService, ExternalServiceStatus

TABLE = "external_services"


class ExternalServiceRepository:
    """Reads and writes rows in ``external_services``."""

    def __init__(self, client: SqlClient) -> None:
        self._client = client

    def create(
        self,
        *,
        user_id: int,
        service_name: str,
        api_key_encrypted: str,
        created_at: datetime,
        max_calls_per_hour: int = 100,
        status: str = ExternalServiceStatus.ACTIVE.value,
    ) -> ExternalService:
        """Insert a new external service and return it."""
        sql = (
            f"INSERT INTO {TABLE} "
            "(user_id, service_name, api_key_encrypted, max_calls_per_hour, status, created_at) "
            f"VALUES ({sql_literal(user_id)}, {sql_literal(service_name)}, "
            f"{sql_literal(api_key_encrypted)}, {sql_literal(max_calls_per_hour)}, "
            f"{sql_literal(status)}, {sql_literal(created_at)}) RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        if row is None:
            raise RuntimeError("External service insert returned no row")
        return ExternalService.from_row(row)

    def list_for_user(self, user_id: int) -> list[ExternalService]:
        """Return every external service of a user, newest first."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE user_id = {sql_literal(user_id)} "
            "ORDER BY created_at DESC, id DESC"
        )
        return [ExternalService.from_row(row) for row in results[0].dicts()] if results else []

    def list_for_user_named(self, user_id: int, service_names: list[str]) -> list[ExternalService]:
        """Return the user's services whose name is in ``service_names``."""
        if not service_names:
            return []
        names = ", ".join(sql_literal(name) for name in service_names)
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE user_id = {sql_literal(user_id)} "
            f"AND service_name IN ({names})"
        )
        return [ExternalService.from_row(row) for row in results[0].dicts()] if results else []

    def get_by_id(self, service_id: int) -> ExternalService | None:
        """Return a service by id, without a tenant filter.

        Used by the provider-call worker, which is handed a service id and
        not the owning user.
        """
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE id = {sql_literal(service_id)}"
        )
        row = results[0].first() if results else None
        return ExternalService.from_row(row) if row else None

    def get_for_user(self, service_id: int, user_id: int) -> ExternalService | None:
        """Return one of a user's external services, or None."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE id = {sql_literal(service_id)} "
            f"AND user_id = {sql_literal(user_id)}"
        )
        row = results[0].first() if results else None
        return ExternalService.from_row(row) if row else None

    def update(
        self,
        service_id: int,
        *,
        api_key_encrypted: str | None = None,
        max_calls_per_hour: int | None = None,
        status: str | None = None,
        error_message: str | None = None,
        clear_error: bool = False,
        clear_last_tested: bool = False,
        last_tested_at: datetime | None = None,
        updated_at: datetime,
    ) -> ExternalService | None:
        """Update a configured external service."""
        assignments = ["updated_at = " + sql_literal(updated_at)]
        if api_key_encrypted is not None:
            assignments.append("api_key_encrypted = " + sql_literal(api_key_encrypted))
        if max_calls_per_hour is not None:
            assignments.append("max_calls_per_hour = " + sql_literal(max_calls_per_hour))
        if status is not None:
            assignments.append("status = " + sql_literal(status))
        if clear_error:
            assignments.append("error_message = NULL")
        elif error_message is not None:
            assignments.append("error_message = " + sql_literal(error_message))
        if clear_last_tested:
            assignments.append("last_tested_at = NULL")
        if last_tested_at is not None:
            assignments.append("last_tested_at = " + sql_literal(last_tested_at))

        sql = (
            f"UPDATE {TABLE} SET {', '.join(assignments)} "
            f"WHERE id = {sql_literal(service_id)} RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        return ExternalService.from_row(row) if row else None

    def delete(self, service_id: int) -> None:
        """Delete a configured external service."""
        self._client.execute(f"DELETE FROM {TABLE} WHERE id = {sql_literal(service_id)}")
