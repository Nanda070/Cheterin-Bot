import pytest

import i18n
import language_core
import settings_db


def test_t_returns_russian_by_default():
    assert i18n.t("error.module_disabled") == "Модуль отключён."


def test_t_returns_english_when_requested():
    assert i18n.t("error.module_disabled", "en") == "This module is disabled."


def test_t_formats_placeholders():
    assert i18n.t("welcome.title", "ru", guild_name="Test") == "Добро пожаловать на Test!"


def test_t_falls_back_to_key_for_unknown():
    assert i18n.t("missing.key", "en") == "missing.key"


def test_t_falls_back_to_russian_for_unknown_lang():
    assert i18n.t("error.module_disabled", "fr") == "Модуль отключён."


def test_module_disabled_named():
    assert "Развлечения" in i18n.module_disabled("ru", "fun")
    assert "Fun" in i18n.module_disabled("en", "fun")


def test_guild_t_uses_server_language(monkeypatch, tmp_path):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    settings_db.init()
    language_core.set_language(42, "en")
    assert i18n.guild_t(42, "verification.success").startswith("✅ Welcome")


def test_pick_random_returns_known_key():
    text = i18n.pick_random("fun.roulette.intro", "ru", 6)
    assert text.endswith("…")
