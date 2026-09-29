import pytest

import bot.core.settings_db as settings_db
from dashboard.backend.routes.spam_settings import routes as spam_settings_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_settings_db(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "test_settings.db"))
    settings_db._cache.clear()
    settings_db.init()


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    return make_moderation_app(FakeBot(guild), [spam_settings_routes])


@pytest.mark.asyncio
async def test_get_spam_settings_defaults(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/spam-settings")
    assert resp.status == 200
    body = await resp.json()
    assert body["limit_with_attachments"] == 3
    assert body["limit_without_attachments"] == 5
    assert body["time_window_sec"] == 60


@pytest.mark.asyncio
async def test_put_spam_settings_roundtrip(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    payload = {
        "limit_with_attachments": 2,
        "limit_without_attachments": 4,
        "time_window_sec": 120,
    }
    resp = await client.put("/api/spam-settings", json=payload)
    assert resp.status == 200
    assert await resp.json() == payload

    resp = await client.get("/api/spam-settings")
    assert await resp.json() == payload


@pytest.mark.asyncio
async def test_put_spam_settings_rejects_invalid_window(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/spam-settings",
        json={"limit_with_attachments": 3, "limit_without_attachments": 5, "time_window_sec": 5},
    )
    assert resp.status == 400
