import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AgentRun, AgentTrace, CommercialQueueAuditEvent, CommercialQueueItem, PipelineJob, Prospect

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _latest_agent_run(db: Session, domain: str) -> AgentRun | None:
    return db.query(AgentRun).filter(AgentRun.domain == domain).order_by(AgentRun.created_at.desc()).first()


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    total = db.query(func.count(Prospect.id)).scalar() or 0
    with_chatbot = db.query(func.count(Prospect.id)).filter(Prospect.has_chatbot.is_(True)).scalar() or 0
    without_chatbot = total - with_chatbot
    with_whatsapp = db.query(func.count(Prospect.id)).filter(Prospect.has_whatsapp.is_(True)).scalar() or 0
    with_ecommerce = (
        db.query(func.count(Prospect.id))
        .filter((Prospect.ecommerce_platform.isnot(None)) | (Prospect.has_products_or_cart.is_(True)))
        .scalar()
        or 0
    )

    def pct_by_cms(name: str) -> float:
        if total == 0:
            return 0.0
        c = db.query(func.count(Prospect.id)).filter(func.lower(Prospect.cms) == name.lower()).scalar() or 0
        return round((c / total) * 100, 2)

    return {
        "total_sites": total,
        "with_chatbot": with_chatbot,
        "without_chatbot": without_chatbot,
        "with_whatsapp": with_whatsapp,
        "with_ecommerce": with_ecommerce,
        "pct_wordpress": pct_by_cms("WordPress"),
        "pct_shopify": pct_by_cms("Shopify"),
        "pct_magento": pct_by_cms("Magento"),
        "pct_html_estatico": pct_by_cms("HTML estático"),
    }


@router.get("/prospects")
def list_prospects(
    technology: str | None = None,
    min_score: int = 0,
    max_score: int = 100,
    rubro: str | None = None,
    provincia: str | None = None,
    sin_chatbot: bool | None = None,
    tiene_whatsapp: bool | None = None,
    con_actividad_agentes: bool | None = None,
    sin_run_reciente_horas: int | None = None,
    hot_sin_chatbot_con_whatsapp: bool | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Prospect)
    if technology:
        q = q.filter(
            (Prospect.cms == technology)
            | (Prospect.ecommerce_platform == technology)
            | (Prospect.frontend_stack == technology)
        )
    q = q.filter(Prospect.netty_fit_score >= min_score, Prospect.netty_fit_score <= max_score)
    if rubro:
        q = q.filter(Prospect.rubro == rubro)
    if provincia:
        q = q.filter(Prospect.provincia == provincia)
    if sin_chatbot is True:
        q = q.filter(Prospect.has_chatbot.is_(False))
    if tiene_whatsapp is True:
        q = q.filter(Prospect.has_whatsapp.is_(True))
    if hot_sin_chatbot_con_whatsapp is True:
        q = q.filter(
            Prospect.netty_fit_score >= 80,
            Prospect.has_chatbot.is_(False),
            Prospect.has_whatsapp.is_(True),
        )

    prospects = q.order_by(Prospect.netty_fit_score.desc()).all()

    rows = []
    cutoff = None
    if sin_run_reciente_horas is not None and sin_run_reciente_horas > 0:
        cutoff = datetime.utcnow() - timedelta(hours=sin_run_reciente_horas)

    for p in prospects:
        latest_run = _latest_agent_run(db, p.domain)
        latest_run_id = latest_run.id if latest_run else None
        latest_run_at = latest_run.created_at.isoformat() if latest_run and latest_run.created_at else None

        if con_actividad_agentes is True and latest_run_id is None:
            continue

        if cutoff is not None:
            # incluir si no tiene run o su último run es antiguo
            if latest_run and latest_run.created_at and latest_run.created_at >= cutoff:
                continue

        rows.append(
            {
                "id": p.id,
                "url": p.url,
                "domain": p.domain,
                "rubro": p.rubro,
                "provincia": p.provincia,
                "cms": p.cms,
                "ecommerce_platform": p.ecommerce_platform,
                "frontend_stack": p.frontend_stack,
                "has_chatbot": p.has_chatbot,
                "has_whatsapp": p.has_whatsapp,
                "netty_fit_score": p.netty_fit_score,
                "fit_classification": p.fit_classification,
                "http_code": p.http_code,
                "response_time_ms": p.response_time_ms,
                # Extracted contact data
                "phone_numbers": p.phone_numbers,
                "email_addresses": p.email_addresses,
                "whatsapp_number": p.whatsapp_number,
                "facebook_url": p.facebook_url,
                "instagram_url": p.instagram_url,
                "linkedin_url": p.linkedin_url,
                "twitter_url": p.twitter_url,
                "youtube_url": p.youtube_url,
                "latest_agent_run_id": latest_run_id,
                "latest_agent_run_at": latest_run_at,
            }
        )

    return rows


