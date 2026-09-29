import pytest

import bot.modules.community.scheduled_messages_core as scheduled_messages_core
import bot.core.settings_db as settings_db
from dashboard.backend.routes.scheduled_messages import routes as scheduled_messages_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app

GUILD_ID = 1


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    bot = FakeBot(guild)
    return bot, guild, make_moderation_app(bot, [scheduled_messages_routes])


@pytest.mark.asyncio
async def test_patch_rejects_schedule_type_without_required_fields(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    scheduled_messages_core.update_enabled(GUILD_ID, True)
    msg = scheduled_messages_core.add_message(
        GUILD_ID,
        channel_id="1",
        content="once",
        schedule_type="once",
        run_at="2099-01-01T00:00:00+00:00",
    )

    resp = await client.patch(
        f"/api/scheduled-messages/{msg['id']}",
        json={"schedule_type": "daily"},
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "daily_time_required"

    # Original message must stay valid for due_messages.
    stored = next(m for m in scheduled_messages_core.get_settings(GUILD_ID)["messages"] if m["id"] == msg["id"])
    assert stored["schedule_type"] == "once"
    assert stored["run_at"]


@pytest.mark.asyncio
async def test_patch_rejects_once_without_run_at(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    msg = scheduled_messages_core.add_message(
        GUILD_ID,
        channel_id="1",
        content="daily",
        schedule_type="daily",
        daily_time="12:00",
    )

    resp = await client.patch(
        f"/api/scheduled-messages/{msg['id']}",
        json={"schedule_type": "once"},
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "run_at_required"
