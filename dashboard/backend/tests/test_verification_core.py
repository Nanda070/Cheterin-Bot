"""Тесты ядра верификации: настройки (выключена по умолчанию), проверка конфигурации."""

import pytest

import settings_db
import verification_core

GUILD_ID = 404


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_settings_disabled_by_default():
    settings = verification_core.get_settings(GUILD_ID)
    assert settings["enabled"] is False
    assert settings["unverified_role_id"] == ""
    assert settings["verified_role_id"] == ""
    assert settings["welcome_text"] == verification_core.resolve_welcome_text(GUILD_ID, "")


def test_welcome_text_follows_guild_language():
    import language_core

    language_core.set_language(GUILD_ID, "en")
    settings = verification_core.get_settings(GUILD_ID)
    assert "Click the button" in settings["welcome_text"]


def test_settings_roundtrip():
    verification_core.save_config(GUILD_ID, {
        "enabled": True, "unverified_role_id": "111", "verified_role_id": "222", "welcome_text": "Жми кнопку",
    })
    settings = verification_core.get_settings(GUILD_ID)
    assert settings["enabled"] is True
    assert settings["unverified_role_id"] == "111"
    assert settings["verified_role_id"] == "222"
    assert settings["welcome_text"] == "Жми кнопку"


def test_is_configured_requires_verified_role():
    settings = verification_core.get_settings(GUILD_ID)
    assert verification_core.is_configured(settings) is False

    verification_core.save_config(GUILD_ID, {"enabled": True, "verified_role_id": "222"})
    assert verification_core.is_configured(verification_core.get_settings(GUILD_ID)) is True


def test_is_configured_does_not_require_unverified_role():
    verification_core.save_config(GUILD_ID, {"enabled": True, "verified_role_id": "222", "unverified_role_id": ""})
    assert verification_core.is_configured(verification_core.get_settings(GUILD_ID)) is True
