import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.commercial.plan_recommender import recommend_plan
from app.commercial.policy_engine import is_manager, requires_manager_approval
from app.commercial.queue_service import redis_enabled
from app.commercial.templates import get_template_for_sector
from app.database import get_db
from app.models import CommercialQueueAuditEvent, CommercialQueueItem, Prospect

router = APIRouter(prefix="/commercial", tags=["commercial"])


class QueueCreateRequest(BaseModel):
    prospect_id: int
    channel: str = Field(pattern="^(email|whatsapp)$")
    actor: str = "system"


class QueueApprovalRequest(BaseModel):
    approve: bool
    actor: str = "system"


class QueueBulkApprovalRequest(BaseModel):
    approve: bool
    actor: str = "system"
    status_filter: str = "pending"
    channel: str | None = None
    max_items: int = Field(default=100, ge=1, le=500)


class DispatchSimulationRequest(BaseModel):
    actor: str = "system"


def _to_dict(item: CommercialQueueItem) -> dict:
    return {
        "id": item.id,
        "channel": item.channel,
        "prospect_id": item.prospect_id,
        "domain": item.domain,
        "payload": json.loads(item.payload_json),
        "status": item.status,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "approved_at": item.approved_at.isoformat() if item.approved_at else None,
    }


def _audit(
    db: Session,
    queue_item_id: str,
    action: str,
    actor: str,
    previous_status: str | None,
    new_status: str | None,
    note: str | None = None,
):
    ev = CommercialQueueAuditEvent(
        queue_item_id=queue_item_id,
        action=action,
        actor=actor,
        previous_status=previous_status,
        new_status=new_status,
        note=note,
        created_at=datetime.now(UTC),
    )
    db.add(ev)


def _policy_for_item(db: Session, item: CommercialQueueItem) -> dict:
    p = db.query(Prospect).filter(Prospect.id == item.prospect_id).first()
    if not p:
        return {
            "requires_manager_approval": False,
            "reasons": ["Prospecto no encontrado para policy"],
        }
    required, reasons = requires_manager_approval(p, item.channel)
    return {
        "requires_manager_approval": required,
        "reasons": reasons,
    }


@router.get("/templates/{sector}")
def sector_templates(sector: str):
    t = get_template_for_sector(sector)
    return t.__dict__


