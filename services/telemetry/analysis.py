"""Pure report metrics backed by server-filtered Supabase reads."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd


EVENT_TYPES = (
    "api.unhandled_exception",
    "api.network_failed",
    "api.response_decode_failed",
    "frontend.uncaught_exception",
    "frontend.unhandled_rejection",
    "frontend.lazy_module_failed",
    "ui.operation_failed",
    "ui.post_write_refresh_failed",
)

ERROR_EVENT_TYPES = (
    "api.unhandled_exception",
    "api.network_failed",
    "api.response_decode_failed",
    "frontend.uncaught_exception",
    "frontend.unhandled_rejection",
    "frontend.lazy_module_failed",
    "ui.operation_failed",
    "ui.post_write_refresh_failed",
    "inventory.movement_validation_failed",
    "inventory.movement_reference_rejected",
    "inventory.negative_stock_rejected",
    "inventory.catalog_validation_failed",
    "inventory.direct_stock_write_rejected",
    "incident.validation_failed",
    "incident.not_found",
)


class TelemetryQueryError(RuntimeError):
    """A safe, credential-free report query error."""


def _read_events(
    start_date: datetime, end_date: datetime, event_types: tuple[str, ...] | None = None
) -> pd.DataFrame:
    """Read only the selected period and event types from Supabase PostgREST."""
    base_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not base_url or not service_key:
        raise TelemetryQueryError("invalid_configuration")

    filters = [
        ("select", '"timestamp",event_type,tags'),
        (
            "and",
            f"(timestamp.gte.{start_date.astimezone(timezone.utc).isoformat()},"
            f"timestamp.lt.{end_date.astimezone(timezone.utc).isoformat()},event_type.not.is.null)",
        ),
    ]
    if event_types is not None:
        filters.append(("event_type", "in.(" + ",".join(event_types) + ")"))
    request = Request(
        f"{base_url}/rest/v1/telemetry_events?{urlencode(filters)}",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Accept": "application/json",
            "Prefer": "count=exact",
            "Range": "0-99999",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload: list[dict[str, Any]] = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        exc.close()
        raise TelemetryQueryError(f"upstream_http_{exc.code}") from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise TelemetryQueryError("upstream_query_failed") from exc
    return pd.DataFrame(payload, columns=["timestamp", "event_type", "tags"])


def _refine(data: pd.DataFrame) -> pd.DataFrame:
    """Extract safe dimensions from tags and normalize timestamp before grouping."""
    result = data.copy()
    tags = result["tags"].apply(lambda value: value if isinstance(value, dict) else {})
    result["outcome"] = tags.apply(lambda value: value.get("outcome"))
    result["httpStatus"] = tags.apply(lambda value: value.get("httpStatus"))
    result = result.dropna(subset=["timestamp", "event_type"])
    result["timestamp"] = pd.to_datetime(result["timestamp"], utc=True, errors="coerce")
    result = result.dropna(subset=["timestamp"])
    result["day"] = result["timestamp"].dt.strftime("%Y-%m-%d")
    return result


def events_per_day(start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
    """Return event volume by UTC day; answers how much telemetry is arriving."""
    rows = _refine(_read_events(start_date, end_date))
    return (
        rows.dropna(subset=["day"])
        .groupby("day", as_index=False)
        .agg(event_count=("event_type", "count"))
        .reset_index(drop=True)
        .to_dict(orient="records")
    )


def error_rate_by_day(start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
    """Return daily technical error count/rate among observed requests."""
    rows = _refine(_read_events(start_date, end_date, ERROR_EVENT_TYPES))
    error_events = rows.assign(is_error=1)
    total_events = _refine(_read_events(start_date, end_date))
    totals = total_events.dropna(subset=["day"]).groupby("day", as_index=False).agg(
        total_count=("event_type", "count")
    )
    errors = error_events.dropna(subset=["day"]).groupby("day", as_index=False).agg(
        error_count=("is_error", "sum")
    )
    result = totals.merge(errors, on="day", how="left").fillna({"error_count": 0})
    result["error_rate"] = result["error_count"] / result["total_count"]
    return result.reset_index(drop=True).to_dict(orient="records")


def event_type_distribution(start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
    """Return event counts by type; answers which telemetry streams dominate."""
    rows = _refine(_read_events(start_date, end_date))
    return (
        rows.dropna(subset=["event_type"])
        .groupby("event_type", as_index=False)
        .agg(event_count=("timestamp", "count"))
        .sort_values("event_count", ascending=False, kind="stable")
        .reset_index(drop=True)
        .to_dict(orient="records")
    )
