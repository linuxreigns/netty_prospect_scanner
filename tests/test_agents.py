from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_agents_run_persists_traces_and_outputs():
    r = client.post(
        "/agents/run",
        json={
            "url": "https://example.com",
            "rubro": "restaurantes",
            "provincia": "Panamá",
            "require_panama": False,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert "agent_traces" in data
    assert isinstance(data["agent_traces"], list)
    assert len(data["agent_traces"]) == 10
    assert "proposal" in data
    assert "outreach" in data
    assert "follow_up" in data
    assert "prospect_id" in data
    assert "pipeline_job_id" in data


def test_agents_runs_list_and_detail():
    lst = client.get("/agents/runs?limit=5&min_score=0")
    assert lst.status_code == 200
    rows = lst.json()
    assert isinstance(rows, list)

    if rows:
        rid = rows[0]["id"]
        detail = client.get(f"/agents/runs/{rid}")
        assert detail.status_code == 200
        data = detail.json()
        assert data["id"] == rid
        assert "agent_traces" in data


def test_agents_run_rejects_invalid_pipeline_job_id():
    r = client.post(
        "/agents/run",
        json={
            "url": "https://example.com",
            "rubro": "restaurantes",
            "provincia": "Panamá",
            "require_panama": False,
            "pipeline_job_id": "job-no-existe",
        },
    )
    assert r.status_code == 400


def test_agents_run_panama_filter_can_block_non_panama():
    r = client.post(
        "/agents/run",
        json={
            "url": "https://example.com",
            "rubro": "academias",
            "provincia": None,
            "require_panama": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "ok" in data
    if not data["ok"]:
        assert "fuera de criterio Panamá" in data.get("message", "")
