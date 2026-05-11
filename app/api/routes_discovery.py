from fastapi import APIRouter, Query

from app.config import settings
from app.discovery.service import DiscoveryService

router = APIRouter(prefix="/discovery", tags=["discovery"])
service = DiscoveryService()


@router.get("/search")
def search_sites(
    rubro: str | None = None,
    provincia: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
):
    results = service.search(rubro=rubro, provincia=provincia, limit=limit)
    return {
        "count": len(results),
        "duckduckgo_enabled": settings.enable_duckduckgo_discovery,
        "providers": [p.name for p in service.providers],
        "results": [r.__dict__ for r in results],
    }


@router.get("/status")
def discovery_status():
    return {
        "duckduckgo_enabled": settings.enable_duckduckgo_discovery,
        "results_per_query": settings.duckduckgo_results_per_query,
        "providers": [p.name for p in service.providers],
        "local_catalog": "data/discovery_catalog.csv",
    }
