from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.exporters.csv_exporter import export_csv
from app.exporters.pdf_exporter import export_summary_pdf
from app.exporters.xlsx_exporter import export_xlsx
from app.models import AgentRun, Prospect

router = APIRouter(prefix="/export", tags=["export"])

EXPORT_DIR = Path("data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _latest_agent_run(db: Session, domain: str) -> AgentRun | None:
    return db.query(AgentRun).filter(AgentRun.domain == domain).order_by(AgentRun.created_at.desc()).first()


def sales_queue_dataframe(db: Session, min_score: int = 60, stale_hours: int = 24, limit: int = 200) -> pd.DataFrame:
    cutoff = datetime.now() - pd.Timedelta(hours=max(1, stale_hours))
    rows = (
        db.query(Prospect)
        .filter(
            Prospect.netty_fit_score >= min_score,
            Prospect.has_chatbot.is_(False),
            Prospect.has_whatsapp.is_(True),
            Prospect.load_ok.is_(True),
        )
        .order_by(Prospect.netty_fit_score.desc())
        .limit(max(1, min(limit, 1000)))
        .all()
    )

    data = []
    for p in rows:
        latest = _latest_agent_run(db, p.domain)
        if latest and latest.created_at and latest.created_at.replace(tzinfo=None) >= cutoff.to_pydatetime():
            continue
        data.append(
            {
                "prospect_id": p.id,
                "domain": p.domain,
                "url": p.url,
                "rubro": p.rubro,
                "provincia": p.provincia,
                "score": p.netty_fit_score,
                "classification": p.fit_classification,
                "has_whatsapp": p.has_whatsapp,
                "has_chatbot": p.has_chatbot,
                "latest_agent_run_id": latest.id if latest else None,
                "latest_agent_run_at": latest.created_at.isoformat() if latest and latest.created_at else None,
            }
        )
    return pd.DataFrame(data)


def prospects_dataframe(db: Session) -> pd.DataFrame:
    rows = db.query(Prospect).all()
    data = [{c.name: getattr(p, c.name) for c in p.__table__.columns} for p in rows]
    return pd.DataFrame(data)


@router.get("/csv")
def export_all_csv(db: Session = Depends(get_db)):
    df = prospects_dataframe(db)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"prospects_{ts}.csv"
    export_csv(df, str(path))
    return {"file": str(path)}


@router.get("/xlsx")
def export_all_xlsx(db: Session = Depends(get_db)):
    df = prospects_dataframe(db)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"prospects_{ts}.xlsx"
    export_xlsx(df, str(path))
    return {"file": str(path)}


@router.get("/pdf-summary")
def export_pdf_summary(db: Session = Depends(get_db)):
    total = db.query(Prospect).count()
    hot = db.query(Prospect).filter(Prospect.fit_classification == "Caliente").count()
    with_whatsapp = db.query(Prospect).filter(Prospect.has_whatsapp.is_(True)).count()

    summary = {
        "total_sites": total,
        "prospectos_calientes": hot,
        "sitios_con_whatsapp": with_whatsapp,
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"summary_{ts}.pdf"
    export_summary_pdf(summary, str(path))
    return {"file": str(path)}


@router.get("/hot-leads")
def export_hot_leads(db: Session = Depends(get_db)):
    df = prospects_dataframe(db)
    if not df.empty:
        df = df[df["fit_classification"] == "Caliente"]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"hot_leads_{ts}.csv"
    export_csv(df, str(path))
    return {"file": str(path)}


@router.get("/sales-list")
def export_sales_list(db: Session = Depends(get_db)):
    df = prospects_dataframe(db)
    if not df.empty:
        cols = [
            c
            for c in ["domain", "rubro", "provincia", "has_whatsapp", "has_email", "has_phone", "netty_fit_score"]
            if c in df.columns
        ]
        df = df[cols].sort_values("netty_fit_score", ascending=False)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"sales_list_{ts}.xlsx"
    export_xlsx(df, str(path))
    return {"file": str(path)}


@router.get("/whatsapp-campaign")
def export_whatsapp_campaign(db: Session = Depends(get_db)):
    df = prospects_dataframe(db)
    if not df.empty:
        df = df[df["has_whatsapp"] & ~df["has_chatbot"]]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"whatsapp_campaign_{ts}.csv"
    export_csv(df, str(path))
    return {"file": str(path)}


@router.get("/email-campaign")
def export_email_campaign(db: Session = Depends(get_db)):
    df = prospects_dataframe(db)
    if not df.empty:
        df = df[df["has_email"]]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"email_campaign_{ts}.csv"
    export_csv(df, str(path))
    return {"file": str(path)}


@router.get("/sales-queue-csv")
def export_sales_queue_csv(
    min_score: int = 60,
    stale_hours: int = 24,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    df = sales_queue_dataframe(db, min_score=min_score, stale_hours=stale_hours, limit=limit)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"sales_queue_{ts}.csv"
    export_csv(df, str(path))
    return {"file": str(path), "rows": len(df)}


@router.get("/sales-queue-xlsx")
def export_sales_queue_xlsx(
    min_score: int = 60,
    stale_hours: int = 24,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    df = sales_queue_dataframe(db, min_score=min_score, stale_hours=stale_hours, limit=limit)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"sales_queue_{ts}.xlsx"
    export_xlsx(df, str(path))
    return {"file": str(path), "rows": len(df)}
