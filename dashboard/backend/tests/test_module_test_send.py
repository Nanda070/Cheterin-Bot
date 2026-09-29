import pytest

import bot.config as bot_config
import bot.modules.community.sticky_core as sticky_core
from dashboard.backend.routes.sticky import routes as sticky_routes
from dashboard.backend.routes.welcome import routes as welcome_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)
from bot.modules.community.sticky import StickyCog


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    import bot.core.settings_db as settings_db

    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


@pytest.mark.asyncio
async def test_welcome_test_sends_to_channel(aiohttp_client):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    channel = FakeChannel(500, name="welcome")
    guild = FakeGuild(members=[moderator], channels=[channel])
    bot_config.save_config(1, {"WELCOME_CHANNEL_ID": "500"})
    app = make_moderation_app(FakeBot(guild), [welcome_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/welcome-settings/test", json={"target": "channel"})
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert body["sent"]["channel"] is True
    assert channel.send_calls
    assert "Test" in (channel.send_calls[0].get("content") or "") or "тест" in (
        channel.send_calls[0].get("content") or ""
    ).lower() or "🧪" in (channel.send_calls[0].get("content") or "")


@pytest.mark.asyncio
async def test_welcome_test_requires_channel(aiohttp_client):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    app = make_moderation_app(FakeBot(guild), [welcome_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/welcome-settings/test", json={"target": "channel"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "welcome_channel_not_set"


@pytest.mark.asyncio
async def test_sticky_test_refreshes_message(aiohttp_client):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    channel = FakeChannel(77, name="rules")
    guild = FakeGuild(members=[moderator], channels=[channel])
    bot = FakeBot(guild)
    cog = StickyCog(bot)
    bot.get_cog = lambda name: cog if name == "StickyCog" else None

    sticky_core.update_enabled(1, True)
    sticky = sticky_core.upsert_sticky(1, channel_id="77", content="Stay sticky")
    assert sticky is not None

    app = make_moderation_app(bot, [sticky_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(f"/api/sticky/{sticky['id']}/test")
    assert resp.status == 200
    assert channel.send_calls
    assert channel.send_calls[0].get("content") == "Stay sticky"


@pytest.mark.asyncio
async def test_sticky_test_reports_send_failure(aiohttp_client):
    import discord

    moderator = FakeMember(10, name="mod", role_ids=[111])
    channel = FakeChannel(77, name="rules")
    channel.send_raises = discord.HTTPException.__new__(discord.HTTPException)
    guild = FakeGuild(members=[moderator], channels=[channel])
    bot = FakeBot(guild)
    cog = StickyCog(bot)
    bot.get_cog = lambda name: cog if name == "StickyCog" else None

    sticky_core.update_enabled(1, True)
    sticky = sticky_core.upsert_sticky(1, channel_id="77", content="Stay sticky")
    sticky_core.set_message_id(1, sticky["id"], "42")
    sticky = sticky_core.get_sticky(1, sticky["id"])

    app = make_moderation_app(bot, [sticky_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(f"/api/sticky/{sticky['id']}/test")
    assert resp.status == 502
    assert (await resp.json())["error"] == "send_failed"
    # Old sticky id must remain when send fails
    assert sticky_core.get_sticky(1, sticky["id"])["message_id"] == "42"
