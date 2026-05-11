from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_prospects_include_latest_agent_run_id_after_agent_run():
    # 1) generar prospecto (scan base)
    s = client.post(
        "/scan/urls",
        json={"urls": ["https://example.com"], "rubro": "restaurantes", "provincia": "Panamá"},
    )
    assert s.status_code == 200

    # 2) ejecutar agentes para mismo dominio
    a = client.post(
        "/agents/run",
        json={
            "url": "https://example.com",
            "rubro": "restaurantes",
            "provincia": "Panamá",
            "require_panama": False,
        },
    )
    assert a.status_code == 200
    run_data = a.json()
    run_id = run_data["id"]

    # 3) validar campo en listado dashboard
    lst = client.get("/dashboard/prospects")
    assert lst.status_code == 200
    rows = lst.json()
    assert isinstance(rows, list)
    target = next((r for r in rows if r["domain"] == "example.com"), None)
    assert target is not None
    assert target["latest_agent_run_id"] == run_id

    # 4) validar campo en detalle prospecto
    pid = target["id"]
    det = client.get(f"/dashboard/prospects/{pid}")
    assert det.status_code == 200
    data = det.json()
    assert data["latest_agent_run_id"] == run_id
