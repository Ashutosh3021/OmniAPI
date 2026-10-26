# OmniAPI Backend

Production-grade FastAPI backend with Pyronites (an HTTP data store backed by
SQLite) and Redis (via Docker Compose).

## Prerequisites

- Python 3.11+
- A [Pyronites](../pyronites/README.md) project with a read/write API key
- Docker (optional, for Redis)

## Quick Start

### 1. Virtual environment

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

Use **Python 3.11** (recommended).

### 2. Environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env.local
```

Update `.env.local`:

- `PYRONITES_URL`, `PYRONITES_KEY`, `PYRONITES_PROJECT_ID` — from your
  Pyronites deployment (see [pyronites/README.md](../pyronites/README.md))
- `SECRET_KEY` — generate a strong random string for production
- `ENCRYPTION_KEY` — Fernet key for external-service credentials
- `GOOGLE_CLIENT_ID` / `GITHUB_CLIENT_ID` and their secrets — sign-in (at
  least one provider must be configured)

### 3. Apply the schema

From the `backend` directory:

```bash
python -m app.db.bootstrap          # apply the schema
python -m app.db.bootstrap --check  # report only
```

There is no ORM and no migration runner. The schema lives in
`app/db/schema.sql` as plain DDL, and every statement is `IF NOT EXISTS`, so
applying it is idempotent — the production start command runs it on every
boot.

### 4. Start Redis (optional)

```bash
docker compose up -d redis
```

### 5. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

## Docker

Redis only (default):

```bash
docker compose up -d redis
```

Full stack (API + Redis):

```bash
docker compose --profile full up -d
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Pydantic settings (store, Redis, OAuth)
│   ├── models/              # Dataclasses — no ORM
│   ├── db/
│   │   ├── schema.sql       # The DDL; source of truth
│   │   ├── client.py        # HTTP client for the data store
│   │   ├── sqlite_client.py # In-process SQLite (tests / local)
│   │   ├── bootstrap.py     # python -m app.db.bootstrap
│   │   └── repositories/    # One module per table
│   ├── api/v1/              # Versioned routes
│   ├── schemas/             # Pydantic request/response schemas
│   ├── middleware/          # Auth, rate limiting, error handling
│   └── utils/               # Custom exceptions
├── tests/
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Data Layer

| Table | Description |
|-------|-------------|
| `omniapi_users` | Accounts with tier (free/pro/enterprise) |
| `omniapi_api_keys` | Hashed API keys per user |
| `omniapi_oauth_identities` | Which provider account maps to which user |
| `external_services` | Third-party API credentials (Fernet-encrypted) |
| `usage_logs` | Request analytics |
| `webhooks` | Outbound webhook subscriptions |
| `webhook_events` | Delivery queue and history |
| `refresh_tokens` | Rotating refresh tokens |

The `omniapi_` prefix exists because the store reserves the bare names for
its own tables. Everything the application does goes through the
repositories in `app/db/repositories/` — no ad-hoc SQL elsewhere.

Constraints you must respect when editing SQL: no triggers (`updated_at` is
maintained in the application layer), no parameter binding (every literal is
hex-encoded via `app/db/sql.py`), and the edge in front of the store blocks
request bodies containing backticks. Details in
[pyronites/README.md](../pyronites/README.md).

## Authentication

Sign-in is OAuth only (Google / GitHub). Password endpoints do not exist.

| Method | Path | Auth |
|--------|------|------|
| `GET`  | `/api/v1/auth/oauth/providers` | Public |
| `GET`  | `/api/v1/auth/oauth/{provider}` | Public (302 to provider) |
| `GET`  | `/api/v1/auth/oauth/{provider}/callback` | Public (302 to frontend) |
| `POST` | `/api/v1/auth/oauth/exchange` | Public (one-time code → tokens) |
| `POST` | `/api/v1/auth/refresh` | Public (refresh token) |
| `POST` | `/api/v1/auth/logout` | JWT |
| `GET`  | `/api/v1/auth/me` | JWT |
| `POST` | `/api/v1/api-keys` | JWT |
| `GET`  | `/api/v1/api-keys` | JWT |
| `DELETE` | `/api/v1/api-keys/{key_id}` | JWT |

