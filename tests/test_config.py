from pathlib import Path

from app.config import DEFAULT_APP_NAME, DEFAULT_DATABASE_URL, load_settings


def test_default_configuration_matches_previous_constants(monkeypatch):
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LEAVE_DATA_DIR", raising=False)

    settings = load_settings()

    assert settings.app_name == DEFAULT_APP_NAME == "leave-app"
    assert settings.database_url == DEFAULT_DATABASE_URL == "sqlite:///./data/leave.db"
    assert settings.data_dir == Path("data")


def test_configuration_reads_environment(monkeypatch):
    monkeypatch.setenv("APP_NAME", "custom-leave")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./custom.db")
    monkeypatch.setenv("LEAVE_DATA_DIR", "custom-data")

    settings = load_settings()

    assert settings.app_name == "custom-leave"
    assert settings.database_url == "sqlite:///./custom.db"
    assert settings.data_dir == Path("custom-data")


def test_data_dir_sets_database_url_when_url_is_absent(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("LEAVE_DATA_DIR", "custom-data")

    settings = load_settings()

    assert settings.database_url == "sqlite:///custom-data/leave.db"
    assert settings.data_dir == Path("custom-data")


def test_pages_use_configured_application_name(client, monkeypatch):
    monkeypatch.setenv("APP_NAME", "northwind-leave")

    landing = client.get("/")
    register = client.get("/register")

    assert "northwind-leave" in landing.text
    assert 'data-testid="landing-title"' in landing.text
    assert "northwind-leave" in register.text
    assert 'data-testid="register-form"' in register.text
