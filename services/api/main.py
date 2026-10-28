import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from routers import incidents, inventory, telemetry, telemetry_report
from storage import telemetry as telemetry_emitter


logger = logging.getLogger("uvicorn.error")

MOVEMENT_TYPES = {"entrada", "salida", "ajuste"}
STOCK_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class HealthResponse(BaseModel):
    status: str
    service: str


app = FastAPI(
    title="Brasaland Central API",
    description="API centralizada para los dominios de Brasaland.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


async def _movement_type_from_body(request: Request) -> dict[str, str]:
    try:
        body = json.loads(await request.body())
    except (ValueError, UnicodeDecodeError):
        return {}
    tipo = body.get("tipo") if isinstance(body, dict) else None
    return {"movementType": tipo} if tipo in MOVEMENT_TYPES else {}


@app.middleware("http")
async def log_request_timing(request: Request, call_next):
    started_at = perf_counter()
    status_code = 500
    request_id = telemetry_emitter.valid_uuid(request.headers.get("x-request-id")) or str(uuid4())
    telemetry_emitter.request_id_var.set(request_id)
    telemetry_emitter.session_id_var.set(
        telemetry_emitter.valid_uuid(request.headers.get("x-telemetry-session-id"))
    )
    telemetry_emitter.form_attempt_id_var.set(
        telemetry_emitter.valid_uuid(request.headers.get("x-telemetry-form-attempt-id"))
    )
    path = request.url.path
    if request.method == "POST" and path == "/inventory/movements":
        # Observed before FastAPI validation so 422s are part of the received total.
        telemetry_emitter.emit(
            "inventory.movement_received",
            {
                "route": "/inventory/movements",
                "method": "POST",
                **await _movement_type_from_body(request),
                **telemetry_emitter.form_attempt_property(),
            },
        )
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_ms = (perf_counter() - started_at) * 1000
        route = request.scope.get("route")
        route_path = getattr(route, "path", path)
        if status_code == 405 and path == "/inventory/stock" and request.method in STOCK_WRITE_METHODS:
            telemetry_emitter.emit(
                "inventory.direct_stock_write_rejected",
                {"route": "/inventory/stock", "method": request.method, "httpStatus": 405},
            )
        logger.info(
            "method=%s path=%s status=%d duration_ms=%.3f request_id=%s",
            request.method,
            route_path,
            status_code,
            duration_ms,
            request_id,
        )


@app.exception_handler(RequestValidationError)
async def track_validation_errors(request: Request, exc: RequestValidationError):
    path = request.url.path
    if request.method == "POST":
        issues = telemetry_emitter.sanitize_issues(exc.errors())
        form_attempt = telemetry_emitter.form_attempt_property()
        if path == "/inventory/movements":
            body = exc.body if isinstance(exc.body, dict) else {}
            tipo = body.get("tipo")
            telemetry_emitter.emit(
                "inventory.movement_validation_failed",
                {
                    "httpStatus": 422,
                    "issues": issues,
                    **({"movementType": tipo} if tipo in MOVEMENT_TYPES else {}),
                    **form_attempt,
                },
            )
        elif path in ("/inventory/articles", "/inventory/locals"):
            telemetry_emitter.emit(
                "inventory.catalog_validation_failed",
                {
                    "entity": "article" if path.endswith("articles") else "local",
                    "httpStatus": 422,
                    "issues": issues,
                    **form_attempt,
                },
            )
    return await request_validation_exception_handler(request, exc)


app.include_router(incidents.router)
app.include_router(inventory.router)
app.include_router(telemetry.router)
app.include_router(telemetry_report.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "brasaland-central-api"}
