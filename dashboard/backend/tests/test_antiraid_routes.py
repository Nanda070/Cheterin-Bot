import pytest

import bot.modules.moderation.antiraid_core as antiraid_core
import bot.core.settings_db as settings_db
from dashboard.backend.routes.antiraid import routes as antiraid_routes
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
    return bot, guild, make_moderation_app(bot, [antiraid_routes])


@pytest.mark.asyncio
async def test_get_defaults_disabled(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/antiraid")
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is False
    assert body["join_threshold"] == 5


@pytest.mark.asyncio
async def test_put_then_get(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/antiraid", json={
        "enabled": True, "join_window_sec": 20, "join_threshold": 8,
        "min_account_age_hours": 48, "action_lockdown": False,
        "action_slowmode_sec": 30, "cooldown_minutes": 15,
    })
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is True
    assert body["action_lockdown"] is False

    resp = await client.get("/api/antiraid")
    assert (await resp.json())["join_threshold"] == 8


@pytest.mark.asyncio
async def test_put_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    cases = [
        {"enabled": "да"},
        {"enabled": True, "join_window_sec": 0},
        {"enabled": True, "join_threshold": 0},
        {"enabled": True, "cooldown_minutes": -1},
        {"enabled": True, "action_slowmode_sec": 999999},
    ]
    for body in cases:
        resp = await client.put("/api/antiraid", json=body)
        assert resp.status == 400, body


@pytest.mark.asyncio
async def test_requires_login(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/antiraid")
    assert resp.status in (401, 403)
