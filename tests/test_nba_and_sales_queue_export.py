from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_next_best_action_endpoint_shape():
    s = client.post(
        "/scan/urls",
        json={"urls": ["https://example.com"], "rubro": "restaurantes", "provincia": "Panamá"},
    )
    assert s.status_code == 200
    pid = s.json()["saved_ids"][0]

    r = client.get(f"/dashboard/prospects/{pid}/next-best-action")
    assert r.status_code == 200
    data = r.json()
    assert {"prospect_id", "next_best_action", "reason"}.issubset(set(data.keys()))


def test_sales_queue_export_endpoints():
    r_csv = client.get("/export/sales-queue-csv?min_score=0&stale_hours=1&limit=20")
    assert r_csv.status_code == 200
    d_csv = r_csv.json()
    assert "file" in d_csv and d_csv["file"].endswith(".csv")

    r_xlsx = client.get("/export/sales-queue-xlsx?min_score=0&stale_hours=1&limit=20")
    assert r_xlsx.status_code == 200
    d_xlsx = r_xlsx.json()
    assert "file" in d_xlsx and d_xlsx["file"].endswith(".xlsx")
