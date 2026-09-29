import pytest

import bot.core.settings_db as settings_db
from dashboard.backend.routes.casino import routes as casino_routes
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
    return bot, guild, make_moderation_app(bot, [casino_routes])


@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/casino")
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is False
    assert body["house_edge_percent"] == 5


@pytest.mark.asyncio
async def test_put_then_get(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/casino", json={
        "enabled": True, "house_edge_percent": 10, "cooldown_sec": 15, "min_bet": 20, "max_bet": 2000,
    })
    assert resp.status == 200
    body = await resp.json()
    assert body["house_edge_percent"] == 10

    resp = await client.get("/api/casino")
    assert (await resp.json())["max_bet"] == 2000


@pytest.mark.asyncio
async def test_put_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    cases = [
        {"enabled": "да"},
        {"enabled": True, "house_edge_percent": 60},
        {"enabled": True, "cooldown_sec": -1},
        {"enabled": True, "min_bet": 0},
        {"enabled": True, "min_bet": 500, "max_bet": 100},  # max < min и не 0
    ]
    for body in cases:
        resp = await client.put("/api/casino", json=body)
        assert resp.status == 400, body


@pytest.mark.asyncio
async def test_put_allows_unlimited_max_bet(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/casino", json={"enabled": True, "min_bet": 500, "max_bet": 0})
    assert resp.status == 200


@pytest.mark.asyncio
async def test_requires_login(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/casino")
    assert resp.status in (401, 403)
