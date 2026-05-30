-- OmniAPI PostgreSQL schema for Supabase
-- Apply via Supabase SQL Editor, or: psql $DATABASE_URL -f supabase/schema.sql
-- Prefer Alembic in app deployments: alembic -c backend/app/db/alembic.ini upgrade head

-- Extensions (Supabase enables these by default)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enums
DO $$ BEGIN
    CREATE TYPE user_tier AS ENUM ('free', 'pro', 'enterprise');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE external_service_status AS ENUM ('active', 'inactive', 'error');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE webhook_event_status AS ENUM ('pending', 'delivered', 'failed');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Users (tenant root)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    tier user_tier NOT NULL DEFAULT 'free',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_login TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_created_at ON users (created_at);

-- API keys (hashed; per-tenant)
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_api_keys_user_id ON api_keys (user_id);
CREATE INDEX IF NOT EXISTS ix_api_keys_key_hash ON api_keys (key_hash);

-- External service credentials (encrypted at rest)
CREATE TABLE IF NOT EXISTS external_services (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,
    api_key_encrypted VARCHAR(500) NOT NULL,
    max_calls_per_hour INTEGER NOT NULL DEFAULT 100,
    status external_service_status NOT NULL DEFAULT 'active',
    error_message VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_tested_at TIMESTAMPTZ,
    CONSTRAINT uq_external_services_user_id_service_name UNIQUE (user_id, service_name)
);

CREATE INDEX IF NOT EXISTS ix_external_services_user_id ON external_services (user_id);
CREATE INDEX IF NOT EXISTS ix_external_services_created_at ON external_services (created_at);
CREATE INDEX IF NOT EXISTS ix_external_services_user_id_created_at ON external_services (user_id, created_at);

-- Usage logs (service_id SET NULL when external service is deleted)
CREATE TABLE IF NOT EXISTS usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES external_services (id) ON DELETE SET NULL,
    endpoint VARCHAR(255) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    status_code INTEGER NOT NULL DEFAULT 200,
    cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    error_message VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS ix_usage_logs_user_id ON usage_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_usage_logs_service_id ON usage_logs (service_id);
CREATE INDEX IF NOT EXISTS ix_usage_logs_created_at ON usage_logs (created_at);
CREATE INDEX IF NOT EXISTS ix_usage_logs_user_id_created_at ON usage_logs (user_id, created_at);

-- Webhooks
CREATE TABLE IF NOT EXISTS webhooks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_encrypted VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 5,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    last_triggered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_webhooks_user_id ON webhooks (user_id);

-- Webhook delivery events
-- Columns map to audit spec: http_status_code = response_status, attempt_count = attempt_number,
-- status enum (delivered/failed) = success indicator
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    webhook_id INTEGER NOT NULL REFERENCES webhooks (id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload TEXT NOT NULL,
    status webhook_event_status NOT NULL DEFAULT 'pending',
    http_status_code INTEGER,
    error_message VARCHAR(500),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_webhook_events_webhook_id ON webhook_events (webhook_id);
CREATE INDEX IF NOT EXISTS ix_webhook_events_user_id ON webhook_events (user_id);
CREATE INDEX IF NOT EXISTS ix_webhook_events_created_at ON webhook_events (created_at);

-- Alembic version tracking (optional if using Alembic against Supabase)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
