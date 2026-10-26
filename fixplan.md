# OmniAPI — Fix Plan

**Status:** Draft for execution
**Created:** 2026-10-21
**Scope:** Everything found broken across two review passes — flow/adoption (primary), backend architecture (secondary).

> ⚠️ **Auth contract superseded (2026-10-23).** The sign-in contract in §3 and
> the items BE-4, BE-12, FE-8, 12e–12g that reference `/auth/register`,
> `/auth/login`, `change-password`, `forgot-password` and `reset-password`
> **no longer exist** — those endpoints return 404, and the same sweep
> replaced SQLAlchemy/Alembic/Supabase with Pyronites. The live auth contract
> is Google/GitHub OAuth and is documented in
> [`docs/oauth-integration.md`](./docs/oauth-integration.md), which is now
> the single source of truth for the auth surface. Treat the §3 auth rows
> below as history, not as work to implement.

---

## 0. Ownership & ground rules

| Lane | Owner | Files |
|---|---|---|
| **A — Backend** | This agent | `backend/**`, `pyronites/**`, `render.yaml`, `backend/docker-compose*.yml`, `backend/start.sh`, `DeploymentGuide.md` |
| **B — Frontend** | Other agent | `frontend/**` |
| **C — Contract** | This agent, jointly reviewed | This document, §3 |

**Hard rules**

1. **This agent does not create or edit any file under `frontend/`.** Zero overlap with Lane B.
2. **No shared file is edited by both lanes.** `frontend/**` and `backend/**` are disjoint. `.github/workflows/` — this agent owns `ci.yml`; Lane B adds a **new** file `frontend-ci.yml` rather than editing `ci.yml` (avoids a merge conflict).
3. **The contract in §3 is the single source of truth.** If the frontend's current shape disagrees with §3, §3 wins and the frontend is wrong. The root cause of the current breakage is that the frontend was built against a product that doesn't exist; §3 ends that class of bug.
4. **Ship in the order in §6.** Lane B can start on items that need only the *already-implemented* backend contract today (**§3.2** external-service CRUD and **§3.3** the response shape are live as-is). Everything else waits for the items marked `NEW` in §3.

> ⚠️ The frontend tree was actively changing while this plan was written (`frontend/components/shared/ConfirmDialog.tsx` appeared mid-review and was absent from the initial inventory). **Lane B must re-verify the file list before starting** — treat every "current behaviour" note in §5 as a snapshot, not a guarantee.

### 0.1 Frontend refactor in progress — coordination notes

`git status` at the time of writing shows Lane B mid-refactor. New: `DESIGN.md`, `frontend/components/shell/`, `frontend/components/fan/`, `frontend/lib/motion/`, `frontend/lib/engine/`, `frontend/lib/content/`, `frontend/app/fonts.ts`, `frontend/components/shared/CodePanel.tsx`, `ConfirmDialog.tsx`, `EmptyState.tsx`. Modified: all of `frontend/components/shared/*`, `frontend/context/NotificationContext.tsx`, `frontend/lib/constants.ts`, `frontend/package.json`, `frontend/tailwind.config.ts`.

**What this changes for Lane B:**

| Plan item | Note |
|---|---|
| **FE-8** (Badge/Button prop mismatch) | `Badge.tsx` and `Button.tsx` are being rewritten. The `variant` vs `tone` mismatch may be resolved by the rewrite — **re-check before fixing.** If the new `Badge` keeps a `variant` prop with the values already in use, FE-8 is done. If it keeps `tone`, decide the vocabulary once and update the call sites in the same pass. **`DESIGN.md` is the design source of truth for the new components — read it before touching any `shared/` file.** |
| **FE-1.1** (delete `SERVICE_TYPES`) | `frontend/lib/constants.ts` is modified. `SERVICE_TYPES` may already be gone. Re-check. |
| **FE-13** (delete `API_KEY_PERMISSIONS`) | Same file — re-check. |
| **FE-5** (orchestrate form) | A new `frontend/components/shared/EmptyState.tsx` and `CodePanel.tsx` now exist. **Use `EmptyState` for the "connect your first service" state and `CodePanel` for the response/curl output** rather than hand-rolling new components. |
| **FE-6** (onboarding checklist) | `frontend/components/shell/` may replace `DashboardShell.tsx`. The new `RecentActivity`/stats components may live under `shell/`. Re-locate before adding a checklist. |
| **FE-7** (mobile nav) | If the shell refactor also replaced `MobileBottomNav.tsx`, the nav item list may now live in `frontend/lib/content/`. Re-locate. |
| **FE-13** (docs hardcoded host) | `frontend/lib/content/` may now own the docs content. The hardcoded `https://omniapi-api.onrender.com` may have moved there. Re-locate. |

**Nothing in this plan requires a specific frontend file path to still be valid.** The *behavioural* requirements (FE-1 … FE-13) are what must hold; the file paths are a snapshot.

**One thing Lane B must not do:** do not "fix" the frontend to match the current backend by *hardcoding* `weather | news | stock` in a new constant. That recreates the exact bug this plan exists to kill. Fetch the list from `GET /external-services/supported` (§3.1) — it is a 30-line backend change and it makes the list impossible to get wrong again.

---

## 1. Root cause, in one paragraph

Users can't make API calls because **the "Add External Service" form can never succeed** — it posts `{name, serviceType, apiKey, rateLimit}` while the backend requires `{service_name, api_key, max_calls_per_hour}` with `service_name` restricted to `weather|news|stock`. Every submit is a 422, and the 422 body is discarded into a generic "Failed to add service" toast. Since `orchestrator_service.py:146-150` raises `ServiceNotConfiguredError` for any service with no row, a user who cannot create one **can never make a single orchestrate call**. Compounding it: the dropdown offers providers (`stripe`, `twilio`, `sendgrid`, `aws_s3`) the backend enum doesn't accept; the "Orchestrate" page is a generic curl box pointed at the wrong origin with no auth header and no knowledge of `/orchestrate`; the dashboard shows a new user three zeroed cards and a hardcoded-empty activity feed with no next step; and users are logged out every 30 minutes because the app clears an expired access token instead of using the refresh token it already holds. The backend is correct. The docs are correct. **The UI is wired to a product that was never built.**

---

## 2. Severity map

| ID | Sev | Lane | Summary |
|---|---|---|---|
| **FE-1** | P0 | B | External-service form payload + provider enum wrong → 422 on every submit |
| **FE-2** | P0 | B | `ExternalService` TS interface: 0 of 7 fields match the backend |
| **FE-3** | P0 | B | No UI path exists to call `/orchestrate` |
| **FE-4** | P1 | B | Session dies every 30 min; `refreshToken()` posts `{}` and logs the user out |
| **FE-5** | P1 | B | Dashboard gives a new user no next step (empty stats + hardcoded-empty activity) |
| **FE-6** | P1 | B | Mobile nav omits External Services → mobile users can't complete the flow |
| **FE-7** | P1 | B | `Badge`/`Button` prop mismatch → **TypeScript build is broken** |
| **FE-8** | P1 | B | Settings page is fake: password/profile updates never reach the API |
| **FE-9** | P2 | B | Billing shows hardcoded "Pro, 5M calls, $99" to free-tier users |
| **FE-10** | P2 | B | Analytics fabricates p50/p95; charts put service names on a time axis |
| **FE-11** | P2 | B | Webhook signing secret is returned by the API then silently dropped by the form |
| **FE-12** | P2 | B | API client can't render FastAPI 422 field errors (`detail` is an array) |
| **FE-13** | P3 | B | Dead/misleading constants (`SERVICE_TYPES`, `API_KEY_PERMISSIONS`), Zod v4 deprecations, hardcoded doc host, `ConfirmDialog` duplication |
| **BE-1** | P0 | A | Celery runs the `solo` pool in every deployment path → zero parallelism |
| **BE-2** | P0 | A | `orchestrate` is not async: `.delay()` + blocking `result.get()` in a thread |
| **BE-3** | P0 | A | Rate limiter is not atomic → overshoot under concurrency |
| **BE-4** | P0 | A | `/auth/login` and `/auth/register` have no rate limit at all |
| **BE-5** | P1 | A | Sync SQLAlchemy on the event loop in `async def` dependencies and endpoint |
| **BE-6** | P1 | A | `max_calls_per_hour` is stored and displayed but never enforced |
| **BE-7** | P1 | A | New Redis connection pool per request |
| **BE-8** | P1 | A | Liveness probe blocks the event loop for up to 5s |
| **BE-9** | P1 | A | One failed webhook delivery permanently disables the webhook |
| **BE-10** | P1 | A | `usage_logs` unbounded, write-amplified, no retention; no `api_key_id` |
| **BE-11** | P1 | A | Refresh tokens never rotated, never revocable |
| **BE-12** | P1 | A | Missing endpoints: change-password, update-profile, forgot/reset-password, service-test, api-key revoke |
| **BE-13** | P2 | A | Upstream provider credentials travel through the broker in decryptable form |
| **BE-14** | P2 | A | `params` unbounded → cache-flood vector that takes down the rate limiter (same Redis) |
| **BE-15** | P2 | A | `compute_hourly_stats` is an N+1 sweep writing snapshots nobody reads |
| **BE-16** | P2 | A | API-key requests cost 3 reads + 1 write transaction; write is on the request path |
| **BE-17** | P2 | A | Webhook delivery has no SSRF hardening beyond HTTPS |
| **BE-18** | P3 | A | Cross-cutting: backend error messages must be actionable |
| **BE-19** | P3 | A | Test gaps: eager Celery, SQLite-only, no Postgres/Redis integration job |

