"""Тест slash-команды тестовой «Мафии» с ботами."""

import pytest

import mafia_core
import mafia_db
import settings_db
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember
from mafia import MafiaCog


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("MAFIA_DB_PATH", str(tmp_path / "mafia.db"))
    mafia_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    monkeypatch.setenv("DASHBOARD_FRONTEND_URL", "https://dash.example")


class _FakeResponse:
    def __init__(self):
        self.messages = []
        self.deferred = False

    async def send_message(self, content=None, embed=None, view=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "embed": embed, "view": view, "ephemeral": ephemeral})

    async def defer(self, ephemeral=False, **kwargs):
        self.deferred = True


class _FakeFollowup:
    def __init__(self):
        self.messages = []

    async def send(self, content=None, embed=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "embed": embed, "ephemeral": ephemeral})


class _FakeInteraction:
    def __init__(self, user, guild, channel):
        self.user = user
        self.guild = guild
        self.guild_id = guild.id
        self.channel = channel
        self.response = _FakeResponse()
        self.followup = _FakeFollowup()


def _cleanup_timer(cog, game_id):
    task = cog._timers.get(game_id)
    if task:
        task.cancel()


@pytest.mark.asyncio
async def test_start_test_game_fills_bots_and_returns_link():
    admin = FakeMember(10, name="admin", manage_guild=True)
    channel = FakeChannel(500, name="mafia-test")
    guild = FakeGuild(members=[admin], channels=[channel])
    bot = FakeBot(guild)
    cog = MafiaCog(bot)
    mafia_core.save_config(guild.id, {"enabled": True})

    interaction = _FakeInteraction(admin, guild, channel)
    await MafiaCog.start_test_game.callback(cog, interaction, 5)

    try:
        game = mafia_db.get_active_game_in_channel(channel.id)
        assert game is not None
        assert game["status"] == "active"
        assert game["phase"] == "night"
        assert bool(game["is_test"]) is True

        players = mafia_db.list_players(game["id"])
        assert len(players) == 5
        host = mafia_db.get_player(game["id"], admin.id)
        assert host["token"]
        assert host["role"]
        bots = [p for p in players if p["user_id"] != admin.id]
        assert len(bots) == 4
        assert all(p["user_id"] < 0 for p in bots)
        assert all(p.get("display_name") for p in bots)
        assert all(p.get("avatar_url") for p in bots)
        assert all(p.get("role") for p in players)

        assert interaction.response.deferred is True
        text = interaction.followup.messages[0]["content"]
        assert host["token"] in text
        assert channel.send_calls
        assert "TEST" in channel.send_calls[0]["embed"].title or "ТЕСТ" in channel.send_calls[0]["embed"].title
    finally:
        active = mafia_db.get_active_game_in_channel(channel.id)
        if active:
            _cleanup_timer(cog, active["id"])
