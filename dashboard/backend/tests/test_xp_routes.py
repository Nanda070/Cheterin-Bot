import pytest

import bot.modules.games.economy_db as economy_db
import bot.core.settings_db as settings_db
import bot.core.stats_db as stats_db
import bot.modules.levels.xp_core as xp_core
from dashboard.backend.routes.xp import routes as xp_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("STATS_DB_PATH", str(tmp_path / "stats.db"))
    stats_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    monkeypatch.setenv("ECONOMY_DB_PATH", str(tmp_path / "economy.db"))
    economy_db.init()


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

    stats_db.xp_add_text(1, 20, 500, 1000)  # только active когда-либо писал

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
    stats_db.xp_add_text(1, 999, 100, 1000)  # участник уже не в guild.members

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
    stats_db.xp_add_text(1, 20, 10, 1000)
    stats_db.xp_add_text(1, 30, 200, 1000)

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

    payload = xp_core.get_settings(1)
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

    payload = xp_core.get_settings(1)
    payload["voice"]["base_per_minute"] = 0
    resp = await client.put("/api/xp", json=payload)
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_voice_base_per_minute"

    payload = xp_core.get_settings(1)
    payload["voice"]["member_multipliers"] = {"abc": 100}
    resp = await client.put("/api/xp", json=payload)
    assert resp.status == 400

    payload = xp_core.get_settings(1)
    payload["voice"]["member_multipliers"] = {"42": 5000}
    resp = await client.put("/api/xp", json=payload)
    assert resp.status == 400

    payload = xp_core.get_settings(1)
    payload["voice"]["member_multipliers"] = ["42"]
    resp = await client.put("/api/xp", json=payload)
    assert resp.status == 400


@pytest.mark.asyncio
async def test_public_leaderboard_legacy_requires_guild_id(aiohttp_client):
    _, app = build([])
    client = await aiohttp_client(app)
    resp = await client.get("/api/public/leaderboard")
    assert resp.status == 400
    body = await resp.json()
    assert body["error"] == "guild_id_required"


@pytest.mark.asyncio
async def test_public_leaderboard_legacy_with_query_param(aiohttp_client):
    member = FakeMember(20, name="alice", display_name="Alice")
    _, app = build([member])
    stats_db.xp_add_text(1, 20, 500, 1000)
    settings = xp_core.get_settings(1)
    settings["enabled"] = True
    settings["public_leaderboard"] = True
    xp_core.save_config(1, settings)

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/leaderboard?guild_id=1")
    assert resp.status == 200
    body = await resp.json()
    assert body["guild_id"] == "1"
    assert body["entries"][0]["xp"] == 500


@pytest.mark.asyncio
async def test_public_leaderboard_for_guild_id(aiohttp_client):
    member = FakeMember(20, name="alice", display_name="Alice")
    _, app = build([member])
    stats_db.xp_add_text(1, 20, 500, 1000)
    # XP on another guild must not leak into guild 1's public page.
    stats_db.xp_add_text(999, 20, 9999, 1000)
    settings = xp_core.get_settings(1)
    settings["enabled"] = True
    settings["public_leaderboard"] = True
    xp_core.save_config(1, settings)
    other = xp_core.get_settings(999)
    other["enabled"] = True
    other["public_leaderboard"] = True
    xp_core.save_config(999, other)

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/leaderboard/1")
    assert resp.status == 200
    body = await resp.json()
    assert body["guild_id"] == "1"
    assert body["entries"][0]["xp"] == 500
    assert body["entries"][0]["display"] == "Alice"


@pytest.mark.asyncio
async def test_public_leaderboard_disabled_returns_404(aiohttp_client):
    _, app = build([])
    settings = xp_core.get_settings(1)
    settings["enabled"] = True
    settings["public_leaderboard"] = False
    xp_core.save_config(1, settings)

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/leaderboard/1")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_public_leaderboard_invalid_guild_id(aiohttp_client):
    _, app = build([])
    client = await aiohttp_client(app)
    resp = await client.get("/api/public/leaderboard/not-a-number")
    assert resp.status == 400


@pytest.mark.asyncio
async def test_profile_card_preview_returns_png(aiohttp_client):
    active = FakeMember(20, name="active", display_name="Active")
    # Valid tiny PNG so avatar decode does not fail oddly in CI
    from dashboard.backend.tests.fakes import FakeAsset
    import struct
    import zlib

    def _tiny_png() -> bytes:
        def chunk(tag: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        sig = b"\x89PNG\r\n\x1a\n"
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        raw = zlib.compress(b"\x00\xff\x00\x00")
        idat = chunk(b"IDAT", raw)
        iend = chunk(b"IEND", b"")
        return sig + ihdr + idat + iend

    active.display_avatar = FakeAsset(data=_tiny_png())
    _, app = build([active])
    stats_db.xp_add_text(1, 20, 500, 1000)

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/xp/profile-card-preview?user_id=20")
    assert resp.status == 200
    assert resp.content_type == "image/png"
    body = await resp.read()
    assert body[:8] == b"\x89PNG\r\n\x1a\n"

    # Default: logged-in moderator
    resp_me = await client.get("/api/xp/profile-card-preview")
    assert resp_me.status == 200
    assert (await resp_me.read())[:8] == b"\x89PNG\r\n\x1a\n"
