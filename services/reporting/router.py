"""Reporting endpoints; requests inspect/trigger Prefect, never perform ETL inline."""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from . import storage
from data.pipelines.trigger import trigger_weekly_sales_summary_flow

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/reporting", tags=["reporting"])


class RunRequest(BaseModel):
    period_start: datetime | None = None
    period_end: datetime | None = None
    initiated_by: str | None = Field(default=None, max_length=200)


def _resolved_period(start: datetime | None, end: datetime | None) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    default_end = datetime.combine(now.date() - timedelta(days=now.weekday()), time.min, timezone.utc)
    default_start = default_end - timedelta(days=7)
    period_start = start or default_start
    period_end = end or default_end
    period_start = period_start.replace(tzinfo=timezone.utc) if period_start.tzinfo is None else period_start.astimezone(timezone.utc)
    period_end = period_end.replace(tzinfo=timezone.utc) if period_end.tzinfo is None else period_end.astimezone(timezone.utc)
    if period_start >= period_end:
        raise HTTPException(status_code=422, detail="period_start must be earlier than period_end")
    return period_start, period_end


STALE_AFTER_DAYS = 8  # weekly cadence + 1 day of tolerance


def _is_stale(completed: dict[str, Any] | None, now: datetime | None = None) -> bool:
    """True when no run ever completed or the last completed run is older than 8 days.

    Distinguishes "the pipeline went silent" from "there was genuinely no activity".
    """
    if not completed or not completed.get("finished_at"):
        return True
    try:
        finished = datetime.fromisoformat(str(completed["finished_at"]).replace("Z", "+00:00"))
    except ValueError:
        return True
    if finished.tzinfo is None:
        finished = finished.replace(tzinfo=timezone.utc)
    return (now or datetime.now(timezone.utc)) - finished > timedelta(days=STALE_AFTER_DAYS)


@router.get("/status")
def reporting_status() -> dict[str, Any]:
    try:
        run = storage.latest_run()
        completed = storage.latest_completed_run()
    except storage.ReportingStorageError as exc:
        logger.error("reporting status query failed reason=%s", exc)
        raise HTTPException(status_code=503, detail="Reporting status unavailable") from exc
    stale = _is_stale(completed)
    last_success = completed["finished_at"] if completed else None
    if run is None:
        return {"status": "NotStarted", "run": None, "stale": True,
                "stale_after_days": STALE_AFTER_DAYS, "last_successful_run_at": None}
    return {"status": run["status"], "run": run, "stale": stale,
            "stale_after_days": STALE_AFTER_DAYS, "last_successful_run_at": last_success}


@router.post("/runs", status_code=202)
async def trigger_reporting_run(
    payload: RunRequest,
    request: Request,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    """Submit to an existing Prefect deployment (no ETL execution in the API process)."""
    start, end = _resolved_period(payload.period_start, payload.period_end)
    try:
        active = storage._read("pipeline_run_log", [
            ("select", "run_id,flow_name,trigger_type,started_at,finished_at,status,period_start,period_end"),
            ("period_start", f"eq.{start.isoformat()}"),
            ("period_end", f"eq.{end.isoformat()}"),
            ("finished_at", "is.null"), ("order", "started_at.desc"), ("limit", "1"),
        ])
    except storage.ReportingStorageError as exc:
        logger.error("reporting active-run query failed reason=%s", exc)
        raise HTTPException(status_code=503, detail="Reporting run unavailable") from exc
    if active:
        response.headers["Idempotency-Replayed"] = "true"
        return {"run_id": active[0]["run_id"], "status": active[0]["status"], "period_start": start, "period_end": end}

    deployment_id = os.getenv("PREFECT_DEPLOYMENT_ID", "").strip()
    if not deployment_id:
        raise HTTPException(status_code=503, detail="Reporting Prefect deployment is not configured")
    request_id = request.headers.get("x-request-id")
    run_id = str(uuid4())
    try:
        flow_run = await trigger_weekly_sales_summary_flow(
            deployment_id=deployment_id,
            period_start=start,
            period_end=end,
            requested_run_id=run_id,
            initiated_by=payload.initiated_by,
            request_id=request_id,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        logger.error("Prefect deployment trigger failed type=%s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Could not submit reporting run") from exc
    return {"flow_run_id": str(flow_run.id), "run_id": run_id, "status": str(flow_run.state_name or "Scheduled"),
            "period_start": start, "period_end": end}


@router.get("/kpis")
def reporting_kpis(
    week_start: date | None = Query(default=None),
    week_end: date | None = Query(default=None),
    market: str | None = Query(default=None, max_length=100),
    local_id: str | None = Query(default=None, max_length=200),
    currency: str | None = Query(default=None, max_length=10),
) -> dict[str, Any]:
    filters: list[tuple[str, str]] = []
    if week_start:
        filters.append(("week_start", f"gte.{week_start.isoformat()}"))
    if week_end:
        filters.append(("week_end", f"lte.{week_end.isoformat()}"))
    for name, value in (("market", market), ("local_id", local_id), ("currency", currency)):
        if value:
            filters.append((name, f"eq.{value}"))
    try:
        rows = storage.weekly_summaries(filters)
    except storage.ReportingStorageError as exc:
        logger.error("reporting KPI query failed reason=%s", exc)
        raise HTTPException(status_code=503, detail="Reporting KPIs unavailable") from exc
    return {"rows": rows, "count": len(rows), "metric_kind": "weekly_inventory_activity_not_sales",
            "data_quality_status": "pending_pos_integration"}
