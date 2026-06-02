# OmniAPI Deployment Guide

Full-stack deployment: **FastAPI backend on Render**, **PostgreSQL on Supabase**, **Redis on Upstash**, **Next.js frontend on Vercel**.

---

## Architecture Overview

```
Browser → Vercel (Next.js) → Render (FastAPI) → Supabase (PostgreSQL)
                                              → Upstash (Redis)
                                              → Render Background Workers (Celery)
```

| Component          | Platform                  | Environment Variable       |
|--------------------|---------------------------|----------------------------|
| PostgreSQL Database| Supabase                  | `DATABASE_URL`             |
| Redis Cache/Broker | Upstash (or Render Redis) | `REDIS_URL`                |
| FastAPI Backend    | Render Web Service        | —                          |
| Celery Worker      | Render Background Worker  | —                          |
| Celery Beat        | Render Background Worker  | —                          |
| Next.js Frontend   | Vercel                    | `NEXT_PUBLIC_API_URL`      |

---

## Pre-Deployment Checklist

Before deploying, complete every item in this section.

### 1. Generate Production Secrets

Run these commands locally to generate secure keys. **Never reuse your development keys.**

```bash
# Navigate to backend directory
cd backend

# Activate your virtual environment
.venv\Scripts\activate.ps1        # Windows
# or: source .venv/bin/activate   # Linux/Mac

# Generate SECRET_KEY (copy the output)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY (copy the output)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Save both values securely — you'll need them when setting environment variables.

### 2. Verify All Tests Pass

```bash
cd backend
pytest --cov=app -v
```

Expected: all tests passing, coverage ≥ 80%.

### 3. Confirm Local Build Works

```bash
# Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm run build   # Must complete with 0 errors
```

---

## Step 1: Supabase (PostgreSQL Database)

### 1.1 Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and sign in.
2. Click **New project**.
3. Set a project name (e.g., `omniapi-production`), choose a region closest to your users, and set a strong database password.
4. Wait 1–2 minutes for the project to provision.

### 1.2 Get Your Connection Strings

You need **two different connection strings** for different purposes:

Go to: **Project Settings → Database → Connection string** and select the **URI** tab.

| Purpose                        | Mode to Select       | Typical Port | When to Use                    |
|--------------------------------|----------------------|--------------|--------------------------------|
| Running the API (Render)       | **Session pooler**   | `6543`       | `DATABASE_URL` in all services |
| Running Alembic migrations     | **Direct connection**| `5432`       | Only during `alembic upgrade`  |

They look like:
```
# Session pooler (use for API runtime)
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

# Direct connection (use only for migrations)
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

> **Note:** If your password contains special characters (`@`, `#`, `$`, etc.), URL-encode them: `@` → `%40`, `#` → `%23`, `$` → `%24`.

### 1.3 Apply Database Schema (Run Migrations)

Run this **once** from your local machine using the **direct connection** URI:

```bash
cd backend

# Set DATABASE_URL to the DIRECT connection (port 5432) just for this command
$env:DATABASE_URL = "postgresql://postgres.[PROJECT-REF]:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# Apply all migrations
alembic -c app/db/alembic.ini upgrade head

# Verify - should output: 007 (head)
alembic -c app/db/alembic.ini current
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade -> 001, Create users table
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, Create api keys table
...
INFO  [alembic.runtime.migration] Running upgrade 006 -> 007, Audit hardening
```

> If you get `type "user_tier" already exists`, the schema was applied twice. Use a fresh database or run `alembic stamp head` if tables already exist from a SQL script.

### 1.4 Verify Tables

In Supabase dashboard: **Table Editor** — you should see these tables:
- `users`, `api_keys`, `external_services`, `usage_logs`, `webhooks`, `webhook_events`, `alembic_version`

---

## Step 2: Upstash Redis

Supabase does not include Redis. Use Upstash for a serverless, free-tier Redis.

### 2.1 Create an Upstash Database

