# OmniAPI Deployment Guide

Deploy the **backend** on [Render](https://render.com) and the **frontend** on [Vercel](https://vercel.com). Never commit `.env`, `.env.local`, or real API keys.

---

## Prerequisites

- GitHub repository with OmniAPI code
- [Supabase](https://supabase.com) project (PostgreSQL) — **recommended** (see `supabase/schema.sql`)
- [Upstash Redis](https://upstash.com) or Render Redis (for cache, rate limits, Celery broker)
- External API keys: OpenWeatherMap, NewsAPI, Alpha Vantage (per tenant in the app)

Generate secrets locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"   # SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # ENCRYPTION_KEY
```

---

## Supabase database setup

1. Create a project at [supabase.com](https://supabase.com).
2. In **Project Settings → Database**, copy the **Connection string** (URI mode, `postgresql://...`).
3. Set `DATABASE_URL` in `backend/.env.local` to that value (use the **Session pooler** or direct connection as appropriate).
4. Apply schema using **one** of:
   - **Alembic (recommended):** `cd backend && alembic -c app/db/alembic.ini upgrade head`
   - **SQL file:** paste or run `supabase/schema.sql` in the Supabase SQL Editor

`backend/app/config.py` validates `DATABASE_URL` as PostgreSQL/Supabase. Redis and Celery still run outside Supabase (Docker locally or Upstash in production).

---

## 1. Backend on Render

### 1.1 PostgreSQL

Use **Supabase** (see above) or Render PostgreSQL:

1. In Render Dashboard → **New** → **PostgreSQL**.
2. Copy the **Internal Database URL** (use `postgresql://` form for SQLAlchemy).

### 1.2 Redis

Use **Upstash** (recommended) or Render Redis:

- Create a Redis database; copy `REDIS_URL` (e.g. `rediss://...` or `redis://...`).

### 1.3 Web service (FastAPI)

1. **New** → **Web Service** → connect your repo.
2. **Root directory:** `backend`
3. **Runtime:** Python 3.11
4. **Build command:**

   ```bash
   pip install -r requirements.txt && alembic -c app/db/alembic.ini upgrade head
   ```

5. **Start command:**

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

6. **Environment variables:**

   | Variable | Value |
   |----------|--------|
   | `DATABASE_URL` | Render/Supabase PostgreSQL URL |
   | `REDIS_URL` | Redis URL |
   | `SECRET_KEY` | Random 32+ char string |
   | `ENCRYPTION_KEY` | Fernet key |
   | `ENVIRONMENT` | `production` |
   | `DEBUG` | `False` |
   | `ALLOWED_ORIGINS` | `https://your-app.vercel.app` |
   | `CELERY_TASK_TIMEOUT` | `10` |

7. Deploy and note the URL, e.g. `https://omniapi-api.onrender.com`.

### 1.4 Celery worker (background)

1. **New** → **Background Worker** → same repo, root `backend`.
2. **Start command:**

   ```bash
   celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
   ```

3. Use the **same environment variables** as the web service.

### 1.5 Celery Beat (scheduled analytics)

1. **New** → **Background Worker**.
2. **Start command:**

   ```bash
   celery -A app.tasks.celery_app beat --loglevel=info
   ```

3. Same env vars as above. Run **only one** beat instance.

### 1.6 Verify backend

```bash
curl https://omniapi-api.onrender.com/api/v1/health
```

Expect `200` with `"status": "healthy"` when DB, Redis, and at least one Celery worker are up. `503` + `"degraded"` if a dependency is down.

---

## 2. Frontend on Vercel

### 2.1 Project setup

1. Import the GitHub repo in Vercel.
2. **Root directory:** `frontend`
3. Framework preset: **Next.js**

### 2.2 Environment variables

| Variable | Value |
|----------|--------|
| `NEXT_PUBLIC_API_URL` | `https://omniapi-api.onrender.com` |

(Adjust if your Next.js app uses a different name — check `frontend` for `process.env` usage.)

### 2.3 Deploy

Deploy from `main`. Vercel provides `https://your-app.vercel.app`.

### 2.4 CORS

Set Render `ALLOWED_ORIGINS` to your Vercel URL (comma-separated if you have preview domains):

```
https://your-app.vercel.app,https://your-app-*.vercel.app
```

Redeploy the API after changing CORS.

---

## 3. Docker production (optional)

On a VPS with Docker:

```bash
cd backend
cp .env.example .env   # fill in production values — do not commit
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile full up -d
```

- Nginx listens on ports 80/443 and proxies to the API.
- PostgreSQL and Redis are **not** published to the host in `docker-compose.prod.yml`.
- Use managed DB/Redis in cloud instead of containerized Postgres when possible.

---

## 4. GitHub Actions CI

Pushes to `main` / `develop` run `.github/workflows/ci.yml`:

- PostgreSQL 15 + Redis 7 service containers
- Alembic migrations
- `pytest --cov=app --cov-fail-under=80`

Add repository secret `TEST_ENCRYPTION_KEY` only if you override the default test key in the workflow.

---

## 5. Post-deploy checklist

- [ ] `GET /api/v1/health` returns healthy
- [ ] Register → login → create API key on production
- [ ] Add external services and run `/api/v1/orchestrate`
- [ ] Webhook test URL receives HTTPS POST
- [ ] Vercel frontend calls Render API without CORS errors
- [ ] Celery worker logs show task execution
- [ ] No secrets in git history

---

## 6. Troubleshooting

| Issue | Fix |
|-------|-----|
| Health `database: unreachable` | Check `DATABASE_URL`, SSL mode for Supabase (`?sslmode=require`) |
| Health `redis: unreachable` | Verify `REDIS_URL`, allow Render IPs on Upstash |
| Health `celery: no_workers` | Ensure worker service is running and shares `REDIS_URL` |
| 401 on API | Clock skew, expired JWT, or wrong `SECRET_KEY` across services |
| CORS errors | Update `ALLOWED_ORIGINS` on Render and redeploy |

---

## 7. URLs summary

| Component | Platform | Example |
|-----------|----------|---------|
| API | Render | `https://omniapi-api.onrender.com` |
| Worker | Render Background Worker | (no public URL) |
| Beat | Render Background Worker | (no public URL) |
| Frontend | Vercel | `https://omniapi.vercel.app` |
| Database | Supabase / Render Postgres | (private connection string) |
| Redis | Upstash / Render Redis | (private connection string) |
