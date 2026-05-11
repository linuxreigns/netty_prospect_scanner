from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Prospect
from app.scanner.crawler import ScanInput, load_csv_urls, scan_batch

router = APIRouter(prefix="/scan", tags=["scan"])
DATA_DIR = Path("data").resolve()


class UrlScanRequest(BaseModel):
    urls: list[str]
    rubro: str | None = None
    provincia: str | None = None


class CsvScanRequest(BaseModel):
    csv_path: str


def upsert_prospect(db: Session, data: dict) -> Prospect:
    existing = db.query(Prospect).filter(Prospect.domain == data["domain"]).first()
    if existing:
        for k, v in data.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    p = Prospect(**{k: v for k, v in data.items() if hasattr(Prospect, k)})
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.post("/urls")
async def scan_urls(payload: UrlScanRequest, db: Session = Depends(get_db)):
    items = [ScanInput(url=u, rubro=payload.rubro, provincia=payload.provincia) for u in payload.urls]
    results = await scan_batch(items)
    saved = [upsert_prospect(db, r).id for r in results]
    return {"scanned": len(results), "saved_ids": saved, "results": results}


@router.post("/csv")
async def scan_csv(payload: CsvScanRequest, db: Session = Depends(get_db)):
    requested = Path(payload.csv_path)
    if requested.suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="El archivo debe ser .csv")

    resolved = requested.resolve()
    if DATA_DIR not in resolved.parents and resolved != DATA_DIR:
        raise HTTPException(status_code=400, detail="Ruta CSV fuera de directorio permitido (data/)")

    try:
        items = load_csv_urls(str(resolved))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="CSV no encontrado") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error leyendo CSV: {exc}") from exc

    results = await scan_batch(items)
    saved = [upsert_prospect(db, r).id for r in results]
    return {"scanned": len(results), "saved_ids": saved}
