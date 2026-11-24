import pytest
from fastapi.testclient import TestClient

from app.database import init_database, reset_database_state
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database_file = tmp_path / "leave.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_file.as_posix()}")
    reset_database_state()
    init_database()
    with TestClient(app) as test_client:
        yield test_client
    reset_database_state()
