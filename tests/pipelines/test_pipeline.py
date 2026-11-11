"""Unit tests for the transformation tasks of the weekly inventory-activity pipeline.

Isolated: in-memory telemetry-shaped events, no database, no network, no Prefect server
(tasks are called through ``.fn``). Run: ``python -m pytest tests/pipelines/test_pipeline.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.pipelines.pipeline import (  # noqa: E402
    assign_iso_week_task,
    build_weekly_summary_rows_task,
    count_weekly_movements_task,
    validate_and_deduplicate_task,
)

EVENT_TYPE = "inventory.movement_created"
LOCAL_A = "11111111-1111-4111-8111-111111111111"
LOCAL_B = "22222222-2222-4222-8222-222222222222"


def make_event(event_id, timestamp, local_id=LOCAL_A, market="unknown"):
    """Shape of a row read from telemetry_events (eventId, timestamp, event_type, tags)."""
    return {"eventId": event_id, "timestamp": timestamp, "event_type": EVENT_TYPE,
            "tags": {"localId": local_id, "market": market}}


def known_events():
    """Known input. ISO weeks: Mon 2026-10-26 .. Sun 2026-11-01, and Mon 2026-11-02 ..

    e1 Mon 26-Oct local A | e2 Wed 28-Oct local A | e2 again (duplicate eventId)
    e3 Fri 30-Oct local B | e5 Sun 01-Nov 23:30Z local A | e4 Mon 02-Nov 00:00Z local A
    """
    return [
        make_event("e1", "2026-10-26T08:00:00+00:00"),
        make_event("e2", "2026-10-28T10:00:00Z"),
        make_event("e2", "2026-10-28T10:00:00Z"),
        make_event("e3", "2026-10-30T23:59:59+00:00", LOCAL_B),
        make_event("e5", "2026-11-01T23:30:00+00:00"),
        make_event("e4", "2026-11-02T00:00:00+00:00"),
    ]


def test_validate_and_deduplicate_keeps_one_event_per_event_id():
    result = validate_and_deduplicate_task.fn({"rows": known_events(), "source_records_read": 6})
    assert result["unique_records_processed"] == 5
    assert result["duplicate_records_skipped"] == 1
    assert result["invalid_records_rejected"] == 0


def test_assign_iso_week_puts_sunday_night_in_the_closing_week():
    validated = validate_and_deduplicate_task.fn({"rows": known_events()})
    assigned = {item["eventId"]: item for item in assign_iso_week_task.fn(validated)}
    assert str(assigned["e5"]["week_start"]) == "2026-10-26"  # Sunday 01-Nov 23:30Z
    assert str(assigned["e4"]["week_start"]) == "2026-11-02"  # Monday 02-Nov 00:00Z
    assert assigned["e3"]["local_id"] == LOCAL_B


def test_weekly_movement_kpi_matches_pipeline_design_definition():
    """KPI 'Actividad semanal de movimientos de inventario' (PIPELINE_DESIGN.md):
    unique inventory.movement_created events by eventId per ISO week and local.

    Hand count: week 2026-10-26 -> local A: e1, e2 (e2 duplicate ignored), e5 = 3;
    local B: e3 = 1. Week 2026-11-02 -> local A: e4 = 1. Total unique = 5.
    """
    validated = validate_and_deduplicate_task.fn({"rows": known_events()})
    counts = count_weekly_movements_task.fn(assign_iso_week_task.fn(validated))
    by_key = {(str(c["week_start"]), c["local_id"]): c["movement_count"] for c in counts}
    assert by_key == {("2026-10-26", LOCAL_A): 3, ("2026-10-26", LOCAL_B): 1, ("2026-11-02", LOCAL_A): 1}
    assert sum(by_key.values()) == validated["unique_records_processed"] == 5


def test_summary_rows_never_present_activity_as_sales_money():
    validated = validate_and_deduplicate_task.fn({"rows": known_events()})
    counts = count_weekly_movements_task.fn(assign_iso_week_task.fn(validated))
    rows = build_weekly_summary_rows_task.fn(counts, "run-1", 1, "2026-11-02T00:00:00+00:00")
    assert len(rows) == 3
    for row in rows:
        assert row["sales_total_amount"] is None
        assert row["data_quality_status"] == "pending_pos_integration"
        assert row["run_id"] == "run-1"
    first = rows[0]
    assert (first["week_start"], first["week_end"]) == ("2026-10-26", "2026-11-01")


def test_malformed_events_are_rejected_without_raising():
    """Defensive: null id, wrong types, invalid timestamp and bad tags must never break the run."""
    malformed = [
        {"eventId": None, "timestamp": "2026-10-26T08:00:00Z", "tags": {}},        # null eventId
        {"eventId": 123, "timestamp": "2026-10-26T08:00:00Z", "tags": {}},         # wrong type id
        {"eventId": "bad-ts", "timestamp": "not-a-date", "tags": {}},              # invalid timestamp
        {"eventId": "no-ts", "timestamp": None, "tags": {}},                       # null timestamp
        "not-a-dict",                                                              # wrong row type
        {"eventId": "ok", "timestamp": "2026-10-27T09:00:00Z", "tags": "oops"},    # tags not a dict
    ]
    validated = validate_and_deduplicate_task.fn({"rows": malformed})
    assert validated["invalid_records_rejected"] == 5
    assert validated["unique_records_processed"] == 1
    assigned = assign_iso_week_task.fn(validated)
    assert assigned[0]["local_id"] == "unknown" and assigned[0]["market"] == "unknown"
    assert validate_and_deduplicate_task.fn({"rows": None})["unique_records_processed"] == 0
