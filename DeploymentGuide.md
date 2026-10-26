# OmniAPI Deployment Guide

Full-stack deployment: **FastAPI backend on Render**, **data on Pyronites**,
**Redis on Upstash**, **Next.js frontend on Vercel**.

---

## Architecture Overview

```
Browser → Vercel (Next.js) → Render (FastAPI) → Pyronites (data store)
                                               → Google / GitHub (sign-in)
                                               → Upstash (Redis)
                                               → Render Background Workers (Celery)
```

| Component          | Platform                  | Environment Variable(s)               |
|--------------------|---------------------------|---------------------------------------|
| Data store         | Pyronites                 | `PYRONITES_URL`, `PYRONITES_KEY`, `PYRONITES_PROJECT_ID` |
| Sign-in            | Google / GitHub           | `GOOGLE_CLIENT_*`, `GITHUB_CLIENT_*`, `OAUTH_*` |
| Redis Cache/Broker | Upstash (or Render Redis) | `REDIS_URL`                           |
| FastAPI Backend    | Render Web Service        | —                                     |
| Celery Worker      | Render Background Worker  | —                                     |
| Celery Beat        | Render Background Worker  | —                                     |
| Next.js Frontend   | Vercel                    | `NEXT_PUBLIC_API_URL`                 |

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

Expected: all tests passing, coverage ≥ 80%. The suite runs against an
in-process SQLite client that speaks the same SQL contract as the hosted
store, so it never touches your production project.

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

## Step 1: Pyronites (Data Store)

There is no ORM and no migration runner. The schema is plain DDL in
`backend/app/db/schema.sql`, applied idempotently with
`python -m app.db.bootstrap`.

### 1.1 Create a Pyronites Project

1. Sign in to your Pyronites deployment.
2. Create a project, e.g. `omniapi-production`.
3. Create an API key with **read/write** (or **admin**) scope for that project.

Note the three values you need: the deployment's base URL, the API key, and
the project id.

### 1.2 Apply the Schema

Run this **once** from your local machine (Render's start command also runs
it on every deploy, which is safe — every statement is `IF NOT EXISTS`):

```bash
cd backend
python -m app.db.bootstrap
```

Expected output:

```
INFO  Applied 16 schema statements.
INFO  Project omniapi-production contains: external_services, omniapi_api_keys, ...
INFO  Schema is up to date (8 tables).
```

To verify without changing anything:

```bash
python -m app.db.bootstrap --check
```

> **Note:** every statement is a network round trip (~450 ms), so the apply
> takes a few seconds. See [pyronites/README.md](./pyronites/README.md) for
> the constraints the schema is written around.

### 1.3 Verify Tables

`python -m app.db.bootstrap --check` should list all eight:
`omniapi_users`, `omniapi_api_keys`, `omniapi_oauth_identities`,
`external_services`, `usage_logs`, `webhooks`, `webhook_events`,
`refresh_tokens`.

---

## Step 2: Upstash Redis

Pyronites does not include Redis. Use Upstash for a serverless, free-tier Redis.

### 2.1 Create an Upstash Database

1. Go to [https://upstash.com](https://upstash.com) and sign in.
2. Click **Create Database**.
3. Choose a name (e.g., `omniapi-redis`), select the same region as your
   Pyronites deployment, and click **Create**.

### 2.2 Get the Redis URL

In your Upstash database dashboard:
- Click **Details**
- Copy the **Redis URL** under "Connect to your database"

It looks like:
```
rediss://default:[PASSWORD]@[ENDPOINT].upstash.io:6379
```

Note the `rediss://` (with double `s`) — this means TLS is enabled, which is
required by Upstash.

Save this URL — you'll need it as `REDIS_URL` in Render.

---

## Step 3: Google and GitHub OAuth Apps

There is no password sign-in. An account is created the first time somebody
signs in with a provider, so you need at least one provider configured before
anybody can use the product.

### 3.1 Google

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials).
2. **Create Credentials → OAuth client ID → Web application**.
3. Add the authorised redirect URI:
   ```
   https://<your-api-host>/api/v1/auth/oauth/google/callback
   ```
   For the first deploy this is `https://omniapi-api.onrender.com/api/v1/auth/oauth/google/callback`.
4. Copy the client id and secret.

### 3.2 GitHub

