import logging
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from routers import incidents, inventory, telemetry


logger = logging.getLogger("uvicorn.error")


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
)


@app.middleware("http")
async def log_request_timing(request: Request, call_next):
    started_at = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = (perf_counter() - started_at) * 1000
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        logger.info(
            "method=%s path=%s status=%d duration_ms=%.3f",
            request.method,
            path,
            status_code,
            duration_ms,
        )


app.include_router(incidents.router)
app.include_router(inventory.router)
app.include_router(telemetry.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "brasaland-central-api"}