@router.get("/prospects/{prospect_id}")
def prospect_detail(prospect_id: int, db: Session = Depends(get_db)):
    p = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not p:
        return {"error": "Prospecto no encontrado"}

    latest_run = _latest_agent_run(db, p.domain)
    data = {c.name: getattr(p, c.name) for c in p.__table__.columns}
    data["latest_agent_run_id"] = latest_run.id if latest_run else None
    data["latest_agent_run_at"] = latest_run.created_at.isoformat() if latest_run and latest_run.created_at else None
    return data


@router.get("/prospects/{prospect_id}/commercial-view")
def prospect_commercial_view(prospect_id: int, db: Session = Depends(get_db)):
    p = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not p:
        return {"error": "Prospecto no encontrado"}

    latest_run = _latest_agent_run(db, p.domain)
    return {
        "prospect": {c.name: getattr(p, c.name) for c in p.__table__.columns},
        "latest_agent_run": (
            {
                "id": latest_run.id,
                "ok": latest_run.ok,
                "score": latest_run.score,
                "classification": latest_run.classification,
                "message": latest_run.message,
                "proposal": latest_run.proposal_json,
                "outreach": latest_run.outreach_json,
                "follow_up": latest_run.follow_up_json,
                "created_at": latest_run.created_at.isoformat() if latest_run.created_at else None,
            }
            if latest_run
            else None
        ),
    }


@router.get("/prospects/{prospect_id}/next-best-action")
def next_best_action(prospect_id: int, db: Session = Depends(get_db)):
    p = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not p:
        return {"error": "Prospecto no encontrado"}

    latest = _latest_agent_run(db, p.domain)
    proposal = None
    outreach = None
    follow_up = None
    if latest:
        try:
            proposal = json.loads(latest.proposal_json) if latest.proposal_json else None
            outreach = json.loads(latest.outreach_json) if latest.outreach_json else None
            follow_up = json.loads(latest.follow_up_json) if latest.follow_up_json else None
        except json.JSONDecodeError:
            proposal = None
            outreach = None
            follow_up = None

    if not p.load_ok:
        action = "Reintentar escaneo técnico antes de contacto comercial"
        reason = "Sitio no accesible en último escaneo"
    elif not p.has_chatbot and p.has_whatsapp and (p.netty_fit_score or 0) >= 80:
        action = "Contacto WhatsApp 1:1 con auditoría breve + CTA a demo"
        reason = "HOT, sin chatbot y con canal WhatsApp visible"
    elif not p.has_chatbot and p.has_contact_form:
        action = "Enviar email/forma con propuesta de automatización de atención"
        reason = "Sin chatbot y con formulario disponible"
    elif p.has_chatbot:
        action = "Pitch comparativo de mejora (ROI, captura de leads, soporte)"
        reason = "Ya usa chatbot, requiere diferenciación"
    else:
        action = "Llamada de descubrimiento comercial"
        reason = "Canales digitales limitados"

    return {
        "prospect_id": p.id,
        "domain": p.domain,
        "score": p.netty_fit_score,
        "classification": p.fit_classification,
        "latest_agent_run_id": latest.id if latest else None,
        "next_best_action": action,
        "reason": reason,
        "suggested_message": (outreach or {}).get("whatsapp_message") if outreach else None,
        "proposal_summary": (proposal or {}).get("summary") if proposal else None,
        "follow_up_hint": (follow_up or {}).get("next_step") if follow_up else None,
    }


