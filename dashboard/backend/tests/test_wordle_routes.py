import pytest

import wordle_core
from dashboard.backend.routes.wordle import routes as wordle_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(wordle_core, "CONFIG_FILE", str(tmp_path / "wordle_config.json"))
    monkeypatch.setattr(wordle_core, "_cache", None, raising=False)
    monkeypatch.setattr(wordle_core, "_cache_mtime", None, raising=False)


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    bot = FakeBot(guild)
    return bot, guild, make_moderation_app(bot, [wordle_routes])


@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/wordle")
    assert resp.status == 200
    body = await resp.json()
    assert body == {"enabled": False, "channel_id": 0, "announce_time": "09:00"}


@pytest.mark.asyncio
async def test_put_then_get(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/wordle",
        json={"enabled": True, "channel_id": 123456, "announce_time": "18:30"},
    )
    assert resp.status == 200
    assert (await resp.json())["enabled"] is True

    resp = await client.get("/api/wordle")
    body = await resp.json()
    assert body["channel_id"] == 123456
    assert body["announce_time"] == "18:30"


@pytest.mark.asyncio
async def test_put_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/wordle", json={"enabled": "да"})
    assert resp.status == 400

    resp = await client.put("/api/wordle", json={"enabled": True, "channel_id": -5})
    assert resp.status == 400

    resp = await client.put("/api/wordle", json={"enabled": True, "announce_time": "25:00"})
    assert resp.status == 400

    resp = await client.put("/api/wordle", json={"enabled": True, "announce_time": "вечером"})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_login(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)

    resp = await client.get("/api/wordle")
    assert resp.status in (401, 403)
