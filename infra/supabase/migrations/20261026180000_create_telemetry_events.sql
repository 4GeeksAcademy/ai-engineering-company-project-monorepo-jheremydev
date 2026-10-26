BEGIN;

-- Snapshot of the top-level properties allowlists in event-schemas.json 1.0.0.
CREATE FUNCTION public.telemetry_tags_allowed(event_type text, tags jsonb)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $$
    SELECT COALESCE(jsonb_typeof(tags) = 'object'
        AND tags - CASE event_type
        WHEN 'inventory.movement_received' THEN ARRAY['route', 'method', 'movementType', 'formAttemptId']::text[]
        WHEN 'inventory.movement_validation_failed' THEN ARRAY['httpStatus', 'issues', 'movementType', 'formAttemptId']::text[]
        WHEN 'inventory.movement_reference_rejected' THEN ARRAY['httpStatus', 'missingEntity', 'movementType', 'formAttemptId']::text[]
        WHEN 'inventory.movement_negative_stock_rejected' THEN ARRAY['httpStatus', 'articleId', 'localId', 'movementType', 'quantity', 'stockBefore', 'unit', 'formAttemptId']::text[]
        WHEN 'inventory.movement_created' THEN ARRAY['httpStatus', 'movementId', 'articleId', 'localId', 'movementType', 'quantity', 'stockAfter', 'unit', 'formAttemptId']::text[]
        WHEN 'inventory.reorder_signal_active' THEN ARRAY['articleId', 'localId', 'stock', 'reorderPoint', 'unit', 'belowReorderPoint']::text[]
        WHEN 'inventory.direct_stock_write_rejected' THEN ARRAY['route', 'method', 'httpStatus']::text[]
        WHEN 'inventory.article_created' THEN ARRAY['articleId', 'category', 'unit', 'reorderPoint', 'formAttemptId']::text[]
        WHEN 'inventory.local_created' THEN ARRAY['localId', 'formAttemptId']::text[]
        WHEN 'inventory.catalog_validation_failed' THEN ARRAY['entity', 'httpStatus', 'issues', 'formAttemptId']::text[]
        WHEN 'inventory.stock_lookup_completed' THEN ARRAY['articleId', 'localId', 'stock', 'unit', 'belowReorderPoint', 'querySource', 'observationCount', 'windowMs']::text[]
        WHEN 'inventory.movement_history_loaded' THEN ARRAY['rowCount', 'articleFilter', 'localFilter']::text[]
        WHEN 'inventory.reorder_indicator_displayed' THEN ARRAY['articleId', 'localId', 'surface']::text[]
        WHEN 'incident.created' THEN ARRAY['incidentId', 'channel', 'incidentType', 'severity', 'area', 'status', 'formAttemptId']::text[]
        WHEN 'incident.validation_failed' THEN ARRAY['method', 'route', 'httpStatus', 'issues', 'formAttemptId']::text[]
        WHEN 'incident.status_changed' THEN ARRAY['incidentId', 'oldStatus', 'newStatus', 'area', 'severity', 'formAttemptId']::text[]
        WHEN 'incident.area_changed' THEN ARRAY['incidentId', 'oldArea', 'newArea', 'incidentType', 'formAttemptId']::text[]
        WHEN 'incident.update_noop' THEN ARRAY['incidentId', 'status', 'area', 'formAttemptId']::text[]
        WHEN 'incident.history_loaded' THEN ARRAY['incidentId', 'changeCount']::text[]
        WHEN 'incident.not_found' THEN ARRAY['method', 'httpStatus', 'formAttemptId']::text[]
        WHEN 'navigation.section_viewed' THEN ARRAY['view', 'trigger']::text[]
        WHEN 'inventory.article_selected' THEN ARRAY['articleId', 'surface', 'formAttemptId']::text[]
        WHEN 'incident.detail_opened' THEN ARRAY['incidentId', 'trigger']::text[]
        WHEN 'incident.filters_applied' THEN ARRAY['filters', 'changedFilter']::text[]
        WHEN 'incident.filter_empty_result' THEN ARRAY['filters', 'rowCount']::text[]
        WHEN 'form.started' THEN ARRAY['formType', 'formAttemptId']::text[]
        WHEN 'form.abandoned' THEN ARRAY['formType', 'formAttemptId', 'reason', 'elapsedMs', 'inferred']::text[]
        WHEN 'inventory.prerequisite_blocked' THEN ARRAY['missing']::text[]
        WHEN 'incident.edit_discarded' THEN ARRAY['incidentId', 'formAttemptId', 'changedFields', 'reason']::text[]
        WHEN 'form.validation_blocked' THEN ARRAY['formType', 'formAttemptId', 'field', 'rule']::text[]
        WHEN 'performance.api_response_timed' THEN ARRAY['method', 'route', 'httpStatus', 'durationMs']::text[]
        WHEN 'performance.client_request_completed' THEN ARRAY['method', 'route', 'durationMs', 'outcome', 'httpStatus']::text[]
        WHEN 'performance.backoffice_initial_load_completed' THEN ARRAY['durationMs', 'outcome', 'requestCount', 'duplicateRequestCount', 'loadKind', 'documentLoadMs']::text[]
        WHEN 'performance.inventory_view_load_completed' THEN ARRAY['durationMs', 'moduleLoadMs', 'dataLoadMs', 'outcome', 'loadKind']::text[]
        WHEN 'performance.incident_detail_load_completed' THEN ARRAY['durationMs', 'moduleLoadMs', 'dataLoadMs', 'outcome', 'loadKind']::text[]
        WHEN 'performance.reorder_batch_completed' THEN ARRAY['localId', 'articleCount', 'successfulCount', 'failedCount', 'durationMs', 'outcome']::text[]
        WHEN 'performance.inventory_cache_lookup' THEN ARRAY['cache', 'result', 'durationMs', 'ttlSeconds']::text[]
        WHEN 'performance.inventory_cache_invalidated' THEN ARRAY['cache', 'reason']::text[]
        WHEN 'frontend.uncaught_exception' THEN ARRAY['module', 'errorFamily', 'releaseVersion', 'errorFingerprint']::text[]
        WHEN 'frontend.unhandled_rejection' THEN ARRAY['module', 'errorFamily', 'releaseVersion', 'errorFingerprint']::text[]
        WHEN 'frontend.lazy_module_failed' THEN ARRAY['module', 'releaseVersion', 'errorFingerprint']::text[]
        WHEN 'api.network_failed' THEN ARRAY['method', 'route', 'operation', 'failureKind', 'formAttemptId']::text[]
        WHEN 'api.response_decode_failed' THEN ARRAY['method', 'route', 'httpStatus', 'operation', 'formAttemptId']::text[]
        WHEN 'ui.operation_failed' THEN ARRAY['operation', 'errorKind', 'httpStatus', 'formAttemptId']::text[]
        WHEN 'ui.post_write_refresh_failed' THEN ARRAY['operation', 'formAttemptId', 'writeConfirmed', 'refreshStage', 'httpStatus']::text[]
        WHEN 'api.unhandled_exception' THEN ARRAY['method', 'route', 'httpStatus', 'errorFamily', 'releaseVersion', 'errorFingerprint']::text[]
        WHEN 'operations.health_check_completed' THEN ARRAY['route', 'durationMs', 'outcome', 'httpStatus']::text[]
        ELSE NULL::text[]
        END = '{}'::jsonb, false);
