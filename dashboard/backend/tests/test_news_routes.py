import pytest

import news
from dashboard.backend.routes.news import routes as news_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(news, "CONFIG_FILE", str(tmp_path / "news_relay.json"))
    monkeypatch.setattr(news, "_cache", None)
    monkeypatch.setattr(news, "_cache_mtime", None)


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator]))
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

    # channel_map теперь работает
    assert news.get_channel_map() == {10: 20}


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
async def test_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/news")
    assert resp.status == 401
