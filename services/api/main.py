from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from routers import incidents, inventory


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

app.include_router(incidents.router)
app.include_router(inventory.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "brasaland-central-api"}
