import pytest

import settings_db
from dashboard.backend.routes.auto_reactions import routes as auto_reactions_routes
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
    return make_moderation_app(bot, [auto_reactions_routes])


@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/auto-reactions")
    assert resp.status == 200
    assert await resp.json() == {"enabled": False, "rules": []}


@pytest.mark.asyncio
async def test_put_rules(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-reactions", json={
        "enabled": True,
        "rules": [{
            "id": "r1",
            "emoji_mode": "list",
            "emojis": ["👍", "<:x:1>"],
            "keywords": ["hi"],
            "channel_mode": "all",
            "channel_ids": [],
            "exclude_channel_ids": ["9"],
            "ignore_bots": True,
        }],
    })
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is True
    assert len(body["rules"]) == 1
    assert body["rules"][0]["emoji_mode"] == "list"
    assert body["rules"][0]["exclude_channel_ids"] == ["9"]


@pytest.mark.asyncio
async def test_put_all_guild_emoji_mode(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-reactions", json={
        "enabled": True,
        "rules": [{
            "id": "r1",
            "emoji_mode": "all_guild",
            "emojis": [],
            "keywords": [],
            "channel_mode": "all",
            "channel_ids": [],
            "exclude_channel_ids": [],
            "ignore_bots": True,
        }],
    })
    assert resp.status == 200
    body = await resp.json()
    assert body["rules"][0]["emoji_mode"] == "all_guild"
    assert body["rules"][0]["emojis"] == []


@pytest.mark.asyncio
async def test_put_include_requires_channels(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-reactions", json={
        "enabled": True,
        "rules": [{
            "id": "r1",
            "emojis": ["👍"],
            "keywords": [],
            "channel_mode": "include",
            "channel_ids": [],
            "exclude_channel_ids": [],
            "ignore_bots": True,
        }],
    })
    assert resp.status == 400
