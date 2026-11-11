"""Prefect deployment trigger shared with the reporting API."""

from datetime import datetime
from typing import Any


async def trigger_weekly_sales_summary_flow(
    *, deployment_id: str, period_start: datetime, period_end: datetime,
    requested_run_id: str, initiated_by: str | None, request_id: str | None,
    idempotency_key: str | None,
) -> Any:
    """Create a Prefect deployment run; the API process does not execute ETL."""
    from prefect.client.orchestration import get_client

    async with get_client() as client:
        return await client.create_flow_run_from_deployment(
            deployment_id=deployment_id,
            parameters={
                "period_start": period_start, "period_end": period_end,
                "trigger_type": "manual", "requested_run_id": requested_run_id,
                "initiated_by": initiated_by, "request_id": request_id,
            },
            idempotency_key=idempotency_key,
        )
