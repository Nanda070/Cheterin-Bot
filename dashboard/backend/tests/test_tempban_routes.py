import pytest

import bot.config as bot_config
import bot.core.settings_db as settings_db
import bot.modules.moderation.tempban_core as tempban_core
from dashboard.backend.routes.tempban_settings import routes as tempban_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build(channels=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator], channels=channels or [])
    bot = FakeBot(guild)
    return make_moderation_app(bot, [tempban_routes]), bot, guild


@pytest.mark.asyncio
async def test_get_includes_new_fields(aiohttp_client):
    app, _, _ = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/tempban-settings")
    assert resp.status == 200
    body = await resp.json()
    assert body["action"] == "softban"
    assert body["ban_count"] == 0
    assert "warning_message" in body
    assert "log_message" in body


@pytest.mark.asyncio
async def test_put_action_mode(aiohttp_client):
    app, _, _ = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/tempban-settings",
        json={
            "action": "ban",
            "dm_enabled": True,
            "dm_message": "bye {guild}",
            "log_enabled": True,
            "log_message": "Log {name}",
            "unban_reason": "",
            "warning_message": "Warn\n\nBody {action}",
            "warning_thumbnail_url": "",
        },
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["action"] == "ban"
    assert body["log_message"] == "Log {name}"


@pytest.mark.asyncio
async def test_put_invalid_action(aiohttp_client):
    app, _, _ = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/tempban-settings",
        json={
            "action": "explode",
            "dm_enabled": True,
            "dm_message": "",
            "log_enabled": True,
            "log_message": "",
            "unban_reason": "",
            "warning_message": "",
            "warning_thumbnail_url": "",
        },
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_put_without_action_preserves_existing_mode(aiohttp_client):
    app, _, guild = build()
    tempban_core.save_settings(
        guild.id,
        {
            "action": "ban",
            "dm_enabled": True,
            "dm_message": "",
            "log_enabled": True,
            "log_message": "",
            "unban_reason": "",
            "warning_message": "",
            "warning_thumbnail_url": "",
        },
    )
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/tempban-settings",
        json={
            "dm_enabled": False,
            "dm_message": "updated",
            "log_enabled": True,
            "log_message": "",
            "unban_reason": "",
            "warning_message": "",
            "warning_thumbnail_url": "",
        },
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["action"] == "ban"
    assert body["dm_enabled"] is False
    assert body["dm_message"] == "updated"


@pytest.mark.asyncio
async def test_publish_warning(aiohttp_client, monkeypatch):
    trap = FakeChannel(77, name="trap")
    app, bot, guild = build(channels=[trap])
    monkeypatch.setattr(bot_config, "get", lambda gid, key, default=None: "77" if key == "TEMPBAN_CHANNEL_ID" else default)

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/tempban-settings/publish-warning", json={})
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert body["message_id"]
    assert trap.send_calls
    settings = tempban_core.get_settings(guild.id)
    assert settings["warning_message_id"] == body["message_id"]
