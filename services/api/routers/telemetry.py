import logging
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from jsonschema import Draft7Validator, FormatChecker
from pydantic import BaseModel, ValidationError

from models.telemetry import TelemetryEvent
from storage.telemetry_events import TelemetryStorageError, store_events

logger = logging.getLogger("uvicorn.error")

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "docs" / "telemetry" / "event-schemas.json"
with SCHEMA_PATH.open(encoding="utf-8") as schema_file:
	_schema = json.load(schema_file)
Draft7Validator.check_schema(_schema)
_validator = Draft7Validator(_schema, format_checker=FormatChecker())

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


class EventsEnvelope(BaseModel):
	events: list[Any]


class EventsResult(BaseModel):
	received: int
	stored: int
	rejected: int


@router.post("/events", response_model=EventsResult)
def receive_events(batch: EventsEnvelope) -> EventsResult:
	rows: list[dict[str, Any]] = []
	rejected = 0
	for raw in batch.events:
		try:
			event = TelemetryEvent.model_validate(raw)
		except ValidationError:
			rejected += 1
			continue
		payload = event.model_dump(mode="json")
		if not _validator.is_valid(payload):
			rejected += 1
			continue
		try:
			json.dumps(payload, allow_nan=False)
		except ValueError:
			rejected += 1
			continue
		payload["tags"] = payload.pop("properties")
		rows.append(payload)

	try:
		stored = store_events(rows)
	except TelemetryStorageError as exc:
		logger.error(
			"telemetry storage failed received=%d valid=%d rejected=%d reason=%s",
			len(batch.events), len(rows), rejected, exc,
		)
		raise HTTPException(status_code=503, detail="Telemetry storage unavailable") from exc
	logger.info(
		"telemetry batch received=%d stored=%d rejected=%d",
		len(batch.events), stored, rejected,
	)
	return EventsResult(received=len(batch.events), stored=stored, rejected=rejected)