---

## 3. THE CONTRACT (v2) — both lanes code against this

Nothing in §3.2–§3.7 requires inventing behaviour. Where the frontend currently disagrees, the frontend is wrong.

### 3.1 Canonical service list — `NEW` (BE-12a)

The frontend must **never hardcode the provider list again**. The backend publishes it.

```
GET /api/v1/external-services/supported
```
```json
{
  "services": [
    {
      "service_name": "weather",
      "label": "OpenWeatherMap",
      "signup_url": "https://home.openweathermap.org/users/sign_up",
      "docs_url": "https://openweathermap.org/api",
      "required_params": "city OR (lat AND lon)",
      "example": { "city": "London" },
      "params": {
        "city":  { "type": "string", "required": false, "example": "London" },
        "lat":   { "type": "number", "required": false, "example": 51.51 },
        "lon":   { "type": "number", "required": false, "example": -0.13 }
      }
    },
    {
      "service_name": "news",
      "label": "NewsAPI",
      "signup_url": "https://newsapi.org/register",
      "docs_url": "https://newsapi.org",
      "required_params": "query",
      "example": { "query": "artificial intelligence" },
      "params": {
        "query":    { "type": "string", "required": true,  "example": "AI" },
        "language": { "type": "string", "required": false, "default": "en" }
      }
    },
    {
      "service_name": "stock",
      "label": "Alpha Vantage",
      "signup_url": "https://www.alphavantage.co/support/#api-key",
      "docs_url": "https://www.alphavantage.co/documentation/",
      "required_params": "symbol",
      "example": { "symbol": "AAPL" },
      "params": {
        "symbol": { "type": "string", "required": true, "example": "AAPL" }
      }
    }
  ]
}
```

> **Routing note (implementation trap):** this route MUST be registered **before** `GET /external-services/{service_id}` in `backend/app/api/v1/endpoints/external_services.py`, or FastAPI will try to parse `"supported"` as an int and 422.

### 3.2 External service CRUD

**Create** — `POST /api/v1/external-services`
```json
{ "service_name": "weather", "api_key": "<provider key>", "max_calls_per_hour": 100 }
```
- `service_name` ∈ `weather | news | stock` (the `ExternalServiceName` enum, `backend/app/schemas/external_service.py:10-15`)
- `api_key` — min length 1. Encrypted with Fernet at rest. **Never returned by any endpoint.**
- `max_calls_per_hour` — int ≥ 1. **Now enforced** (BE-6). Default 100.
- Response `201`: `ExternalServiceResponse` (see 3.3)

**List / read** — `GET /api/v1/external-services`, `GET /api/v1/external-services/{service_id}`

**Update** — `PATCH /api/v1/external-services/{service_id}`
```json
{ "api_key": "<new key>", "max_calls_per_hour": 250, "status": "inactive" }
```
- All fields optional. `status` ∈ `active | inactive`.
- `service_name` is **immutable** (it is the cache namespace and the upstream routing key).

**Delete** — `DELETE /api/v1/external-services/{service_id}` → 204. `usage_logs.service_id` → `NULL` (`ON DELETE SET NULL`).

**Test** — `NEW` (BE-12b): `POST /api/v1/external-services/{service_id}/test`
```json
{ "success": true, "service_name": "weather", "message": "Connection successful", "checked_at": "2026-10-21T12:00:00Z" }
```
- Always `200`, even on failure — `success:false` + a human-readable `message` (e.g. `"Weather API returned 401"`). The UI shows the message inline.
- Side effects: updates `status` (`active` on success, `error` on auth failure, unchanged otherwise), `error_message`, `last_tested_at`.

### 3.3 `ExternalService` response shape (canonical)

```json
{
  "service_id": 1,
  "service_name": "weather",
  "max_calls_per_hour": 100,
  "status": "active",
  "error_message": null,
  "last_tested_at": null,
  "created_at": "2026-10-01T09:12:00Z"
}
```

- `status` ∈ `active | inactive | error`. **There is no `"connected"` state.** The frontend's `"connected" | "error" | "disconnected"` is invented and must be deleted.
- `error_message` and `last_tested_at` are currently never written — BE-12b/13 makes them real.

### 3.4 API keys

**Create** — `POST /api/v1/api-keys` → `201` with `raw_key` returned **once**.
```json
{ "key_id": 1, "name": "prod", "is_active": true, "expires_at": null, "created_at": "...", "raw_key": "omni_..." }
```

**Update** — `PATCH /api/v1/api-keys/{key_id}` — **CHANGED** (BE-12c)
```json
{ "name": "prod", "expires_at": "2026-12-01T00:00:00Z", "is_active": false }
```
- `is_active` is now accepted. **Revocation ≠ deletion**: revoking sets `is_active=false` and keeps the row so `usage_logs.api_key_id` still attributes its traffic. Delete is for keys you never want to see again.
- The UI renders a "Revoked" badge for `is_active === false` — that state becomes reachable.

### 3.5 Auth

**Existing (unchanged)**
```
POST /api/v1/auth/register   { full_name, email, password }  → 201 UserResponse
POST /api/v1/auth/login      { email, password }              → 200 Token
GET  /api/v1/auth/me                                       → 200 UserResponse
POST /api/v1/auth/refresh   { refresh_token }                → 200 Token
```

**`UserResponse`** (unchanged, canonical)
```json
{ "user_id": 1, "email": "a@b.c", "full_name": "A B", "tier": "free", "created_at": "..." }
```
- `tier` ∈ `free | pro | enterprise`. **This is the single source of truth for plan display** (FE-9).

**`POST /api/v1/auth/refresh` — `CHANGED` (BE-11)**
- Body: `{ "refresh_token": "<token>" }` — **required**. (Today the frontend sends `{}` and gets a 422.)
- Rotation: the response contains a **new** `refresh_token`; the old one is revoked immediately.
- Reusing a revoked refresh token revokes the whole family (reuse detection).
- Frontend must **store** the returned `refresh_token`. (Today `frontend/lib/api.ts:55` stores only the access token and throws the new refresh token away.)

**`NEW` endpoints**

```
PATCH /api/v1/auth/me          { full_name }        → 200 UserResponse
POST  /api/v1/auth/change-password  { current_password, new_password }  → 204
POST  /api/v1/auth/forgot-password  { email }       → 202  (always 202 — no user enumeration)
POST  /api/v1/auth/reset-password   { token, new_password } → 204
POST  /api/v1/auth/logout        { refresh_token }   → 204  (revokes the token)
```
- `change-password`: verifies `current_password`; on success **revokes all refresh tokens** for the user (all other sessions are invalidated) and returns 204.
- `forgot-password`: creates a single-use reset token, TTL 1h, hashed at rest. Response is **always 202** with body `{"status": "accepted"}` regardless of whether the email exists. Email delivery is a separate integration — until a mail provider is wired, the token is written to the application log and returned in the response **only when `ENVIRONMENT != "production"`** (so dev/staging is testable). The UI must show the same message either way.
- `new_password` min length 8, same rule as registration.

### 3.6 Orchestrate

