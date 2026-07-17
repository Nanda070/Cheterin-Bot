import pytest

import daily_topic_core
from dashboard.backend.routes.daily_topic import routes as daily_topic_routes
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
    monkeypatch.setattr(daily_topic_core, "CONFIG_FILE", str(tmp_path / "daily_topic_config.json"))


class FakeDailyTopicCog:
    def __init__(self):
        self.posted = []

    async def post_topic_now(self):
        topic = daily_topic_core.pick_next_topic()
        if topic is not None:
            daily_topic_core.mark_posted_today()
            self.posted.append(topic["id"])
        return topic


def build(with_cog=True):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    channel = FakeChannel(500, name="general")
    bot = FakeBot(FakeGuild(members=[moderator], channels=[channel]))
    cog = FakeDailyTopicCog() if with_cog else None
    bot.get_cog = lambda name: cog
    return bot, cog, make_moderation_app(bot, [daily_topic_routes])


@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/daily-topic")
    assert resp.status == 200
    assert await resp.json() == {"enabled": False, "channel_id": "", "post_times": [], "topics": []}


@pytest.mark.asyncio
async def test_update_settings(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/daily-topic/settings",
        json={"enabled": True, "channel_id": "500", "post_times": ["09:00", "20:00"]},
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is True
    assert body["post_times"] == ["09:00", "20:00"]


@pytest.mark.asyncio
async def test_update_settings_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    base = {"enabled": False, "channel_id": "", "post_times": []}

    resp = await client.put("/api/daily-topic/settings", json={**base, "channel_id": "abc"})
    assert resp.status == 400
    resp = await client.put("/api/daily-topic/settings", json={**base, "post_times": ["25:00"]})
    assert resp.status == 400
    resp = await client.put("/api/daily-topic/settings", json={**base, "enabled": True})
    assert resp.status == 400  # channel_required
    resp = await client.put("/api/daily-topic/settings", json={**base, "enabled": True, "channel_id": "500"})
    assert resp.status == 400  # post_times_required


@pytest.mark.asyncio
async def test_topic_crud(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/daily-topic/topics", json={"text": "Вопрос дня"})
    assert resp.status == 201
    topic = await resp.json()
    assert topic["text"] == "Вопрос дня"

    resp = await client.patch(f"/api/daily-topic/topics/{topic['id']}", json={"text": "Изменённый"})
    assert resp.status == 200
    assert (await resp.json())["text"] == "Изменённый"

    resp = await client.patch("/api/daily-topic/topics/999", json={"text": "x"})
    assert resp.status == 404

    resp = await client.delete(f"/api/daily-topic/topics/{topic['id']}")
    assert resp.status == 200
    resp = await client.delete(f"/api/daily-topic/topics/{topic['id']}")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_create_topic_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/daily-topic/topics", json={"text": " "})
    assert resp.status == 400
    resp = await client.post("/api/daily-topic/topics", json={"text": "x" * 301})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_post_now(aiohttp_client):
    _, cog, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.put("/api/daily-topic/settings", json={"enabled": False, "channel_id": "500", "post_times": []})
    await client.post("/api/daily-topic/topics", json={"text": "Вопрос"})

    resp = await client.post("/api/daily-topic/post-now")
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert cog.posted == [body["topic"]["id"]]


@pytest.mark.asyncio
async def test_post_now_requires_channel(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/daily-topic/post-now")
    assert resp.status == 409


@pytest.mark.asyncio
async def test_post_now_requires_topics(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.put("/api/daily-topic/settings", json={"enabled": False, "channel_id": "500", "post_times": []})
    resp = await client.post("/api/daily-topic/post-now")
    assert resp.status == 409


@pytest.mark.asyncio
async def test_post_now_no_cog(aiohttp_client):
    _, _, app = build(with_cog=False)
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/daily-topic/post-now")
    assert resp.status == 503


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/daily-topic")
    assert resp.status == 401
