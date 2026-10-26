"""Shared helpers for mapping database rows onto models."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def parse_bool(value: Any) -> bool:
    """Interpret a stored boolean.

    Booleans live in the database as INTEGER 0/1.
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes"}
    return bool(value)


def parse_datetime(value: Any) -> datetime | None:
    """Parse a stored timestamp.

    Timestamps are ISO-8601 strings in UTC, for example
    ``2026-10-22T05:42:29.493527+00:00``.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def parse_int(value: Any) -> int | None:
    """Interpret a stored integer."""
    if value is None:
        return None
    return int(value)
