"""Process-wide shared ``httpx`` client for upstream provider calls.

Creating an ``httpx.AsyncClient`` per request means a new connection pool and
a fresh TLS handshake to every upstream provider on every call. One shared
client per process keeps connections alive and lets the event loop multiplex
the concurrent provider calls that the orchestrator fans out.
"""

import httpx

# Connect quickly so a dead upstream fails fast; give the response body room.
UPSTREAM_TIMEOUT = httpx.Timeout(30.0, connect=5.0)

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Return the shared async HTTP client, creating it on first use."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT, follow_redirects=False)
    return _client


async def close_client() -> None:
    """Close the shared client. Called from the application shutdown hook."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