$$;

CREATE TABLE public.telemetry_events (
    "eventId" uuid PRIMARY KEY,
    "timestamp" timestamptz NOT NULL,
    "sessionId" uuid,
    "userId" uuid CHECK ("userId" IS NULL),
    event_type text NOT NULL,
    "schemaVersion" text NOT NULL CHECK ("schemaVersion" = '1.0.0'),
    "requestId" uuid,
    tags jsonb NOT NULL,
    source text NOT NULL CHECK (source IN ('browser', 'api', 'probe')),
    environment text NOT NULL CHECK (environment IN ('production', 'development', 'test')),
    CONSTRAINT telemetry_events_tags_allowlist CHECK (
        public.telemetry_tags_allowed(event_type, tags) IS TRUE
    )
);

CREATE INDEX telemetry_events_timestamp_idx ON public.telemetry_events ("timestamp");
CREATE INDEX telemetry_events_event_type_idx ON public.telemetry_events (event_type);
CREATE INDEX telemetry_events_tags_gin_idx ON public.telemetry_events USING gin (tags);

CREATE FUNCTION public.telemetry_events_reject_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
    RAISE EXCEPTION 'telemetry_events is append-only: % is forbidden', TG_OP
        USING ERRCODE = '42501';
END;
$$;

CREATE TRIGGER telemetry_events_append_only
BEFORE UPDATE OR DELETE OR TRUNCATE ON public.telemetry_events
FOR EACH STATEMENT EXECUTE FUNCTION public.telemetry_events_reject_mutation();

ALTER TABLE public.telemetry_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.telemetry_events FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, INSERT ON TABLE public.telemetry_events TO service_role;

COMMENT ON TABLE public.telemetry_events IS
    'Immutable telemetry envelope 1.0.0. Backend-only access; properties maps to tags.';
COMMENT ON COLUMN public.telemetry_events.tags IS
    'Event-specific allowlisted properties; preserves localId, articleId and exact decimal strings.';

COMMIT;
