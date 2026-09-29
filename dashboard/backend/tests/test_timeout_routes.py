import pytest

import bot.core.moderation_log as moderation_log
import bot.core.settings_db as settings_db
from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    member = FakeMember(100, name="fighter", display_name="Fighter")
    bot = FakeBot(FakeGuild(members=[moderator, member]))
    return bot, member, make_moderation_app(bot, [moderation_routes])


@pytest.mark.asyncio
async def test_timeout_member(aiohttp_client):
    bot, member, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/members/100/timeout",
        json={"reason": "флуд", "duration": "10m"},
    )
    assert resp.status == 200
    assert member.is_timed_out()
    assert bot.sent_logs
    events = moderation_log.load_events(1)
    assert any(e["type"] == "manual_mute" for e in events)


@pytest.mark.asyncio
async def test_timeout_invalid_duration(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/members/100/timeout",
        json={"reason": "флуд", "duration": "nope"},
    )
    assert resp.status == 400
    body = await resp.json()
    assert body["error"] == "invalid_duration"


@pytest.mark.asyncio
async def test_untimeout_member(aiohttp_client):
    bot, member, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/members/100/timeout", json={"reason": "флуд", "duration": "1h"})
    resp = await client.delete("/api/members/100/timeout", json={"reason": "достаточно"})
    assert resp.status == 200
    assert not member.is_timed_out()
    events = moderation_log.load_events(1)
    assert any(e["type"] == "manual_unmute" for e in events)
    assert bot.sent_logs
