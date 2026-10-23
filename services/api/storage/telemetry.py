"""Server-side telemetry emitter (source=api).

Builds the closed envelope of docs/telemetry/event-schemas.json, buffers events in memory and
ships them in batches to TELEMETRY_ENDPOINT (the /telemetry/events stub). Emission never raises
into the request that produced it.
"""

import json
import logging
import os
import re
import threading
import urllib.request
from contextvars import ContextVar
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Iterable, Optional
from uuid import uuid4

from models.telemetry import SCHEMA_VERSION, UUID_V4_PATTERN, TelemetryEvent

logger = logging.getLogger("uvicorn.error")

TELEMETRY_ENDPOINT = os.getenv("TELEMETRY_ENDPOINT")
_ENVIRONMENT = os.getenv("TELEMETRY_ENVIRONMENT", "development")
ENVIRONMENT = _ENVIRONMENT if _ENVIRONMENT in ("production", "development", "test") else "development"

MAX_BATCH_SIZE = 20
FLUSH_INTERVAL_SECONDS = 1.0

_UUID_RE = re.compile(UUID_V4_PATTERN)

request_id_var: ContextVar[Optional[str]] = ContextVar("telemetry_request_id", default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar("telemetry_session_id", default=None)
form_attempt_id_var: ContextVar[Optional[str]] = ContextVar("telemetry_form_attempt_id", default=None)

_buffer: list[dict[str, Any]] = []
_lock = threading.Lock()
_wakeup = threading.Event()
_worker: Optional[threading.Thread] = None


def valid_uuid(value: Optional[str]) -> Optional[str]:
	"""Returns a lowercase UUID v4 or None; never trusts arbitrary header content."""
	if not value or len(value) != 36:
		return None
	value = value.lower()
	return value if _UUID_RE.match(value) else None


def decimal_string(value: Decimal) -> Optional[str]:
	"""Canonical decimal string without exponent; None if it cannot be represented."""
	if not value.is_finite():
		return None
	if value == 0:
		value = Decimal("0")
	text = format(value, "f")
	return text if len(text) <= 64 else None


def form_attempt_property() -> dict[str, str]:
	form_attempt_id = form_attempt_id_var.get()
	return {"formAttemptId": form_attempt_id} if form_attempt_id else {}


def emit(event_type: str, properties: dict[str, Any]) -> None:
	try:
		event = TelemetryEvent(
			eventId=str(uuid4()),
			timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
			sessionId=session_id_var.get(),
			userId=None,
			event_type=event_type,
			schemaVersion=SCHEMA_VERSION,
			requestId=request_id_var.get(),
			properties=properties,
			source="api",
			environment=ENVIRONMENT,
		)
	except Exception:
		logger.warning("telemetry event discarded event_type=%s reason=invalid_envelope", event_type)
		return
	with _lock:
		_buffer.append(event.model_dump(mode="json"))
		should_flush_now = len(_buffer) >= MAX_BATCH_SIZE
	_ensure_worker()
	if should_flush_now:
		_wakeup.set()


def _ensure_worker() -> None:
	global _worker
	if _worker is not None and _worker.is_alive():
		return
	with _lock:
		if _worker is not None and _worker.is_alive():
			return
		_worker = threading.Thread(target=_run, name="telemetry-emitter", daemon=True)
		_worker.start()


def _run() -> None:
	while True:
		_wakeup.wait(FLUSH_INTERVAL_SECONDS)
		_wakeup.clear()
		flush()


def flush() -> None:
	while True:
		with _lock:
			batch = _buffer[:MAX_BATCH_SIZE]
			del _buffer[:MAX_BATCH_SIZE]
		if not batch:
			return
		_deliver(batch)


def _deliver(batch: list[dict[str, Any]]) -> None:
	if not TELEMETRY_ENDPOINT:
		for event in batch:
			logger.info("telemetry local sink event_type=%s source=api", event["event_type"])
		return
	request = urllib.request.Request(
		TELEMETRY_ENDPOINT,
		data=json.dumps({"events": batch}).encode("utf-8"),
		headers={"Content-Type": "application/json"},
		method="POST",
	)
	try:
		with urllib.request.urlopen(request, timeout=5) as response:
			response.read()
	except Exception:
		logger.warning("telemetry batch dropped count=%d reason=delivery_failed", len(batch))


_FIELDS = {
	"articulo_id", "local", "tipo", "cantidad", "autor", "fecha", "motivo", "nombre",
	"categoria", "unidad_medida", "punto_reorden", "estado", "severidad", "area_responsable", "canal",
}
_QUANTITY_RULES = {"non_finite", "positive_required", "nonzero_required"}


def _rule_for(error: dict[str, Any]) -> str:
	error_type = str(error.get("type", ""))
	if error_type == "missing":
		return "required"
	if error_type == "string_too_short":
		return "empty_text"
	if error_type == "enum":
		return "invalid_enum"
	if error_type.startswith(("datetime_", "date_")):
		return "invalid_datetime"
	if error_type == "json_invalid":
		return "malformed_json"
	if error_type == "finite_number":
		return "non_finite"
	if error_type == "greater_than_equal":
		return "nonnegative_required"
	if error_type == "greater_than":
		return "positive_required"
	if error_type == "value_error":
		# Messages come from our own model validators, never from user input.
		message = str((error.get("ctx") or {}).get("error", ""))
		if "finito" in message:
			return "non_finite"
		if "mayor que cero" in message:
			return "positive_required"
		if "no puede ser cero" in message:
			return "nonzero_required"
		return "other"
	if error_type.endswith(("_type", "_parsing")):
		return "invalid_type"
	return "other"


def sanitize_issues(errors: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
	"""Maps validation errors to at most 16 distinct field/rule codes, without raw messages."""
	issues: list[dict[str, str]] = []
	seen: set[tuple[str, str]] = set()
	for error in errors:
		location = [str(part) for part in error.get("loc", ())]
		rule = _rule_for(error)
		field = next((part for part in location[1:] if part in _FIELDS), None)
		if field is None:
			if rule in _QUANTITY_RULES:
				field = "cantidad"
			elif location[:1] in (["body"], ["query"]):
				field = location[0]
			else:
				field = "unknown"
		key = (field, rule)
		if key in seen:
			continue
		seen.add(key)
		issues.append({"field": field, "rule": rule})
		if len(issues) == 16:
			break
	return issues or [{"field": "unknown", "rule": "other"}]