```
POST /api/v1/orchestrate
{
  "services": ["weather", "news"],
  "params": {
    "weather": { "city": "London" },
    "news":    { "query": "AI" }
  }
}
```
- Auth: `X-API-Key: omni_...` **or** `Authorization: Bearer <jwt>`.
- `params` keys must be a subset of `services` (already validated, `schemas/orchestrate.py:14-22`).
- Per-service params are validated against §3.1 (BE-14). Unknown params for a service → 422 with the allowed list.
- Response headers on **every** response (BE-8, BE-14c):
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 73
  X-RateLimit-Reset: 1758456000
  X-Cache: HIT | MISS        ← new, per request
  ```
  `X-Cache` is `HIT` when **all** requested services were served from cache, `MISS` otherwise, `PARTIAL` when mixed.
- Response body (unchanged):
```json
{
  "request_id": "uuid",
  "results": [
    { "service": "weather", "success": true, "data": {...}, "error": null, "response_time_ms": 210, "cache_hit": true }
  ],
  "total_time_ms": 210,
  "timestamp": "2026-10-21T12:00:00Z"
}
```

### 3.7 Errors — actionable messages (BE-18)

All errors keep FastAPI's `{"detail": ...}` shape, but `detail` must be **actionable**.

| Status | When | Example `detail` |
|---|---|---|
| 401 | bad/expired token or key | `"Session expired. Sign in again."` |
| 404 | service not configured | `"Service 'weather' is not configured. Add it under External Services."` |
| 404 | service inactive | `"Service 'weather' is inactive. Activate it under External Services."` |
| 429 | tenant rate limit | `"Rate limit exceeded for the free tier (100 requests/hour). Try again in 42 minutes."` |
| 429 | per-service quota | `"Service 'weather' reached your 100 calls/hour limit. Raise it under External Services or wait."` |
| 400 | provider auth failure | `"OpenWeatherMap rejected your API key (401). Update it under External Services."` |

422 validation errors keep FastAPI's array form: `{"detail": [{"loc": ["body","service_name"], "msg": "Field required", "type": "value_error.missing"}]}`. The frontend must render this (FE-12).

---

## 4. Lane A — Backend work (this agent)

### BE-1 · Celery `solo` pool → real concurrency (P0)

**File:** `backend/app/tasks/celery_app.py:34`

`worker_pool="solo"` is set in app config. Celery's `celery/bin/worker.py:44-61` (`WorkersPool.convert`) reads `app.conf.worker_pool` and **overrides the CLI `--pool` default**, and `celery/concurrency/solo.py` sets `self.limit = 1` / `max-concurrency: 1`. Therefore `--concurrency=2` (`backend/start.sh:3`), `--concurrency=4` (`backend/docker-compose.yml:20`) and `--concurrency=4` (`DeploymentGuide.md:248`) are all inert. The banner even prints `concurrency: 4 (solo)`.

**Fix**
1. Delete the hardcoded `worker_pool="solo"`. Replace with:
   ```python
   # Windows has no POSIX semaphores; prefork cannot start there.
   worker_pool="solo" if os.name == "nt" else "prefork",
   ```
2. Add `task_routes` so the three task families cannot starve each other:
   ```python
   task_routes={
       "tasks.call_weather_api": {"queue": "external"},
       "tasks.call_news_api":    {"queue": "external"},
       "tasks.call_stock_api":   {"queue": "external"},
       "tasks.dispatch_webhook": {"queue": "webhooks"},
       "tasks.compute_hourly_stats": {"queue": "analytics"},
   },
   ```
3. `backend/start.sh` — run one worker per queue, foreground the API:
   ```bash
   celery -A app.tasks.celery_app worker -Q external --concurrency=4 --loglevel=info &
   celery -A app.tasks.celery_app worker -Q webhooks --concurrency=2 --loglevel=info &
   celery -A app.tasks.celery_app beat --loglevel=info &
   exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. `backend/docker-compose.yml` — same three workers, `-Q` per queue.
5. `render.yaml` — add **three** `type: worker` services (`omniapi-worker-external`, `omniapi-worker-webhooks`, `omniapi-beat`) with the matching `-Q` flags. Today `render.yaml` has only a `web` service, so the worker only exists because `start.sh` backgrounds it inside the web dyno — they share a process group and a free-plan dyno.
6. `DeploymentGuide.md:237-265` — update the worker start commands to include `-Q`.

**Acceptance:** `celery -A app.tasks.celery_app worker` banner shows `concurrency: 4 (prefork)`. `celery_app.control.inspect().stats()` reports `max-concurrency: 4`.

> Note: BE-2 removes the external-API tasks from the request path entirely, so after BE-2 the `external` queue carries almost no traffic. The queue split still matters for `webhooks`.

---

### BE-2 · Make orchestrate genuinely async (P0)

**Files:** `backend/app/services/orchestrator_service.py:81,192`, `backend/app/tasks/external_api_tasks.py`, `backend/app/external_apis/*.py`

Today the "async offload" is a synchronous round trip: `.delay()` publishes to Redis, a worker picks it up, the result is written to the Redis result backend, and the request polls `AsyncResult.get(timeout=30)` in a thread — with `solo` (BE-1) those tasks run **serially**, so `total_time_ms` is the *sum* of upstream latencies, not the max.

**Recommended fix: drop Celery from the request path.** Celery is for fire-and-forget (webhooks) and schedules, not for a request/response gateway.

1. Move the provider calls into an async function that uses a **shared, module-level `httpx.AsyncClient`** (currently a new client per call — `weather_api.py:40`, `news_api.py:38`, `stock_api.py:38`):
   ```python
   # backend/app/external_apis/client_pool.py
   _client: httpx.AsyncClient | None = None
   def get_client() -> httpx.AsyncClient:
       global _client
       if _client is None:
           _client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0))
       return _client
   ```
