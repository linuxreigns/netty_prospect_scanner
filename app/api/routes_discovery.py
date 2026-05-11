from fastapi import APIRouter, Query

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
        "results": [r.__dict__ for r in results],
    }
