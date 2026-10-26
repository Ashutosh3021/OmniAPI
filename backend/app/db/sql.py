"""Helpers for building SQL text safely.

Two properties matter here, and both come from the same place: the data store
has no parameter binding, so every value reaches it as part of the SQL text.

**No value is ever interpolated raw.** String values are sent as hex literals
(``CAST(x'68656c6c6f' AS TEXT)``) instead of quoted strings. That removes two
whole classes of problem at once:

* *Injection* — a value cannot break out of its literal, because it is not
  inside a literal at all. There is nothing to escape.
* *Edge filtering* — the API sits behind a web application firewall that
  inspects request bodies and blocks anything resembling a shell or SQL
  injection attempt (a backtick is enough to trip it). Hex encoding keeps
  user-supplied text out of the payload, so no user content can ever be
  mistaken for an attack.

Identifiers (table and column names) are never taken from user input; they
are constants in the repositories.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Iterable


def split_statements(sql: str) -> list[str]:
    """Split a SQL script into individual statements.

    Quoted literals and comments are respected, so a semicolon inside a string
    does not end a statement.
    """
    statements: list[str] = []
    buffer = ""

    for line in sql.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statement = buffer.strip()
            if statement:
                statements.append(statement)
            buffer = ""

    tail = buffer.strip()
    if tail:
        statements.append(tail)
    return statements


def strip_comments(sql: str) -> str:
    """Remove ``--`` line comments from a SQL script.

    Comments are documentation for the people reading ``schema.sql``. They are
    stripped before the script is sent to the data store so that prose in a
    comment can never be mistaken for an injection attempt.
    """
    lines = []
    for line in sql.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    return "\n".join(lines)


def sql_text(value: str) -> str:
    """Return ``value`` as a hex-encoded SQL text literal.

    The result is a TEXT value identical to ``value``; it is merely spelled
    differently so that no character of the value appears in the statement.
    """
    return "CAST(x'" + value.encode("utf-8").hex() + "' AS TEXT)"


def sql_literal(value: Any) -> str:
    """Return ``value`` as a SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, datetime):
        return sql_text(value.isoformat())
    if isinstance(value, str):
        return sql_text(value)
    raise TypeError(f"Cannot use {type(value).__name__} as a SQL literal")


def sql_in(values: Iterable[Any]) -> str:
    """Return a parenthesised list of literals for an ``IN`` clause.

    An empty sequence becomes ``(NULL)``, which matches no row — the correct
    behaviour for an empty filter, and safer than producing invalid SQL.
    """
    literals = [sql_literal(value) for value in values]
    if not literals:
        return "(NULL)"
    return "(" + ", ".join(literals) + ")"


def sql_where(clauses: Iterable[str]) -> str:
    """Join ``WHERE`` clauses with ``AND``."""
    parts = [clause for clause in clauses if clause]
    if not parts:
        return ""
    return " WHERE " + " AND ".join(parts)
