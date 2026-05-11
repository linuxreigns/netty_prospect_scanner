from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.commercial_analysis import analyze_commercial_fit
from app.database import get_db
from app.models import Prospect

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/prospect/{prospect_id}/analysis")
def ai_analysis_for_prospect(prospect_id: int, db: Session = Depends(get_db)):
    p = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado")

    payload = {c.name: getattr(p, c.name) for c in p.__table__.columns}
    return analyze_commercial_fit(payload)
