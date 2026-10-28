"""Append-only bulk persistence through Supabase's PostgREST API."""

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class TelemetryStorageError(RuntimeError):
	"""A safe error code, without credentials, payloads or upstream error bodies."""


def store_events(rows: list[dict[str, Any]]) -> int:
	if not rows:
		return 0

	url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
	key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
	try:
		parsed = urlsplit(url)
	except ValueError as exc:
		raise TelemetryStorageError("invalid_configuration") from exc
	if (
		not key or parsed.scheme != "https" or not parsed.hostname
		or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path
	):
		raise TelemetryStorageError("invalid_configuration")

	request = Request(
		f"{url}/rest/v1/telemetry_events",
		data=json.dumps(rows, allow_nan=False).encode("utf-8"),
		headers={
			"apikey": key,
			"Authorization": f"Bearer {key}",
			"Content-Type": "application/json",
			"Prefer": "return=minimal",
		},
		method="POST",
	)
	try:
		with urlopen(request, timeout=10) as response:
			if response.status != 201:
				raise TelemetryStorageError(f"unexpected_status_{response.status}")
			response.read()
	except HTTPError as exc:
		status = exc.code
		exc.close()
		raise TelemetryStorageError(f"upstream_http_{status}") from exc
	except (URLError, TimeoutError, OSError) as exc:
		raise TelemetryStorageError("upstream_connection_failed") from exc
	# PostgREST commits the array atomically; no upsert or per-event request.
	return len(rows)
