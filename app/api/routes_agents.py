import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.orchestrator import NettySalesEngineOrchestrator
from app.database import get_db
from app.models import AgentRun, AgentTrace, PipelineJob, Prospect

router = APIRouter(prefix="/agents", tags=["agents"])
orchestrator = NettySalesEngineOrchestrator()


class AgentRunRequest(BaseModel):
    url: str
    rubro: str | None = None
    provincia: str | None = None
    require_panama: bool = Field(default=True)
    pipeline_job_id: str | None = None


def _run_to_dict(run: AgentRun) -> dict:
    return {
        "id": run.id,
        "url": run.url,
        "domain": run.domain,
        "rubro": run.rubro,
        "provincia": run.provincia,
        "prospect_id": run.prospect_id,
        "pipeline_job_id": run.pipeline_job_id,
        "ok": run.ok,
        "score": run.score,
        "classification": run.classification,
        "message": run.message,
        "analysis": json.loads(run.analysis_json) if run.analysis_json else None,
        "proposal": json.loads(run.proposal_json) if run.proposal_json else None,
        "outreach": json.loads(run.outreach_json) if run.outreach_json else None,
        "follow_up": json.loads(run.follow_up_json) if run.follow_up_json else None,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "agent_traces": [
            {
                "id": t.id,
                "agent": t.agent_name,
                "status": t.status,
                "summary": t.summary,
                "output": json.loads(t.output_json) if t.output_json else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in run.traces
        ],
    }


@router.post("/run")
async def run_agents(payload: AgentRunRequest, db: Session = Depends(get_db)):
    result = await orchestrator.run_for_url(url=payload.url, rubro=payload.rubro, provincia=payload.provincia)

    if payload.require_panama and result.get("ok"):
        panama = result.get("analysis", {}).get("panama_validation", {})
        if not panama.get("is_panama", False):
            result["ok"] = False
            result["message"] = "Prospecto fuera de criterio Panamá (filtro require_panama activo)."

    linked_pipeline_job_id = None
    if payload.pipeline_job_id:
        pj = db.query(PipelineJob).filter(PipelineJob.job_id == payload.pipeline_job_id).first()
        if not pj:
            raise HTTPException(status_code=400, detail="pipeline_job_id no existe")
        linked_pipeline_job_id = pj.job_id

    prospect = None
    domain = result.get("domain") or ""
    if domain:
        prospect = db.query(Prospect).filter(Prospect.domain == domain).first()

    run = AgentRun(
        prospect_id=prospect.id if prospect else None,
        pipeline_job_id=linked_pipeline_job_id,
        url=result.get("url") or payload.url,
        domain=result.get("domain") or "",
        rubro=result.get("rubro") or payload.rubro,
        provincia=result.get("provincia") or payload.provincia,
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

    traces = result.get("agent_traces") or []
    for t in traces:
        tr = AgentTrace(
            run_id=run.id,
            agent_name=str(t.get("agent") or "unknown-agent"),
            status=str(t.get("status") or "done"),
            summary=str(t.get("summary") or ""),
            output_json=json.dumps(t.get("output") or {}, ensure_ascii=False),
        )
        db.add(tr)
    db.commit()
    db.refresh(run)

    return _run_to_dict(run)


@router.get("/runs")
def list_runs(limit: int = 50, min_score: int = 0, db: Session = Depends(get_db)):
    rows = (
        db.query(AgentRun).filter(AgentRun.score >= min_score).order_by(AgentRun.created_at.desc()).limit(limit).all()
    )
    return [
        {
            "id": r.id,
            "url": r.url,
            "domain": r.domain,
            "rubro": r.rubro,
            "provincia": r.provincia,
            "prospect_id": r.prospect_id,
            "pipeline_job_id": r.pipeline_job_id,
            "ok": r.ok,
            "score": r.score,
            "classification": r.classification,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="run_id no encontrado")
    return _run_to_dict(run)
