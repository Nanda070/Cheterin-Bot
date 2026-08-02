import pytest

import settings_db
from dashboard.backend.routes.quote import routes as quote_routes
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
    return make_moderation_app(bot, [quote_routes])


@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/quote")
    assert resp.status == 200
    assert await resp.json() == {"enabled": True, "delete_trigger": False, "min_length": 0}


@pytest.mark.asyncio
async def test_put_settings(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/quote",
        json={"enabled": False, "delete_trigger": True, "min_length": 5},
    )
    assert resp.status == 200
    assert await resp.json() == {"enabled": False, "delete_trigger": True, "min_length": 5}
