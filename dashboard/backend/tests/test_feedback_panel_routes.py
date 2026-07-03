import pytest

from dashboard.backend.routes.feedback import routes as feedback_routes
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, force_login, make_moderation_app


def build(channels=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator], channels=channels or [])
    return guild, make_moderation_app(FakeBot(guild), [feedback_routes])


@pytest.mark.asyncio
async def test_publish_feedback_panel_success(aiohttp_client):
    channel = FakeChannel(500, name="reports")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-panel/publish", json={"channel_id": "500"})

    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert len(channel.send_calls) == 1


@pytest.mark.asyncio
async def test_publish_feedback_panel_404_when_channel_missing(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-panel/publish", json={"channel_id": "500"})

    assert resp.status == 404
    assert (await resp.json())["error"] == "channel_not_found"


@pytest.mark.asyncio
async def test_publish_feedback_panel_rejects_missing_channel_id(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-panel/publish", json={})

    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_publish_feedback_panel_requires_auth(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)

    resp = await client.post("/api/feedback-panel/publish", json={"channel_id": "500"})

    assert resp.status == 401


@pytest.mark.asyncio
async def test_publish_feedback_panel_attributes_to_session_moderator_not_body(aiohttp_client):
    channel = FakeChannel(500, name="reports")
    _, app = build(channels=[channel])
    bot = app["bot"]
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-panel/publish", json={"channel_id": "500"})

    assert resp.status == 200
    assert "<@10>" in bot.sent_logs[0].description
