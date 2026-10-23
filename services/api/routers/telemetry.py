import logging
import os

from fastapi import APIRouter

from models.telemetry import TelemetryBatch, TelemetryBatchResponse

logger = logging.getLogger("uvicorn.error")

# Read for future forwarding; the stub does not redirect traffic yet.
TELEMETRY_ENDPOINT = os.getenv("TELEMETRY_ENDPOINT")

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/events", response_model=TelemetryBatchResponse)
def receive_events(batch: TelemetryBatch) -> TelemetryBatchResponse:
	count = len(batch.events)
	logger.info("telemetry batch received count=%d", count)
	for event in batch.events:
		logger.info(
			"telemetry event event_type=%s source=%s", event.event_type, event.source
		)
	return TelemetryBatchResponse(received=count)
