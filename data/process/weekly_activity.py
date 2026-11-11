"""Pure transformation logic for the weekly inventory-activity report.

No I/O, no Prefect, no globals: every function receives its input explicitly and
returns a new value, so it can be unit tested with in-memory telemetry events.

KPI "Actividad semanal de movimientos de inventario" (PIPELINE_DESIGN.md):
number of UNIQUE ``inventory.movement_created`` events (unique by ``eventId``)
per ISO week, local and market.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

UNKNOWN = "unknown"


def parse_event_timestamp(value: Any) -> datetime | None:
    """Return an aware UTC datetime, or None when the value is not a valid ISO timestamp."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def validate_and_deduplicate_events(rows: Any) -> dict[str, Any]:
    """Drop malformed events and keep one event per ``eventId``.

    Never raises on bad input: malformed records are counted in
    ``invalid_records_rejected`` so the pipeline keeps running.
    """
    unique: dict[str, dict[str, Any]] = {}
    invalid = 0
    valid_seen = 0
    source_records_read = 0
    for row in rows if isinstance(rows, list) else []:
        source_records_read += 1
        if not isinstance(row, dict):
            invalid += 1
            continue
        event_id = row.get("eventId")
        if not isinstance(event_id, str) or not event_id.strip():
            invalid += 1
            continue
        if parse_event_timestamp(row.get("timestamp")) is None:
            invalid += 1
            continue
        valid_seen += 1
        unique.setdefault(event_id, row)
    return {
        "rows": list(unique.values()),
        "source_records_read": source_records_read,
        "unique_records_processed": len(unique),
        "duplicate_records_skipped": valid_seen - len(unique),
        "invalid_records_rejected": invalid,
    }


def iso_week_start(moment: datetime) -> date:
    """Monday (UTC) of the ISO week that contains ``moment``."""
    iso_year, iso_week, _ = moment.astimezone(timezone.utc).isocalendar()
    return date.fromisocalendar(iso_year, iso_week, 1)


def assign_iso_week(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach week_start (ISO Monday), market and local_id to each valid event."""
    assigned: list[dict[str, Any]] = []
    for event in events:
        stamp = parse_event_timestamp(event.get("timestamp"))
        if stamp is None:
            continue
        tags = event.get("tags") if isinstance(event.get("tags"), dict) else {}
        market = tags.get("market") if isinstance(tags.get("market"), str) and tags.get("market") else UNKNOWN
        local_id = tags.get("localId") if isinstance(tags.get("localId"), str) and tags.get("localId") else UNKNOWN
        assigned.append({
            "eventId": event.get("eventId"),
            "timestamp": stamp.isoformat(),
            "week_start": iso_week_start(stamp),
            "market": market,
            "local_id": local_id,
        })
    return assigned


def count_weekly_movements(assigned: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """KPI: unique inventory movements per (ISO week, market, local)."""
    groups: dict[tuple[date, str, str], int] = {}
    for item in assigned:
        key = (item["week_start"], item["market"], item["local_id"])
        groups[key] = groups.get(key, 0) + 1
    return [
        {"week_start": week, "market": market, "local_id": local_id, "movement_count": count}
        for (week, market, local_id), count in sorted(groups.items())
    ]


def build_weekly_summary_rows(counts: list[dict[str, Any]], *, run_id: str, now: datetime,
                              duplicate_records_skipped: int = 0,
                              source_watermark: str | None = None) -> list[dict[str, Any]]:
    """Shape KPI counts as rows of reporting.weekly_sales_summary.

    There is no POS data yet: sales amounts stay NULL and the row is flagged
    ``pending_pos_integration`` so it is never read as money.
    """
    return [{
        "week_start": item["week_start"].isoformat(),
        "week_end": (item["week_start"] + timedelta(days=6)).isoformat(),
        "market": item["market"],
        "local_id": item["local_id"],
        "currency": "N/A",
        "sales_total_amount": None,
        "ticket_count": item["movement_count"],
        "average_ticket_amount": None,
        "source_watermark": source_watermark,
        "source_record_count": item["movement_count"],
        "duplicate_record_count": duplicate_records_skipped,
        "last_refreshed_at": now.isoformat(),
        "run_id": run_id,
        "data_quality_status": "pending_pos_integration",
    } for item in counts]
