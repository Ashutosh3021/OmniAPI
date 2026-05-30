# Supabase setup for OmniAPI

OmniAPI stores all relational data in **Supabase PostgreSQL**. Redis (cache, rate limits, Celery) stays separate—locally via Docker or [Upstash](https://upstash.com) in production.

## 1. Create a Supabase project

1. Go to [supabase.com](https://supabase.com) → **New project**.
2. Save the **database password** (you need it for connection strings).

## 2. Connection strings

In the dashboard: **Project Settings → Database → Connection string → URI**.

| Use case | Supabase mode | Port | Notes |
|----------|---------------|------|--------|
| **Alembic migrations** | **Direct connection** | `5432` | Required for DDL (`CREATE TYPE`, etc.) |
| **FastAPI / SQLAlchemy app** | **Session pooler** (recommended) or Direct | `6543` / `5432` | Set `DATABASE_URL` in `.env.local` |

Replace `[YOUR-PASSWORD]` in the URI. If the password contains `@`, `#`, or `%`, [URL-encode](https://www.urlencoder.org/) it.

Example (direct, for migrations only):

```text
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
```

Use the exact URI from your dashboard—host format varies by region.

## 3. Configure the backend

Copy `backend/.env.example` → `backend/.env.local` and set at minimum:

```env
DATABASE_URL=postgresql://...   # Session pooler URI for running the API
SECRET_KEY=...                  # python -c "import secrets; print(secrets.token_urlsafe(32))"
ENCRYPTION_KEY=...              # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
REDIS_URL=redis://localhost:6379/0
```

Optional (for future Supabase client features):

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_anon_or_service_role_key
```

The app uses **SQLAlchemy + `DATABASE_URL`** today; it does not require the `supabase` Python package.

## 4. Apply the schema (choose one method)

### Option A — Alembic (recommended)

Use the **direct** connection string (temporarily) so enums and FKs apply cleanly:

```bash
cd backend
# Windows PowerShell (one-off):
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres"
alembic -c app/db/alembic.ini upgrade head
```

Then point `DATABASE_URL` in `.env.local` at the **pooler** URI for day-to-day API runs.

Verify:

```bash
alembic -c app/db/alembic.ini current
# Should show: 007 (head)
```

### Option B — SQL Editor

1. Open **SQL → New query** in Supabase.
2. Paste the contents of [`schema.sql`](schema.sql) and run.

If you use Option B on an empty database, stamp Alembic so it does not re-run migrations:

```bash
cd backend
alembic -c app/db/alembic.ini stamp head
```

**Do not** run `schema.sql` and `upgrade head` on the same empty database—you will get duplicate tables/types.

## 5. Run the stack locally

```bash
# Terminal 1 — Redis + Celery
cd backend
docker compose up redis celery_worker celery_beat

# Terminal 2 — API (after .env.local is set)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Or with Docker API profile:

```bash
docker compose --profile full up
```

Health check: `GET http://localhost:8000/api/v1/health`

## 6. GitHub Actions / CI

CI uses a **local Postgres service** in the workflow—not your Supabase project—so PRs never touch production data. Your Supabase project is only for local dev and deployed environments.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `type "user_tier" already exists` | DB partially migrated or `schema.sql` already run. Use a fresh DB, or `alembic stamp head` if schema matches. |
| `connection refused` on port 5432 | Wrong host, IP allowlist, or use pooler port `6543` for the app. |
| `password authentication failed` | Reset DB password in Supabase; update `DATABASE_URL`. |
| Migrations hang | Use **direct** connection, not transaction pooler, for `alembic upgrade`. |
