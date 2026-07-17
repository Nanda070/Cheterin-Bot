import pytest

import stats_db
import xp_core
from dashboard.backend.routes.xp import routes as xp_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("STATS_DB_PATH", str(tmp_path / "stats.db"))
    stats_db.init()
    monkeypatch.setattr(xp_core, "CONFIG_FILE", str(tmp_path / "xp_config.json"))
    monkeypatch.setattr(xp_core, "_cache", None, raising=False)
    monkeypatch.setattr(xp_core, "_cache_mtime", None, raising=False)


def build(members):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild_members = [moderator] + members
    bot = FakeBot(FakeGuild(members=guild_members))
    return bot, make_moderation_app(bot, [xp_routes])


@pytest.mark.asyncio
async def test_leaderboard_shows_every_guild_member_even_without_xp(aiohttp_client):
    active = FakeMember(20, name="active", display_name="Active")
    lurker = FakeMember(30, name="lurker", display_name="Lurker")
    bot_member = FakeMember(40, name="botty", display_name="Botty", bot=True)
    _, app = build([active, lurker, bot_member])

    stats_db.xp_add_text(20, 500, 1000)  # только active когда-либо писал

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/xp/leaderboard")
    assert resp.status == 200
    body = await resp.json()

    displays = {e["display"]: e["xp"] for e in body["entries"]}
    assert displays["Active"] == 500
    assert displays["Lurker"] == 0
    assert "Botty" not in displays  # боты исключены
    assert "mod" in displays
    assert body["total"] == 3  # moderator + active + lurker, без бота


@pytest.mark.asyncio
async def test_leaderboard_keeps_members_who_left(aiohttp_client):
    _, app = build([])
    stats_db.xp_add_text(999, 100, 1000)  # участник уже не в guild.members

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/xp/leaderboard")
    body = await resp.json()
    entry = next(e for e in body["entries"] if e["user_id"] == "999")
    assert entry["on_server"] is False
    assert entry["display"] == "999"
    assert entry["xp"] == 100


@pytest.mark.asyncio
async def test_leaderboard_sorted_by_xp_desc(aiohttp_client):
    low = FakeMember(20, name="low", display_name="Low")
    high = FakeMember(30, name="high", display_name="High")
    _, app = build([low, high])
    stats_db.xp_add_text(20, 10, 1000)
    stats_db.xp_add_text(30, 200, 1000)

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/xp/leaderboard")
    body = await resp.json()
    order = [e["display"] for e in body["entries"]]
    assert order.index("High") < order.index("Low")


@pytest.mark.asyncio
async def test_leaderboard_search_filters_by_display_name(aiohttp_client):
    alice = FakeMember(20, name="alice", display_name="Alice")
    bob = FakeMember(30, name="bob", display_name="Bob")
    _, app = build([alice, bob])

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/xp/leaderboard?search=ali")
    body = await resp.json()
    displays = [e["display"] for e in body["entries"]]
    assert displays == ["Alice"]


@pytest.mark.asyncio
async def test_leaderboard_pagination_over_merged_roster(aiohttp_client):
    members = [FakeMember(100 + i, name=f"u{i}", display_name=f"U{i}") for i in range(30)]
    _, app = build(members)

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/xp/leaderboard?page=1")
    body = await resp.json()
    assert body["total"] == 31  # moderator + 30 members
    assert len(body["entries"]) == body["page_size"]

    resp = await client.get("/api/xp/leaderboard?page=2")
    body2 = await resp.json()
    assert len(body2["entries"]) == 31 - body["page_size"]


@pytest.mark.asyncio
async def test_leaderboard_guild_unavailable(aiohttp_client):
    bot, app = build([])
    bot.get_guild = lambda gid: None
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/xp/leaderboard")
    assert resp.status == 503


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, app = build([])
    client = await aiohttp_client(app)
    resp = await client.get("/api/xp/leaderboard")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_put_settings_voice_base_and_member_multipliers(aiohttp_client):
    _, app = build([])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    payload = xp_core.get_settings()
    payload["voice"]["base_per_minute"] = 10
    payload["voice"]["member_multipliers"] = {"42": 150, "77": 0}

    resp = await client.put("/api/xp", json=payload)
    assert resp.status == 200
    saved = (await resp.json())["settings"]["voice"]
    assert saved["base_per_minute"] == 10
    assert saved["member_multipliers"] == {"42": 150, "77": 0}


@pytest.mark.asyncio
async def test_put_settings_rejects_bad_voice_base_and_multipliers(aiohttp_client):
    _, app = build([])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    payload = xp_core.get_settings()
    payload["voice"]["base_per_minute"] = 0
    resp = await client.put("/api/xp", json=payload)
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_voice_base_per_minute"

    payload = xp_core.get_settings()
    payload["voice"]["member_multipliers"] = {"abc": 100}
    resp = await client.put("/api/xp", json=payload)
    assert resp.status == 400

    payload = xp_core.get_settings()
    payload["voice"]["member_multipliers"] = {"42": 5000}
    resp = await client.put("/api/xp", json=payload)
    assert resp.status == 400

    payload = xp_core.get_settings()
    payload["voice"]["member_multipliers"] = ["42"]
    resp = await client.put("/api/xp", json=payload)
    assert resp.status == 400
