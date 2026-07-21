import pytest

import bot_config
from dashboard.backend.routes.auto_roles import routes as auto_roles_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, FakeRole, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_settings_db(tmp_path, monkeypatch):
    import settings_db
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "test_settings.db"))
    settings_db._cache.clear()
    settings_db.init()


def build(roles=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot_top = FakeRole(900, name="bot-role", position=50)
    me = FakeMember(1, name="bot", top_role=bot_top)
    guild = FakeGuild(members=[moderator], roles=roles or [], me=me)
    return guild, make_moderation_app(FakeBot(guild), [auto_roles_routes])


@pytest.mark.asyncio
async def test_get_auto_roles_defaults_to_empty_when_file_missing(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/auto-roles")
    assert resp.status == 200
    assert (await resp.json()) == {"role_ids": []}


@pytest.mark.asyncio
async def test_get_auto_roles_returns_stored_values(aiohttp_client):
    bot_config.save_config(1, {"AUTO_ROLE_IDS": ["7", "8"]})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/auto-roles")
    assert (await resp.json()) == {"role_ids": ["7", "8"]}


@pytest.mark.asyncio
async def test_get_auto_roles_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/auto-roles")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_update_auto_roles_persists_valid_roles(aiohttp_client):
    role = FakeRole(7, name="Member", position=5)
    _, app = build(roles=[role])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-roles", json={"role_ids": ["7"]})
    assert resp.status == 200
    assert (await resp.json()) == {"role_ids": ["7"]}
    assert bot_config.load_config(1)["AUTO_ROLE_IDS"] == ["7"]


@pytest.mark.asyncio
async def test_update_auto_roles_rejects_role_above_bot(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    _, app = build(roles=[role])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-roles", json={"role_ids": ["9"]})
    assert resp.status == 403
    assert (await resp.json())["error"] == "role_not_assignable"


@pytest.mark.asyncio
async def test_update_auto_roles_rejects_managed_role(aiohttp_client):
    role = FakeRole(8, name="BotRole", position=5, managed=True)
    _, app = build(roles=[role])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-roles", json={"role_ids": ["8"]})
    assert resp.status == 403
    assert (await resp.json())["error"] == "role_not_assignable"


@pytest.mark.asyncio
async def test_update_auto_roles_rejects_unknown_role(aiohttp_client):
    _, app = build(roles=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-roles", json={"role_ids": ["999"]})
    assert resp.status == 403
    assert (await resp.json())["error"] == "role_not_assignable"


@pytest.mark.asyncio
async def test_update_auto_roles_rejects_non_list_body(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-roles", json={"role_ids": "7"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_update_auto_roles_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.put("/api/auto-roles", json={"role_ids": []})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_auto_roles_route_is_registered_in_the_real_app(aiohttp_client):
    from dashboard.backend.app import create_app
    from dashboard.backend.config import load_dashboard_config

    class _FakeBot:
        def get_guild(self, guild_id):
            return None

    config = load_dashboard_config(
        {
            "DASHBOARD_PORT": "0",
            "DISCORD_CLIENT_ID": "id",
            "DISCORD_CLIENT_SECRET": "secret",
            "DISCORD_OAUTH_REDIRECT_URI": "http://localhost:8080/api/auth/discord/callback",
            "SESSION_SECRET": "x" * 32,
            "DASHBOARD_ACCESS_ROLE_IDS": "111",
        }
    )
    app = create_app(_FakeBot(), config, guild_id=1)
    client = await aiohttp_client(app)
    # 401 (not 404) proves the route is registered and reachable in the real
    # app, and that the dashboard-access auth gate — not a missing route —
    # is what's rejecting the unauthenticated request.
    resp = await client.get("/api/auto-roles")
    assert resp.status == 401
