from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sales_queue_endpoint_shape():
    # prepara al menos un prospecto escaneado
    s = client.post(
        "/scan/urls",
        json={"urls": ["https://example.com"], "rubro": "restaurantes", "provincia": "Panamá"},
    )
    assert s.status_code == 200

    r = client.get("/dashboard/sales-queue?limit=20&min_score=0&stale_hours=0")
    assert r.status_code == 200
    data = r.json()
    assert {"count", "limit", "min_score", "stale_hours", "items"}.issubset(set(data.keys()))
    assert isinstance(data["items"], list)