2. `OrchestratorService.orchestrate` calls the providers directly with `asyncio.gather(...)` and an in-process retry (3 attempts, 1s/2s/4s backoff) instead of a Celery retry.
3. `backend/app/tasks/external_api_tasks.py` keeps the task wrappers (they're still useful for ad-hoc/manual invocation) but they are no longer on the request path.
4. `backend/app/services/orchestrator_service.py:192` — delete the `asyncio.to_thread(item.async_result.get, ...)` call. This also removes the `min(32, cpu+4)` thread-pool ceiling on concurrent orchestrate requests.

**Result:** `total_time_ms` becomes `max(upstream)` instead of `sum(upstream)`; no broker round trip; no result polling; no thread occupied for the request duration.

**Acceptance:** a 3-service orchestrate takes ~the slowest single upstream call, not the sum. `celery` is no longer in the orchestrate request path.

> **Alternative (if Celery must stay):** keep `.delay()`, but (a) fix BE-1 so the pool is `prefork`, (b) use `AsyncResult.get(timeout=..., interval=0.05)` to cut poll latency, and (c) raise `celery_task_timeout` above the 30s upstream timeout. This is strictly worse than removing it — prefer the direct path.

---

### BE-3 · Make the rate limiter atomic (P0)

**File:** `backend/app/services/rate_limiter.py:45-58`

`zremrangebyscore` + `zcard` run in a pipeline (not atomic), then `zadd` runs in a **second** pipeline. Every concurrent request between the read and the write sees the same count and passes. A 50-request burst against a limit of 100 lets all 50 through.

**Fix** — one Lua script, one round trip:
```lua
-- KEYS[1] = rate key, ARGV[1] = window start, ARGV[2] = now, ARGV[3] = limit
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])
local count = redis.call('ZCARD', KEYS[1])
if count >= tonumber(ARGV[3]) then return {0, 0} end
redis.call('ZADD', KEYS[1], ARGV[2], ARGV[2] .. '-' .. math.random())
redis.call('EXPIRE', KEYS[1], tonumber(ARGV[3]))
return {1, tonumber(ARGV[3]) - count - 1}
```
Register it with `self._redis.register_script(LUA)`. `fakeredis` supports Lua, so it is unit-testable.

**Also add:** a `Retry-After` value that reflects the oldest entry in the window (`ZRANGE ... WITHSCORES` → `oldest + window - now`), not a flat 3600.

**Tests:** add `backend/tests/test_rate_limiter.py::test_concurrent_burst_respects_limit` — fire 100 concurrent `is_allowed` calls at a limit of 10, assert exactly 10 succeed. This test does not exist today.

---

### BE-4 · Rate limit login and registration (P0)

**Files:** `backend/app/api/v1/endpoints/auth.py:29,51`, `backend/app/middleware/rate_limit.py`

`apply_rate_limit` is only reachable from `get_current_user` and the API-key decorators. `/auth/login` and `/auth/register` are completely unthrottled — an unthrottled password-guessing endpoint and an unthrottled account-farming endpoint (no email verification, so each signup buys 100 free-tier requests/hour).

**Fix**
1. Add an IP-keyed limiter to `backend/app/services/rate_limiter.py`:
   ```python
   async def is_allowed_ip(self, client_ip: str, limit: int, window_seconds: int) -> tuple[bool, int]
   ```
   Key: `omniapi:ratelimit:auth:{client_ip}`.
2. Add a FastAPI dependency `enforce_auth_rate_limit` in `backend/app/middleware/rate_limit.py` that reads the client IP from `request.client.host`, honouring `X-Forwarded-For` **only** when the app is behind a trusted proxy (set a `TRUSTED_PROXY_HEADER` setting; default off).
3. Apply to `login` (e.g. 10 / 15 min per IP) and `register` (5 / hour per IP), and 5 failed logins / 15 min per **account** (keyed on the email hash) → 429 with a clear message.
4. Add `RATE_LIMIT_LOGIN`, `RATE_LIMIT_REGISTER` to `backend/app/config.py`.

**Acceptance:** 11 rapid failed logins from one IP → 429. A correct password on attempt 11 still 429s (the limit is on attempts, not failures) — or key on failures only; pick one and document it. **Decision: key on attempts (simpler, no oracle).**

---

### BE-5 · Stop blocking the event loop (P1)

**Files:** `backend/app/middleware/auth_middleware.py:17,41`, `backend/app/utils/decorators.py:26-41,44-82`, `backend/app/api/v1/endpoints/orchestrate.py:28`, `backend/app/services/orchestrator_service.py:103`

`get_current_user` and `require_api_key` are `async def` but hold a **sync** SQLAlchemy `Session` and call `db.scalar(...)` / `db.commit()` — on the event loop thread. Every authenticated request blocks the whole event loop for at least one DB round trip; `require_api_key` does three reads plus a write transaction.

**Fix — phase 1 (this PR, small and safe):** make the auth dependencies plain `def` so FastAPI runs them in its threadpool (default 40 threads):
- `backend/app/middleware/auth_middleware.py` → `def get_current_user(...)`
- `backend/app/utils/decorators.py` → `def require_api_key(...)`, `def require_auth_or_api_key(...)`
- Keep `apply_rate_limit` awaited — it uses the async Redis client, so it must stay in an `async def` wrapper. Split it: do the Redis call in an `async def` helper, the DB call in the `def` dependency.

**Fix — phase 2 (separate PR, optional):** full async migration to `postgresql+asyncpg` + `AsyncSession`. Not required for the flow fix.

**Also:** move the `usage_logs` insert + `commit` out of the request path (it currently commits inside `orchestrate`). Use `BackgroundTasks` or a Celery `record_usage` task so the request doesn't wait on the write.

---

### BE-6 · Enforce `max_calls_per_hour` (P1)

**File:** `backend/app/services/orchestrator_service.py`

Grep confirms the column is read **nowhere** outside CRUD (`models/external_service.py:39`, `endpoints/external_services.py:30,65,129-130`, migrations). The user sets a limit, the UI displays it, and it does nothing.

**Fix** — a second Redis counter, per service, same sliding-window mechanism as BE-3:
- Key: `omniapi:rate:svc:{user_id}:{service_id}`
- Counted in `_load_configured_services` (before dispatch) so an over-quota service returns 429 with the §3.7 message and is **not** dispatched upstream.
- Per-service limit is `ExternalService.max_calls_per_hour`; it does **not** consume the tenant tier limit.
- Add `max_calls_per_hour` to the 429 detail message.

---

### BE-7 · Reuse the Redis connection (P1)

**Files:** `backend/app/services/rate_limiter.py:19`, `backend/app/services/cache_service.py:23`, `backend/app/api/v1/endpoints/health.py:24`

`RateLimiter()` and `CacheService()` each call `aioredis.from_url(...)` in `__init__`, and `apply_rate_limit` closes the client in a `finally` (`middleware/rate_limit.py:36-37`). Every authenticated request therefore does a TCP connect + AUTH + teardown — a full TLS handshake against Upstash.

**Fix**
1. New file `backend/app/services/redis_client.py`:
   ```python
   _redis: aioredis.Redis | None = None
   def get_redis() -> aioredis.Redis:
       global _redis
       if _redis is None:
           _redis = aioredis.from_url(get_settings().redis_url, decode_responses=True)
       return _redis
   ```
2. `RateLimiter.__init__` / `CacheService.__init__` use `get_redis()`.
3. **Delete** the `close()` calls in `middleware/rate_limit.py` and `orchestrator_service.py:137`. Close the client once in the FastAPI `lifespan` shutdown hook (`backend/app/main.py:30-35`).
4. `health.py:_check_redis` uses `get_redis()` too.

---

### BE-8 · Unblock the liveness probe; split live vs ready (P1)

**File:** `backend/app/api/v1/endpoints/health.py:51,71`

`health_check` is `async def` and calls the **synchronous** `_check_celery()` (`:71`), which runs `celery_app.control.inspect(timeout=5).ping()` — a blocking broker round trip on the event loop. `render.yaml:9` points `healthCheckPath` at this endpoint, so every platform probe can freeze the API for 5 seconds.

**Fix**
1. `await asyncio.to_thread(_check_celery)` with `timeout=2`.
2. Split the endpoints:
   - `GET /api/v1/health/live` — process liveness only, no I/O. Always 200 if the process is up. → `render.yaml:9` `healthCheckPath`.
   - `GET /api/v1/health/ready` — DB + Redis + Celery. 200 if all ok, 503 if any is down. Used by uptime monitoring.
3. Keep `GET /api/v1/health` as an alias of `/ready` for compatibility, but the platform should use `/live`.
4. **Make Celery critical for `/ready`.** Rationale: with the broker up but the worker down, `.delay()` still succeeds and the request blocks for the full `celery_task_timeout` before failing. Today `/health` reports `degraded` + 200 for exactly that state (`:73-84`), so the load balancer keeps routing traffic to a service that can only produce 30-second timeouts.

---

### BE-9 · Stop permanently disabling webhooks on first exhaustion (P1)

**File:** `backend/app/tasks/webhook_tasks.py:127-140`

After the final retry the task sets `webhook.is_active = False` permanently. A user endpoint that 500s for ~17 minutes (backoff 10/30/60/300/600s) loses its webhook forever, with no auto-recovery and no notification.

**Fix**
1. New column `webhooks.consecutive_failures` (int, default 0) — migration `008`.
2. On failure: `consecutive_failures += 1`. Disable only when `consecutive_failures >= 20`.
3. On success: reset `consecutive_failures = 0` and `retry_count = 0`.
4. Surface the counter in the `WebhookResponse` schema so the UI can show "3 consecutive failures" and offer a manual re-enable (`PATCH /webhooks/{id}` with `is_active: true` already exists).

---

### BE-10 · `usage_logs` hygiene (P1)

**Files:** `backend/app/models/usage_log.py`, new migration `008`

1. Add `api_key_id` (FK → `api_keys.id`, `ON DELETE SET NULL`, indexed) so traffic is attributable to a key even after revocation (FE-2 / §3.4).
2. Retention: new Celery beat task `tasks.purge_usage_logs` — daily, deletes `usage_logs` older than 90 days and `webhook_events` older than 30 days. Add to `beat_schedule` in `backend/app/tasks/celery_app.py:35-40`.
3. `webhook_events.payload` (a `TEXT` column holding the full JSON body, written on every attempt) — clear it to `NULL` after a terminal delivery, or move to object storage. Make it nullable in migration `008`.
4. Partitioning by month is a phase-3 item, not required now.

---

### BE-11 · Refresh token rotation, revocation, reuse detection (P1)

**File:** `backend/app/api/v1/endpoints/auth.py:67-88`, new migration `008`

Today `/auth/refresh` accepts any valid refresh JWT and mints a new pair. No `jti`, no server-side store, no rotation, no revocation, no reuse detection. Logout (`clearAuth` in the frontend) only wipes the browser — the token keeps working for 7 days from anywhere.

**Fix**
1. New table `refresh_tokens`:
   ```
   id           serial pk
   user_id      int not null references users(id) on delete cascade
   token_hash   varchar(255) not null unique     -- sha256 of the token
   family_id    uuid not null                     -- rotation family
   expires_at   timestamptz not null
   revoked_at   timestamptz null
   replaced_by  int null references refresh_tokens(id)
   created_at   timestamptz not null default now()
   ```
   Index on `user_id`, `family_id`, `token_hash`.
2. `POST /auth/login` and `/auth/register`-then-login issue a refresh token **and** persist its hash. The JWT keeps its `type: "refresh"` claim for stateless validation, but the DB row is the source of truth for validity.
3. `POST /auth/refresh`:
   - Look up the presented token by hash. If not found, or `revoked_at` is set → **401** and revoke the entire `family_id` (reuse detection — a revoked token being presented means it leaked).
   - If found and valid → revoke it, issue a new one, set `replaced_by`.
   - Access tokens are unaffected (they remain stateless, 30 min).
4. `POST /auth/logout` revokes the presented refresh token.
5. `POST /auth/change-password` revokes **all** refresh tokens for the user.
6. The `refresh_token` body field stays **required** — the frontend must be updated in the same release (FE-4). Do not accept a bodyless refresh; that would let a stale build silently keep a 7-day token alive.

---

### BE-12 · Missing endpoints (P1)

**File:** `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/external_services.py`, `backend/app/api/v1/endpoints/api_keys.py`, `backend/app/schemas/`

Implement, per §3:

| # | Endpoint | Purpose |
|---|---|---|
| 12a | `GET /external-services/supported` | Canonical provider list + param schemas (§3.1). **Register before `/{service_id}`.** |
| 12b | `POST /external-services/{id}/test` | Verify the stored provider credential; writes `status`, `error_message`, `last_tested_at` |
| 12c | `PATCH /api-keys/{id}` accepts `is_active` | Revocation distinct from deletion |
| 12d | `PATCH /auth/me` `{ full_name }` | Profile update |
| 12e | `POST /auth/change-password` | Real password change; revokes all refresh tokens |
| 12f | `POST /auth/forgot-password` | Always 202; issues a single-use reset token (logged in non-production) |
| 12g | `POST /auth/reset-password` | Consumes the reset token |
| 12h | `POST /auth/logout` | Revokes the refresh token |

**12b implementation detail:** call the provider with the stored (decrypted) key using a minimal request, catch `ExternalAPIError`, and map:
- success → `status = ACTIVE`, `error_message = None`
- 401/403 from the provider → `status = ERROR`, `error_message = "<Provider> rejected your API key (401)"`
- 429 from the provider → `status` unchanged, `error_message = "<Provider> rate limit reached"`

**12f implementation detail:** table `password_reset_tokens` (hashed token, user_id, expires_at, used_at) in migration `008`. No email provider is wired yet — the token is written to the log and included in the response body **only if `settings.environment != "production"`**. The response body is `{"status": "accepted"}` in production regardless.

---

### BE-13 · Stop shipping upstream credentials through the broker (P2)

**File:** `backend/app/services/orchestrator_service.py:83`

`encrypted_key=external_service.api_key_encrypted` is passed as a Celery task argument, so the Fernet ciphertext of every tenant's provider key lands in the Redis broker message and the result backend. Anyone with read access to Redis can collect every tenant's upstream credentials and decrypt them with `ENCRYPTION_KEY`.

**Fix** — pass the `service_id` instead; the worker reads the credential from Postgres (it already has DB access — see `backend/app/tasks/webhook_tasks.py:13`).
```python
async_result = task_fn.delay(
    service_id=external_service.id,
    params=params,
)
```
and in the task: `encrypted_key = db.get(ExternalService, service_id).api_key_encrypted`.

**Note:** if BE-2 lands, the provider call happens in-process and the credential never leaves the request at all — this item becomes moot for the request path but still applies to any remaining Celery-based provider task.

---

### BE-14 · Validate and bound `params` (P2)

**File:** `backend/app/schemas/orchestrate.py:8-22`

`params: dict[str, dict[str, Any]]` — unbounded in both shape and size. The whole dict is md5'd into the cache key (`backend/app/services/cache_service.py:31`) and shipped to the broker. A client sending many distinct large param sets floods Redis with full upstream responses. `backend/docker-compose.yml` runs `redis:7-alpine` with the default `noeviction` policy, so a flood surfaces as **Redis write errors**, and since the rate limiter shares that Redis, it takes down all auth.

**Fix**
1. Per-service pydantic param models, driven by the same registry that produces §3.1:
   ```python
   class WeatherParams(BaseModel):
       city: str | None = Field(default=None, max_length=100)
       lat: float | None = None
       lon: float | None = None
       model_config = ConfigDict(extra="forbid")
   class NewsParams(BaseModel):
       query: str = Field(..., min_length=1, max_length=200)
       language: str = Field(default="en", max_length=5)
   class StockParams(BaseModel):
       symbol: str = Field(..., min_length=1, max_length=10)
   ```
   With a `model_validator` on `WeatherParams` enforcing `city XOR (lat AND lon)`.
2. `extra="forbid"` → unknown params produce a 422 listing the allowed fields.
3. Cap the total request body: add a `max_request_bytes` setting and reject oversized bodies in middleware (or at minimum cap `len(json.dumps(params))` at 8 KB).
4. Add `maxmemory 256mb` + `maxmemory-policy allkeys-lru` to the Redis service in `backend/docker-compose.yml` and `backend/docker-compose.prod.yml` so a flood evicts rather than errors.

---

### BE-15 · Delete the dead hourly stats task (P2)

**File:** `backend/app/tasks/analytics_tasks.py`

`compute_hourly_stats` runs an N+1 sweep — one query for the tenant list (`:40`) then one aggregate **per tenant** (`:45-60`) — every hour, on the same single worker, and writes `omniapi:stats:{user_id}:hourly` into Redis. Grep confirms that key has **zero readers**; the dashboard reads Postgres directly through `AnalyticsService`.

**Fix:** delete `backend/app/tasks/analytics_tasks.py` and its `beat_schedule` entry (`celery_app.py:35-40`). If per-tenant aggregates later become too slow, reintroduce them as a real `usage_daily` rollup table — not as a Redis snapshot nobody reads.

---

### BE-16 · Cut API-key request cost (P2)

**File:** `backend/app/utils/decorators.py:36-37`, `backend/app/services/api_key_service.py:41-72`

`require_api_key` queries `APIKey` by hash, then `validate_api_key` runs **the same query again**, plus `db.get(User, ...)`, plus `api_key.last_used_at = ...; db.commit()`. Three reads and a write transaction per API-key request, on the request path.

**Fix**
1. `validate_api_key` returns the `APIKey` object alongside the user (or the decorator uses the `api_key` it already fetched and skips the second lookup).
2. Batch `last_used_at`: only write it if the stored value is older than 60 seconds. `UPDATE api_keys SET last_used_at = now() WHERE id = :id AND (last_used_at IS NULL OR last_used_at < now() - interval '60 seconds')` — one statement, no read.
3. `require_auth_or_api_key` has the same double-query — fix both together.

---

### BE-17 · SSRF hardening for webhook delivery (P2)

**File:** `backend/app/tasks/webhook_tasks.py:97-102`, `backend/app/schemas/webhook.py:24-29`

The URL is user-supplied and the worker POSTs to it. HTTPS-only is already enforced at the schema level, which blocks the classic plaintext-metadata-endpoint vector — good. But HTTPS to an internal address is still possible.

**Fix**
1. Resolve the hostname before delivering; reject if **any** resolved IP is loopback / private / link-local / reserved (`ipaddress.ip_address(ip).is_private or .is_loopback or .is_link_local or .is_reserved`).
2. `httpx.Client(follow_redirects=False)` — currently the default is already `False`, but make it explicit; a redirect to `169.254.169.254` must not be followed.
3. Enforce a max URL length and reject URLs with credentials embedded.
4. Re-check the resolved IP at connect time if possible (pin the resolved IP in the `Host` header) to close the DNS-rebinding window.

---

### BE-18 · Actionable error messages (P3)

**Files:** `backend/app/utils/exceptions.py`, `backend/app/services/orchestrator_service.py:146-160`, `backend/app/middleware/rate_limit.py:43-50`, `backend/app/api/v1/endpoints/`

Every user-facing error must tell the user what to do next. Apply the §3.7 table. Specific edits:
- `orchestrator_service.py:148` → `"Service 'weather' is not configured. Add it under External Services."`
- `orchestrator_service.py:158` → `"Service 'weather' is inactive. Activate it under External Services."`
- `rate_limit.py:45` → include the tier, the limit, and minutes remaining.
- Upstream auth failures → name the provider and the status code.

---

### BE-19 · Test coverage gaps (P3)

**File:** `backend/tests/conftest.py:43-45`, `.github/workflows/ci.yml`

`task_always_eager = True` + `result_backend = "cache+memory://"` means **the distributed path is never exercised** — which is exactly why BE-1 is green in CI. Local runs also use SQLite (`:26`), so Postgres-specific behaviour (native enums, `SERIAL`, `TIMESTAMPTZ`, `ON DELETE SET NULL`) is only covered in the CI job.

**Fix**
1. Keep eager mode for unit tests, but add a **real** integration suite: `backend/tests/integration/` against a live Postgres + Redis + a real Celery worker.
2. Add a CI job to `.github/workflows/ci.yml` (this agent owns this file) that runs the integration suite with `services: postgres:15, redis:7-alpine` and a `celery -A app.tasks.celery_app worker -Q external --concurrency=4` process.
3. New tests to add:
   - `test_rate_limiter.py::test_concurrent_burst_respects_limit` (BE-3)
   - `test_external_services.py::test_create_with_backend_payload_shape` — posts `{service_name, api_key, max_calls_per_hour}` and asserts 201
   - `test_orchestrate.py::test_orchestrate_fans_out_in_parallel` — asserts `total_time_ms < sum(per-service response_time_ms)` (fails today with `solo`)
   - `test_auth.py::test_refresh_rotates_and_revokes_old_token` (BE-11)
   - `test_auth.py::test_login_rate_limited` (BE-4)
   - `test_webhooks.py::test_failed_delivery_does_not_disable_after_first_exhaustion` (BE-9)
   - `test_external_services.py::test_max_calls_per_hour_is_enforced` (BE-6)

---

## 5. Lane B — Frontend spec (other agent)

**Lane B does not touch `backend/`.** This section is the specification.

### FE-1 · External-service form (P0)

**Files:** `frontend/components/forms/CreateExternalServiceForm.tsx`, `frontend/lib/validators.ts:29-34`, `frontend/lib/constants.ts:36-42`

1. `frontend/lib/constants.ts` — **delete `SERVICE_TYPES`** (stripe/twilio/sendgrid/aws_s3/custom — none of which the backend accepts). Replace with a fetch of `GET /external-services/supported` (§3.1), cached in a module-level variable or React context. The dropdown must be populated from the server, never hardcoded.
2. `frontend/lib/validators.ts` — `externalServiceSchema` must mirror the backend body:
   ```ts
   export const externalServiceSchema = z.object({
     service_name: z.enum(["weather", "news", "stock"]),   // or z.string() validated against the fetched list
     api_key: z.string().min(1, "API key is required"),
     max_calls_per_hour: z.coerce.number().int().min(1).max(100000).optional(),
   });
   ```
   - **Fix the NaN bug:** `z.coerce.number()` on an empty string yields `0`; use `z.preprocess((v) => (v === "" || v == null ? undefined : v), z.number().int().min(1).optional())` so a blank optional field is `undefined`, not `NaN`/`0`. (`z.number()` rejects `NaN` outright, so today's blank field fails validation with "Expected number, received nan" on a field the user was told is optional.)
   - **Remove** the free-text "Service Name" input — the backend has no `name` field on `external_services`.
3. `CreateExternalServiceForm.tsx` — build the payload explicitly, the way `CreateAPIKeyForm.tsx:34-38` already does correctly:
   ```ts
   await api.post("/external-services", {
     service_name: data.service_name,
     api_key: data.api_key,
     max_calls_per_hour: data.max_calls_per_hour ?? 100,
   });
   ```
4. Error handling: surface the 422 field errors (see FE-12) and the §3.7 messages inline, not as a generic toast.
5. Fix the copy: "Stored securely using AES-256 encryption" → "Encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256)" (§3.3 note), or simply "Stored encrypted at rest."
6. Add a **"Test connection"** button that calls `POST /external-services/{id}/test` (§3.2) and shows the result inline. This is what tells the user their provider key actually works.

### FE-2 · `ExternalService` type (P0)

**File:** `frontend/types/api.ts:10-18`

Replace with the canonical shape (§3.3):
```ts
export interface ExternalService {
  service_id: number;
  service_name: "weather" | "news" | "stock";
  max_calls_per_hour: number;
  status: "active" | "inactive" | "error";
  error_message: string | null;
  last_tested_at: string | null;
  created_at: string;
}
```
**Delete** `id`, `name`, `serviceType`, `rateLimit`, `createdAt`, `lastSync`, and the `"connected" | "error" | "disconnected"` status union.

### FE-3 · External-services list + detail (P0)

**Files:** `frontend/components/tables/ExternalServicesTable.tsx`, `frontend/app/(dashboard)/external-services/[serviceId]/page.tsx`

| Old | New |
|---|---|
| `svc.id` | `svc.service_id` |
| `svc.name` | `svc.service_name` (display via the label from §3.1) |
| `svc.serviceType` | `svc.service_name` |
| `svc.status === "connected" ? "success" : "error"` | `svc.status === "active" ? "success" : svc.status === "error" ? "error" : "neutral"` |
| `svc.rateLimit ?? "Unlimited"` | `svc.max_calls_per_hour` |
| `svc.createdAt` | `svc.created_at` |
| `svc.lastSync` | `svc.last_tested_at` |
| `onDelete(svc.id)` | `onDelete(svc.service_id)` |
| `href={`/external-services/${svc.id}`}` | `href={`/external-services/${svc.service_id}`}` |

Also: `frontend/app/(dashboard)/external-services/[serviceId]/page.tsx:74` — "Reconfigure" links to `/external-services/create`, which would create a *second* service and hit the `(user_id, service_name)` unique constraint. Point it at an **edit** mode that `PATCH`es `/external-services/{id}`.

### FE-4 · Session lifecycle (P1)

**Files:** `frontend/context/AuthContext.tsx:86-95,147-165`, `frontend/lib/api.ts:20-70,55-56`

1. **`AuthContext.tsx:86-95`** — on mount, if the access token is expired but a refresh token exists, call `/auth/refresh` and restore the session. Only `clearAuth()` if the refresh fails. Today it clears unconditionally, so every user is bounced to `/login` after 30 minutes of inactivity.
2. **`AuthContext.tsx:149`** — `api.post("/auth/refresh", {})` → `api.post("/auth/refresh", { refresh_token: getStoredRefreshToken() })`. The backend requires the field; `{}` yields a 422 and the catch calls `clearAuth()`, i.e. the "refresh" path is currently a logout path.
3. **`api.ts:55-56`** — the refresh response's new `refresh_token` is **discarded**. Store it (BE-11 rotates tokens; not storing the new one means the next refresh presents a revoked token and gets logged out).
4. **`api.ts:98-108`** — the retry path stores only the access token too; use the same `storeAuth` logic.
5. **Storage keys** — `AuthContext.tsx:105,153` and `api.ts:56` hardcode the literal `"omniapi_access_token"` instead of using `TOKEN_STORAGE_KEY` (`frontend/lib/constants.ts:56`). Same value today, silent desync later.
6. **Logout** — call `POST /auth/logout` with the refresh token (BE-11) before clearing local state.

### FE-5 · A real orchestrate form (P0)

**Files:** `frontend/components/orchestrate/APIPlayground.tsx` (rewrite), `frontend/app/(dashboard)/orchestrate/page.tsx`

Today the playground is a generic method+URL+body box that:
- resolves relative URLs against `window.location.origin` (`:53`) — the **Next.js origin**, not the backend. The default `/api/analytics` (`:33`) doesn't exist (`frontend/app/api/` was deleted), so the default request 404s against Vercel.
- sends only the headers typed in the textarea (`:55`) — no `Authorization`/`X-API-Key`, so the backend returns 401.
- has no knowledge of `/orchestrate`; nothing in the frontend ever POSTs to it.
- reads `x-cache` (`:74`), which the backend never sets (BE-14c adds it).

**Replace with** a purpose-built form:
- **Service picker** — checkboxes populated from `GET /external-services` (only the user's configured services), showing `service_name` + `status`.
- **Params builder** — per selected service, a set of inputs driven by the `params` metadata from `GET /external-services/supported` (§3.1). Prefill with each service's `example`.
- **Request** — hardcoded `POST ${API_BASE}/orchestrate`, body `{ services, params }`, `Authorization: Bearer ${getStoredToken()}`.
- **Response** — render `results[]` per service: success/fail, `response_time_ms`, `cache_hit`, `data` or `error`. Show the `X-Cache`, `X-RateLimit-Remaining` headers.
- **Copy-as-curl** — a button that emits a ready-to-paste curl with `X-API-Key` so the user can move the request into their app (this also gives the generated OmniAPI key its first in-product use).
- If the user has **no** configured services, render an empty state: "Connect your first service →" linking to `/external-services/create`. Do not show a raw 404.
- Keep the template/quick-test feature, but templates must store `{services, params}` rather than a raw URL.
- Show the `X-RateLimit-Remaining` value so the user understands the free-tier ceiling before they hit 429.

### FE-6 · Onboarding (P1)

**Files:** `frontend/app/(dashboard)/dashboard/page.tsx`, new `frontend/components/dashboard/OnboardingChecklist.tsx`

The post-signup landing page currently shows three stat cards (all zero for a new account) and a `RecentActivity` feed that is **hardcoded empty** (`dashboard/page.tsx:36`, `setActivity([])` with the comment "not yet exposed by /analytics/usage"). There is no onboarding CTA anywhere in the app.

**Build** a 4-step checklist matching the docs' own steps (`frontend/app/(dashboard)/docs/page.tsx:106-110`), with each step's completion derived from real state:
| Step | Complete when | Link |
|---|---|---|
| 1. Create your account | `GET /auth/me` returns a user | — |
| 2. Connect a provider key | `GET /external-services` returns ≥ 1 | `/external-services/create` |
| 3. Generate an OmniAPI key | `GET /api-keys` returns ≥ 1 | `/api-keys/create` |
| 4. Make your first call | `GET /analytics/summary` shows `calls_today > 0` | `/orchestrate` |

Show the checklist **above** the stat cards when any step is incomplete; hide it (and show the stats) once all four are done. Every step links to the page that completes it.

### FE-7 · Mobile navigation (P1)

**File:** `frontend/lib/constants.ts:22-28`

`MOBILE_NAV_ITEMS` = Home, API, Flows, Docs. **No External Services** — and configuring a service is a prerequisite for any call, so mobile users are hard-blocked at step 2 of 4.

**Fix:** add `{ href: "/external-services", label: "Services", icon: "Plug" }`. `frontend/components/shared/MobileBottomNav.tsx:9-14` has an `iconMap` that must gain the `Plug` entry. Re-check the 4-item layout at 375px width; if it's cramped, use 5 items with smaller labels or move Docs into the Navbar.

### FE-8 · TypeScript build is broken (P1)

**Files:** `frontend/components/shared/Badge.tsx`, `frontend/components/shared/Button.tsx`, ~15 call sites

- `Badge` accepts **`tone`** (`"ok" | "warn" | "bad" | "accent" | "neutral"`), but **every** call site passes `variant` (`"success" | "error" | "info" | "neutral"`): `APIKeysTable.tsx:133,179`, `ExternalServicesTable.tsx:51,75`, `WebhooksTable.tsx:49,83`, `ActivityTable.tsx:33,53`, `APIPlayground.tsx:163,169`, `BillingInfo.tsx:7`, `webhooks/[webhookId]/page.tsx:47,50`, `docs/page.tsx:278,279,391,399`. `variant` is not in `BadgeProps` → TypeScript error TS2322 on every one.
- `Button` accepts `variant` ∈ `"primary" | "secondary" | "danger" | "ghost"`, but `ExportReport.tsx:28,32` and `APIPlayground.tsx:133` pass **`"outline"`** → TS error.

**Decide and apply one vocabulary.** Recommendation: extend `Badge` to accept `variant` with the values already in use (`success | error | info | neutral | warning`) and map them onto the existing tone classes — that touches one file instead of fifteen. Add `"outline"` to `Button`'s union, or change the three call sites to `"secondary"`.

**Verify:** `npm run build` currently fails on these. `PRODUCTION_READY.md:57` claims "TypeScript compiles with 0 errors" — that claim is false and there is no CI job that would catch it (see FE-9). **Add a `frontend-ci.yml` workflow that runs `npm ci && npm run build` and `npm run lint`.** Do not edit `.github/workflows/ci.yml` — the backend agent owns it.

### FE-9 · Settings page is fake (P1)

**Files:** `frontend/components/forms/ProfileForm.tsx:33-38`, `SecuritySettings.tsx:27-33`, `ForgotPasswordForm.tsx:26-32`, `BillingInfo.tsx:7-23`

All three forms **pretend to work**:
- `ProfileForm` waits 500ms and toasts "Profile updated". The change is discarded. → wire to `PATCH /auth/me` (§3.5), then update `AuthContext`'s user.
- `SecuritySettings` waits 500ms and toasts "Password updated successfully". **The password is not changed.** A user who believes they rotated a compromised password has not. → wire to `POST /auth/change-password`.
- `ForgotPasswordForm` waits 800ms and toasts "Password reset link sent to your email". **No email is sent and no endpoint exists** — the user is permanently locked out. → wire to `POST /auth/forgot-password` (BE-12f), and show the dev-mode token when the API returns one in non-production.
- `BillingInfo` hardcodes "Pro", "5M API calls per month", "$99 / month", "Jun 1, 2026". **Every free-tier user is told they have 5M calls** while their real limit is 100/hour (`backend/app/config.py:44`, `backend/app/middleware/rate_limit.py:14-19`). That actively misleads users into thinking they're not being throttled. → read the real `tier` from `GET /auth/me` and show the matching limit from the `X-RateLimit-Limit` header. Never hardcode a plan.

### FE-10 · Analytics and charts (P2)

**File:** `frontend/app/(dashboard)/analytics/page.tsx`, `frontend/app/(dashboard)/dashboard/page.tsx`

- `analytics/page.tsx:62-66` **fabricates** p50/p95 as `avg * 0.85` and `avg * 1.4`. The backend only provides `avg_response_time_ms`. Fabricated percentiles presented as measurements is a data-integrity problem. → either compute real percentiles in the backend (BE-14 note / a new aggregate) or relabel the chart "Average response time by service" and plot a single `avg` series.
- `analytics/page.tsx:45-48` and `dashboard/page.tsx:29-34` map `by_service` onto a `UsageDataPoint[]` whose x-axis is `time`, so service names are plotted on a time axis. → either add a real time-series aggregate to the backend (a `GROUP BY date_trunc('hour', created_at)` query) or rename the chart to "Calls by service" and use a bar chart.
- `dashboard/page.tsx:36` — `setActivity([])` is hardcoded. Either add an activity endpoint (the data exists in `usage_logs`) or remove the `RecentActivity` component from the dashboard until it exists. An empty "Recent Activity" panel reads as broken.

### FE-11 · Webhook signing secret is dropped (P2)

**File:** `frontend/components/forms/CreateWebhookForm.tsx:37`

`POST /webhooks` returns `WebhookCreatedResponse` — the base `WebhookResponse` **plus `secret`** (`backend/app/schemas/webhook.py:59-62`). The form types the response as `Webhook` (no `secret` field) and immediately navigates to `/webhooks`, so the **HMAC signing secret is shown exactly zero times and can never be recovered**.

**Fix:** capture `result.secret` and display it in a copy-once panel, exactly like `CreateAPIKeyForm.tsx:53-72` does for `raw_key`. Add `secret?: string` to the frontend `Webhook` type with a comment that it is only present in the create response.

### FE-12 · API client can't render validation errors (P2)

**File:** `frontend/lib/api.ts:110-128`

FastAPI 422 bodies are `{"detail": [ {loc, msg, type}, ... ]}` — an **array**. The client checks `typeof data.detail === "string"`, fails, and falls back to `response.statusText` ("Unprocessable Entity"). Every field-level validation message is thrown away.

**Fix:** handle the array form and expose it:
```ts
export class ApiError extends Error {
  constructor(message: string, public status: number, public data?: unknown,
              public fieldErrors?: Record<string, string>) { ... }
}
```
Map `detail[]` → `{ "service_name": "Field required", ... }` using the last element of `loc` as the key, and let the forms render them next to the inputs.

### FE-13 · Cleanup (P3)

- `frontend/lib/constants.ts:29-34` — `API_KEY_PERMISSIONS` (read/write/delete/admin) is **dead code** and advertises a permission model the backend does not implement (the `APIKey` model has no scopes column). **Delete it**, or implement scopes.
- `frontend/lib/constants.ts:36-42` — `SERVICE_TYPES` is **deleted** under FE-1.
- `frontend/lib/validators.ts` — Zod v4 (`package.json:25` pins `zod@^4.4.3`): `z.string().email()` is deprecated in favour of `z.email()`; `z.enum([...], { error })` is already v4-correct. Migrate the deprecated calls.
- `frontend/app/(dashboard)/docs/page.tsx:123,136,182,424` hardcodes `https://omniapi-api.onrender.com`. Source it from `API_BASE` / `NEXT_PUBLIC_API_URL` so the copy-pasteable curl commands work in any deployment.
- `frontend/components/shared/ConfirmDialog.tsx` and the inline `DeleteConfirmDialog` in `frontend/components/tables/APIKeysTable.tsx:21-73` are duplicates — pick one.
- `frontend/components/forms/CreateExternalServiceForm.tsx:44-49` — the "Service Name" free-text input is removed under FE-1.
- `frontend/app/(dashboard)/external-services/[serviceId]/page.tsx` — "Reconfigure" → edit mode (FE-3).

---

## 6. Sequencing

```
Wave 0 (no dependencies — start immediately)
  Lane A: BE-1, BE-3, BE-4, BE-7, BE-18
  Lane B: FE-1 (payload shape), FE-2 (type), FE-3 (table+detail),
          FE-8 (build fix), FE-12 (api client), FE-11 (webhook secret)
  → Note: FE-1/FE-2/FE-3 need only the EXISTING backend contract (§3.2/§3.3).
    They do not wait for any new endpoint.

Wave 1 (needs BE-12a: the /supported endpoint)
  Lane A: BE-12a, BE-12b, BE-12c
  Lane B: swap the hardcoded provider list for the fetched one

Wave 2 (needs BE-11 + BE-12d-h: auth endpoints)
  Lane A: BE-11, BE-12d, BE-12e, BE-12f, BE-12g, BE-12h
  Lane B: FE-4 (session lifecycle), FE-9 (settings page), FE-6 (onboarding)

Wave 3 (needs BE-2, BE-6, BE-14c: orchestrate behaviour + headers)
  Lane A: BE-2, BE-6, BE-8, BE-9, BE-10, BE-13, BE-14, BE-15, BE-16, BE-17
  Lane B: FE-5 (real orchestrate form), FE-7 (mobile nav), FE-10 (analytics)

Wave 4 (hardening + verification)
  Lane A: BE-19 (integration suite + CI job)
  Lane B: FE-13 (cleanup)
```

**Cross-lane coordination points**
- §3.1 `/external-services/supported` must land before Lane B can remove the hardcoded list. Lane B can start everything else in Wave 0 in parallel.
- §3.5 refresh-token rotation is a **breaking change**: the frontend must send `refresh_token` in the body. Ship BE-11 and FE-4 together or BE-11 will 401 every existing session.
- `X-Cache` (BE-14c) is additive — the frontend can read it before it exists; it just shows nothing.

---

## 7. Verification

### 7.1 Manual end-to-end script (the flow that currently fails)

Run against a local stack (`docker compose up -d redis celery_worker celery_beat` + uvicorn + `npm run dev`).

```bash
# 0. Health
curl -s localhost:8000/api/v1/health | jq

# 1. Register
curl -s -X POST localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"full_name":"Test User","email":"t@example.com","password":"password123"}' | jq

# 2. Login
TOK=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"t@example.com","password":"password123"}' | jq -r .access_token)
REFRESH=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"t@example.com","password":"password123"}' | jq -r .refresh_token)

# 3. Supported services (NEW — §3.1)
curl -s localhost:8000/api/v1/external-services/supported \
  -H "Authorization: Bearer $TOK" | jq '.services[].service_name'
# EXPECT: ["weather","news","stock"]

# 4. Create an external service (the call that 422s today)
curl -s -X POST localhost:8000/api/v1/external-services \
  -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
  -d '{"service_name":"weather","api_key":"'"$OPENWEATHER_KEY"'","max_calls_per_hour":100}' | jq
# EXPECT: 201, service_name "weather", status "active"

# 5. Test the credential (NEW — §3.2)
SID=$(curl -s localhost:8000/api/v1/external-services \
  -H "Authorization: Bearer $TOK" | jq -r '.[0].service_id')
curl -s -X POST "localhost:8000/api/v1/external-services/$SID/test" \
  -H "Authorization: Bearer $TOK" | jq
# EXPECT: {"success":true,...} on a valid key; success:false + a message otherwise

# 6. Create an OmniAPI key
RAW=$(curl -s -X POST localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
  -d '{"name":"prod"}' | jq -r .raw_key)

# 7. Orchestrate
curl -s -X POST localhost:8000/api/v1/orchestrate \
  -H "X-API-Key: $RAW" -H 'Content-Type: application/json' \
  -d '{"services":["weather"],"params":{"weather":{"city":"London"}}}' \
  -D /tmp/h | jq
grep -iE 'x-cache|x-ratelimit' /tmp/h
# EXPECT: X-Cache, X-RateLimit-Limit, X-RateLimit-Remaining headers

# 8. Parallel fan-out (NEW — BE-2)
# 3 services: total_time_ms MUST be < the sum of the per-service response_time_ms

# 9. Per-service quota (NEW — BE-6)
# Set max_calls_per_hour=1, call twice → 2nd is 429 with the §3.7 message

# 10. Refresh rotation (NEW — BE-11)
NEW=$(curl -s -X POST localhost:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$REFRESH\"}" | jq -r .refresh_token)
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$REFRESH\"}"
# EXPECT: 401 — the old token is revoked

# 11. Rate limiter atomicity (NEW — BE-3)
# 20 concurrent calls at a limit of 10 → exactly 10 succeed
```

### 7.2 UI checklist (Lane B)

- [ ] Register → land on the dashboard → the checklist shows step 1 done, steps 2–4 pending
- [ ] "Add Service" → the provider dropdown is populated from the server → submit → **201**, and the row shows the provider label, `active` (green), the rate limit, and a working delete/link
- [ ] "Test connection" → shows the provider's actual verdict inline
- [ ] "Create Key" → the raw key is shown once and copyable
- [ ] "Orchestrate" → service checkboxes from the configured services → params fields match the provider → Send → results render per service with timings, cache hit, and errors
- [ ] "Copy as curl" emits a request with `X-API-Key`
- [ ] Delete the session, wait 31 minutes, reload → **still signed in** (FE-4)
- [ ] Settings → change the password → it actually changes (sign out, sign in with the new one)
- [ ] Settings → the plan shown matches `GET /auth/me`'s `tier` and the real rate limit
- [ ] Mobile viewport (375px) → External Services is reachable in the bottom nav
- [ ] `npm run build` → 0 errors; `npm run lint` → 0 errors
- [ ] Every 422 shows the offending field name and message next to the input

### 7.3 Automated

- Backend: `pytest` (unit) + the new integration job (Postgres + Redis + a real worker) — BE-19
- Frontend: `npm run build` + `npm run lint` in CI — FE-8
- Coverage gate stays at 80% (`ci.yml:65`)

---

## 8. Risks & rollback

| Risk | Mitigation |
|---|---|
| Refresh-token rotation logs out every existing session on deploy | Ship BE-11 + FE-4 in the same release; announce it. Access tokens keep working for up to 30 min, so the blast radius is one session cycle. |
| `/external-services/supported` collides with `/{service_id}` | Register the static route **first**; assert it in a test |
| Switching to `prefork` on a constrained host (Render free, 512MB) | Prefork forks the parent; if memory is tight use `--pool=threads` instead (Celery's `threads` pool needs no fork). Render's free plan is the constraint — measure before switching the plan. |
| Removing Celery from the request path changes retry semantics | In-process retry (3 attempts, 1/2/4s backoff) covers the common transient case; the old Celery path retried 3× with a 5s delay |
| Direct `httpx` calls bypass the broker's rate limiting | The per-service and per-tenant limiters still run before dispatch — no change |
| New migration `008` (refresh_tokens, password_reset_tokens, `usage_logs.api_key_id`, `webhooks.consecutive_failures`, nullable `webhook_events.payload`) | Additive only — no column drops or renames. `downgrade()` provided |
| Redis `maxmemory-policy allkeys-lru` evicts the rate-limit counters | Rate-limit keys are TTL'd 1h and evicted only under pressure; if the counter is evicted the user gets a fresh window (fail-open). Move rate-limit keys to a separate Redis DB or instance if strictness matters |

---

## 9. Open decisions (need an owner)

1. **Email provider** — `forgot-password` needs one. Options: (a) ship the endpoint with dev-mode token logging and defer the mail integration, (b) integrate a provider now (Resend/Postmark/SES), (c) remove the forgot-password UI until (b). *Recommendation: (a) now, (b) next.*
2. **Billing** — there is no billing system, but the UI shows a plan and a price. Either (a) drop the plan/price UI and show only the real tier + rate limit, or (b) integrate Stripe for the `pro`/`enterprise` tiers. *Recommendation: (a) now — the lie is actively hurting.*
3. **Provider list growth** — `stripe`/`twilio`/`sendgrid`/`aws_s3` were in the UI but are not implemented. Are they planned? If yes, §3.1 is the registry they plug into. If no, they should be deleted everywhere, including `readme.md`.
4. **Webhook auto-disable threshold** — 20 consecutive failures proposed. Tune after real data.
5. **Cache TTLs** — `SERVICE_TTL` is 3600/1800/300s. If the upstream is a free tier, the TTL may exceed the provider's quota. Tie TTL to the user's `max_calls_per_hour`?
6. **Async DB migration (BE-5 phase 2)** — do it, or accept the threadpool?

---

## 10. Definition of done

- [ ] A new user can go signup → connect a provider → generate a key → make a successful orchestrate call **entirely through the UI**, with no docs and no curl.
- [ ] Every 4xx error in the flow names the field or the next action.
- [ ] `npm run build` and `npm run lint` pass; both run in CI.
- [ ] `pytest` passes, including a real-Postgres/Redis/worker integration job.
- [ ] `POST /external-services` returns 201 from the UI form, and the row renders the real provider, status, and limit.
- [ ] A 3-service orchestrate takes ≈ the slowest single upstream call.
- [ ] No request exceeds the tenant rate limit under concurrency.
- [ ] The Celery banner reports `prefork` with the configured concurrency.
- [ ] A session survives 31+ minutes of inactivity.
- [ ] Nothing in the UI claims a plan, a limit, a price, or a permission scope that the backend does not enforce.
