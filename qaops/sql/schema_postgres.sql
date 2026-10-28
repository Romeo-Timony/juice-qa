-- PostgreSQL 16 Schema for Enterprise QAOps Event Store & Orchestration
-- Database: qaops_db

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Append-Only Event Stream (Event Sourcing)
CREATE TABLE IF NOT EXISTS qa_pipeline_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    correlation_id VARCHAR(64) NOT NULL,
    issue_key VARCHAR(32) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    producer VARCHAR(32) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS ix_events_issue_created ON qa_pipeline_events(issue_key, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_events_correlation ON qa_pipeline_events(correlation_id);
CREATE INDEX IF NOT EXISTS ix_events_type ON qa_pipeline_events(event_type);

-- 2. Materialized Pipeline State Projection (Current Task State)
CREATE TABLE IF NOT EXISTS qa_pipeline_state (
    issue_key VARCHAR(32) PRIMARY KEY,
    current_stage INT NOT NULL DEFAULT 1,
    stage_name VARCHAR(64) NOT NULL DEFAULT 'DoR Gate',
    hitl_gate1_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    hitl_gate2_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    rqi_score NUMERIC(5, 2) DEFAULT 0.00,
    last_execution_id VARCHAR(64),
    metadata JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

-- 3. Scheduled & Queued Events (Outbox, Retries, Scheduled Nightly Regressions)
CREATE TABLE IF NOT EXISTS qa_scheduled_events (
    schedule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_key VARCHAR(32),
    action VARCHAR(64) NOT NULL,
    target_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
    retry_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 3,
    payload JSONB DEFAULT '{}'::jsonb,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS ix_scheduled_pending 
ON qa_scheduled_events(status, target_time) 
WHERE status = 'SCHEDULED';

-- 4. Idempotency Keys (Distributed Lock & Deduplication)
CREATE TABLE IF NOT EXISTS qaops_idempotency (
    idem_key VARCHAR(128) PRIMARY KEY,
    scope VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL,
    result_json JSONB DEFAULT '{}'::jsonb,
    attempts INT DEFAULT 1,
    completions INT DEFAULT 0,
    blocked_duplicates INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

-- 5. Outbox Mutations for External APIs (Guaranteed Delivery)
CREATE TABLE IF NOT EXISTS qaops_outbox (
    id BIGSERIAL PRIMARY KEY,
    idem_key VARCHAR(128),
    service VARCHAR(32) NOT NULL DEFAULT 'generic',
    method VARCHAR(10) NOT NULL,
    url TEXT NOT NULL,
    payload_json JSONB DEFAULT 'null'::jsonb,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    last_error TEXT,
    attempts INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

-- 6. Circuit Breaker Persistent States
CREATE TABLE IF NOT EXISTS qaops_breaker (
    service VARCHAR(32) PRIMARY KEY,
    failures INT DEFAULT 0,
    opened_at DOUBLE PRECISION DEFAULT 0
);

-- 7. Distributed Telemetry Spans
CREATE TABLE IF NOT EXISTS qaops_spans (
    id VARCHAR(64) PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    parent_id VARCHAR(64),
    issue_key VARCHAR(32),
    name VARCHAR(128) NOT NULL,
    kind VARCHAR(32) NOT NULL,
    level VARCHAR(16) DEFAULT 'DEFAULT',
    latency_ms DOUBLE PRECISION,
    iterations INT DEFAULT 1,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    model VARCHAR(64),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

-- 8. Release Quality Index Metrics Log
CREATE TABLE IF NOT EXISTS qaops_metrics (
    id BIGSERIAL PRIMARY KEY,
    issue_key VARCHAR(32) NOT NULL,
    metric VARCHAR(64) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    passed SMALLINT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

-- 9. Global Error Audit Table
CREATE TABLE IF NOT EXISTS qa_pipeline_errors (
    error_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_key VARCHAR(32),
    workflow_name VARCHAR(128) NOT NULL,
    execution_id VARCHAR(64),
    failed_node VARCHAR(128),
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

CREATE INDEX IF NOT EXISTS ix_errors_issue_created ON qa_pipeline_errors(issue_key, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_errors_workflow ON qa_pipeline_errors(workflow_name);

