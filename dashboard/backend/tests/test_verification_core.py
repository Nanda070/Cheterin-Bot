"""Тесты ядра верификации: настройки (выключена по умолчанию), проверка конфигурации."""

import pytest

import verification_core


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(verification_core, "CONFIG_FILE", str(tmp_path / "verification_config.json"))
    monkeypatch.setattr(verification_core, "_cache", None, raising=False)
    monkeypatch.setattr(verification_core, "_cache_mtime", None, raising=False)


def test_settings_disabled_by_default():
    settings = verification_core.get_settings()
    assert settings["enabled"] is False
    assert settings["unverified_role_id"] == 0
    assert settings["verified_role_id"] == 0
    assert settings["welcome_text"] == verification_core.DEFAULT_WELCOME_TEXT


def test_settings_roundtrip():
    verification_core.save_config({
        "enabled": True, "unverified_role_id": 111, "verified_role_id": 222, "welcome_text": "Жми кнопку",
    })
    settings = verification_core.get_settings()
    assert settings["enabled"] is True
    assert settings["unverified_role_id"] == 111
    assert settings["verified_role_id"] == 222
    assert settings["welcome_text"] == "Жми кнопку"


def test_is_configured_requires_verified_role():
    settings = verification_core.get_settings()
    assert verification_core.is_configured(settings) is False

    verification_core.save_config({"enabled": True, "verified_role_id": 222})
    assert verification_core.is_configured(verification_core.get_settings()) is True


def test_is_configured_does_not_require_unverified_role():
    verification_core.save_config({"enabled": True, "verified_role_id": 222, "unverified_role_id": 0})
    assert verification_core.is_configured(verification_core.get_settings()) is True