1. Go to [https://upstash.com](https://upstash.com) and sign in.
2. Click **Create Database**.
3. Choose a name (e.g., `omniapi-redis`), select the same region as your Supabase project, and click **Create**.

### 2.2 Get the Redis URL

In your Upstash database dashboard:
- Click **Details**
- Copy the **Redis URL** under "Connect to your database"

It looks like:
```
rediss://default:[PASSWORD]@[ENDPOINT].upstash.io:6379
```

Note the `rediss://` (with double `s`) — this means TLS is enabled, which is required by Upstash.

Save this URL — you'll need it as `REDIS_URL` in Render.

---

## Step 3: Render — Backend Deployment

### 3.1 Connect Your Repository

1. Go to [https://render.com](https://render.com) and sign in.
2. Click **New** → **Web Service**.
3. Connect your GitHub account and select the OmniAPI repository.

### 3.2 Configure the Web Service (FastAPI)

Fill in these settings:

| Setting           | Value                                           |
|-------------------|-------------------------------------------------|
| **Name**          | `omniapi-api`                                   |
| **Root Directory**| `backend`                                       |
| **Runtime**       | `Python 3`                                      |
| **Build Command** | `pip install -r requirements.txt`               |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

> **Migrations:** Run them from your local machine (Step 1.3) before the first deploy, or as a separate one-off Render Job. Do not run migrations in the build command — a failed migration will break your build.

### 3.3 Set Environment Variables for the Web Service

In Render dashboard → your service → **Environment** tab, add:

| Variable                    | Value                                              |
|-----------------------------|----------------------------------------------------|
| `ENVIRONMENT`               | `production`                                       |
| `DEBUG`                     | `False`                                            |
| `LOG_LEVEL`                 | `warning`                                          |
| `DATABASE_URL`              | Supabase **session pooler** URI (port `6543`)      |
| `REDIS_URL`                 | Upstash Redis URL                                  |
| `SECRET_KEY`                | Your generated secret key (Step 0)                 |
| `ENCRYPTION_KEY`            | Your generated Fernet key (Step 0)                 |
| `ALGORITHM`                 | `HS256`                                            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                                             |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7`                                                |
| `ALLOWED_ORIGINS`           | `https://your-app.vercel.app` *(update after Step 4)* |
| `CELERY_TASK_TIMEOUT`       | `30`                                               |
| `RATE_LIMIT_FREE`           | `100`                                              |
| `RATE_LIMIT_PRO`            | `1000`                                             |
| `RATE_LIMIT_ENTERPRISE`     | `10000`                                            |

Click **Save Changes**, then **Deploy**.

### 3.4 Note Your Backend URL

After deployment, Render assigns a URL like:
```
https://omniapi-api.onrender.com
```

Test it:
```bash
curl https://omniapi-api.onrender.com/api/v1/health
```

Expected response (`celery` may show `no_workers` until Step 3.5):
```json
{
  "status": "degraded",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "celery": "no_workers"
  },
  "version": "1.0.0"
}
```

### 3.5 Create Celery Worker Service

1. Click **New** → **Background Worker**.
2. Connect the same repository.

| Setting           | Value                                                      |
|-------------------|------------------------------------------------------------|
| **Name**          | `omniapi-worker`                                           |
| **Root Directory**| `backend`                                                  |
| **Runtime**       | `Python 3`                                                 |
| **Build Command** | `pip install -r requirements.txt`                          |
| **Start Command** | `celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4` |

Set the **same environment variables** as the web service.

### 3.6 Create Celery Beat Service

1. Click **New** → **Background Worker**.

| Setting           | Value                                                      |
|-------------------|------------------------------------------------------------|
| **Name**          | `omniapi-beat`                                             |
| **Root Directory**| `backend`                                                  |
| **Runtime**       | `Python 3`                                                 |
| **Build Command** | `pip install -r requirements.txt`                          |
| **Start Command** | `celery -A app.tasks.celery_app beat --loglevel=info`      |

Set the **same environment variables** as the web service.

> **Important:** Run only **one** beat instance. Multiple beat instances will cause duplicate scheduled tasks.

### 3.7 Configure Health Check

In Render: Web Service → **Settings** → **Health & Alerts**:

| Setting             | Value                |
|---------------------|----------------------|
| **Health Check Path**| `/api/v1/health`    |
| **Health Check Timeout** | `30` seconds   |

---

## Step 4: Vercel — Frontend Deployment

### 4.1 Prerequisites

- Node.js 18.x or higher (check with `node --version`)
- Vercel account at [https://vercel.com](https://vercel.com)

### 4.2 Import the Repository

1. Go to [https://vercel.com/new](https://vercel.com/new).
2. Click **Import Git Repository** and select your OmniAPI repository.
3. When prompted for the root directory, enter: `frontend`
4. Framework preset should auto-detect as **Next.js** — if not, select it manually.

### 4.3 Set Environment Variables

Before clicking **Deploy**, add this environment variable:

| Variable               | Value                                    |
|------------------------|------------------------------------------|
| `NEXT_PUBLIC_API_URL`  | `https://omniapi-api.onrender.com/api/v1` |

> Replace `omniapi-api.onrender.com` with your actual Render service URL from Step 3.4.

### 4.4 Build Settings (Verify)

| Setting          | Value           |
|------------------|-----------------|
| **Build Command**| `npm run build` |
| **Output Directory** | `.next`     |
| **Install Command** | `npm install` |

### 4.5 Deploy

Click **Deploy**. Vercel will:
1. Install dependencies (`npm install`)
2. Build the Next.js app (`npm run build`)
3. Deploy to a URL like `https://your-app.vercel.app`

The build should complete in 1–3 minutes.

### 4.6 Custom Domain (Optional)

1. In Vercel: your project → **Settings** → **Domains**.
2. Click **Add Domain** and enter your domain (e.g., `app.yourdomain.com`).
3. Follow Vercel's DNS instructions to add CNAME or A records at your domain registrar.
4. Vercel automatically provisions an SSL certificate.

---

## Step 5: Connect Frontend to Backend (CORS)

Now that Vercel has assigned your frontend URL, update the backend CORS setting:

1. Go to Render → `omniapi-api` service → **Environment**.
2. Update `ALLOWED_ORIGINS` to your Vercel URL:
   ```
   https://your-app.vercel.app
   ```
   If you have a custom domain:
   ```
   https://app.yourdomain.com
   ```
3. Click **Save Changes** — Render will automatically redeploy the API.

---

## Step 6: Post-Deployment Verification

Run through this checklist to confirm everything works end-to-end.

### 6.1 Backend Health Check

```bash
curl https://omniapi-api.onrender.com/api/v1/health
```

Expected (all green):
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok"
  },
  "version": "1.0.0"
}
```

### 6.2 Frontend Smoke Test

1. Open `https://your-app.vercel.app`
2. Open browser DevTools → **Network** tab
3. Click **Sign Up** and create a new account
4. Verify the network request goes to `omniapi-api.onrender.com` (not `localhost`)
5. Verify you are redirected to `/dashboard` after signup
6. Open DevTools → **Console** — confirm no CORS errors

### 6.3 Full Flow Test

- [ ] Register a new user account
- [ ] Log in and verify session persists on page refresh
- [ ] Create an API key
- [ ] Add an external service (Weather, News, or Stock)
- [ ] Call `POST /api/v1/orchestrate` from the Orchestrate page
- [ ] Create a webhook and verify it appears in the list
- [ ] Log out and verify redirect to login page

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `database: unreachable` in health check | Wrong `DATABASE_URL` | Verify you're using session pooler (port 6543) on Render. Add `?sslmode=require` if needed. |
| `redis: unreachable` | Wrong `REDIS_URL` or Upstash IP restriction | Check REDIS_URL format — Upstash uses `rediss://` (with double s). Verify no IP allowlist is blocking Render. |
| `celery: no_workers` | Worker service not running | Check Render Background Worker logs. Verify `REDIS_URL` matches the web service. |
| CORS error in browser | `ALLOWED_ORIGINS` not set correctly | Set to exact Vercel URL without trailing slash, e.g. `https://your-app.vercel.app`. Redeploy after changing. |
| `alembic.ini: file not found` | Wrong working directory | Ensure Render root directory is `backend` and run `alembic -c app/db/alembic.ini upgrade head`. |
| `type "user_tier" already exists` | Migrations ran twice | Run `alembic stamp head` on a clean database, or drop the `user_tier` enum manually in Supabase SQL editor. |
| Vercel build fails | TypeScript errors or missing env var | Run `npm run build` locally to see errors. Ensure `NEXT_PUBLIC_API_URL` is set in Vercel environment. |
| Frontend shows blank page | API URL mismatch | Open browser console. Check `NEXT_PUBLIC_API_URL` is set and matches Render URL exactly. |
| 401 errors after login | Token not sent | Verify `TOKEN_STORAGE_KEY` in localStorage after login in browser DevTools → Application. |
| Render service sleeps (free tier) | Free tier auto-sleep after 15 min inactivity | Upgrade to paid plan, or use a service like [Cron-job.org](https://cron-job.org) to ping `/api/v1/health` every 10 minutes. |

---

## Environment Variables Reference

### Backend (Render)

| Variable                      | Required | Description                                  | Example                                    |
|-------------------------------|----------|----------------------------------------------|---------------------------------------------|
| `ENVIRONMENT`                 | Yes      | Deployment environment                        | `production`                               |
| `DEBUG`                       | Yes      | Enable debug mode                             | `False`                                    |
| `DATABASE_URL`                | Yes      | Supabase session pooler PostgreSQL URI        | `postgresql://...@pooler.supabase.com:6543/postgres` |
| `REDIS_URL`                   | Yes      | Redis connection URL                          | `rediss://default:xxx@endpoint.upstash.io:6379` |
| `SECRET_KEY`                  | Yes      | JWT signing secret (32+ chars)                | Generated via `secrets.token_urlsafe(32)` |
| `ENCRYPTION_KEY`              | Yes      | Fernet key for encrypting API credentials     | Generated via `Fernet.generate_key()`     |
| `ALLOWED_ORIGINS`             | Yes      | Comma-separated allowed CORS origins          | `https://your-app.vercel.app`             |
| `ALGORITHM`                   | No       | JWT algorithm                                 | `HS256`                                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No       | Access token TTL                              | `30`                                       |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | No       | Refresh token TTL                             | `7`                                        |
| `CELERY_TASK_TIMEOUT`         | No       | Max seconds for a Celery task                 | `30`                                       |
| `RATE_LIMIT_FREE`             | No       | Requests/hour for free tier                   | `100`                                      |
| `RATE_LIMIT_PRO`              | No       | Requests/hour for pro tier                    | `1000`                                     |
| `RATE_LIMIT_ENTERPRISE`       | No       | Requests/hour for enterprise tier             | `10000`                                    |

### Frontend (Vercel)

| Variable               | Required | Description                      | Example                                          |
|------------------------|----------|----------------------------------|--------------------------------------------------|
| `NEXT_PUBLIC_API_URL`  | Yes      | Full URL to the backend API      | `https://omniapi-api.onrender.com/api/v1`        |

---

## Security Checklist

Before going live, verify:

- [ ] `SECRET_KEY` and `ENCRYPTION_KEY` are freshly generated (not from `.env.local`)
- [ ] `DEBUG=False` on Render
- [ ] `ENVIRONMENT=production` on Render
- [ ] `ALLOWED_ORIGINS` is set to your exact Vercel URL (no wildcards)
- [ ] `.env.local` files are in `.gitignore` and not committed to git
- [ ] Supabase database has **RLS (Row Level Security)** enabled for sensitive tables
- [ ] Render services are behind HTTPS (automatic on Render)
- [ ] Upstash Redis has a password (enabled by default)

---

## Local Development Setup

For new developers joining the project:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/omniapi.git
cd omniapi

# 2. Backend setup
cd backend
python -m venv .venv
.venv\Scripts\activate.ps1      # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt

# Copy example env and fill in values
cp .env.example .env.local
# Edit .env.local with your local Supabase and Redis credentials

# Run migrations
alembic -c app/db/alembic.ini upgrade head

# 3. Start all backend processes (3 terminals)

# Terminal 1 - API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3 - Celery beat (optional for scheduled tasks)
celery -A app.tasks.celery_app beat --loglevel=info

# 4. Frontend setup (new terminal)
cd frontend
npm install
cp .env.example .env.local
# .env.local already contains NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm run dev
```

Frontend: `http://localhost:3000`
Backend API: `http://localhost:8000`
API docs: `http://localhost:8000/docs`
Health check: `http://localhost:8000/api/v1/health`

---

## Deployment URLs Reference

| Service          | Platform | URL                                      |
|------------------|----------|------------------------------------------|
| Frontend         | Vercel   | `https://your-app.vercel.app`            |
| Backend API      | Render   | `https://omniapi-api.onrender.com`       |
| API Docs         | Render   | `https://omniapi-api.onrender.com/docs`  |
| Health Check     | Render   | `https://omniapi-api.onrender.com/api/v1/health` |
| Database         | Supabase | Managed via Supabase dashboard           |
| Redis            | Upstash  | Managed via Upstash dashboard            |