`/auth/register`, `/auth/login`, `/auth/change-password`,
`/auth/forgot-password` and `/auth/reset-password` return **404**.

The full contract for the frontend is in
[docs/oauth-integration.md](../docs/oauth-integration.md).

API keys are prefixed with `omni_`. The raw key is returned only on
creation. Use `Authorization: Bearer <access_token>` or
`X-API-Key: omni_...` for protected routes (via `require_auth` /
`require_api_key` dependencies).

## Orchestration

Generate a Fernet encryption key for external API credentials:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add it to `.env.local` as `ENCRYPTION_KEY`.

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/api/v1/external-services` | JWT |
| `GET` | `/api/v1/external-services` | JWT |
| `GET` | `/api/v1/external-services/{service_id}` | JWT |
| `PATCH` | `/api/v1/external-services/{service_id}` | JWT |
| `DELETE` | `/api/v1/external-services/{service_id}` | JWT |
| `POST` | `/api/v1/orchestrate` | JWT or `X-API-Key` |

Supported services: `weather` (OpenWeatherMap), `news` (NewsAPI), `stock`
(Alpha Vantage).

Example orchestrate request:

```json
{
  "services": ["weather", "news"],
  "params": {
    "weather": {"city": "London"},
    "news": {"query": "artificial intelligence", "language": "en"}
  }
}
```

## Testing & CI

```bash
cd backend
pip install -r requirements.txt
pytest --cov=app --cov-fail-under=80
```

- Offline by default: the suite uses the in-process SQLite client
  (`app/db/sqlite_client.py`) plus fakeredis mocks, so it never touches a
  live data store
- CI: `.github/workflows/ci.yml` (Redis 7 on push to `main`/`develop`); an
  integration job runs the suite against a real Celery worker
- Production Docker: `docker-compose.prod.yml` + `nginx.conf`
- Deploy guide: [`DeploymentGuide.md`](../DeploymentGuide.md) (Render backend
  + Vercel frontend)

## Observability

| Method | Path | Auth |
|--------|------|------|
| `POST/GET/PATCH/DELETE` | `/api/v1/webhooks` | JWT |
| `POST` | `/api/v1/webhooks/{id}/test` | JWT |
| `GET` | `/api/v1/analytics/usage?period=last_24h` | JWT |
| `GET` | `/api/v1/analytics/reports` | JWT (CSV download) |

Webhook event types: `orchestrate.complete`, `orchestrate.failed`,
`api_key.created` (HTTPS URLs only).

Start the Celery workers (webhook delivery, maintenance) and the scheduler:

```bash
docker compose up -d redis celery_webhooks celery_maintenance celery_beat
```

## Performance layer

Start Redis and the Celery workers:

```bash
docker compose up -d redis celery_webhooks celery_maintenance
```

Run the API locally (separate terminal):

```bash
uvicorn app.main:app --reload --port 8000
```

Features:
- **Redis cache** — per-service TTLs (`weather` 1h, `news` 30m, `stock` 5m);
  `cache_hit` on repeat requests
- **User cache** — a 30 s Redis cache in front of the ~450 ms data-store
  round trip, so authenticated requests do not pay it every time
- **Rate limiting** — sliding window per tenant/API key; tier limits: free
  100/hr, pro 1000/hr, enterprise 10000/hr
- **Parallel fan-out** — the orchestrator calls the providers directly with
  `asyncio.gather`, so `total_time_ms` is the slowest single upstream call,
  not the sum of all of them
- **Celery workers** — outbound webhook delivery and scheduled retention, on
  separate queues
- **Headers** on `POST /orchestrate`: `X-RateLimit-Limit`,
  `X-RateLimit-Remaining`, `X-Cache` (`HIT` / `MISS` / `PARTIAL`)

## Testing

```bash
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

## Code Quality

```bash
black app tests
isort app tests
flake8 app tests
mypy app
```

## Security Notes

- Never commit `.env` or `.env.local`
- Keep the Pyronites key scoped to its project; rotate it if leaked
- OAuth client secrets stay server-side (Render environment), never in the
  frontend bundle
- Rotate `SECRET_KEY` and `ENCRYPTION_KEY` in production
