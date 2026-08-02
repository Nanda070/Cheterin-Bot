"""Тесты кога OwnerAlertsCog: еженедельный дайджест активности дашборда."""

import time
from datetime import datetime, timezone

import pytest

import owner_alerts_core
import settings_db
import stats_db
import timezone_core
from owner_alerts import OwnerAlertsCog
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember

GUILD_ID = 1


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setenv("STATS_DB_PATH", str(tmp_path / "stats.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    stats_db.init()
    owner_alerts_core._ban_events.clear()
    owner_alerts_core._module_errors.clear()


def build():
    member = FakeMember(20, name="owner")
    channel = FakeChannel(55, name="alerts")
    guild = FakeGuild(guild_id=GUILD_ID, members=[member], channels=[channel])
    bot = FakeBot(guild)
    cog = OwnerAlertsCog(bot)
    cog.perms_loop.cancel()
    cog.weekly_digest_loop.cancel()
    return cog, guild, channel, bot


@pytest.mark.asyncio
async def test_build_weekly_digest_embed_empty():
    cog, guild, _channel, _bot = build()
    embed = cog.build_weekly_digest_embed(guild, 7, "en")
    assert "No dashboard activity" in embed.description


@pytest.mark.asyncio
async def test_build_weekly_digest_embed_groups_actions():
    cog, guild, _channel, _bot = build()
    now = int(time.time())
    stats_db.audit_add(GUILD_ID, now, 10, "mod", "PUT", "/api/economy", "audit.action.economy_balance", 200)
    stats_db.audit_add(GUILD_ID, now, 10, "mod", "PUT", "/api/economy", "audit.action.economy_balance", 200)
    stats_db.audit_add(GUILD_ID, now, 10, "mod", "PUT", "/api/wordle", "audit.action.wordle", 200)

    embed = cog.build_weekly_digest_embed(guild, 7, "en")
    assert "Economy balance" in embed.description
    assert "2×" in embed.description
    assert "Wordle" in embed.description


@pytest.mark.asyncio
async def test_post_weekly_digest_sends_and_marks_posted(monkeypatch):
    monkeypatch.setattr(timezone_core, "now_local", lambda guild_id: datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc))
    cog, guild, channel, _bot = build()
    owner_alerts_core.save_settings(GUILD_ID, {"enabled": True, "weekly_digest_enabled": True, "channel_id": "55"})
    now = int(time.time())
    stats_db.audit_add(GUILD_ID, now, 10, "mod", "PUT", "/api/economy", "audit.action.economy_balance", 200)

    posted = await cog.post_weekly_digest(GUILD_ID)
    assert posted is True
    assert len(channel.send_calls) == 1
    assert channel.send_calls[0]["embed"] is not None

    settings = owner_alerts_core.get_settings(GUILD_ID)
    assert settings["last_weekly_digest_date"]


@pytest.mark.asyncio
async def test_post_weekly_digest_false_without_channel():
    cog, _guild, _channel, _bot = build()
    owner_alerts_core.save_settings(GUILD_ID, {"enabled": True, "weekly_digest_enabled": True, "channel_id": ""})

    posted = await cog.post_weekly_digest(GUILD_ID)
    assert posted is False
