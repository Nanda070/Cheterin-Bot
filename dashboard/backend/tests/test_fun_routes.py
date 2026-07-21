import pytest

import fun_core
import settings_db
from dashboard.backend.routes.fun import routes as fun_routes
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
    return bot, guild, make_moderation_app(bot, [fun_routes])


@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/fun")
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is False
    assert body["roulette_timeout_minutes"] == fun_core.DEFAULT_ROULETTE_TIMEOUT_MINUTES
    assert body["roulette_cooldown_sec"] == fun_core.DEFAULT_ROULETTE_COOLDOWN_SEC


@pytest.mark.asyncio
async def test_put_then_get(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/fun",
        json={"enabled": True, "roulette_timeout_minutes": 10, "roulette_cooldown_sec": 120},
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is True
    assert body["roulette_timeout_minutes"] == 10

    resp = await client.get("/api/fun")
    assert (await resp.json())["roulette_cooldown_sec"] == 120


@pytest.mark.asyncio
async def test_put_zero_disables_punishment_and_cooldown(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/fun",
        json={"enabled": True, "roulette_timeout_minutes": 0, "roulette_cooldown_sec": 0},
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["roulette_timeout_minutes"] == 0
    assert body["roulette_cooldown_sec"] == 0


@pytest.mark.asyncio
async def test_put_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/fun", json={"enabled": "yes"})
    assert resp.status == 400

    resp = await client.put("/api/fun", json={"enabled": True, "roulette_timeout_minutes": -1})
    assert resp.status == 400

    resp = await client.put(
        "/api/fun", json={"enabled": True, "roulette_timeout_minutes": fun_core.TIMEOUT_MINUTES_MAX + 1}
    )
    assert resp.status == 400

    resp = await client.put("/api/fun", json={"enabled": True, "roulette_cooldown_sec": 100000})
    assert resp.status == 400

    resp = await client.put("/api/fun", json={"enabled": True, "roulette_timeout_minutes": True})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/fun")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_put_auto_emoji_roundtrip_and_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/fun", json={
        "enabled": True,
        "auto_emoji_enabled": True,
        "auto_emoji_chance_percent": 10,
        "auto_emoji_min_interval_sec": 60,
        "auto_emoji_remove_after_sec": 0,
    })
    assert resp.status == 200
    body = await resp.json()
    assert body["auto_emoji_enabled"] is True
    assert body["auto_emoji_chance_percent"] == 10
    assert body["auto_emoji_min_interval_sec"] == 60
    assert body["auto_emoji_remove_after_sec"] == 0

    for bad in (
        {"auto_emoji_enabled": "yes"},
        {"auto_emoji_chance_percent": 0},
        {"auto_emoji_chance_percent": 101},
        {"auto_emoji_min_interval_sec": -1},
        {"auto_emoji_remove_after_sec": 999999},
    ):
        resp = await client.put("/api/fun", json={"enabled": True, **bad})
        assert resp.status == 400, bad
