from fastapi import FastAPI

from routers import incidents

app = FastAPI(
    title="Brasaland Central API",
    description="API centralizada para los dominios de Brasaland.",
    version="0.1.0",
)

app.include_router(incidents.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "brasaland-central-api"}
