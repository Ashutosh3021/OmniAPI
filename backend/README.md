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
