import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.orchestrator import NettySalesEngineOrchestrator
from app.database import SessionLocal, get_db
from app.discovery.service import DiscoveryService
from app.exporters.csv_exporter import export_csv
from app.exporters.xlsx_exporter import export_xlsx
from app.models import AgentRun, AgentTrace, PipelineJob, Prospect
from app.queue import enqueue_pipeline_job
from app.scanner.crawler import ScanInput, normalize_url, scan_batch

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
service = DiscoveryService()
orchestrator = NettySalesEngineOrchestrator()
EXPORT_DIR = Path("data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

JOB_STATUS = {"queued", "running", "retry", "done", "error"}


class PipelineRequest(BaseModel):
    rubro: str | None = None
    provincia: str | None = None
    limit: int = Field(default=50, ge=1, le=500)
    min_hot_score: int = Field(default=80, ge=0, le=100)
    run_agents_for_hot: bool = False


def _now() -> datetime:
    return datetime.now(UTC)


def _job_to_dict(job: PipelineJob) -> dict:
    result = None
    if job.result_json:
        try:
            result = json.loads(job.result_json)
        except json.JSONDecodeError:
            result = None

    return {
        "job_id": job.job_id,
        "status": job.status,
        "phase": job.phase,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        "payload": json.loads(job.payload_json),
        "result": result,
        "error": job.error_message,
        "metrics": {
            "discovered": job.discovered_count,
            "scanned": job.scanned_count,
            "saved": job.saved_count,
            "hot_count": job.hot_count,
        },
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


def _persist_agent_run_from_result(
    db: Session,
    pipeline_job_id: str | None,
    prospect_id: int | None,
    result: dict,
) -> int:
    run = AgentRun(
        prospect_id=prospect_id,
        pipeline_job_id=pipeline_job_id,
        url=result.get("url") or "",
        domain=result.get("domain") or "",
        rubro=result.get("rubro"),
        provincia=result.get("provincia"),
        ok=bool(result.get("ok", False)),
        score=int(result.get("score") or 0),
        classification=str(result.get("classification") or "LOW"),
        message=result.get("message"),
        analysis_json=json.dumps(result.get("analysis") or {}, ensure_ascii=False),
        proposal_json=json.dumps(result.get("proposal") or {}, ensure_ascii=False),
        outreach_json=json.dumps(result.get("outreach") or {}, ensure_ascii=False),
        follow_up_json=json.dumps(result.get("follow_up") or {}, ensure_ascii=False),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    for t in result.get("agent_traces") or []:
        tr = AgentTrace(
            run_id=run.id,
            agent_name=str(t.get("agent") or "unknown-agent"),
            status=str(t.get("status") or "done"),
            summary=str(t.get("summary") or ""),
            output_json=json.dumps(t.get("output") or {}, ensure_ascii=False),
        )
        db.add(tr)
    db.commit()
    return run.id


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


async def _run_pipeline(payload: PipelineRequest, job: PipelineJob | None = None, db: Session | None = None) -> dict:
    discovered = service.search(rubro=payload.rubro, provincia=payload.provincia, limit=payload.limit)
    if job and db:
        job.phase = "discovery"
        job.discovered_count = len(discovered)
        db.add(job)
        db.commit()

    scan_items = [
        ScanInput(url=normalize_url(d.url), rubro=d.rubro or payload.rubro, provincia=d.provincia or payload.provincia)
        for d in discovered
    ]

    if not scan_items:
        return {
            "discovered": 0,
            "scanned": 0,
            "saved": 0,
            "hot_count": 0,
            "hot_export_csv": None,
            "hot_export_xlsx": None,
            "message": "No se encontraron sitios en discovery con los filtros dados.",
        }

    scanned = await scan_batch(scan_items)
    if job and db:
        job.phase = "scan"
        job.scanned_count = len(scanned)
        db.add(job)
        db.commit()

    session = db or SessionLocal()
    close_session = db is None
    try:
        saved_rows = [upsert_prospect(session, r) for r in scanned]
    finally:
        if close_session:
            session.close()

    hot_rows = [p for p in saved_rows if (p.netty_fit_score or 0) >= payload.min_hot_score]
    hot = [{c.name: getattr(p, c.name) for c in p.__table__.columns} for p in hot_rows]

    hot_agent_runs: list[dict] = []
    if payload.run_agents_for_hot:
        for p in hot_rows:
            agent_result = await orchestrator.run_for_url(url=p.url, rubro=p.rubro, provincia=p.provincia)
            run_id = _persist_agent_run_from_result(
                session,
                job.job_id if job else None,
                p.id,
                agent_result,
            )
            hot_agent_runs.append({"prospect_id": p.id, "domain": p.domain, "agent_run_id": run_id})

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_csv_path = None
    export_xlsx_path = None

    if hot:
        df = pd.DataFrame(hot)
        csv_path = EXPORT_DIR / f"pipeline_hot_leads_{ts}.csv"
        xlsx_path = EXPORT_DIR / f"pipeline_hot_leads_{ts}.xlsx"
        export_csv(df, str(csv_path))
        export_xlsx(df, str(xlsx_path))
        export_csv_path = str(csv_path)
        export_xlsx_path = str(xlsx_path)

    return {
        "discovered": len(discovered),
        "scanned": len(scanned),
        "saved": len(saved_rows),
        "hot_count": len(hot),
        "hot_export_csv": export_csv_path,
        "hot_export_xlsx": export_xlsx_path,
        "hot_agent_runs": hot_agent_runs,
    }


async def _execute_job(job_id: str):
    max_backoff_seconds = 6

    for attempt in range(1, 4):  # 3 intentos máximo
        db = SessionLocal()
        try:
            job = db.query(PipelineJob).filter(PipelineJob.job_id == job_id).first()
            if not job:
                return

            job.attempts = attempt
            job.status = "running" if attempt == 1 else "retry"
            job.phase = "start"
            if not job.started_at:
                job.started_at = _now()
            db.add(job)
            db.commit()

            payload = PipelineRequest(**json.loads(job.payload_json))
            result = await _run_pipeline(payload, job=job, db=db)

            job.status = "done"
            job.phase = "finished"
            job.finished_at = _now()
            job.result_json = json.dumps(result, ensure_ascii=False)
            job.error_message = None
            job.discovered_count = result.get("discovered", 0)
            job.scanned_count = result.get("scanned", 0)
            job.saved_count = result.get("saved", 0)
            job.hot_count = result.get("hot_count", 0)
            db.add(job)
            db.commit()
            return
        except Exception as exc:
            # refrescar job en caso de rollback implícito
            job = db.query(PipelineJob).filter(PipelineJob.job_id == job_id).first()
            if not job:
                return

            job.error_message = str(exc)
            if attempt >= 3:
                job.status = "error"
                job.phase = "failed"
                job.finished_at = _now()
                db.add(job)
                db.commit()
                return

            job.status = "retry"
            job.phase = "retry_wait"
            db.add(job)
            db.commit()
            await asyncio.sleep(min(2**attempt, max_backoff_seconds))
        finally:
            db.close()


@router.post("/discover-scan-export")
async def discover_scan_export(payload: PipelineRequest, db: Session = Depends(get_db)):
    _ = db  # mantiene dependencia para consistencia DI
    return await _run_pipeline(payload)


@router.post("/discover-scan-export/async")
async def discover_scan_export_async(
    payload: PipelineRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    job_id = str(uuid4())
    job = PipelineJob(
        job_id=job_id,
        status="queued",
        payload_json=json.dumps(payload.model_dump(), ensure_ascii=False),
        attempts=0,
        max_attempts=3,
        phase="queued",
    )
    db.add(job)
    db.commit()

    if not await enqueue_pipeline_job(job_id):
        background_tasks.add_task(_execute_job, job_id)

    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(PipelineJob).filter(PipelineJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="job_id no encontrado")
    return _job_to_dict(job)


@router.get("/jobs")
def list_jobs(limit: int = 50, status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(PipelineJob)
    if status:
        if status not in JOB_STATUS:
            raise HTTPException(status_code=400, detail=f"status inválido. Use: {sorted(JOB_STATUS)}")
        q = q.filter(PipelineJob.status == status)

    jobs = q.order_by(PipelineJob.created_at.desc()).limit(limit).all()
    return [_job_to_dict(j) for j in jobs]
