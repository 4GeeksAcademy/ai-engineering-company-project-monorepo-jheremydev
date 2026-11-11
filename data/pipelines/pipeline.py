"""Resilient weekly operational activity pipeline (not a financial sales KPI).

Run manually with ``python data/pipelines/pipeline.py``. The approved business
cadence is every Monday at 07:00 (timezone confirmation remains operationally pending).

Structure (Part 3): the main flow ``weekly_sales_summary_flow`` only records the run
and calls three subflows in sequence, each with explicit inputs/outputs:

    extract_inventory_movement_activity_flow  -> validated telemetry events
    transform_weekly_inventory_activity_flow  -> weekly summary rows
    load_weekly_sales_summary_flow            -> rows upserted

``export_eval_snapshot_flow`` is optional and runs with ``return_state=True`` so its
failure never stops the load. Pure KPI logic lives in ``data/process/weekly_activity.py``.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

# Allow ``python data/pipelines/pipeline.py`` to import the ``data`` package from the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from prefect import flow, get_run_logger, task  # noqa: E402
from prefect.tasks import task_input_hash  # noqa: E402

from data.process import weekly_activity  # noqa: E402

logger = logging.getLogger("prefect.pipeline")
FLOW_NAME = "weekly_sales_summary_flow"
EVENT_TYPE = "inventory.movement_created"


def _load_env_file() -> None:
    """Load repo-root .env into os.environ for local CLI runs (Docker gets this via env_file)."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file()


