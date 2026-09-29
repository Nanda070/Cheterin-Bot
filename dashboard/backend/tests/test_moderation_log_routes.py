import pytest

import bot.core.moderation_log as moderation_log
from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_moderation_log(tmp_path, monkeypatch):
    monkeypatch.setattr(moderation_log, "LOG_FILE", str(tmp_path / "moderation_log.json"))


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator]))
    return make_moderation_app(bot, [moderation_routes])


@pytest.mark.asyncio
async def test_get_moderation_log_returns_events_newest_first(aiohttp_client):
    moderation_log.append_event(1, "spam_punish", 1, "userA", "reason1")
    moderation_log.append_event(1, "tempban", 2, "userB", "reason2")
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/moderation-log")
    assert resp.status == 200
    body = await resp.json()
    assert [e["type"] for e in body["events"]] == ["tempban", "spam_punish"]


@pytest.mark.asyncio
async def test_get_moderation_log_respects_limit(aiohttp_client):
    for i in range(5):
        moderation_log.append_event(1, "spam_punish", i, f"user{i}", "reason")
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/moderation-log?limit=2")
    body = await resp.json()
    assert len(body["events"]) == 2


@pytest.mark.asyncio
async def test_get_moderation_log_requires_auth(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/moderation-log")
    assert resp.status == 401
