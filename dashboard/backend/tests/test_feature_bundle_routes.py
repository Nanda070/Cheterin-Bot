import pytest

import birthdays_core
import invites_db
import owner_alerts_core
import sticky_roles_core
from dashboard.backend.routes.birthdays import routes as birthdays_routes
from dashboard.backend.routes.invites import routes as invites_routes
from dashboard.backend.routes.owner_alerts import routes as owner_alerts_routes
from dashboard.backend.routes.sticky_roles import routes as sticky_roles_routes
from dashboard.backend.routes.timezone import routes as timezone_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    FakePermissions,
    FakeRole,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    import settings_db

    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setenv("STICKY_ROLES_DB_PATH", str(tmp_path / "sticky_roles.db"))
    monkeypatch.setenv("INVITES_DB_PATH", str(tmp_path / "invites.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    sticky_roles_core.init()
    invites_db.init()
    owner_alerts_core._ban_events.clear()
    owner_alerts_core._module_errors.clear()


@pytest.fixture
def text_channel_isinstance(monkeypatch):
    """Birthdays test route checks isinstance(..., discord.TextChannel)."""
    import dashboard.backend.routes.birthdays as birthdays_module

    class _FakeDiscord:
        TextChannel = FakeChannel
        HTTPException = birthdays_module.discord.HTTPException

    monkeypatch.setattr(birthdays_module, "discord", _FakeDiscord)


@pytest.mark.asyncio
async def test_setup_health_reports_missing_and_ok(aiohttp_client):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    me = FakeMember(1, name="bot", bot=True)
    me.guild_permissions = FakePermissions(send_messages=False, embed_links=False)
    guild = FakeGuild(members=[moderator], me=me)
    app = make_moderation_app(FakeBot(guild), [owner_alerts_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/setup-health")
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is False
    assert "Send Messages" in body["missing_permissions"]

    me.guild_permissions = FakePermissions(administrator=True)
    resp = await client.get("/api/setup-health")
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert body["missing_permissions"] == []


@pytest.mark.asyncio
async def test_owner_alerts_test_sends(aiohttp_client):
    owner = FakeMember(99, name="owner")
    moderator = FakeMember(10, name="mod", role_ids=[111])
    channel = FakeChannel(55, name="alerts")
    guild = FakeGuild(members=[moderator, owner], channels=[channel], owner_id=99)
    guild.owner = owner
    bot = FakeBot(guild)

    class _Cog:
        def __init__(self):
            self.calls = []

        async def send_alert(self, guild_arg, kind, detail, *, force=False):
            self.calls.append((guild_arg.id, kind, detail, force))
            return True

    cog = _Cog()
    bot.get_cog = lambda name: cog if name == "OwnerAlertsCog" else None

    owner_alerts_core.save_settings(1, {"enabled": False, "channel_id": "55", "notify_dm": False})
    app = make_moderation_app(bot, [owner_alerts_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/owner-alerts/test")
    assert resp.status == 200
    assert cog.calls
    assert cog.calls[0][3] is True


@pytest.mark.asyncio
async def test_owner_alerts_test_reports_not_delivered(aiohttp_client):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    bot = FakeBot(guild)

    class _Cog:
        async def send_alert(self, guild_arg, kind, detail, *, force=False):
            return False

    bot.get_cog = lambda name: _Cog() if name == "OwnerAlertsCog" else None
    app = make_moderation_app(bot, [owner_alerts_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/owner-alerts/test")
    assert resp.status == 502
    assert (await resp.json())["error"] == "not_delivered"


@pytest.mark.asyncio
async def test_birthdays_test_sends(aiohttp_client, text_channel_isinstance):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    channel = FakeChannel(77, name="bday")
    guild = FakeGuild(members=[moderator], channels=[channel])
    birthdays_core.save_settings(1, enabled=True, channel_id="77", ping_role_id="")
    app = make_moderation_app(FakeBot(guild), [birthdays_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/birthdays/test")
    assert resp.status == 200
    assert channel.send_calls


@pytest.mark.asyncio
async def test_birthdays_test_rejects_non_text_channel(aiohttp_client, text_channel_isinstance):
    moderator = FakeMember(10, name="mod", role_ids=[111])

    class _VoiceLike:
        def __init__(self):
            self.id = 77
            self.name = "voice"
            self.send_calls = []

        async def send(self, *args, **kwargs):
            self.send_calls.append((args, kwargs))

    voice = _VoiceLike()
    guild = FakeGuild(members=[moderator], channels=[voice])
    birthdays_core.save_settings(1, enabled=True, channel_id="77", ping_role_id="")
    app = make_moderation_app(FakeBot(guild), [birthdays_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/birthdays/test")
    assert resp.status == 409
    assert (await resp.json())["error"] == "channel_not_text"
    assert voice.send_calls == []


@pytest.mark.asyncio
async def test_invites_get_dedupes_user_fetches(aiohttp_client):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    bot = FakeBot(guild)
    fetch_ids: list[int] = []

    async def tracking_fetch(user_id):
        fetch_ids.append(user_id)
        return FakeMember(user_id, name=f"user-{user_id}")

    bot.fetch_user = tracking_fetch
    bot.get_user = lambda user_id: None

    # Same inviter appears in stats and multiple joins — must fetch once.
    invites_db.record_join(1, 201, 100, "abc")
    invites_db.record_join(1, 202, 100, "abc")
    invites_db.record_join(1, 203, 100, "abc")

    app = make_moderation_app(bot, [invites_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/invites")
    assert resp.status == 200
    body = await resp.json()
    assert len(body["recent_joins"]) == 3
    assert set(fetch_ids) == {100, 201, 202, 203}
    assert fetch_ids.count(100) == 1


@pytest.mark.asyncio
async def test_timezone_get_put(aiohttp_client):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    app = make_moderation_app(FakeBot(guild), [timezone_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/timezone")
    assert resp.status == 200
    body = await resp.json()
    assert body["code"] == "Europe/Moscow"
    assert "UTC" in body["supported"]

    resp = await client.put("/api/timezone", json={"code": "UTC"})
    assert resp.status == 200
    assert (await resp.json())["code"] == "UTC"


@pytest.mark.asyncio
async def test_sticky_roles_roundtrip(aiohttp_client):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    role = FakeRole(7, name="VIP")
    guild = FakeGuild(members=[moderator], roles=[role])
    app = make_moderation_app(FakeBot(guild), [sticky_roles_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/sticky-roles")
    assert resp.status == 200
    assert (await resp.json())["enabled"] is False

    resp = await client.put(
        "/api/sticky-roles",
        json={"enabled": True, "tracked_role_ids": ["7"], "ignored_role_ids": []},
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is True
    assert body["tracked_role_ids"] == ["7"]
