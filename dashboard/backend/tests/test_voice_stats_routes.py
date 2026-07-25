"""Voice stats route: hour/weekday bucketing uses guild timezone via timezone_core."""

from datetime import datetime, timedelta, timezone

import pytest

import stats_db
import timezone_core
from dashboard.backend.routes.voice_stats import routes as voice_stats_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app

GUILD = 1
UTC3 = timezone(timedelta(hours=3), name="UTC+3")
UTC0 = timezone.utc


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("STATS_DB_PATH", str(tmp_path / "stats.db"))
    stats_db.init()


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator]))
    return bot, make_moderation_app(bot, [voice_stats_routes])


@pytest.mark.asyncio
async def test_voice_stats_buckets_by_guild_timezone(aiohttp_client, monkeypatch):
    monkeypatch.setattr(timezone_core, "get_tz", lambda _gid: UTC3)
    monkeypatch.setattr(timezone_core, "get_timezone", lambda _gid: "Europe/Moscow")

    # 10:00–11:00 UTC+3 on a fixed day → unix range for that hour.
    start = int(datetime(2026, 7, 24, 10, 0, tzinfo=UTC3).timestamp())
    end = int(datetime(2026, 7, 24, 11, 0, tzinfo=UTC3).timestamp())
    stats_db.voice_session_add(GUILD, 20, 500, "General", start, end, end - start)

    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/voice-stats?days=30")
    assert resp.status == 200
    body = await resp.json()
    assert body["timezone"] == "Europe/Moscow"
    assert body["session_count"] == 1
    assert body["by_hour_minutes"][10] == 60
    assert sum(body["by_hour_minutes"]) == 60
    # Friday 2026-07-24
    assert body["by_weekday_minutes"][4] == 60


@pytest.mark.asyncio
async def test_voice_stats_same_unix_different_hour_in_utc(aiohttp_client, monkeypatch):
    monkeypatch.setattr(timezone_core, "get_tz", lambda _gid: UTC0)
    monkeypatch.setattr(timezone_core, "get_timezone", lambda _gid: "UTC")

    # Same absolute window as above: 07:00–08:00 UTC.
    start = int(datetime(2026, 7, 24, 10, 0, tzinfo=UTC3).timestamp())
    end = int(datetime(2026, 7, 24, 11, 0, tzinfo=UTC3).timestamp())
    stats_db.voice_session_add(GUILD, 20, 500, "General", start, end, end - start)

    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/voice-stats?days=30")
    body = await resp.json()
    assert body["timezone"] == "UTC"
    assert body["by_hour_minutes"][7] == 60
    assert body["by_hour_minutes"][10] == 0
