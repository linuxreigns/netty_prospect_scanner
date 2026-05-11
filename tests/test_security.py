from fastapi.testclient import TestClient

import app.auth as auth_module
from app.main import app
from app.scanner.crawler import is_blocked_target

client = TestClient(app)


def test_ssrf_targets_are_blocked():
    assert is_blocked_target("http://localhost") is True
    assert is_blocked_target("http://127.0.0.1") is True


def test_scan_csv_rejects_outside_data_dir_and_non_csv():
    r1 = client.post("/scan/csv", json={"csv_path": "../etc/passwd"})
    assert r1.status_code == 400

    r2 = client.post("/scan/csv", json={"csv_path": "data/input_urls.txt"})
    assert r2.status_code == 400


# --- Auth ---


def test_auth_disabled_by_default():
    """Sin API_KEY configurada, endpoints protegidos responden normalmente."""
    assert auth_module.settings.api_key is None
    r = client.post("/scan/csv", json={"csv_path": "data/input_urls.csv"})
    assert r.status_code != 403


def test_auth_blocks_missing_key(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "api_key", "clave-secreta")
    r = client.post("/scan/csv", json={"csv_path": "data/input_urls.csv"})
    assert r.status_code == 403


def test_auth_blocks_wrong_key(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "api_key", "clave-secreta")
    r = client.post(
        "/scan/csv",
        json={"csv_path": "data/input_urls.csv"},
        headers={"X-API-Key": "clave-incorrecta"},
    )
    assert r.status_code == 403


def test_auth_allows_correct_key(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "api_key", "clave-secreta")
    r = client.post(
        "/scan/csv",
        json={"csv_path": "data/input_urls.csv"},
        headers={"X-API-Key": "clave-secreta"},
    )
    assert r.status_code != 403


def test_public_endpoints_need_no_key(monkeypatch):
    """Dashboard y discovery no requieren API key aunque esté configurada."""
    monkeypatch.setattr(auth_module.settings, "api_key", "clave-secreta")
    assert client.get("/").status_code == 200
    assert client.get("/dashboard/summary").status_code == 200
    assert client.get("/discovery/search?rubro=restaurantes&provincia=Panamá").status_code == 200
