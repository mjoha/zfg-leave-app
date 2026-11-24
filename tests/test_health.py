from fastapi.testclient import TestClient

from app.database import reset_database_state
from app.main import app


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"].startswith("application/json")
    assert "leave_session" not in response.headers.get("set-cookie", "")


def test_health_does_not_require_a_database(tmp_path, monkeypatch):
    database_file = tmp_path / "missing-dir" / "leave.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_file.as_posix()}")
    reset_database_state()
    try:
        with TestClient(app) as bare_client:
            response = bare_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert not database_file.exists()
    finally:
        reset_database_state()
