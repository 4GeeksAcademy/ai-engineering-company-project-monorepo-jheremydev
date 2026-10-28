"""Technical telemetry report endpoint with a short in-memory TTL cache."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from threading import Lock
from time import monotonic
from typing import Any

from fastapi import APIRouter, HTTPException, Response

from telemetry import analysis

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/telemetry", tags=["telemetry"])
CACHE_TTL_SECONDS = 60
_cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
_cache_lock = Lock()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.get("/report")
def telemetry_report(
    response: Response,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """Build or return cached report metrics for one resolved UTC period."""
    now = datetime.now(timezone.utc)
    period_end = _as_utc(end_date) if end_date is not None else now
    period_start = _as_utc(start_date) if start_date is not None else period_end - timedelta(days=7)
    if period_start > period_end:
        raise HTTPException(status_code=422, detail="start_date must be before or equal to end_date")

    # Preserve the caller's date combination: a default end time moves on every
    # request, but two identical parameter-less requests must share the 60s cache.
    cache_key = (
        start_date.isoformat() if start_date is not None else "default-7d",
        end_date.isoformat() if end_date is not None else "default-now",
    )
    cache_now = monotonic()
    with _cache_lock:
        cached = _cache.get(cache_key)
        if cached is not None and cache_now - cached[0] < CACHE_TTL_SECONDS:
            response.headers["X-Telemetry-Cache"] = "HIT"
            return cached[1]

    try:
        result: dict[str, Any] = {
            "period": {"from": period_start.isoformat(), "to": period_end.isoformat()},
            "metrics": {
                "events_per_day": analysis.events_per_day(period_start, period_end),
                "error_rate_by_day": analysis.error_rate_by_day(period_start, period_end),
                "event_type_distribution": analysis.event_type_distribution(period_start, period_end),
            },
        }
    except analysis.TelemetryQueryError as exc:
        logger.error("telemetry report query failed reason=%s", exc)
        raise HTTPException(status_code=503, detail="Telemetry report unavailable") from exc

    with _cache_lock:
        _cache[cache_key] = (monotonic(), result)
    response.headers["X-Telemetry-Cache"] = "MISS"
    return result