@router.get("/agents/summary")
def agents_summary(db: Session = Depends(get_db)):
    total_runs = db.query(func.count(AgentRun.id)).scalar() or 0
    hot_runs = db.query(func.count(AgentRun.id)).filter(AgentRun.classification == "HOT").scalar() or 0
    ok_runs = db.query(func.count(AgentRun.id)).filter(AgentRun.ok.is_(True)).scalar() or 0

    hot_ratio = round((hot_runs / total_runs) * 100, 2) if total_runs else 0.0
    ok_ratio = round((ok_runs / total_runs) * 100, 2) if total_runs else 0.0

    top_agents_rows = (
        db.query(AgentTrace.agent_name, func.count(AgentTrace.id).label("count"))
        .group_by(AgentTrace.agent_name)
        .order_by(func.count(AgentTrace.id).desc())
        .limit(10)
        .all()
    )

    return {
        "total_agent_runs": total_runs,
        "hot_agent_runs": hot_runs,
        "hot_ratio_pct": hot_ratio,
        "ok_ratio_pct": ok_ratio,
        "top_agents": [{"agent": r[0], "count": r[1]} for r in top_agents_rows],
    }


@router.get("/sales-queue")
def sales_queue(limit: int = 50, min_score: int = 60, stale_hours: int = 24, db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(hours=max(1, stale_hours))

    prospects = (
        db.query(Prospect)
        .filter(
            Prospect.netty_fit_score >= min_score,
            Prospect.has_chatbot.is_(False),
            Prospect.has_whatsapp.is_(True),
            Prospect.load_ok.is_(True),
        )
        .order_by(Prospect.netty_fit_score.desc())
        .limit(max(1, min(limit, 500)))
        .all()
    )

    queue = []
    for p in prospects:
        latest = _latest_agent_run(db, p.domain)
        latest_at = latest.created_at if latest else None

        # priorizar si no existe run o está stale
        if latest_at and latest_at >= cutoff:
            continue

        queue.append(
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
                "phone_numbers": p.phone_numbers,
                "email_addresses": p.email_addresses,
                "whatsapp_number": p.whatsapp_number,
                "facebook_url": p.facebook_url,
                "instagram_url": p.instagram_url,
                "linkedin_url": p.linkedin_url,
                "latest_agent_run_id": latest.id if latest else None,
                "latest_agent_run_at": latest.created_at.isoformat() if latest and latest.created_at else None,
            }
        )

    return {
        "count": len(queue),
        "limit": limit,
        "min_score": min_score,
        "stale_hours": stale_hours,
        "items": queue,
    }


@router.get("/pipeline-states")
def pipeline_states(limit: int = 200, db: Session = Depends(get_db)):
    rows = db.query(PipelineJob).order_by(PipelineJob.created_at.desc()).limit(max(1, min(limit, 1000))).all()

    status_counts: dict[str, int] = {"queued": 0, "running": 0, "retry": 0, "done": 0, "error": 0}
    phase_counts: dict[str, int] = {}

    items = []
    for r in rows:
        status = r.status or "queued"
        phase = r.phase or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

        items.append(
            {
                "job_id": r.job_id,
                "status": status,
                "phase": phase,
                "attempts": r.attempts,
                "max_attempts": r.max_attempts,
                "discovered": r.discovered_count,
                "scanned": r.scanned_count,
                "saved": r.saved_count,
                "hot_count": r.hot_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            }
        )

    return {
        "status_counts": status_counts,
        "phase_counts": phase_counts,
        "items": items,
    }


@router.get("/funnel")
def funnel(db: Session = Depends(get_db)):
    discovered = db.query(func.count(Prospect.id)).scalar() or 0
    loaded_ok = db.query(func.count(Prospect.id)).filter(Prospect.load_ok.is_(True)).scalar() or 0
    scored = db.query(func.count(Prospect.id)).filter(Prospect.netty_fit_score.isnot(None)).scalar() or 0
    with_agent_run = (
        db.query(func.count(func.distinct(AgentRun.prospect_id))).filter(AgentRun.prospect_id.isnot(None)).scalar() or 0
    )
    hot = db.query(func.count(Prospect.id)).filter(Prospect.netty_fit_score >= 80).scalar() or 0
    queue_ready = (
        db.query(func.count(Prospect.id))
        .filter(
            Prospect.netty_fit_score >= 60,
            Prospect.has_chatbot.is_(False),
            Prospect.has_whatsapp.is_(True),
            Prospect.load_ok.is_(True),
        )
        .scalar()
        or 0
    )

    def pct(a: int, b: int) -> float:
        return round((a / b) * 100, 2) if b else 0.0

    conversions = {
        "discover_to_load_ok_pct": pct(loaded_ok, discovered),
        "load_ok_to_scored_pct": pct(scored, loaded_ok),
        "scored_to_agent_run_pct": pct(with_agent_run, scored),
        "scored_to_hot_pct": pct(hot, scored),
        "hot_to_queue_ready_pct": pct(queue_ready, hot),
    }

    return {
        "discovered": discovered,
        "loaded_ok": loaded_ok,
        "scored": scored,
        "with_agent_run": with_agent_run,
        "hot": hot,
        "queue_ready": queue_ready,
        "conversions": conversions,
    }


