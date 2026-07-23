import custom_commands_core
import settings_db

import pytest

GUILD_ID = 404


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_get_settings_defaults():
    assert custom_commands_core.get_settings(GUILD_ID) == {"enabled": False, "commands": []}


def test_add_update_delete_and_match():
    assert custom_commands_core.update_enabled(GUILD_ID, True)["enabled"] is True
    cmd = custom_commands_core.add_command(
        GUILD_ID, trigger="hello", match="exact", reply_text="world"
    )
    assert cmd is not None
    assert cmd["id"] == "1"
    assert cmd["trigger"] == "hello"

    updated = custom_commands_core.update_command(GUILD_ID, "1", reply_text="hi", match="contains")
    assert updated["reply_text"] == "hi"
    assert updated["match"] == "contains"

    assert custom_commands_core.match_message(GUILD_ID, "say hello please")["id"] == "1"
    assert custom_commands_core.match_message(GUILD_ID, "Say Hello please")["id"] == "1"

    assert custom_commands_core.delete_command(GUILD_ID, "1") is True
    assert custom_commands_core.get_settings(GUILD_ID)["commands"] == []
    assert custom_commands_core.match_message(GUILD_ID, "hello") is None


def test_max_commands_limit(monkeypatch):
    monkeypatch.setattr(custom_commands_core, "MAX_COMMANDS", 2)
    assert custom_commands_core.add_command(GUILD_ID, trigger="a", reply_text="1") is not None
    assert custom_commands_core.add_command(GUILD_ID, trigger="b", reply_text="2") is not None
    assert custom_commands_core.add_command(GUILD_ID, trigger="c", reply_text="3") is None


def test_exact_match_priority():
    custom_commands_core.update_enabled(GUILD_ID, True)
    custom_commands_core.add_command(GUILD_ID, trigger="ping", match="exact", reply_text="exact")
    custom_commands_core.add_command(GUILD_ID, trigger="ping", match="contains", reply_text="contains")
    matched = custom_commands_core.match_message(GUILD_ID, "ping")
    assert matched["reply_text"] == "exact"
