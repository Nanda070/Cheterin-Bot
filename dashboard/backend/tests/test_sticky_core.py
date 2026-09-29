import pytest

import bot.core.settings_db as settings_db
import bot.modules.community.sticky_core as sticky_core

GUILD_ID = 501


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_get_settings_defaults():
    assert sticky_core.get_settings(GUILD_ID) == {"enabled": False, "stickies": []}


def test_upsert_replace_per_channel_and_delete():
    sticky_core.update_enabled(GUILD_ID, True)
    first = sticky_core.upsert_sticky(GUILD_ID, channel_id="100", content="hello")
    assert first is not None
    assert first["id"] == "1"
    assert first["content"] == "hello"

    replaced = sticky_core.upsert_sticky(GUILD_ID, channel_id="100", content="updated")
    assert replaced["id"] == "1"
    assert replaced["content"] == "updated"
    assert len(sticky_core.get_settings(GUILD_ID)["stickies"]) == 1

    second = sticky_core.upsert_sticky(GUILD_ID, channel_id="200", content="other")
    assert second["id"] == "2"
    assert sticky_core.sticky_for_channel(GUILD_ID, 100)["content"] == "updated"
    assert sticky_core.sticky_for_channel(GUILD_ID, "200")["id"] == "2"

    sticky_core.set_message_id(GUILD_ID, "1", "999")
    assert sticky_core.get_settings(GUILD_ID)["stickies"][0]["message_id"] == "999"

    assert sticky_core.delete_sticky(GUILD_ID, "1") is True
    assert sticky_core.sticky_for_channel(GUILD_ID, 100) is None
    assert sticky_core.delete_sticky(GUILD_ID, "1") is False


def test_disabled_module_hides_sticky():
    sticky_core.upsert_sticky(GUILD_ID, channel_id="1", content="x")
    sticky_core.update_enabled(GUILD_ID, False)
    assert sticky_core.sticky_for_channel(GUILD_ID, 1) is None


def test_max_stickies(monkeypatch):
    monkeypatch.setattr(sticky_core, "MAX_STICKIES", 1)
    sticky_core.update_enabled(GUILD_ID, True)
    assert sticky_core.upsert_sticky(GUILD_ID, channel_id="1", content="a") is not None
    assert sticky_core.upsert_sticky(GUILD_ID, channel_id="2", content="b") is None
