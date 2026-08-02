import pytest

import settings_db
import starboard_core
from dashboard.backend.routes.starboard import routes as starboard_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    bot = FakeBot(guild)
    return bot, guild, make_moderation_app(bot, [starboard_routes])


@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/starboard")
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is False
    assert body["emoji"] == "⭐"
    assert body["threshold"] == 3


@pytest.mark.asyncio
async def test_put_then_get(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/starboard", json={
        "enabled": True,
        "channel_id": "555",
        "emoji": "🔥",
        "threshold": 4,
        "self_star": True,
        "ignore_nsfw": True,
    })
    assert resp.status == 200
    body = await resp.json()
    assert body["channel_id"] == "555"
    assert body["threshold"] == 4

    assert starboard_core.get_settings(1)["emoji"] == "🔥"


@pytest.mark.asyncio
async def test_put_requires_channel_when_enabled(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/starboard", json={
        "enabled": True,
        "channel_id": "",
        "emoji": "⭐",
        "threshold": 3,
        "self_star": False,
        "ignore_nsfw": False,
    })
    assert resp.status == 400
