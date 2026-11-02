"""Read/reporting PostgREST access; source telemetry remains read-only."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ReportingStorageError(RuntimeError):
    """Safe upstream/configuration error without credential or payload details."""


def _read(table: str, filters: list[tuple[str, str]]) -> list[dict[str, Any]]:
    base_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not base_url or not key:
        raise ReportingStorageError("invalid_configuration")
    url = f"{base_url}/rest/v1/{table}?{urlencode(filters)}"
    request = Request(url, headers={
        "apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json",
        "Accept-Profile": "reporting",
    }, method="GET")
    try:
        with urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result if isinstance(result, list) else []
    except HTTPError as exc:
        status = exc.code
        exc.close()
        raise ReportingStorageError(f"upstream_http_{status}") from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise ReportingStorageError("upstream_query_failed") from exc


def latest_run() -> dict[str, Any] | None:
    rows = _read("pipeline_run_log", [
        ("select", "run_id,flow_name,trigger_type,started_at,finished_at,status,period_start,period_end,source_watermark,source_records_read,unique_records_processed,duplicate_records_skipped,destination_rows_upserted,error_code,error_summary,initiated_by,request_id"),
        ("order", "started_at.desc"), ("limit", "1"),
    ])
    return rows[0] if rows else None


def weekly_summaries(filters: list[tuple[str, str]]) -> list[dict[str, Any]]:
    select = ("select", "week_start,week_end,market,local_id,currency,sales_total_amount,ticket_count,average_ticket_amount,source_watermark,source_record_count,duplicate_record_count,last_refreshed_at,run_id,data_quality_status")
    return _read("weekly_sales_summary", [select, ("order", "week_start.desc,market.asc,local_id.asc"), *filters])