def _request(method: str, table: str, *, query: str = "", payload: Any = None,
             reporting: bool = False, prefer: str | None = None) -> tuple[int, Any]:
    base_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not base_url or not service_key:
        raise RuntimeError("invalid_configuration")
    schema = "reporting" if reporting else "public"
    url = f"{base_url}/rest/v1/{table}{'?' + query if query else ''}"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Accept": "application/json",
        "Content-Profile": schema,
        "Accept-Profile": schema,
    }
    data = None
    if payload is not None:
        data = json.dumps(payload, allow_nan=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except HTTPError as exc:
        status = exc.code
        exc.close()
        raise RuntimeError(f"upstream_http_{status}") from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise RuntimeError("upstream_request_failed") from exc


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


@task(retries=3, retry_delay_seconds=5)
def extract_telemetry_control_task(period_start: datetime, period_end: datetime) -> dict[str, Any]:
    """Read telemetry only; retries tolerate transient network/Supabase faults without manual intervention."""
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        filters = [
            ("select", '"eventId",timestamp,event_type,tags'),
            ("event_type", f"eq.{EVENT_TYPE}"),
            ("timestamp", f"gte.{_iso(period_start)}"),
            ("timestamp", f"lt.{_iso(period_end)}"),
            ("order", 'timestamp.asc,"eventId".asc'),
            ("limit", "1000"),
            ("offset", str(offset)),
        ]
        _, payload = _request("GET", "telemetry_events", query=urlencode(filters))
        page = payload if isinstance(payload, list) else []
        rows.extend(page)
        if len(page) < 1000:
            break
        offset += len(page)
    return {"rows": rows, "source_records_read": len(rows)}


@task
def validate_and_deduplicate_task(extracted: dict[str, Any]) -> dict[str, Any]:
    """Reject malformed events (never raises) and keep one event per eventId."""
    return weekly_activity.validate_and_deduplicate_events(extracted.get("rows"))


@task
def assign_iso_week_task(validated: dict[str, Any]) -> list[dict[str, Any]]:
    """Assign each unique movement to its ISO week (Monday), market and local."""
    return weekly_activity.assign_iso_week(validated["rows"])


@task
def count_weekly_movements_task(assigned: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """KPI: unique inventory movements per ISO week, market and local."""
    return weekly_activity.count_weekly_movements(assigned)


@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(minutes=15))
def build_weekly_summary_rows_task(counts: list[dict[str, Any]], run_id: str,
                                   duplicate_records_skipped: int,
                                   source_watermark: str | None) -> list[dict[str, Any]]:
    """Shape KPI counts as destination rows. Cache key hashes the parameters; lasts 15 minutes."""
    return weekly_activity.build_weekly_summary_rows(
        counts, run_id=run_id, now=datetime.now(timezone.utc),
        duplicate_records_skipped=duplicate_records_skipped, source_watermark=source_watermark)


@task(retries=3, retry_delay_seconds=5)
def load_reporting_summary_task(rows: list[dict[str, Any]]) -> int:
    """Upsert by the destination natural key, replacing values rather than accumulating deltas.

    The on_conflict query param is required: the table has no primary key, only the
    named UNIQUE constraint on (week_start, market, local_id, currency), and PostgREST
    only knows which constraint to resolve against when it is told explicitly —
    otherwise "Prefer: resolution=merge-duplicates" falls back to a plain INSERT and a
    repeat run fails with 409 instead of upserting.
    """
    if not rows:
        return 0
    _, response = _request(
        "POST", "weekly_sales_summary",
        query=urlencode([("on_conflict", "week_start,market,local_id,currency")]),
        payload=rows,
        reporting=True,
        prefer="resolution=merge-duplicates,return=representation",
    )
    return len(response) if isinstance(response, list) else len(rows)


@task(retries=2, retry_delay_seconds=3)
def finalize_run_log_task(run_record: dict[str, Any]) -> None:
    _request(
        "PATCH", "pipeline_run_log",
        query=urlencode([("run_id", f"eq.{run_record['run_id']}")]),
        payload={key: value for key, value in run_record.items() if key != "run_id"},
        reporting=True,
        prefer="return=minimal",
    )


@task
def export_eval_snapshot_task(rows: list[dict[str, Any]], run_id: str) -> str:
    output_dir = Path(__file__).resolve().parents[1] / "eval"
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"weekly-activity-{run_id}.json"
    target.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(target)


@flow(name="extract_inventory_movement_activity_flow")
def extract_inventory_movement_activity_flow(period_start: datetime, period_end: datetime) -> dict[str, Any]:
    """Read telemetry_events (read-only) and return validated, deduplicated events + counters."""
    extracted = extract_telemetry_control_task(period_start, period_end)
    return validate_and_deduplicate_task(extracted)


@flow(name="transform_weekly_inventory_activity_flow")
def transform_weekly_inventory_activity_flow(validated: dict[str, Any], run_id: str) -> list[dict[str, Any]]:
    """Validated events -> weekly summary rows (ISO week, market, local)."""
    assigned = assign_iso_week_task(validated)
    counts = count_weekly_movements_task(assigned)
    watermark = max((row["timestamp"] for row in validated["rows"]), default=None)
    return build_weekly_summary_rows_task(
        counts, run_id, validated["duplicate_records_skipped"], watermark)


@flow(name="load_weekly_sales_summary_flow")
def load_weekly_sales_summary_flow(rows: list[dict[str, Any]]) -> int:
    """Idempotent upsert into reporting.weekly_sales_summary; returns rows written."""
    return load_reporting_summary_task(rows)


@flow(name="export_eval_snapshot_flow")
def export_eval_snapshot_flow(rows: list[dict[str, Any]], run_id: str) -> str:
    """Optional: JSON snapshot under data/eval/. Invoked with return_state=True."""
    return export_eval_snapshot_task(rows, run_id)


def _default_period() -> tuple[datetime, datetime]:
    today = datetime.now(timezone.utc).date()
    this_monday = today - timedelta(days=today.weekday())
    start = this_monday - timedelta(days=7)
    return datetime.combine(start, time.min, timezone.utc), datetime.combine(this_monday, time.min, timezone.utc)


@flow(name=FLOW_NAME)
def weekly_sales_summary_flow(period_start: datetime | None = None,
                             period_end: datetime | None = None,
                             trigger_type: str = "manual",
                             requested_run_id: str | None = None,
                             initiated_by: str | None = None,
                             request_id: str | None = None) -> dict[str, Any]:
    run_logger = get_run_logger()
    if period_start is None or period_end is None:
        default_start, default_end = _default_period()
        period_start = period_start or default_start
        period_end = period_end or default_end
    period_start = period_start.astimezone(timezone.utc) if period_start.tzinfo else period_start.replace(tzinfo=timezone.utc)
    period_end = period_end.astimezone(timezone.utc) if period_end.tzinfo else period_end.replace(tzinfo=timezone.utc)
    if period_start >= period_end:
        raise ValueError("period_start must be earlier than period_end")

    run_id = requested_run_id or str(uuid4())
    started = datetime.now(timezone.utc)
    counters = {"source_records_read": 0, "unique_records_processed": 0,
                "duplicate_records_skipped": 0, "destination_rows_upserted": 0}
    status, error_code, error_summary, watermark = "Running", None, None, None
    # An active-run partial unique index in the migration provides a DB-level window lock.
    _request("POST", "pipeline_run_log", payload={
        "run_id": run_id, "flow_name": FLOW_NAME, "trigger_type": trigger_type,
        "started_at": started.isoformat(), "finished_at": None, "status": "Running",
        "period_start": period_start.isoformat(), "period_end": period_end.isoformat(),
        "source_records_read": 0, "unique_records_processed": 0,
        "duplicate_records_skipped": 0, "destination_rows_upserted": 0,
        "initiated_by": initiated_by, "request_id": request_id,
    }, reporting=True, prefer="return=minimal")

    try:
        validated = extract_inventory_movement_activity_flow(period_start, period_end)
        counters.update({key: validated[key] for key in (
            "source_records_read", "unique_records_processed", "duplicate_records_skipped")})
        watermark = max((row["timestamp"] for row in validated["rows"]), default=None)
        aggregates = transform_weekly_inventory_activity_flow(validated, run_id)
        try:
            snapshot_state = export_eval_snapshot_flow(aggregates, run_id, return_state=True)
            if snapshot_state.is_failed():
                run_logger.warning("Optional eval snapshot failed; loading report continues")
            else:
                run_logger.info("Optional snapshot saved: %s", snapshot_state.result())
        except Exception:
            run_logger.exception("Optional eval snapshot raised; loading report continues")
        counters["destination_rows_upserted"] = load_weekly_sales_summary_flow(aggregates)
        status = "Completed"
        return {"run_id": run_id, "status": status, **counters, "aggregates": aggregates}
    except Exception as exc:
        status = "Failed"
        error_code = str(exc).split(":", 1)[0][:100]
        error_summary = "Pipeline task failed; see sanitized service logs."
        run_logger.exception("Weekly operational activity pipeline failed run_id=%s", run_id)
        raise
    finally:
        try:
            finalize_run_log_task({
                "run_id": run_id, "finished_at": datetime.now(timezone.utc).isoformat(),
                "status": status, "source_watermark": watermark,
                **counters, "error_code": error_code, "error_summary": error_summary,
            })
        except Exception:
            run_logger.exception("Could not finalize reporting run log run_id=%s", run_id)


if __name__ == "__main__":
    weekly_sales_summary_flow(trigger_type="manual")
