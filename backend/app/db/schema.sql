-- OmniAPI schema (SQLite dialect, applied to the Pyronites project DB).
--
-- This file is the single source of truth for the schema. It replaces the
-- Alembic migration tree: Pyronites exposes raw SQL execution, so the schema
-- is applied idempotently with `python -m app.db.bootstrap`.
--
-- Conventions
--   * Primary keys are INTEGER PRIMARY KEY AUTOINCREMENT, so the public API
--     keeps the integer identifiers it has always exposed.
--   * Booleans are INTEGER 0/1 with a CHECK constraint.
--   * Enumerations are TEXT with a CHECK constraint listing the allowed
--     values (SQLite has no native enum type).
--   * Timestamps are ISO-8601 UTC strings ("2026-10-22T05:42:29.493527+00:00").
--     Every timestamp is written in that exact format, so lexicographic
--     comparison in SQL is chronological comparison.
--   * `updated_at` is maintained by the application. The Pyronites SQL
--     executor splits statements on ";", which makes SQLite triggers
--     impossible to install, so there is no database-side default for it.

-- ---------------------------------------------------------------------------
-- Users
-- ---------------------------------------------------------------------------
-- `omniapi_` prefix: Pyronites owns a global `users` table, and the bare name
-- is reserved by its table API.
CREATE TABLE IF NOT EXISTS omniapi_users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT    NOT NULL UNIQUE,
    first_name  TEXT,
    last_name   TEXT,
    tier        TEXT    NOT NULL DEFAULT 'free'
                CHECK (tier IN ('free', 'pro', 'enterprise')),
    is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at  TEXT    NOT NULL,
    updated_at  TEXT,
    last_login  TEXT
);

-- ---------------------------------------------------------------------------
-- API keys
-- ---------------------------------------------------------------------------
-- `omniapi_` prefix: Pyronites keeps its own `api_keys` table for the keys
-- that authenticate against the Pyronites API itself.
CREATE TABLE IF NOT EXISTS omniapi_api_keys (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES omniapi_users(id) ON DELETE CASCADE,
    key_hash      TEXT    NOT NULL UNIQUE,
    name          TEXT    NOT NULL,
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    last_used_at  TEXT,
    expires_at    TEXT,
    created_at    TEXT    NOT NULL,
    updated_at    TEXT
);

CREATE INDEX IF NOT EXISTS ix_omniapi_api_keys_user_id
    ON omniapi_api_keys(user_id);

-- ---------------------------------------------------------------------------
-- External services
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS external_services (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL REFERENCES omniapi_users(id) ON DELETE CASCADE,
    service_name       TEXT    NOT NULL,
    api_key_encrypted  TEXT    NOT NULL,
    max_calls_per_hour INTEGER NOT NULL DEFAULT 100,
    status             TEXT    NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active', 'inactive', 'error')),
    error_message      TEXT,
    created_at         TEXT    NOT NULL,
    updated_at         TEXT,
    last_tested_at     TEXT,
    UNIQUE (user_id, service_name)
);

CREATE INDEX IF NOT EXISTS ix_external_services_user_id
    ON external_services(user_id);

-- ---------------------------------------------------------------------------
-- Usage logs
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usage_logs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES omniapi_users(id) ON DELETE CASCADE,
    service_id          INTEGER REFERENCES external_services(id) ON DELETE SET NULL,
    api_key_id          INTEGER REFERENCES omniapi_api_keys(id) ON DELETE SET NULL,
    endpoint            TEXT    NOT NULL,
    response_time_ms    INTEGER NOT NULL,
    status_code         INTEGER NOT NULL DEFAULT 200,
    cache_hit           INTEGER NOT NULL DEFAULT 0 CHECK (cache_hit IN (0, 1)),
    request_size_bytes  INTEGER,
    response_size_bytes INTEGER,
    created_at          TEXT    NOT NULL,
    error_message       TEXT
);

CREATE INDEX IF NOT EXISTS ix_usage_logs_user_id_created_at
    ON usage_logs(user_id, created_at);

-- ---------------------------------------------------------------------------
-- Webhooks
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS webhooks (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id              INTEGER NOT NULL REFERENCES omniapi_users(id) ON DELETE CASCADE,
    event_type           TEXT    NOT NULL,
    url                  TEXT    NOT NULL,
    secret_encrypted     TEXT,
    is_active            INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    retry_count          INTEGER NOT NULL DEFAULT 0,
    max_retries          INTEGER NOT NULL DEFAULT 5,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    created_at           TEXT    NOT NULL,
    updated_at           TEXT,
    last_triggered_at    TEXT
);

CREATE INDEX IF NOT EXISTS ix_webhooks_user_id_event_type
    ON webhooks(user_id, event_type);

-- ---------------------------------------------------------------------------
-- Webhook delivery events
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS webhook_events (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    webhook_id       INTEGER NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
    user_id          INTEGER NOT NULL REFERENCES omniapi_users(id) ON DELETE CASCADE,
    event_type       TEXT    NOT NULL,
    payload          TEXT,
    status           TEXT    NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'delivered', 'failed')),
    http_status_code INTEGER,
    error_message    TEXT,
    attempt_count    INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT    NOT NULL,
    delivered_at     TEXT,
    next_retry_at    TEXT
);

CREATE INDEX IF NOT EXISTS ix_webhook_events_webhook_id_created_at
    ON webhook_events(webhook_id, created_at);

-- ---------------------------------------------------------------------------
-- Refresh tokens
-- ---------------------------------------------------------------------------
-- Only the SHA-256 hash of a token is stored. Rotation replaces the hash and
-- marks the old row revoked; presenting a revoked token means it leaked, so
-- the whole family is revoked.
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES omniapi_users(id) ON DELETE CASCADE,
    token_hash     TEXT    NOT NULL UNIQUE,
    family_id      TEXT    NOT NULL,
    expires_at     TEXT    NOT NULL,
    revoked_at     TEXT,
    replaced_by_id INTEGER REFERENCES refresh_tokens(id) ON DELETE SET NULL,
    created_at     TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id
    ON refresh_tokens(user_id);

CREATE INDEX IF NOT EXISTS ix_refresh_tokens_family_id
    ON refresh_tokens(family_id);

-- ---------------------------------------------------------------------------
-- OAuth identities
-- ---------------------------------------------------------------------------
-- `omniapi_` prefix: Pyronites owns an `oauth_identities` table for the
-- identities its own OAuth flow creates. Ours is keyed on the OmniAPI user.
CREATE TABLE IF NOT EXISTS omniapi_oauth_identities (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL REFERENCES omniapi_users(id) ON DELETE CASCADE,
    provider         TEXT    NOT NULL,
    provider_user_id TEXT    NOT NULL,
    email            TEXT,
    email_verified   INTEGER NOT NULL DEFAULT 0 CHECK (email_verified IN (0, 1)),
    display_name     TEXT,
    avatar_url       TEXT,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT,
    UNIQUE (provider, provider_user_id)
);

CREATE INDEX IF NOT EXISTS ix_omniapi_oauth_identities_user_id
    ON omniapi_oauth_identities(user_id);
