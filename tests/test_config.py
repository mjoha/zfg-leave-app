from pathlib import Path

from app.config import DEFAULT_APP_NAME, DEFAULT_DATABASE_URL, load_settings


def test_default_configuration_matches_previous_constants(monkeypatch):
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LEAVE_DATA_DIR", raising=False)
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    monkeypatch.delenv("SESSION_HTTPS_ONLY", raising=False)

    settings = load_settings()

    assert settings.app_name == DEFAULT_APP_NAME == "leave-app"
    assert settings.database_url == DEFAULT_DATABASE_URL == "sqlite:///./data/leave.db"
    assert settings.data_dir == Path("data")
    assert settings.session_secret == "test-session-secret"
    assert settings.session_https_only is False
    assert settings.session_max_age == 8 * 60 * 60


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


def test_session_secret_is_generated_once_beside_the_data_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    monkeypatch.setenv("LEAVE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'leave.db').as_posix()}")

    from app.config import load_settings

    first = load_settings()
    second = load_settings()

    assert first.session_secret == second.session_secret
    assert len(first.session_secret) >= 32
    assert (tmp_path / "session_secret").read_text(encoding="utf-8").strip() == first.session_secret


def test_session_https_only_follows_environment(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("SESSION_HTTPS_ONLY", "true")

    from app.config import load_settings

    assert load_settings().session_https_only is True


def test_pages_use_configured_application_name(client, monkeypatch):
    monkeypatch.setenv("APP_NAME", "northwind-leave")

    landing = client.get("/")
    register = client.get("/register")

    assert "northwind-leave" in landing.text
    assert 'data-testid="landing-title"' in landing.text
    assert "northwind-leave" in register.text
    assert 'data-testid="register-form"' in register.text