1. Go to [GitHub → Settings → Developer settings → OAuth Apps](https://github.com/settings/developers).
2. **New OAuth App**.
3. Set the callback URL to:
   ```
   https://<your-api-host>/api/v1/auth/oauth/github/callback
   ```
4. Copy the client id and generate a client secret.

### 3.3 Frontend callback

The backend finishes the provider exchange and then redirects the browser to
`OAUTH_SUCCESS_REDIRECT_URL` with a one-time code in the query string. The
frontend exchanges that code for tokens. Point it at your Vercel URL:

```
https://your-app.vercel.app/auth/callback
```

The `/auth/callback` page must store the tokens exactly like the old login
did — the token pair returned by `POST /api/v1/auth/oauth/exchange` has the
same shape the login response used to have. See
[docs/oauth-integration.md](./docs/oauth-integration.md).

---

## Step 4: Render — Backend Deployment

### 4.1 Connect Your Repository

1. Go to [https://render.com](https://render.com) and sign in.
2. Click **New** → **Web Service**.
3. Connect your GitHub account and select the OmniAPI repository.

### 4.2 Configure the Web Service (FastAPI)

Fill in these settings:

| Setting           | Value                                           |
|-------------------|-------------------------------------------------|
| **Name**          | `omniapi-api`                                   |
| **Root Directory**| `backend`                                       |
| **Runtime**       | `Python 3`                                      |
| **Build Command** | `pip install -r requirements.txt`               |
| **Start Command** | `bash -c "python -m app.db.bootstrap && bash start.sh"` |

> The start command applies the schema first. Because every statement is
> `IF NOT EXISTS`, this is idempotent — a failed deploy never leaves the
> database half-migrated the way a migration runner could.

### 4.3 Set Environment Variables for the Web Service

In Render dashboard → your service → **Environment** tab, add:

| Variable                    | Value                                              |
|-----------------------------|----------------------------------------------------|
| `ENVIRONMENT`               | `production`                                       |
| `DEBUG`                     | `False`                                            |
| `LOG_LEVEL`                 | `warning`                                          |
| `PYRONITES_URL`             | Your Pyronites deployment URL                      |
| `PYRONITES_KEY`             | Your read/write API key                            |
| `PYRONITES_PROJECT_ID`      | The production project id                          |
| `REDIS_URL`                 | Upstash Redis URL                                  |
| `SECRET_KEY`                | Your generated secret key (Pre-Deployment §1)      |
| `ENCRYPTION_KEY`            | Your generated Fernet key (Pre-Deployment §1)      |
| `ALGORITHM`                 | `HS256`                                            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                                             |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7`                                                |
| `GOOGLE_CLIENT_ID`          | From Step 3.1                                      |
| `GOOGLE_CLIENT_SECRET`      | From Step 3.1                                      |
| `GITHUB_CLIENT_ID`          | From Step 3.2                                      |
| `GITHUB_CLIENT_SECRET`      | From Step 3.2                                      |
| `OAUTH_REDIRECT_BASE_URL`   | `https://omniapi-api.onrender.com`                 |
| `OAUTH_SUCCESS_REDIRECT_URL`| `https://your-app.vercel.app/auth/callback`        |
| `OAUTH_FAILURE_REDIRECT_URL`| `https://your-app.vercel.app/login?error=oauth_failed` |
| `ALLOWED_ORIGINS`           | `https://your-app.vercel.app` *(update after Step 5)* |
| `CELERY_TASK_TIMEOUT`       | `30`                                               |
| `RATE_LIMIT_FREE`           | `100`                                              |
| `RATE_LIMIT_PRO`            | `1000`                                             |
| `RATE_LIMIT_ENTERPRISE`     | `10000`                                            |
| `RATE_LIMIT_OAUTH_PER_IP`   | `20`                                               |

Click **Save Changes**, then **Deploy**.

### 4.4 Note Your Backend URL

After deployment, Render assigns a URL like:
```
https://omniapi-api.onrender.com
```

Test it:
```bash
curl https://omniapi-api.onrender.com/api/v1/health
```

Expected response (`celery` may show `no_workers` until Step 4.5):
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

> **If you started from a different hostname:** update the redirect URIs in
> the Google and GitHub consoles to the final URL before testing sign-in.

### 4.5 Create Celery Worker Service (webhook delivery)

1. Click **New** → **Background Worker**.
2. Connect the same repository.

| Setting           | Value                                                      |
|-------------------|------------------------------------------------------------|
| **Name**          | `omniapi-worker-webhooks`                                  |
| **Root Directory**| `backend`                                                  |
| **Runtime**       | `Python 3`                                                 |
| **Build Command** | `pip install -r requirements.txt`                          |
| **Start Command** | `celery -A app.tasks.celery_app worker -Q webhooks --concurrency=4 --loglevel=info` |

Set the **same environment variables** as the web service.

> **Important:** the `-Q webhooks` flag pins this worker to the webhook queue.
> The queues are separated so a slow user endpoint cannot starve the
> maintenance worker. Use a **paid plan** for this worker — a free background
> worker sleeps after 15 minutes of inactivity, which delays queued
> deliveries.

### 4.6 Create Celery Beat Service

1. Click **New** → **Background Worker**.

| Setting           | Value                                                      |
|-------------------|------------------------------------------------------------|
| **Name**          | `omniapi-beat`                                             |
| **Root Directory**| `backend`                                                  |
| **Runtime**       | `Python 3`                                                 |
| **Build Command** | `pip install -r requirements.txt`                          |
| **Start Command** | `celery -A app.tasks.celery_app beat --loglevel=info`      |

Set the **same environment variables** as the web service.

> **Important:** Run only **one** beat instance. Multiple beat instances will
> cause duplicate scheduled tasks.

### 4.7 Configure Health Check

In Render: Web Service → **Settings** → **Health & Alerts**:

| Setting             | Value                |
|---------------------|----------------------|
| **Health Check Path**| `/api/v1/health/live`    |
| **Health Check Timeout** | `30` seconds   |

> Use `/api/v1/health/live`, not `/api/v1/health`. The liveness endpoint
> performs no dependency I/O, so it can never block the event loop or take
> the service out of rotation because the data store or Redis is briefly
> unreachable. Use `/api/v1/health/ready` for uptime monitoring instead —
> that one verifies the data store and Redis and returns 503 when they are
> down.

---

## Step 5: Vercel — Frontend Deployment

### 5.1 Prerequisites

- Node.js 18.x or higher (check with `node --version`)
- Vercel account at [https://vercel.com](https://vercel.com)

### 5.2 Import the Repository

1. Go to [https://vercel.com/new](https://vercel.com/new).
2. Click **Import Git Repository** and select your OmniAPI repository.
3. When prompted for the root directory, enter: `frontend`
4. Framework preset should auto-detect as **Next.js** — if not, select it
   manually.

### 5.3 Set Environment Variables

Before clicking **Deploy**, add this environment variable:

| Variable               | Value                                    |
|------------------------|------------------------------------------|
| `NEXT_PUBLIC_API_URL`  | `https://omniapi-api.onrender.com/api/v1` |

> Replace `omniapi-api.onrender.com` with your actual Render service URL from
> Step 4.4.

### 5.4 Build Settings (Verify)

| Setting          | Value           |
|------------------|-----------------|
| **Build Command**| `npm run build` |
| **Output Directory** | `.next`     |
| **Install Command** | `npm install` |

### 5.5 Deploy

Click **Deploy**. Vercel will:
1. Install dependencies (`npm install`)
2. Build the Next.js app (`npm run build`)
3. Deploy to a URL like `https://your-app.vercel.app`

The build should complete in 1–3 minutes.

### 5.6 Custom Domain (Optional)

1. In Vercel: your project → **Settings** → **Domains**.
2. Click **Add Domain** and enter your domain (e.g. `app.yourdomain.com`).
3. Follow Vercel's DNS instructions to add CNAME or A records at your domain
   registrar.
4. Vercel automatically provisions an SSL certificate.

---

## Step 6: Connect Frontend to Backend (CORS)

Now that Vercel has assigned your frontend URL, update the backend CORS
setting:

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

## Step 7: Post-Deployment Verification

Run through this checklist to confirm everything works end-to-end.

### 7.1 Backend Health Check

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

### 7.2 Sign-In Providers

```bash
curl https://omniapi-api.onrender.com/api/v1/auth/oauth/providers
```

Expected: the providers you configured report `"configured": true`.

### 7.3 Frontend Smoke Test

1. Open `https://your-app.vercel.app`
2. Open browser DevTools → **Network** tab
3. Click **Sign in with Google** (or GitHub) and complete the flow
4. Verify the browser is redirected through
   `omniapi-api.onrender.com/api/v1/auth/oauth/...` and lands on
   `/auth/callback`
5. Verify you are redirected to `/dashboard` after sign-in
6. Open DevTools → **Console** — confirm no CORS errors

### 7.4 Full Flow Test

- [ ] Sign in with Google; a new account is created on first sign-in
- [ ] Sign in with GitHub with the same email — it links to the same account
- [ ] Verify session persists on page refresh
- [ ] Create an API key
- [ ] Add an external service (Weather, News, or Stock)
- [ ] Call `POST /api/v1/orchestrate` from the Orchestrate page
- [ ] Create a webhook and verify it appears in the list
- [ ] Log out and verify redirect to the sign-in page

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `database: unreachable` in health check | Wrong `PYRONITES_URL` or key | Verify the URL, key and project id. A cold free-tier instance can take >30 s to answer the first request. |
| `401 unauthorized` from the data store | Key missing, wrong, or scoped to another project | Re-check `PYRONITES_KEY` and its scope |
| `403` from the data store, intermittent | Cloudflare blocked the request body (a backtick in a string literal) | All literals are hex-encoded via `app/db/sql.py`; keep it that way. The client retries a block once. |
| Health check ok but sign-in redirect fails | Wrong `OAUTH_REDIRECT_BASE_URL` | It must be the public API origin, with no trailing path: `https://omniapi-api.onrender.com` |
| Provider says "redirect URI mismatch" | The callback URI in the Google/GitHub console does not match | It must be exactly `https://<api-host>/api/v1/auth/oauth/{provider}/callback` |
| `redis: unreachable` | Wrong `REDIS_URL` or Upstash IP restriction | Check REDIS_URL format — Upstash uses `rediss://` (with double s). Verify no IP allowlist is blocking Render. |
| `celery: no_workers` | Worker service not running | Check Render Background Worker logs. Verify `REDIS_URL` matches the web service. |
| CORS error in browser | `ALLOWED_ORIGINS` not set correctly | Set to exact Vercel URL without trailing slash, e.g. `https://your-app.vercel.app`. Redeploy after changing. |
| Vercel build fails | TypeScript errors or missing env var | Run `npm run build` locally to see errors. Ensure `NEXT_PUBLIC_API_URL` is set in Vercel environment. |
| Frontend shows blank page | API URL mismatch | Open browser console. Check `NEXT_PUBLIC_API_URL` is set and matches Render URL exactly. |
| 401 errors after sign-in | Token not sent | Verify the token pair is stored after `/auth/oauth/exchange` in browser DevTools → Application. |
| 401 after 30 minutes of inactivity | Access token expired and not refreshed | The dashboard must send the stored `refresh_token` to `POST /api/v1/auth/refresh` and store the returned pair. Refresh tokens rotate: the old one is revoked, so it must be replaced on every refresh. |
| 429 on sign-in | OAuth throttling | Sign-in starts are limited per IP (default 20 per 15 minutes). Raise `RATE_LIMIT_OAUTH_PER_IP` if legitimate traffic is being blocked. |
| Every data call is slow (~450 ms) | Expected: every statement is a network round trip to the data store | Reads that are hit often should be cached (see the 30 s user cache in `app/services/user_cache.py`); statement batching saves connection setup, not per-statement cost. |
| Render service sleeps (free tier) | Free tier auto-sleep after 15 min inactivity | Upgrade to paid plan, or use a service like [Cron-job.org](https://cron-job.org) to ping `/api/v1/health/live` every 10 minutes. |

---

## Environment Variables Reference

### Backend (Render)

| Variable                      | Required | Description                                  | Example                                    |
|-------------------------------|----------|----------------------------------------------|---------------------------------------------|
| `ENVIRONMENT`                 | Yes      | Deployment environment                        | `production`                               |
| `DEBUG`                       | Yes      | Enable debug mode                             | `False`                                    |
| `PYRONITES_URL`               | Yes      | Data store base URL                           | `https://pyrocore-backend.onrender.com`    |
| `PYRONITES_KEY`               | Yes      | API key with read/write scope                 | `pyro_live_...`                            |
| `PYRONITES_PROJECT_ID`        | Yes      | Project the key is scoped to                  | `omniapi-production`                       |
| `PYRONITES_TIMEOUT`           | No       | Per-request timeout in seconds                | `30`                                       |
| `REDIS_URL`                   | Yes      | Redis connection URL                          | `rediss://default:xxx@endpoint.upstash.io:6379` |
| `SECRET_KEY`                  | Yes      | JWT signing secret (32+ chars)                | Generated via `secrets.token_urlsafe(32)` |
| `ENCRYPTION_KEY`              | Yes      | Fernet key for encrypting API credentials     | Generated via `Fernet.generate_key()`     |
| `ALLOWED_ORIGINS`             | Yes      | Comma-separated allowed CORS origins          | `https://your-app.vercel.app`             |
| `ALGORITHM`                   | No       | JWT algorithm                                 | `HS256`                                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No       | Access token TTL                              | `30`                                       |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | No       | Refresh token TTL                             | `7`                                        |
| `GOOGLE_CLIENT_ID`            | No*      | Google OAuth client id                        | From Google Cloud Console                  |
| `GOOGLE_CLIENT_SECRET`        | No*      | Google OAuth client secret                    | From Google Cloud Console                  |
| `GITHUB_CLIENT_ID`            | No*      | GitHub OAuth client id                        | From GitHub OAuth Apps                     |
| `GITHUB_CLIENT_SECRET`        | No*      | GitHub OAuth client secret                    | From GitHub OAuth Apps                     |
| `OAUTH_REDIRECT_BASE_URL`     | No*      | Public origin of this API                     | `https://omniapi-api.onrender.com`         |
| `OAUTH_SUCCESS_REDIRECT_URL`  | No*      | Where the browser lands after sign-in         | `https://your-app.vercel.app/auth/callback`|
| `OAUTH_FAILURE_REDIRECT_URL`  | No       | Where the browser lands on a failed sign-in   | `https://your-app.vercel.app/login?error=oauth_failed` |
| `OAUTH_STATE_TTL_SECONDS`     | No       | How long a sign-in attempt stays valid        | `600`                                      |
| `OAUTH_CODE_TTL_SECONDS`      | No       | How long the one-time code stays valid        | `300`                                      |
| `CELERY_TASK_TIMEOUT`         | No       | Max seconds for a Celery task                 | `30`                                       |
| `RATE_LIMIT_FREE`             | No       | Requests/hour for free tier                   | `100`                                      |
| `RATE_LIMIT_PRO`              | No       | Requests/hour for pro tier                    | `1000`                                     |
| `RATE_LIMIT_ENTERPRISE`       | No       | Requests/hour for enterprise tier             | `10000`                                    |
| `RATE_LIMIT_OAUTH_PER_IP`     | No       | Sign-in starts per IP per window              | `20`                                       |
| `RATE_LIMIT_AUTH_WINDOW_SECONDS` | No    | Sign-in throttle window                       | `900`                                      |

\* Required if that provider is offered on the sign-in screen. A provider with
no credentials is simply not listed — the product needs at least one.

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
- [ ] The Pyronites API key is scoped to the production project only, and is
      never committed
- [ ] OAuth client secrets live only in Render's environment, never in the
      frontend
- [ ] The OAuth redirect URIs in the Google/GitHub consoles match the deployed
      API exactly
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
# Edit .env.local with your Pyronites, Redis and OAuth values

# Apply the schema (idempotent)
python -m app.db.bootstrap

# 3. Start all backend processes (3 terminals)

# Terminal 1 - API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Celery worker (webhook delivery)
celery -A app.tasks.celery_app worker -Q webhooks --concurrency=4 --loglevel=info

# Terminal 3 - Celery beat (scheduled retention)
celery -A app.tasks.celery_app beat --loglevel=info

# 4. Frontend setup (new terminal)
cd frontend
npm install
cp .env.example .env.local
# .env.local already contains NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm run dev
```

> The automated test suite does not need a live data store: it uses an
> in-process SQLite client with the same contract
> (`backend/app/db/sqlite_client.py`), so `pytest` works on a clean machine.

Frontend: `http://localhost:3000`
Backend API: `http://localhost:8000`
API docs: `http://localhost:8000/docs`
Health check: `http://localhost:8000/api/v1/health`

For local OAuth against `localhost`, register these redirect URIs in the
provider consoles as well:

```
http://localhost:8000/api/v1/auth/oauth/google/callback
http://localhost:8000/api/v1/auth/oauth/github/callback
```

---

## Deployment URLs Reference

| Service          | Platform  | URL                                      |
|------------------|-----------|------------------------------------------|
| Frontend         | Vercel    | `https://your-app.vercel.app`            |
| Backend API      | Render    | `https://omniapi-api.onrender.com`       |
| API Docs         | Render    | `https://omniapi-api.onrender.com/docs`  |
| Health Check     | Render    | `https://omniapi-api.onrender.com/api/v1/health` |
| Data store       | Pyronites | Managed via the Pyronites deployment     |
| Sign-in          | Google / GitHub | Managed in each provider's console  |
| Redis            | Upstash   | Managed via Upstash dashboard            |
