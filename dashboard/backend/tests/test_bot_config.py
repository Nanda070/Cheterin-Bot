import json

import pytest

import bot_config


@pytest.fixture(autouse=True)
def isolated_config_file(tmp_path, monkeypatch):
    monkeypatch.setattr(bot_config, "CONFIG_FILE", str(tmp_path / "config.json"))


def test_load_config_returns_empty_dict_when_file_missing():
    assert bot_config.load_config() == {}


def test_save_then_load_roundtrips():
    bot_config.save_config({"LOG_CHANNEL_ID": "123"})
    assert bot_config.load_config() == {"LOG_CHANNEL_ID": "123"}


def test_load_config_reads_fresh_after_external_write():
    bot_config.load_config()
    with open(bot_config.CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"LOG_CHANNEL_ID": "999"}, f)
    assert bot_config.load_config() == {"LOG_CHANNEL_ID": "999"}


def test_get_returns_default_when_key_missing():
    bot_config.save_config({})
    assert bot_config.get("LOG_CHANNEL_ID", "fallback") == "fallback"


def test_get_returns_stored_value():
    bot_config.save_config({"LOG_CHANNEL_ID": "456"})
    assert bot_config.get("LOG_CHANNEL_ID") == "456"


def test_migrate_from_env_if_needed_creates_file_from_env(monkeypatch):
    monkeypatch.setenv("LOG_CHANNEL_ID", "100")
    monkeypatch.setenv("WELCOME_CHANNEL_ID", "200")
    bot_config.migrate_from_env_if_needed()
    data = bot_config.load_config()
    assert data["LOG_CHANNEL_ID"] == "100"
    assert data["WELCOME_CHANNEL_ID"] == "200"


def test_migrate_from_env_if_needed_defaults_missing_keys_to_empty(monkeypatch):
    monkeypatch.delenv("CTD_ROLE_ID", raising=False)
    bot_config.migrate_from_env_if_needed()
    data = bot_config.load_config()
    assert data["CTD_ROLE_ID"] == ""
    assert data["SPAM_EXCEPTION_CHANNELS"] == []


def test_migrate_from_env_if_needed_skips_if_file_exists(monkeypatch):
    bot_config.save_config({"LOG_CHANNEL_ID": "existing"})
    monkeypatch.setenv("LOG_CHANNEL_ID", "should_not_overwrite")
    bot_config.migrate_from_env_if_needed()
    assert bot_config.load_config()["LOG_CHANNEL_ID"] == "existing"


def test_migrate_from_env_if_needed_parses_list_keys_from_comma_separated_env(monkeypatch):
    monkeypatch.setenv("SPAM_EXCEPTION_CHANNELS", "111, 222,333")
    bot_config.migrate_from_env_if_needed()
    data = bot_config.load_config()
    assert data["SPAM_EXCEPTION_CHANNELS"] == ["111", "222", "333"]
