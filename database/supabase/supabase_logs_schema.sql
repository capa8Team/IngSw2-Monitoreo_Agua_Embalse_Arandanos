-- Tablas de logging por subsistema (Monitoreo Embalse Arándanos)
-- Ejecutar en Supabase SQL Editor

BEGIN;

CREATE TABLE IF NOT EXISTS dashboard_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    level VARCHAR(10) NOT NULL CHECK (level IN ('INFO', 'WARN', 'FATAL')),
    message TEXT NOT NULL,
    component VARCHAR(80) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    correlation_id UUID,
    service_name VARCHAR(80),
    environment VARCHAR(40),
    host VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS registro_historico_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    level VARCHAR(10) NOT NULL CHECK (level IN ('INFO', 'WARN', 'FATAL')),
    message TEXT NOT NULL,
    component VARCHAR(80) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    correlation_id UUID
);

CREATE TABLE IF NOT EXISTS exportar_pdf_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    level VARCHAR(10) NOT NULL CHECK (level IN ('INFO', 'WARN', 'FATAL')),
    message TEXT NOT NULL,
    component VARCHAR(80) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    correlation_id UUID
);

CREATE TABLE IF NOT EXISTS login_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    level VARCHAR(10) NOT NULL CHECK (level IN ('INFO', 'WARN', 'FATAL')),
    message TEXT NOT NULL,
    component VARCHAR(80) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    correlation_id UUID
);

CREATE TABLE IF NOT EXISTS supabase_db_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    level VARCHAR(10) NOT NULL CHECK (level IN ('INFO', 'WARN', 'FATAL')),
    message TEXT NOT NULL,
    component VARCHAR(80) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    correlation_id UUID,
    operation VARCHAR(50),
    table_name VARCHAR(100),
    query_type VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS telegram_bot_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    level VARCHAR(10) NOT NULL CHECK (level IN ('INFO', 'WARN', 'FATAL')),
    message TEXT NOT NULL,
    component VARCHAR(80) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    correlation_id UUID,
    chat_id_hash VARCHAR(64),
    command VARCHAR(100),
    sent_count INTEGER,
    failed_count INTEGER
);

CREATE TABLE IF NOT EXISTS mailersend_api_logs (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    level VARCHAR(10) NOT NULL CHECK (level IN ('INFO', 'WARN', 'FATAL')),
    message TEXT NOT NULL,
    component VARCHAR(80) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    correlation_id UUID,
    http_status INTEGER,
    recipient_count INTEGER,
    provider_message_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS ix_dashboard_logs_created_at ON dashboard_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_registro_historico_logs_created_at ON registro_historico_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_supabase_db_logs_created_at ON supabase_db_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_login_logs_created_at ON login_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_telegram_bot_logs_created_at ON telegram_bot_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_mailersend_api_logs_created_at ON mailersend_api_logs (created_at DESC);

ALTER TABLE dashboard_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE registro_historico_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE exportar_pdf_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE supabase_db_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_bot_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE mailersend_api_logs ENABLE ROW LEVEL SECURITY;

COMMIT;
