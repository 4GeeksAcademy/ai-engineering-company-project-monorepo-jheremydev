# Telemetry storage - Phase 1

Run `migrations/20261026180000_create_telemetry_events.sql` once in the target
Supabase project's SQL Editor as the database owner. It runs in a transaction
and fails on existing objects instead of silently accepting an incompatible
schema. Do not rerun it after successful application.

No connection credentials belong in this repository or in chat. This migration
does not change the API or frontend. The operator confirmed successful remote
application and all Phase 1 verification results on 2026-10-26.
The [Phase 2 API collector](../../services/api/README.md) now performs per-item
validation and bulk insertion. In Phase 3 the operator confirmed seven real
events in Supabase, including two movement creation events from UI entry/exit
and two UI operation failures from forced network failures on actual requests.
The real mixed batch returned received=13, stored=10, rejected=3; queried invalid
IDs were absent. The operator authorized tabular evidence instead of a screenshot.

## Envelope mapping

| Envelope | Column | PostgreSQL type |
| --- | --- | --- |
| eventId | eventId (primary key) | uuid |
| timestamp | timestamp | timestamptz |
| sessionId | sessionId | uuid, nullable |
| userId | userId | uuid, always null in 1.0.0 |
| event_type | event_type | text |
| schemaVersion | schemaVersion | text, fixed to 1.0.0 |
| requestId | requestId | uuid, nullable |
| properties | tags | jsonb object |
| source | source | text: browser/api/probe |
| environment | environment | text: production/development/test |

Camel-case SQL identifiers are quoted to preserve the existing contract.
`timestamp` stores the observation instant, not insertion time or movement date;
PostgreSQL preserves the instant, not the original timestamp string's formatting.
JSONB preserves decimal strings without converting inventory quantities to floats.
Duplicate event IDs raise a primary-key violation; this migration implements no
upsert or mutation path.

The allowlist constraint mirrors all 47 top-level payload key sets in
[event-schemas.json](../../docs/telemetry/event-schemas.json). Unknown event types,
non-object tags and extra top-level keys are rejected, not silently discarded.
This is not a complete JSON Schema validator: required payload keys, value types,
nested allowlists (`issues`, `filters`) and cross-field rules must be validated
before bulk insertion by the Phase 2 collector without changing `TelemetryEvent`.
Future schema changes must update the SQL allowlists deliberately.

Brasaland's operational dimension is `localId`, not a warehouse or office.
Mapping `properties` to `tags` retains `localId`, `articleId`, `movementId`,
`movementType`, `unit`, quantities, stock and reorder thresholds wherever the
event-specific allowlist permits them. Incident dimensions such as `area`,
`oldArea` and `newArea` are retained in their respective variants.
No location names, country inferred from a local, author names or invented
warehouse/office fields are added. The existing
[telemetry plan](../../docs/telemetry/telemetry-plan.md) cites
[CONTEXT.md](../../CONTEXT.md); there is no `empresa-BRIEFING.md` in this workspace.

## Access and immutability

RLS is enabled without client policies: `anon` and `authenticated` cannot read
or write events. The backend's `service_role` bypasses RLS and receives only
`INSERT` and `SELECT`. Never expose its credentials in the frontend.
A statement trigger rejects `UPDATE`, `DELETE` and `TRUNCATE`, including for
`service_role`. The database owner can still change or disable database objects;
this is application-level append-only storage, not tamper-proof archival storage.

There are three explicit indexes: timestamp B-tree, event_type B-tree and tags
GIN (default JSONB operator class, supporting containment and key existence).
The primary key additionally creates its own uniqueness index.

## Verify after application

Run these read-only queries in the SQL Editor and share their results:

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'telemetry_events'
ORDER BY ordinal_position;

SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public' AND tablename = 'telemetry_events'
ORDER BY indexname;

SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.telemetry_events'::regclass;

SELECT tgname, pg_get_triggerdef(oid)
FROM pg_trigger
WHERE tgrelid = 'public.telemetry_events'::regclass AND NOT tgisinternal;

SELECT relrowsecurity
FROM pg_class
WHERE oid = 'public.telemetry_events'::regclass;

SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public' AND table_name = 'telemetry_events'
ORDER BY grantee, privilege_type;

SELECT
    public.telemetry_tags_allowed(
        'inventory.movement_created',
        '{"localId":"00000000-0000-4000-8000-000000000001","movementType":"entrada"}'
    ) AS business_dimensions_allowed,
    NOT public.telemetry_tags_allowed(
        'inventory.movement_created', '{"autor":"must not be stored"}'
    ) AS extra_key_rejected,
    (public.telemetry_tags_allowed('unknown.event', '{}') IS NOT TRUE)
        AS unknown_event_rejected;
```

Expected: 10 columns; 4 indexes including the primary key; append-only trigger;
RLS true; no client grants; service_role SELECT/INSERT only; three final booleans
true. No synthetic events are inserted by these checks. Actual persisted events
and mixed-batch acceptance belong to later phases, after explicit confirmation.
