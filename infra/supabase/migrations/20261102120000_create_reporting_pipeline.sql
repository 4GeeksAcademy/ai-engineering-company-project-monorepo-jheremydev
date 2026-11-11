BEGIN;

CREATE SCHEMA IF NOT EXISTS reporting;

CREATE TABLE reporting.pipeline_run_log (
    run_id uuid PRIMARY KEY,
    flow_name text NOT NULL,
    trigger_type text NOT NULL,
    started_at timestamptz NOT NULL,
    finished_at timestamptz NULL,
    status text NOT NULL CHECK (status IN ('Running', 'Completed', 'Failed')),
    period_start timestamptz NOT NULL,
    period_end timestamptz NOT NULL,
    source_watermark timestamptz NULL,
    source_records_read integer NOT NULL DEFAULT 0,
    unique_records_processed integer NOT NULL DEFAULT 0,
    duplicate_records_skipped integer NOT NULL DEFAULT 0,
    destination_rows_upserted integer NOT NULL DEFAULT 0,
    error_code text NULL,
    error_summary text NULL,
    initiated_by text NULL,
    request_id text NULL
);

CREATE TABLE reporting.weekly_sales_summary (
    week_start date NOT NULL,
    week_end date NOT NULL,
    market text NOT NULL,
    local_id text NOT NULL,
    currency text NOT NULL,
    sales_total_amount numeric NULL,
    ticket_count integer NOT NULL DEFAULT 0,
    average_ticket_amount numeric NULL,
    source_watermark timestamptz NULL,
    source_record_count integer NOT NULL DEFAULT 0,
    duplicate_record_count integer NOT NULL DEFAULT 0,
    last_refreshed_at timestamptz NOT NULL,
    run_id uuid NOT NULL,
    data_quality_status text NOT NULL,
    CONSTRAINT weekly_sales_summary_natural_key UNIQUE (week_start, market, local_id, currency)
);

CREATE INDEX pipeline_run_log_started_at_idx
    ON reporting.pipeline_run_log (started_at DESC);
-- Database-enforced per-window lock; finished runs release the key.
CREATE UNIQUE INDEX pipeline_run_log_active_window_unique
    ON reporting.pipeline_run_log (period_start, period_end)
    WHERE finished_at IS NULL;
CREATE INDEX weekly_sales_summary_week_idx
    ON reporting.weekly_sales_summary (week_start DESC);

GRANT USAGE ON SCHEMA reporting TO service_role;

ALTER TABLE reporting.pipeline_run_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE reporting.weekly_sales_summary ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE reporting.pipeline_run_log FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON TABLE reporting.weekly_sales_summary FROM PUBLIC, anon, authenticated, service_role;

GRANT SELECT, INSERT, UPDATE ON reporting.pipeline_run_log TO service_role;
GRANT SELECT, INSERT, UPDATE ON reporting.weekly_sales_summary TO service_role;

COMMIT;
