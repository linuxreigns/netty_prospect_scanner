from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_prospects_filters_and_commercial_view():
    # preparar datos base
    r_scan = client.post(
        "/scan/urls",
        json={"urls": ["https://example.com"], "rubro": "restaurantes", "provincia": "Panamá"},
    )
    assert r_scan.status_code == 200

    r_run = client.post(
        "/agents/run",
        json={
            "url": "https://example.com",
            "rubro": "restaurantes",
            "provincia": "Panamá",
            "require_panama": False,
        },
    )
    assert r_run.status_code == 200
    run_data = r_run.json()

    # filtros CRM
    r_list = client.get("/dashboard/prospects?con_actividad_agentes=true")
    assert r_list.status_code == 200
    rows = r_list.json()
    assert isinstance(rows, list)
    assert any(row.get("latest_agent_run_id") == run_data["id"] for row in rows)

    # vista comercial consolidada
    pid = next(row["id"] for row in rows if row.get("domain") == "example.com")
    r_view = client.get(f"/dashboard/prospects/{pid}/commercial-view")
    assert r_view.status_code == 200
    v = r_view.json()
    assert "prospect" in v
    assert "latest_agent_run" in v
    assert v["latest_agent_run"] is not None
