from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_pipeline_sync_endpoint_works():
    r = client.post(
        "/pipeline/discover-scan-export",
        json={"rubro": "restaurantes", "provincia": "Panamá", "limit": 5, "min_hot_score": 60},
    )
    assert r.status_code == 200
    data = r.json()
    assert {"discovered", "scanned", "saved", "hot_count", "hot_export_csv", "hot_export_xlsx"}.issubset(data.keys())


def test_pipeline_async_job_lifecycle_persisted():
    r = client.post(
        "/pipeline/discover-scan-export/async",
        json={"rubro": "restaurantes", "provincia": "Panamá", "limit": 1, "min_hot_score": 80},
    )
    assert r.status_code == 200
    payload = r.json()
    assert "job_id" in payload

    status = client.get(f"/pipeline/jobs/{payload['job_id']}")
    assert status.status_code == 200
    sdata = status.json()
    assert sdata["status"] in {"queued", "running", "retry", "done", "error"}
    assert "metrics" in sdata
    assert "payload" in sdata


def test_pipeline_jobs_list_and_status_filter():
    r = client.get("/pipeline/jobs?limit=5")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    r_bad = client.get("/pipeline/jobs?status=invalid")
    assert r_bad.status_code == 400
