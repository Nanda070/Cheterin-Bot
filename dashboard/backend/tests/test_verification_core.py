"""Тесты ядра верификации: настройки (выключена по умолчанию), проверка конфигурации, re-verify."""

from datetime import datetime, timedelta, timezone

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
    assert settings["rules_consent_enabled"] is False
    assert settings["reverify_enabled"] is False
    assert settings["reverify_days"] == verification_core.DEFAULT_REVERIFY_DAYS


def test_welcome_text_follows_guild_language():
    import language_core

    language_core.set_language(GUILD_ID, "en")
    settings = verification_core.get_settings(GUILD_ID)
    assert "Click the button" in settings["welcome_text"]


def test_rules_panel_text_when_rules_consent_enabled():
    import language_core

    language_core.set_language(GUILD_ID, "en")
    verification_core.save_config(GUILD_ID, {
        "enabled": True,
        "rules_consent_enabled": True,
        "verified_role_id": "222",
    })
    settings = verification_core.get_settings(GUILD_ID)
    assert "accept them" in settings["welcome_text"].lower()


def test_settings_roundtrip():
    verification_core.save_config(GUILD_ID, {
        "enabled": True,
        "unverified_role_id": "111",
        "verified_role_id": "222",
        "welcome_text": "Жми кнопку",
        "rules_consent_enabled": True,
        "reverify_enabled": True,
        "reverify_days": 14,
    })
    settings = verification_core.get_settings(GUILD_ID)
    assert settings["enabled"] is True
    assert settings["unverified_role_id"] == "111"
    assert settings["verified_role_id"] == "222"
    assert settings["welcome_text"] == "Жми кнопку"
    assert settings["rules_consent_enabled"] is True
    assert settings["reverify_enabled"] is True
    assert settings["reverify_days"] == 14


def test_clamp_reverify_days():
    assert verification_core.clamp_reverify_days(0) == 1
    assert verification_core.clamp_reverify_days(999) == 365
    assert verification_core.clamp_reverify_days("nope") == verification_core.DEFAULT_REVERIFY_DAYS


def test_is_configured_requires_verified_role():
    settings = verification_core.get_settings(GUILD_ID)
    assert verification_core.is_configured(settings) is False

    verification_core.save_config(GUILD_ID, {"enabled": True, "verified_role_id": "222"})
    assert verification_core.is_configured(verification_core.get_settings(GUILD_ID)) is True


def test_is_configured_does_not_require_unverified_role():
    verification_core.save_config(GUILD_ID, {"enabled": True, "verified_role_id": "222", "unverified_role_id": ""})
    assert verification_core.is_configured(verification_core.get_settings(GUILD_ID)) is True


def test_consent_expiry():
    settings = {
        "reverify_enabled": True,
        "reverify_days": 7,
    }
    now = datetime(2026, 7, 24, tzinfo=timezone.utc)
    fresh = (now - timedelta(days=3)).isoformat()
    stale = (now - timedelta(days=8)).isoformat()
    assert verification_core.is_consent_expired(fresh, settings, now=now) is False
    assert verification_core.is_consent_expired(stale, settings, now=now) is True
    assert verification_core.has_valid_consent({"verified_at": fresh}, settings, now=now) is True
    assert verification_core.has_valid_consent({"verified_at": stale}, settings, now=now) is False

    settings_off = {"reverify_enabled": False, "reverify_days": 7}
    assert verification_core.is_consent_expired(stale, settings_off, now=now) is False
