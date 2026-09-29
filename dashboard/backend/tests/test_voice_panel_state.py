"""Тесты состояния панели голосовых комнат (voice_rooms) — per-guild в settings_db."""

import pytest

import bot.core.settings_db as settings_db
import bot.modules.voice.voice_rooms as voice_rooms


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setenv("GUILD_ID", "404")
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_panel_state_defaults_empty():
    assert voice_rooms.load_panel_state(404) == {}


def test_panel_state_round_trip():
    voice_rooms.save_panel_state({"message_id": 123, "channel_id": 456}, guild_id=404)
    state = voice_rooms.load_panel_state(404)
    assert state["message_id"] == 123
    assert state["channel_id"] == 456


def test_panel_state_is_per_guild():
    voice_rooms.save_panel_state({"message_id": 1, "channel_id": 10}, guild_id=100)
    voice_rooms.save_panel_state({"message_id": 2, "channel_id": 20}, guild_id=200)
    assert voice_rooms.load_panel_state(100)["message_id"] == 1
    assert voice_rooms.load_panel_state(200)["message_id"] == 2


@pytest.mark.asyncio
async def test_on_ready_publishes_panel_for_each_guild(monkeypatch):
    published: list[int] = []

    class FakeGuild:
        def __init__(self, guild_id: int):
            self.id = guild_id

    class FakeBot:
        def __init__(self):
            self.guilds = [FakeGuild(10), FakeGuild(20)]
            self.views = []

        def add_view(self, view):
            self.views.append(view)

    bot = FakeBot()
    cog = voice_rooms.PanelManager(bot)

    async def fake_publish(guild_id: int):
        published.append(guild_id)
        return None

    monkeypatch.setattr(cog, "publish_panel", fake_publish)
    await cog.on_ready()

    assert published == [10, 20]
    assert len(bot.views) == 1
    # Second on_ready must not re-publish.
    await cog.on_ready()
    assert published == [10, 20]
