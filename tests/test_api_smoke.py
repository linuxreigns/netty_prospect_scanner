from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_api_info():
    r = client.get("/api/info")
    assert r.status_code == 200
    data = r.json()
    assert data["version"] == "1.0.0"
    assert "queue_backend" in data
    assert "db_backend" in data
    assert "endpoints" in data


def test_dashboard_summary_shape():
    r = client.get("/dashboard/summary")
    assert r.status_code == 200
    data = r.json()
    expected = {
        "total_sites",
        "with_chatbot",
        "without_chatbot",
        "with_whatsapp",
        "with_ecommerce",
        "pct_wordpress",
        "pct_shopify",
        "pct_magento",
        "pct_html_estatico",
    }
    assert expected.issubset(set(data.keys()))


def test_dashboard_agents_analytics_shape():
    r1 = client.get("/dashboard/agents/summary")
    assert r1.status_code == 200
    d1 = r1.json()
    expected_summary = {"total_agent_runs", "hot_agent_runs", "hot_ratio_pct", "ok_ratio_pct", "top_agents"}
    assert expected_summary.issubset(set(d1.keys()))

    r2 = client.get("/dashboard/agents/activity?days=7")
    assert r2.status_code == 200
    d2 = r2.json()
    expected_activity = {"days", "from", "to", "activity"}
    assert expected_activity.issubset(set(d2.keys()))


def test_dashboard_stage3_operational_shapes():
    rf = client.get("/dashboard/funnel")
    assert rf.status_code == 200
    df = rf.json()
    assert {"discovered", "loaded_ok", "scored", "with_agent_run", "hot", "queue_ready", "conversions"}.issubset(
        set(df.keys())
    )

    rs = client.get("/dashboard/pipeline-states?limit=50")
    assert rs.status_code == 200
    ds = rs.json()
    assert {"status_counts", "phase_counts", "items"}.issubset(set(ds.keys()))

    ra = client.get("/dashboard/pipeline-aging?hours_threshold=24")
    assert ra.status_code == 200
    da = ra.json()
    assert {"hours_threshold", "aging", "stale_items"}.issubset(set(da.keys()))

    rh = client.get("/dashboard/hot-alerts?limit=10&stale_hours=24")
    assert rh.status_code == 200
    dh = rh.json()
    assert {"count", "stale_hours", "severity", "alerts"}.issubset(set(dh.keys()))
