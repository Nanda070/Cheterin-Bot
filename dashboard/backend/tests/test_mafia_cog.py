"""Tests for MafiaCog's dashboard host overrides: force_advance_phase / force_end_game."""

import time

import pytest

import bot.modules.games.mafia_db as mafia_db
import bot.core.settings_db as settings_db
from bot.modules.games.mafia import MafiaCog
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("MAFIA_DB_PATH", str(tmp_path / "mafia.db"))
    mafia_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build(members=None):
    channel = FakeChannel(500, name="mafia-game")
    guild = FakeGuild(members=members or [], channels=[channel])
    bot = FakeBot(guild)
    cog = MafiaCog(bot)
    bot.get_cog = lambda name: cog if name == "MafiaCog" else None
    return bot, guild, channel, cog


def _setup_game(guild, channel, phase="night", round_number=1, players=None):
    game = mafia_db.create_game(guild.id, channel.id, 10, 5, 20, 60, 120, 60)
    mafia_db.update_game(
        game["id"], status="active", phase=phase, round_number=round_number,
        phase_deadline_ts=int(time.time()) + 60,
    )
    for user_id, role in (players or {}).items():
        mafia_db.add_player(game["id"], user_id)
        mafia_db.assign_player_role(game["id"], user_id, role, f"tok-{user_id}")
    return mafia_db.get_game(game["id"])


def _cleanup_timer(cog, game_id):
    task = cog._timers.get(game_id)
    if task:
        task.cancel()


@pytest.mark.asyncio
async def test_force_advance_phase_night_to_day():
    # Three citizens keep the game going after a night kill (mafia parity not reached yet).
    mafia1 = FakeMember(20, name="mafia1")
    citizen = FakeMember(22, name="citizen")
    citizen2 = FakeMember(23, name="citizen2")
    citizen3 = FakeMember(24, name="citizen3")
    bot, guild, channel, cog = build(members=[mafia1, citizen, citizen2, citizen3])
    game = _setup_game(
        guild, channel, phase="night",
        players={20: "mafia", 22: "citizen", 23: "citizen", 24: "citizen"},
    )

    ok = await cog.force_advance_phase(game["id"])
    assert ok is True

    updated = mafia_db.get_game(game["id"])
    assert updated["phase"] == "day_discussion"
    _cleanup_timer(cog, game["id"])


@pytest.mark.asyncio
async def test_force_advance_phase_returns_false_for_inactive_game():
    bot, guild, channel, cog = build()
    game = mafia_db.create_game(guild.id, channel.id, 10, 5, 20, 60, 120, 60)  # status="lobby"

    ok = await cog.force_advance_phase(game["id"])
    assert ok is False


@pytest.mark.asyncio
async def test_force_advance_phase_returns_false_for_missing_game():
    _, _, _, cog = build()
    ok = await cog.force_advance_phase(999)
    assert ok is False


@pytest.mark.asyncio
async def test_force_end_game_marks_finished_without_winner():
    mafia1 = FakeMember(20, name="mafia1")
    citizen = FakeMember(22, name="citizen")
    bot, guild, channel, cog = build(members=[mafia1, citizen])
    game = _setup_game(guild, channel, phase="day_discussion", players={20: "mafia", 22: "citizen"})

    ok = await cog.force_end_game(game["id"])
    assert ok is True

    updated = mafia_db.get_game(game["id"])
    assert updated["status"] == "finished"
    assert updated["phase"] == "ended"


@pytest.mark.asyncio
async def test_force_end_game_returns_false_for_inactive_game():
    bot, guild, channel, cog = build()
    game = mafia_db.create_game(guild.id, channel.id, 10, 5, 20, 60, 120, 60)  # status="lobby"

    ok = await cog.force_end_game(game["id"])
    assert ok is False
