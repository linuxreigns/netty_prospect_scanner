from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_pipeline_can_return_hot_agent_runs_mapping():
    r = client.post(
        "/pipeline/discover-scan-export",
        json={
            "rubro": "restaurantes",
            "provincia": "Panamá",
            "limit": 10,
            "min_hot_score": 0,
            "run_agents_for_hot": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "hot_agent_runs" in data
    assert isinstance(data["hot_agent_runs"], list)
