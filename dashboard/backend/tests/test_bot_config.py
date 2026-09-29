import os
import pytest

import bot.config as bot_config
import bot.core.settings_db as settings_db

@pytest.fixture(autouse=True)
def isolated_settings_db(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "test_settings.db"))
    settings_db._cache.clear()
    settings_db.init()

def test_load_config_returns_empty_dict_when_missing():
    assert bot_config.load_config(1) == {}

def test_save_then_load_roundtrips():
    bot_config.save_config(1, {"LOG_CHANNEL_ID": "123"})
    assert bot_config.load_config(1) == {"LOG_CHANNEL_ID": "123"}
    assert bot_config.load_config(2) == {}

def test_get_returns_default_when_key_missing():
    bot_config.save_config(1, {})
    assert bot_config.get(1, "LOG_CHANNEL_ID", "fallback") == "fallback"

def test_get_returns_stored_value():
    bot_config.save_config(1, {"LOG_CHANNEL_ID": "456"})
    assert bot_config.get(1, "LOG_CHANNEL_ID") == "456"


def test_resolve_server_invite_link_returns_trimmed_value():
    bot_config.save_config(1, {"SERVER_INVITE_LINK": " https://discord.gg/test "})
    assert bot_config.resolve_server_invite_link(1) == "https://discord.gg/test"


def test_resolve_server_invite_link_empty_when_unset():
    bot_config.save_config(1, {})
    assert bot_config.resolve_server_invite_link(1) == ""

def test_migrate_from_env_if_needed_creates_from_env(monkeypatch):
    monkeypatch.setenv("LOG_CHANNEL_ID", "100")
    monkeypatch.setenv("WELCOME_CHANNEL_ID", "200")
    bot_config.migrate_from_env_if_needed(1)
    data = bot_config.load_config(1)
    assert data["LOG_CHANNEL_ID"] == "100"
    assert data["WELCOME_CHANNEL_ID"] == "200"

def test_migrate_from_env_if_needed_defaults_missing_keys_to_empty(monkeypatch):
    monkeypatch.delenv("CTD_ROLE_ID", raising=False)
    bot_config.migrate_from_env_if_needed(1)
    data = bot_config.load_config(1)
    assert data["CTD_ROLE_ID"] == ""
    assert data["SPAM_EXCEPTION_CHANNELS"] == []

def test_migrate_from_env_if_needed_skips_if_exists(monkeypatch):
    bot_config.save_config(1, {"LOG_CHANNEL_ID": "existing"})
    monkeypatch.setenv("LOG_CHANNEL_ID", "should_not_overwrite")
    bot_config.migrate_from_env_if_needed(1)
    assert bot_config.load_config(1)["LOG_CHANNEL_ID"] == "existing"

def test_migrate_from_env_if_needed_parses_list_keys_from_comma_separated_env(monkeypatch):
    monkeypatch.setenv("SPAM_EXCEPTION_CHANNELS", "111, 222,333")
    bot_config.migrate_from_env_if_needed(1)
    data = bot_config.load_config(1)
    assert data["SPAM_EXCEPTION_CHANNELS"] == ["111", "222", "333"]
