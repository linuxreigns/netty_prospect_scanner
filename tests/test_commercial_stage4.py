from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _seed_prospect() -> int:
    r = client.post(
        "/scan/urls",
        json={"urls": ["https://example.com"], "rubro": "restaurantes", "provincia": "Panamá"},
    )
    assert r.status_code == 200
    return r.json()["saved_ids"][0]


def test_sector_template_endpoint():
    r = client.get("/commercial/templates/restaurantes")
    assert r.status_code == 200
    d = r.json()
    assert {"sector", "pitch", "email_subject", "email_body", "whatsapp_message", "follow_up_48h"}.issubset(
        set(d.keys())
    )


def test_plan_recommendation_endpoint():
    pid = _seed_prospect()
    r = client.get(f"/commercial/prospects/{pid}/plan")
    assert r.status_code == 200
    d = r.json()
    assert {"prospect_id", "recommended_plan", "reasons"}.issubset(set(d.keys()))


def test_commercial_queue_manual_approval_flow():
    pid = _seed_prospect()

    create = client.post("/commercial/queue", json={"prospect_id": pid, "channel": "email", "actor": "qa_user"})
    assert create.status_code == 200
    assert create.json()["queue_backend"] == "db"
    item = create.json()["item"]
    item_id = item["id"]
    assert item["status"] == "pending"

    listing = client.get("/commercial/queue?status=pending")
    assert listing.status_code == 200
    assert isinstance(listing.json().get("items"), list)

    approve = client.post(f"/commercial/queue/{item_id}/approval", json={"approve": True, "actor": "qa_manager"})
    assert approve.status_code == 200
    assert approve.json()["item"]["status"] == "approved"
    assert approve.json()["dispatch"] == "manual_only"

    audit = client.get(f"/commercial/queue/audit?queue_item_id={item_id}")
    assert audit.status_code == 200
    items = audit.json().get("items", [])
    assert len(items) >= 2
    assert items[0]["action"] in {"approve", "reject", "bulk_approve", "bulk_reject", "create"}


def test_commercial_queue_bulk_approval_flow():
    p1 = _seed_prospect()
    p2 = _seed_prospect()

    c1 = client.post("/commercial/queue", json={"prospect_id": p1, "channel": "whatsapp", "actor": "ops"})
    c2 = client.post("/commercial/queue", json={"prospect_id": p2, "channel": "whatsapp", "actor": "ops"})
    assert c1.status_code == 200 and c2.status_code == 200

    # actor no-manager debe saltar ítems que requieran manager
    bulk_non_manager = client.post(
        "/commercial/queue/bulk-approval",
        json={
            "approve": False,
            "actor": "ops_user",
            "status_filter": "pending",
            "channel": "whatsapp",
            "max_items": 10,
        },
    )
    assert bulk_non_manager.status_code == 200
    assert "skipped_policy_count" in bulk_non_manager.json()

    bulk = client.post(
        "/commercial/queue/bulk-approval",
        json={
            "approve": False,
            "actor": "ops_manager",
            "status_filter": "pending",
            "channel": "whatsapp",
            "max_items": 10,
        },
    )
    assert bulk.status_code == 200
    assert bulk.json()["updated_count"] >= 1
    assert bulk.json()["new_status"] == "rejected"


def test_policy_blocks_non_manager_approval_and_allows_manager_then_dispatch_simulation():
    pid = _seed_prospect()

    created = client.post("/commercial/queue", json={"prospect_id": pid, "channel": "whatsapp", "actor": "ops"})
    assert created.status_code == 200
    item_id = created.json()["item"]["id"]

    blocked = client.post(f"/commercial/queue/{item_id}/approval", json={"approve": True, "actor": "ops_user"})
    assert blocked.status_code == 403

    approved = client.post(f"/commercial/queue/{item_id}/approval", json={"approve": True, "actor": "ops_manager"})
    assert approved.status_code == 200
    assert approved.json()["item"]["status"] == "approved"

    sim = client.post(f"/commercial/queue/{item_id}/simulate-dispatch", json={"actor": "ops_dispatcher"})
    assert sim.status_code == 200
    assert sim.json()["item"]["status"] == "sent"
    assert sim.json()["dispatch_mode"] == "simulation_only"


def test_queue_metrics_endpoint_shape():
    r = client.get("/dashboard/commercial/queue-metrics?hours_threshold=24")
    assert r.status_code == 200
    d = r.json()
    assert {"hours_threshold", "counts", "pending_aging", "approval_time_avg_hours", "bulk_efficiency_pct"}.issubset(
        set(d.keys())
    )