@router.get("/pipeline-aging")
def pipeline_aging(hours_threshold: int = 24, db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(hours=max(1, min(hours_threshold, 720)))
    prospects = db.query(Prospect).filter(Prospect.load_ok.is_(True)).all()

    aging_buckets = {
        "no_run": 0,
        "stale_run": 0,
        "fresh_run": 0,
    }

    stale_items = []
    for p in prospects:
        latest = _latest_agent_run(db, p.domain)
        if not latest:
            aging_buckets["no_run"] += 1
            stale_items.append(
                {
                    "prospect_id": p.id,
                    "domain": p.domain,
                    "score": p.netty_fit_score,
                    "reason": "no_run",
                }
            )
            continue

        if latest.created_at and latest.created_at < cutoff:
            aging_buckets["stale_run"] += 1
            stale_items.append(
                {
                    "prospect_id": p.id,
                    "domain": p.domain,
                    "score": p.netty_fit_score,
                    "latest_agent_run_id": latest.id,
                    "latest_agent_run_at": latest.created_at.isoformat(),
                    "reason": "stale_run",
                }
            )
        else:
            aging_buckets["fresh_run"] += 1

    stale_items = sorted(stale_items, key=lambda x: x.get("score") or 0, reverse=True)

    return {
        "hours_threshold": hours_threshold,
        "aging": aging_buckets,
        "stale_items": stale_items[:100],
    }


@router.get("/hot-alerts")
def hot_alerts(limit: int = 20, stale_hours: int = 24, db: Session = Depends(get_db)):
    queue = sales_queue(limit=max(1, min(limit, 200)), min_score=80, stale_hours=stale_hours, db=db)
    items = queue.get("items", [])

    now = datetime.utcnow()
    alerts = []
    for item in items:
        latest_at = item.get("latest_agent_run_at")
        if latest_at:
            try:
                dt = datetime.fromisoformat(latest_at)
                age_hours = round((now - dt).total_seconds() / 3600, 2)
            except ValueError:
                age_hours = None
        else:
            age_hours = None

        if age_hours is None:
            level = "CRITICAL"
            reason = "HOT sin run histórico de agentes"
            sla_bucket = "no_run"
        elif age_hours >= 72:
            level = "CRITICAL"
            reason = "HOT sin seguimiento >72h"
            sla_bucket = "72h+"
        elif age_hours >= 48:
            level = "HIGH"
            reason = "HOT sin seguimiento >48h"
            sla_bucket = "48-72h"
        elif age_hours >= 24:
            level = "MEDIUM"
            reason = "HOT sin seguimiento >24h"
            sla_bucket = "24-48h"
        else:
            level = "LOW"
            reason = "HOT reciente"
            sla_bucket = "<24h"

        alerts.append(
            {
                **item,
                "age_hours": age_hours,
                "alert_level": level,
                "alert_reason": reason,
                "sla_bucket": sla_bucket,
            }
        )

    severity_counts = {
        "CRITICAL": sum(1 for a in alerts if a["alert_level"] == "CRITICAL"),
        "HIGH": sum(1 for a in alerts if a["alert_level"] == "HIGH"),
        "MEDIUM": sum(1 for a in alerts if a["alert_level"] == "MEDIUM"),
        "LOW": sum(1 for a in alerts if a["alert_level"] == "LOW"),
    }

    return {
        "count": len(alerts),
        "stale_hours": stale_hours,
        "severity": severity_counts,
        "alerts": alerts,
    }


@router.get("/commercial/queue-metrics")
def commercial_queue_metrics(hours_threshold: int = 24, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=max(1, min(hours_threshold, 720)))

    pending = db.query(CommercialQueueItem).filter(CommercialQueueItem.status == "pending").all()
    approved = db.query(CommercialQueueItem).filter(CommercialQueueItem.status == "approved").all()
    rejected = db.query(CommercialQueueItem).filter(CommercialQueueItem.status == "rejected").all()
    sent = db.query(CommercialQueueItem).filter(CommercialQueueItem.status == "sent").all()

    pending_aging = {
        "pending_total": len(pending),
        "pending_older_than_threshold": sum(1 for x in pending if x.created_at and x.created_at < cutoff),
    }

    # approval SLA promedio (create -> approve/reject)
    approval_events = (
        db.query(CommercialQueueAuditEvent)
        .filter(CommercialQueueAuditEvent.action.in_(["approve", "reject", "bulk_approve", "bulk_reject"]))
        .all()
    )

    durations = []
    for ev in approval_events:
        item = db.query(CommercialQueueItem).filter(CommercialQueueItem.id == ev.queue_item_id).first()
        if item and item.created_at and ev.created_at:
            durations.append((ev.created_at - item.created_at).total_seconds() / 3600)

    approval_time_avg_hours = round(sum(durations) / len(durations), 2) if durations else None

    bulk_events = (
        db.query(CommercialQueueAuditEvent)
        .filter(CommercialQueueAuditEvent.action.in_(["bulk_approve", "bulk_reject"]))
        .all()
    )
    total_approval_events = len(approval_events)
    bulk_efficiency_pct = round((len(bulk_events) / total_approval_events) * 100, 2) if total_approval_events else 0.0

    return {
        "hours_threshold": hours_threshold,
        "counts": {
            "pending": len(pending),
            "approved": len(approved),
            "rejected": len(rejected),
            "sent": len(sent),
        },
        "pending_aging": pending_aging,
        "approval_time_avg_hours": approval_time_avg_hours,
        "bulk_efficiency_pct": bulk_efficiency_pct,
    }


@router.get("/agents/activity")
def agents_activity(days: int = 7, db: Session = Depends(get_db)):
    days = max(1, min(days, 90))
    now = datetime.utcnow()
    since = now - timedelta(days=days)

    runs = db.query(AgentRun).filter(AgentRun.created_at >= since).order_by(AgentRun.created_at.asc()).all()

    per_day: dict[str, dict[str, int]] = {}
    for r in runs:
        key = r.created_at.date().isoformat() if r.created_at else now.date().isoformat()
        if key not in per_day:
            per_day[key] = {"runs": 0, "hot": 0, "ok": 0}
        per_day[key]["runs"] += 1
        if r.classification == "HOT":
            per_day[key]["hot"] += 1
        if r.ok:
            per_day[key]["ok"] += 1

    items = [{"date": k, **v} for k, v in sorted(per_day.items(), key=lambda kv: kv[0])]

    return {
        "days": days,
        "from": since.isoformat(),
        "to": now.isoformat(),
        "activity": items,
    }
