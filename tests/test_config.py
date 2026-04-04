"""
Tests for the Settings configuration class.

Each test that modifies environment variables creates a fresh Settings instance
to verify validation behavior. The globally imported `settings` from the
config module is not reloaded to avoid side effects between tests.
"""
import importlib

import pytest

from app.core import config as config_module


def _fresh_settings(monkeypatch, env_updates=None):
    """
    Reload the config module and return a new Settings instance.

    env_updates: dict of env var name -> value (set via monkeypatch)
    None values in the dict will be deleted from the environment.
    """
    if env_updates:
        for key, value in env_updates.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)

    # Also clear the .env file source so only env vars are used
    monkeypatch.setenv("PYDANTIC_SETTINGS_DOTENV_FILE", "")

    importlib.reload(config_module)
    return config_module.Settings()


class TestSettingsLoading:
    def test_settings_loads_with_valid_env(self, monkeypatch):
        """Settings should load correctly when all required env vars are set."""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing")
        monkeypatch.setenv("POSTGRES_PASSWORD", "test-db-password")
        monkeypatch.setenv("FIRST_SUPERUSER_PASSWORD", "test-superuser-password")

        settings = _fresh_settings(monkeypatch)

        assert settings.SECRET_KEY == "test-secret-key-for-testing"
        assert settings.SERVER_HOST == "http://localhost"
        assert settings.API_VERSION == "1"
        assert settings.PROJECT_NAME == "Myths and Legends API"

    def test_database_uri_is_assembled(self, monkeypatch):
        """SQLALCHEMY_DATABASE_URI should be built from PostgresDsn components."""
        monkeypatch.setenv("SECRET_KEY", "test-secret-key")
        monkeypatch.setenv("POSTGRES_PASSWORD", "db-pass")
        monkeypatch.setenv("FIRST_SUPERUSER_PASSWORD", "super-pass")
        monkeypatch.setenv("POSTGRES_HOST", "my-db-host")
        monkeypatch.setenv("POSTGRES_USER", "my-user")
        monkeypatch.setenv("POSTGRES_DB", "my-db")

        settings = _fresh_settings(monkeypatch)

        assert "my-db-host" in str(settings.SQLALCHEMY_DATABASE_URI)
        assert "my-user" in str(settings.SQLALCHEMY_DATABASE_URI)
        assert "my-db" in str(settings.SQLALCHEMY_DATABASE_URI)


class TestRequiredSecretsValidation:
    def test_raises_when_secret_key_missing(self, monkeypatch):
        """Missing SECRET_KEY should raise ValueError with a helpful message."""
        monkeypatch.setenv("SECRET_KEY", "")
        monkeypatch.setenv("POSTGRES_PASSWORD", "db-pass")
        monkeypatch.setenv("FIRST_SUPERUSER_PASSWORD", "super-pass")

        with pytest.raises(ValueError, match="SECRET_KEY is required"):
            _fresh_settings(monkeypatch)

    def test_raises_when_postgres_password_missing(self, monkeypatch):
        """Missing POSTGRES_PASSWORD should raise ValueError."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("POSTGRES_PASSWORD", "")
        monkeypatch.setenv("FIRST_SUPERUSER_PASSWORD", "super-pass")

        with pytest.raises(ValueError, match="POSTGRES_PASSWORD is required"):
            _fresh_settings(monkeypatch)

    def test_raises_when_superuser_password_missing(self, monkeypatch):
        """Missing FIRST_SUPERUSER_PASSWORD should raise ValueError."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("POSTGRES_PASSWORD", "db-pass")
        monkeypatch.setenv("FIRST_SUPERUSER_PASSWORD", "")

        with pytest.raises(ValueError, match="FIRST_SUPERUSER_PASSWORD is required"):
            _fresh_settings(monkeypatch)


class TestCorsOriginsParsing:
    def test_parses_comma_separated_string(self, monkeypatch):
        """BACKEND_CORS_ORIGINS should parse a comma-separated string via the validator."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("POSTGRES_PASSWORD", "db-pass")
        monkeypatch.setenv("FIRST_SUPERUSER_PASSWORD", "super-pass")
        # Use JSON format which pydantic-settings handles natively
        monkeypatch.setenv(
            "BACKEND_CORS_ORIGINS",
            '["http://example.com","http://test.com","http://api.com"]',
        )

        settings = _fresh_settings(monkeypatch)

        assert settings.BACKEND_CORS_ORIGINS == [
            "http://example.com",
            "http://test.com",
            "http://api.com",
        ]

    def test_accepts_list_format(self, monkeypatch):
        """BACKEND_CORS_ORIGINS should accept a JSON-formatted list."""
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("POSTGRES_PASSWORD", "db-pass")
        monkeypatch.setenv("FIRST_SUPERUSER_PASSWORD", "super-pass")
        monkeypatch.setenv("BACKEND_CORS_ORIGINS", '["http://example.com"]')

        settings = _fresh_settings(monkeypatch)

        assert settings.BACKEND_CORS_ORIGINS == ["http://example.com"]
