# OmniAPI Backend

Production-grade FastAPI backend with Supabase PostgreSQL, SQLAlchemy ORM, Alembic migrations, and Redis (via Docker Compose).

## Prerequisites

- Python 3.11+
- [Supabase](https://supabase.com) project with PostgreSQL credentials
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

Use **Python 3.11** (recommended). If `pip` reports a conflict between `supabase` and `httpx`, install core dependencies first, then `pip install supabase==2.3.5`.

### 2. Environment variables

Copy the example file and fill in your Supabase credentials:

```bash
cp .env.example .env.local
```

Update `.env.local`:

- `DATABASE_URL` — from Supabase Dashboard → **Settings** → **Database** → **Connection string** (URI mode)
- `SUPABASE_URL` and `SUPABASE_KEY` — from **Settings** → **API**
- `SECRET_KEY` — generate a strong random string for production

Example `DATABASE_URL`:

```
postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
```

### 3. Run database migrations

From the `backend` directory:

```bash
alembic -c app/db/alembic.ini upgrade head
```

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
│   ├── config.py            # Pydantic settings
│   ├── models/              # SQLAlchemy models (6 tables)
│   ├── db/                  # Base, session, Alembic
│   ├── api/v1/              # Versioned routes
│   ├── schemas/             # Pydantic schemas
│   ├── middleware/          # Error handling
│   └── utils/               # Custom exceptions
├── tests/
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Database Models

| Table | Description |
|-------|-------------|
| `users` | Accounts with tier (free/pro/enterprise) |
| `api_keys` | Hashed API keys per user |
| `external_services` | Third-party API credentials |
| `usage_logs` | Request analytics |
| `webhooks` | Outbound webhook subscriptions |
| `webhook_events` | Delivery queue and history |

## Authentication (Phase 2)

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/api/v1/auth/register` | Public |
| `POST` | `/api/v1/auth/login` | Public |
| `POST` | `/api/v1/auth/refresh` | Public |
| `GET` | `/api/v1/auth/me` | JWT |
| `POST` | `/api/v1/api-keys` | JWT |
| `GET` | `/api/v1/api-keys` | JWT |
| `DELETE` | `/api/v1/api-keys/{key_id}` | JWT |

API keys are prefixed with `omni_`. The raw key is returned only on creation. Use `Authorization: Bearer <access_token>` or `X-API-Key: omni_...` for protected routes (via `require_auth` / `require_api_key` dependencies).

## Orchestration (Phase 3)

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

Supported services: `weather` (OpenWeatherMap), `news` (NewsAPI), `stock` (Alpha Vantage).

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

## Testing & deployment (Phase 6)

```bash
cd backend
pip install -r requirements.txt
pytest --cov=app --cov-fail-under=80
```

- **62 tests**, offline by default (SQLite + fakeredis mocks)
- CI: `.github/workflows/ci.yml` (PostgreSQL 15 + Redis 7 on push to `main`/`develop`)
- Production Docker: `docker-compose.prod.yml` + `nginx.conf`
- Deploy guide: [`DeploymentGuide.md`](../DeploymentGuide.md) (Render backend + Vercel frontend)

## Observability (Phase 5)

| Method | Path | Auth |
|--------|------|------|
| `POST/GET/PATCH/DELETE` | `/api/v1/webhooks` | JWT |
| `POST` | `/api/v1/webhooks/{id}/test` | JWT |
| `GET` | `/api/v1/analytics/usage?period=last_24h` | JWT |
| `GET` | `/api/v1/analytics/reports` | JWT (CSV download) |

Webhook event types: `orchestrate.complete`, `orchestrate.failed`, `api_key.created` (HTTPS URLs only).

Start Celery Beat for hourly stats snapshots:

```bash
docker compose up -d redis celery_worker celery_beat
```

## Performance layer (Phase 4)

Start Redis and the Celery worker:

```bash
docker compose up -d redis celery_worker
```

Run the API locally (separate terminal):

```bash
uvicorn app.main:app --reload --port 8000
```

Features:
- **Redis cache** — per-service TTLs (`weather` 1h, `news` 30m, `stock` 5m); `cache_hit` on repeat requests
- **Rate limiting** — sliding window per tenant/API key; tier limits: free 100/hr, pro 1000/hr, enterprise 10000/hr
- **Celery workers** — external API calls run in parallel via `call_weather_api`, `call_news_api`, `call_stock_api` tasks
- **Headers** on `POST /orchestrate`: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

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

## Alembic Commands

```bash
# Apply all migrations
alembic -c app/db/alembic.ini upgrade head

# Roll back one revision
alembic -c app/db/alembic.ini downgrade -1

# Create new migration (after model changes)
alembic -c app/db/alembic.ini revision --autogenerate -m "description"
```

## Security Notes

- Never commit `.env` or `.env.local`
- Use Supabase connection pooling for serverless deployments
- Enable RLS on tables if exposing data via Supabase Data API
- Rotate `SECRET_KEY` and database passwords in production
