"""Apply the OmniAPI schema to the configured Pyronites project.

The schema lives in ``schema.sql`` and is applied with plain DDL, so running
this is idempotent — every statement is ``IF NOT EXISTS``.

Usage::

    python -m app.db.bootstrap          # apply the schema
    python -m app.db.bootstrap --check  # report what is present
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from app.db.client import DatabaseError, PyronitesClient
from app.db.sql import split_statements, strip_comments
from app.config import get_settings

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

EXPECTED_TABLES = (
    "omniapi_users",
    "omniapi_api_keys",
    "external_services",
    "usage_logs",
    "webhooks",
    "webhook_events",
    "refresh_tokens",
    "omniapi_oauth_identities",
)


def _tables(client: PyronitesClient) -> list[str]:
    results = client.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
    return [row[0] for row in results[0].rows] if results else []


def apply_schema(client: PyronitesClient, schema: str) -> int:
    """Apply the schema. Returns the number of statements that ran.

    The whole script is sent as one request so the schema is applied in a
    single transaction. If the batch fails, the statements are replayed one by
    one so the offending statement can be named.

    Comments are stripped first: they are written for people, and prose in a
    comment is not something the data store should have to parse.
    """
    statements = split_statements(schema)
    payload = strip_comments(schema)
    try:
        client.execute(payload)
        return len(statements)
    except DatabaseError as exc:
        logger.warning("Batched schema apply failed (%s); retrying statement by statement", exc)

    applied = 0
    for statement in split_statements(payload):
        try:
            client.execute(statement)
            applied += 1
        except DatabaseError as statement_exc:
            raise DatabaseError(
                f"Failed to apply statement: {statement.splitlines()[0][:120]} "
                f"({statement_exc})",
                code=statement_exc.code,
            ) from statement_exc
    return applied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply the OmniAPI schema to Pyronites.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only report the tables that exist; do not change anything.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = get_settings()

    client = PyronitesClient(
        url=settings.pyronites_url,
        key=settings.pyronites_key,
        project_id=settings.pyronites_project_id,
        timeout=settings.pyronites_timeout,
    )
    try:
        if args.check:
            present = _tables(client)
            missing = [name for name in EXPECTED_TABLES if name not in present]
            logger.info(
                "Project %s contains: %s", settings.pyronites_project_id, ", ".join(present)
            )
            if missing:
                logger.error("Missing tables: %s", ", ".join(missing))
                return 1
            logger.info("All %s OmniAPI tables are present.", len(EXPECTED_TABLES))
            return 0

        count = apply_schema(client, SCHEMA_PATH.read_text(encoding="utf-8"))
        logger.info("Applied %s schema statements.", count)
        present = _tables(client)
        missing = [name for name in EXPECTED_TABLES if name not in present]
        if missing:
            logger.error("Missing tables after apply: %s", ", ".join(missing))
            return 1
        logger.info("Schema is up to date (%s tables).", len(EXPECTED_TABLES))
        return 0
    except DatabaseError as exc:
        logger.error("Schema apply failed: %s", exc)
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
