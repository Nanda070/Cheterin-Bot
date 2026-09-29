"""Ретрансляция новостей — привилегия мейна (Фаза 2b): доступ только у супер-админа,
целевые каналы обязаны принадлежать мейн-серверу."""

import pytest

import bot.modules.community.news as news
import bot.core.settings_db as settings_db
from dashboard.backend.routes.news import routes as news_routes
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
    monkeypatch.setenv("GUILD_ID", "1")


def build(admin=True):
    # Супер-админ определяется на мейне (app["guild_id"] == 1): администратор проходит.
    moderator = FakeMember(10, name="mod", administrator=admin)
    channels = [FakeChannel(20, name="t1"), FakeChannel(30, name="t2"), FakeChannel(456, name="log")]
    bot = FakeBot(FakeGuild(members=[moderator], channels=channels))
    return bot, make_moderation_app(bot, [news_routes])


VALID_BODY = {
    "enabled": True,
    "source_guild_id": "123",
    "source_bot_ids": ["1", "2"],
    "log_channel_id": "456",
    "mappings": [
        {"source_channel_id": "10", "target_channel_id": "20", "label": "Valorant"},
    ],
}


@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/news")
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is True
    assert body["mappings"] == []


@pytest.mark.asyncio
async def test_put_then_get(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/news", json=VALID_BODY)
    assert resp.status == 200
    body = await resp.json()
    assert body["source_guild_id"] == "123"
    assert body["mappings"][0]["label"] == "Valorant"

    resp = await client.get("/api/news")
    assert (await resp.json()) == body

    # channel_map теперь работает (settings под мейн-сервером == 1)
    assert news.get_channel_map(1) == {10: 20}


@pytest.mark.asyncio
async def test_put_validation(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/news", json={**VALID_BODY, "source_guild_id": "abc"})
    assert resp.status == 400

    resp = await client.put("/api/news", json={**VALID_BODY, "source_bot_ids": ["x"]})
    assert resp.status == 400

    resp = await client.put(
        "/api/news",
        json={**VALID_BODY, "mappings": [{"source_channel_id": "", "target_channel_id": "20", "label": ""}]},
    )
    assert resp.status == 400

    duplicated = [
        {"source_channel_id": "10", "target_channel_id": "20", "label": ""},
        {"source_channel_id": "10", "target_channel_id": "30", "label": ""},
    ]
    resp = await client.put("/api/news", json={**VALID_BODY, "mappings": duplicated})
    assert resp.status == 400
    assert (await resp.json())["error"] == "duplicate_source_channel"


@pytest.mark.asyncio
async def test_put_rejects_target_channel_outside_main_guild(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    body = {**VALID_BODY, "mappings": [{"source_channel_id": "10", "target_channel_id": "999", "label": ""}]}
    resp = await client.put("/api/news", json=body)
    assert resp.status == 404
    assert (await resp.json())["error"] == "target_channel_not_found"


@pytest.mark.asyncio
async def test_put_rejects_log_channel_outside_main_guild(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/news", json={**VALID_BODY, "log_channel_id": "999"})
    assert resp.status == 404
    assert (await resp.json())["error"] == "log_channel_id_not_found"


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/news")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_forbidden_for_non_super_admin(aiohttp_client):
    _, app = build(admin=False)
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/news")
    assert resp.status == 403
