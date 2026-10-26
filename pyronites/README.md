# Pyronites setup for OmniAPI

OmniAPI stores all relational data in **Pyronites** — an HTTP data store backed
by SQLite. Redis stays separate: locally via Docker Compose, or
[Upstash](https://upstash.com) in production.

There is no ORM and no migration runner. The schema is plain DDL in
[`backend/app/db/schema.sql`](../backend/app/db/schema.sql), applied with
`python -m app.db.bootstrap`. Every statement is `IF NOT EXISTS`, so applying
it is idempotent and safe to run on every deploy (that is what the Render
start command does).

## 1. Create a Pyronites project

1. Sign in to your Pyronites deployment.
2. Create a project, e.g. `omniapi-db`.
3. Create an API key with **read/write** (or **admin**) scope for that project.

You need three values:

| Setting | Where it comes from | Example |
|---|---|---|
| `PYRONITES_URL` | The deployment's base URL | `https://pyrocore-backend.onrender.com` |
| `PYRONITES_KEY` | The API key you created | `pyro_live_...` |
| `PYRONITES_PROJECT_ID` | The project's id (or name, if the deployment allows it) | `omniapi-db` |

Set them in `backend/.env.local` (see `backend/.env.example`).

## 2. Apply the schema

From `backend/`:

```bash
python -m app.db.bootstrap          # apply the schema
python -m app.db.bootstrap --check  # report what exists; changes nothing
```

A successful apply reports the number of statements run and ends with
`Schema is up to date (8 tables)`.

The eight tables:

| Table | Notes |
|---|---|
| `omniapi_users` | Prefixed — the bare name `users` is reserved by the store |
| `omniapi_api_keys` | Prefixed — same reason |
| `omniapi_oauth_identities` | Prefixed — the store owns an `oauth_identities` table |
| `external_services` | |
| `usage_logs` | |
| `webhooks` | |
| `webhook_events` | |
| `refresh_tokens` | |

## 3. Constraints baked into the schema

The schema is written for this store, not for Postgres. Keep these in mind
before editing it:

- **No triggers.** `updated_at` is maintained by the application layer, not
  by a trigger.
- **No parameter binding.** The SQL execution endpoint takes a raw string.
  Every literal in `schema.sql` and in the repositories is therefore
  hex-encoded (`CAST(x'…' AS TEXT)`) via `app/db/sql.py`. Do not interpolate
  user input into SQL strings.
- **The edge filters request bodies.** A backtick in a request body trips a
  Cloudflare rule and returns 403 before the request reaches the store. The
  client retries such a block once (`app/db/client.py`), and comments are
  stripped from the schema before it is sent.
- **Every statement is a network round trip.** Roughly 450 ms against the
  hosted deployment. The client uses a keep-alive connection (a fresh
  connection per query costs about five times as much), and the repositories
  batch multi-statement reads into a single request. Batching does **not**
  reduce per-statement cost — it only saves the connection setup.
- **Foreign keys and CHECK constraints are enforced**, so the test suite
  exercises the real constraint behaviour.

## 4. Local development without the hosted store

Tests and local development use an in-process SQLite client that speaks the
same contract (`backend/app/db/sqlite_client.py`). `backend/tests/conftest.py`
points the app at it, so the suite never touches the hosted project. To use
it explicitly, point `PYRONITES_URL` at a local Pyronites instance, or let
the test fixtures configure it.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `403` from the store, intermittently | Cloudflare blocked the body (a backtick in a string literal) | Hex-encode the literal with `sql_literal()` from `app/db/sql.py`. The client retries one block per request. |
| `401 unauthorized` | The key is missing, wrong, or scoped to another project | Check `PYRONITES_KEY` and that its scope includes this project |
| Requests take ~450 ms each | Expected: every statement is a network round trip | Rely on the keep-alive client and statement batching; cache hot reads (e.g. the 30 s user cache in `app/services/user_cache.py`) |
| `Missing tables: ...` from `--check` | Schema not applied yet | `python -m app.db.bootstrap` |
| `Failed to apply statement: ...` | A statement in `schema.sql` is invalid for SQLite | Fix the statement; bootstrap replays the batch one statement at a time and names the offender |
| Local tests fail on a live-looking call | A test forgot the SQLite fixture | Tests get the in-process client from `conftest.py`; do not point them at the hosted project |
