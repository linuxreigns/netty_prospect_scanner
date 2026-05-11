from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app import queue as job_queue
from app.api.routes_agents import router as agents_router
from app.api.routes_ai import router as ai_router
from app.api.routes_commercial import router as commercial_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_discovery import router as discovery_router
from app.api.routes_export import router as export_router
from app.api.routes_pipeline import _execute_job
from app.api.routes_pipeline import router as pipeline_router
from app.api.routes_scan import router as scan_router
from app.auth import require_api_key
from app.config import settings

API_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(_: FastAPI):
    await job_queue.init_redis()
    await job_queue.start_consumer(_execute_job)
    yield
    await job_queue.close_redis()


app = FastAPI(
    title=settings.app_name,
    version=API_VERSION,
    description="Netty Sales Engine — API interna para prospección B2B en Panamá.",
    lifespan=lifespan,
)

# Públicos: solo lectura, no desencadenan operaciones
app.include_router(discovery_router)
app.include_router(dashboard_router)

# Protegidos: desencadenan scraping, ejecución de agentes o exponen datos
_auth = [Depends(require_api_key)]
app.include_router(scan_router, dependencies=_auth)
app.include_router(export_router, dependencies=_auth)
app.include_router(pipeline_router, dependencies=_auth)
app.include_router(agents_router, dependencies=_auth)
app.include_router(commercial_router, dependencies=_auth)
app.include_router(ai_router, dependencies=_auth)


@app.get("/")
def health():
    return {"status": "ok", "app": settings.app_name, "version": API_VERSION}


@app.get("/api/info", tags=["meta"])
def api_info():
    return {
        "version": API_VERSION,
        "name": settings.app_name,
        "stable_since": "2026-05-11",
        "queue_backend": "redis" if job_queue.is_available() else "background_tasks",
        "db_backend": "postgresql" if settings.database_url.startswith("postgresql") else "sqlite",
        "auth_enabled": bool(settings.api_key),
        "endpoints": {
            "scan": "/scan",
            "pipeline": "/pipeline",
            "dashboard": "/dashboard",
            "export": "/export",
            "agents": "/agents",
            "commercial": "/commercial",
            "ai": "/ai",
            "discovery": "/discovery",
        },
    }
