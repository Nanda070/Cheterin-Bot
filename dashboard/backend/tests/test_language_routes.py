import pytest

import bot.core.language_core as language_core
import bot.core.settings_db as settings_db
from dashboard.backend.routes.language import routes as language_routes
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
    return bot, guild, make_moderation_app(bot, [language_routes])


@pytest.mark.asyncio
async def test_get_language_defaults_to_ru(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/language")
    assert resp.status == 200
    body = await resp.json()
    assert body == {"code": "ru"}


@pytest.mark.asyncio
async def test_put_and_get_language_round_trip(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    put = await client.put("/api/language", json={"code": "en"})
    assert put.status == 200
    assert await put.json() == {"code": "en"}

    get = await client.get("/api/language")
    assert await get.json() == {"code": "en"}


@pytest.mark.asyncio
async def test_put_rejects_invalid_language(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/language", json={"code": "de"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_language"


@pytest.mark.asyncio
async def test_language_isolated_per_guild(aiohttp_client):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild_a = FakeGuild(guild_id=1, members=[moderator])
    guild_b = FakeGuild(guild_id=2, members=[moderator])
    bot = FakeBot(guild_a, guilds=[guild_a, guild_b])
    app = make_moderation_app(bot, [language_routes])
    client = await aiohttp_client(app)

    await force_login(client, 10, active_guild_id=1)
    await client.put("/api/language", json={"code": "en"})

    await force_login(client, 10, active_guild_id=2)
    resp = await client.get("/api/language")
    assert (await resp.json())["code"] == "ru"


def test_language_core_set_and_get():
    language_core.set_language(99, "en")
    assert language_core.get_language(99) == "en"
    assert language_core.get_settings(99) == {"code": "en"}