@router.get("/prospects/{prospect_id}/plan")
def plan_for_prospect(prospect_id: int, db: Session = Depends(get_db)):
    p = db.query(Prospect).filter(Prospect.id == prospect_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado")

    rec = recommend_plan(
        score=int(p.netty_fit_score or 0),
        has_ecommerce=bool(p.ecommerce_platform or p.has_products_or_cart),
        has_whatsapp=bool(p.has_whatsapp),
        has_chatbot=bool(p.has_chatbot),
    )
    return {
        "prospect_id": p.id,
        "domain": p.domain,
        "score": p.netty_fit_score,
        "classification": p.fit_classification,
        **rec,
    }


@router.post("/queue")
def create_queue_item(payload: QueueCreateRequest, db: Session = Depends(get_db)):
    p = db.query(Prospect).filter(Prospect.id == payload.prospect_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Prospecto no encontrado")

    template = get_template_for_sector(p.rubro)
    policy_required, policy_reasons = requires_manager_approval(p, payload.channel)

    row = CommercialQueueItem(
        id=str(uuid4()),
        channel=payload.channel,
        prospect_id=p.id,
        domain=p.domain,
        payload_json=json.dumps(
            {
                "sector": p.rubro,
                "template": template.__dict__,
                "note": "No enviado automáticamente. Requiere aprobación manual.",
                "policy": {
                    "requires_manager_approval": policy_required,
                    "reasons": policy_reasons,
                },
            },
            ensure_ascii=False,
        ),
        status="pending",
        created_at=datetime.now(UTC),
    )
    db.add(row)
    db.flush()
    _audit(db, row.id, "create", payload.actor, None, "pending")
    db.commit()
    db.refresh(row)

    return {
        "queue_backend": "redis" if redis_enabled() else "db",
        "item": _to_dict(row),
    }


@router.get("/queue")
def list_queue(status: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(CommercialQueueItem)
    if status:
        q = q.filter(CommercialQueueItem.status == status)
    rows = q.order_by(CommercialQueueItem.created_at.desc()).limit(max(1, min(limit, 500))).all()

    items = []
    for r in rows:
        d = _to_dict(r)
        d["policy"] = _policy_for_item(db, r)
        items.append(d)

    return {
        "queue_backend": "redis" if redis_enabled() else "db",
        "items": items,
    }


@router.post("/queue/{item_id}/approval")
def approve_queue_item(item_id: str, payload: QueueApprovalRequest, db: Session = Depends(get_db)):
    row = db.query(CommercialQueueItem).filter(CommercialQueueItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="item_id no encontrado")

    policy = _policy_for_item(db, row)
    if policy["requires_manager_approval"] and not is_manager(payload.actor):
        raise HTTPException(
            status_code=403,
            detail="Este ítem requiere aprobación de manager según policy engine",
        )

    prev = row.status
    row.status = "approved" if payload.approve else "rejected"
    row.approved_at = datetime.now(UTC)
    db.add(row)
    _audit(
        db,
        row.id,
        "approve" if payload.approve else "reject",
        payload.actor,
        prev,
        row.status,
    )
    db.commit()
    db.refresh(row)

    return {
        "message": "Aprobación actualizada",
        "item": _to_dict(row),
        "dispatch": "manual_only",
    }


@router.post("/queue/bulk-approval")
def bulk_approval(payload: QueueBulkApprovalRequest, db: Session = Depends(get_db)):
    q = db.query(CommercialQueueItem).filter(CommercialQueueItem.status == payload.status_filter)
    if payload.channel:
        q = q.filter(CommercialQueueItem.channel == payload.channel)

    rows = q.order_by(CommercialQueueItem.created_at.asc()).limit(payload.max_items).all()
    updated: list[str] = []
    skipped_policy: list[str] = []

    for row in rows:
        policy = _policy_for_item(db, row)
        if policy["requires_manager_approval"] and not is_manager(payload.actor):
            skipped_policy.append(row.id)
            continue

        prev = row.status
        row.status = "approved" if payload.approve else "rejected"
        row.approved_at = datetime.now(UTC)
        db.add(row)
        _audit(
            db,
            row.id,
            "bulk_approve" if payload.approve else "bulk_reject",
            payload.actor,
            prev,
            row.status,
            note=f"status_filter={payload.status_filter};channel={payload.channel}",
        )
        updated.append(row.id)

    db.commit()
    return {
        "updated_count": len(updated),
        "updated_ids": updated,
        "skipped_policy_count": len(skipped_policy),
        "skipped_policy_ids": skipped_policy,
        "new_status": "approved" if payload.approve else "rejected",
        "dispatch": "manual_only",
    }


@router.post("/queue/{item_id}/simulate-dispatch")
def simulate_dispatch(item_id: str, payload: DispatchSimulationRequest, db: Session = Depends(get_db)):
    row = db.query(CommercialQueueItem).filter(CommercialQueueItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="item_id no encontrado")

    if row.status != "approved":
        raise HTTPException(status_code=400, detail="Solo se puede simular dispatch de ítems aprobados")

    prev = row.status
    row.status = "sent"
    db.add(row)
    _audit(
        db,
        row.id,
        "simulate_dispatch",
        payload.actor,
        prev,
        row.status,
        note="Simulación sin envío real",
    )
    db.commit()
    db.refresh(row)

    return {
        "message": "Dispatch simulado",
        "item": _to_dict(row),
        "dispatch_mode": "simulation_only",
    }


@router.get("/queue/audit")
def queue_audit(limit: int = 100, queue_item_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(CommercialQueueAuditEvent)
    if queue_item_id:
        q = q.filter(CommercialQueueAuditEvent.queue_item_id == queue_item_id)

    rows = q.order_by(CommercialQueueAuditEvent.created_at.desc()).limit(max(1, min(limit, 500))).all()
    return {
        "items": [
            {
                "id": r.id,
                "queue_item_id": r.queue_item_id,
                "action": r.action,
                "actor": r.actor,
                "previous_status": r.previous_status,
                "new_status": r.new_status,
                "note": r.note,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }
