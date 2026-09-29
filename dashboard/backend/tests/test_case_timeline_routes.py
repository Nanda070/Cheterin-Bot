import pytest

import bot.core.moderation_log as moderation_log
import bot.core.settings_db as settings_db
import bot.modules.moderation.warns_core as warns_core
import bot.modules.moderation.warns_db as warns_db
from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(warns_db, "get_db_path", lambda: str(tmp_path / "warns.db"))
    warns_db.db_init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    monkeypatch.setattr(moderation_log, "LOG_FILE", str(tmp_path / "moderation_log.json"))


def build(*, members=None, fetchable_users=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild_members = [moderator] + (members or [])
    bot = FakeBot(FakeGuild(members=guild_members), fetchable_users=fetchable_users or [])
    return bot, make_moderation_app(bot, [moderation_routes])


@pytest.mark.asyncio
async def test_case_timeline_merges_warns_and_mod_log(aiohttp_client):
    member = FakeMember(100, name="fighter", display_name="Fighter")
    _, app = build(members=[member])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    warns_core.add_warn(1, 100, "flood", 10, source="manual")
    moderation_log.append_event(
        1, "manual_ban", 100, "fighter", "ban reason",
        moderator_id=10, moderator_display="mod", extra="0d",
    )
    moderation_log.append_event(
        1, "manual_kick", 999, "other", "other user",
        moderator_id=10, moderator_display="mod",
    )

    resp = await client.get("/api/members/100/case-timeline")
    assert resp.status == 200
    body = await resp.json()
    assert body["in_guild"] is True
    assert body["user"]["id"] == "100"
    assert body["user"]["display_name"] == "Fighter"
    assert body["user"]["avatar"]
    kinds = [i["kind"] for i in body["items"]]
    assert "manual_ban" in kinds
    assert "warn" in kinds
    assert "manual_kick" not in kinds
    assert kinds[0] == "manual_ban"  # newest first


@pytest.mark.asyncio
async def test_case_timeline_fetch_user_when_not_in_guild(aiohttp_client):
    left = FakeMember(200, name="leftuser", display_name="Left User")
    _, app = build(members=[], fetchable_users=[left])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    moderation_log.append_event(
        1, "command_ban", 200, "leftuser", "banned after leave",
        moderator_id=10, moderator_display="mod",
    )

    resp = await client.get("/api/members/200/case-timeline")
    assert resp.status == 200
    body = await resp.json()
    assert body["in_guild"] is False
    assert body["user"]["id"] == "200"
    assert body["user"]["username"] == "leftuser"
    assert body["items"][0]["kind"] == "command_ban"


@pytest.mark.asyncio
async def test_case_timeline_404_when_user_unknown(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/members/999999/case-timeline")
    assert resp.status == 404
    body = await resp.json()
    assert body["error"] == "user_not_found"


@pytest.mark.asyncio
async def test_case_timeline_dedupes_warn_manual(aiohttp_client):
    member = FakeMember(100, name="fighter")
    _, app = build(members=[member])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    warn = warns_core.add_warn(1, 100, "spam", 10, source="manual")
    moderation_log.append_event(
        1, "warn_manual", 100, "fighter", "spam",
        moderator_id=10, moderator_display="mod",
    )
    # Force matching timestamps for dedupe (append_event uses now).
    events = settings_db.get(1, "moderation_log", [])
    events[-1]["timestamp"] = warn["created_at"][:19] + "+00:00"
    settings_db.put(1, "moderation_log", events)

    resp = await client.get("/api/members/100/case-timeline")
    body = await resp.json()
    kinds = [i["kind"] for i in body["items"]]
    assert kinds.count("warn") == 1
    assert "warn_manual" not in kinds


@pytest.mark.asyncio
async def test_case_timeline_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/members/100/case-timeline")
    assert resp.status == 401
