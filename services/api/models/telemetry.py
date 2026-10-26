from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0.0"

# Mirrors definitions._uuid in docs/telemetry/event-schemas.json (lowercase UUID v4).
UUID_V4_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"

UuidV4 = Annotated[str, Field(pattern=UUID_V4_PATTERN)]


# UTC ISO 8601 ending in Z, as required by the schema's timestamp field.
UtcTimestamp = Annotated[
	str, Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")
]


class TelemetryEvent(BaseModel):
	"""Closed envelope from docs/telemetry/event-schemas.json (schemaVersion 1.0.0)."""

	model_config = ConfigDict(extra="forbid")

	eventId: UuidV4
	timestamp: UtcTimestamp
	sessionId: Optional[UuidV4]
	userId: None
	event_type: str
	schemaVersion: Literal["1.0.0"]
	requestId: Optional[UuidV4]
	properties: dict[str, Any]
	source: Literal["browser", "api", "probe"]
	environment: Literal["production", "development", "test"]


class TelemetryBatch(BaseModel):
	model_config = ConfigDict(extra="forbid")

	events: list[TelemetryEvent]


class TelemetryBatchResponse(BaseModel):
	received: int
