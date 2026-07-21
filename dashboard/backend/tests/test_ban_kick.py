import discord
import pytest

from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)

import moderation_log


@pytest.fixture(autouse=True)
def isolated_moderation_log(tmp_path, monkeypatch):
    monkeypatch.setattr(moderation_log, "LOG_FILE", str(tmp_path / "moderation_log.json"))


class _StubForbidden(discord.Forbidden):
    def __init__(self):
        pass


class _StubNotFound(discord.NotFound):
    def __init__(self):
        pass


def build(members):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator] + members))
    return bot, make_moderation_app(bot, [moderation_routes])


@pytest.mark.asyncio
async def test_ban_calls_discord_and_logs(aiohttp_client):
    target = FakeMember(60, name="rulebreaker")
    bot, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/members/60/ban", json={"reason": "спам", "delete_message_days": 7}
    )
    assert resp.status == 200
    action, kwargs = target.action_calls[0]
    assert action == "ban"
    assert kwargs["delete_message_seconds"] == 7 * 86400
    assert "Dashboard: спам" in kwargs["reason"]
    assert "(10)" in kwargs["reason"]
    assert len(bot.sent_logs) == 1


@pytest.mark.asyncio
async def test_kick_calls_discord_and_logs(aiohttp_client):
    target = FakeMember(61, name="mild")
    bot, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/61/kick", json={"reason": "флуд"})
    assert resp.status == 200
    action, kwargs = target.action_calls[0]
    assert action == "kick"
    assert "Dashboard: флуд" in kwargs["reason"]
    assert len(bot.sent_logs) == 1


@pytest.mark.asyncio
async def test_ban_requires_reason_and_valid_days(aiohttp_client):
    target = FakeMember(62)
    _, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/62/ban", json={"reason": "  ", "delete_message_days": 0})
    assert resp.status == 400
    resp = await client.post("/api/members/62/ban", json={"reason": "ok", "delete_message_days": 3})
    assert resp.status == 400
    assert target.action_calls == []


@pytest.mark.asyncio
async def test_ban_forbidden_maps_to_403(aiohttp_client):
    target = FakeMember(63)
    target.action_raises = _StubForbidden()
    _, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/63/ban", json={"reason": "x", "delete_message_days": 0})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_ban_missing_member_maps_to_404(aiohttp_client):
    _, app = build([])
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.post("/api/members/9999/ban", json={"reason": "x", "delete_message_days": 0})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_ban_discord_not_found_maps_to_404(aiohttp_client):
    target = FakeMember(64)
    target.action_raises = _StubNotFound()
    _, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/64/ban", json={"reason": "x", "delete_message_days": 0})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_ban_invalid_json_body_returns_400(aiohttp_client):
    target = FakeMember(65)
    _, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/65/ban", data=b"not json")
    assert resp.status == 400
    body = await resp.json()
    assert body.get("error") == "invalid_request"


@pytest.mark.asyncio
async def test_ban_records_moderation_log_entry(aiohttp_client):
    target = FakeMember(70, name="rulebreaker")
    _, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/members/70/ban", json={"reason": "спам", "delete_message_days": 0})

    events = moderation_log.load_events(1)
    assert len(events) == 1
    assert events[0]["type"] == "manual_ban"
    assert events[0]["user_id"] == "70"
    assert events[0]["moderator_id"] == "10"


@pytest.mark.asyncio
async def test_kick_records_moderation_log_entry(aiohttp_client):
    target = FakeMember(71, name="mild")
    _, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/members/71/kick", json={"reason": "флуд"})

    events = moderation_log.load_events(1)
    assert len(events) == 1
    assert events[0]["type"] == "manual_kick"
    assert events[0]["moderator_id"] == "10"
