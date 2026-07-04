import pytest

import bot_config
from dashboard.backend.routes.welcome import routes as welcome_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_config_file(tmp_path, monkeypatch):
    monkeypatch.setattr(bot_config, "CONFIG_FILE", str(tmp_path / "config.json"))


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    return guild, make_moderation_app(FakeBot(guild), [welcome_routes])


@pytest.mark.asyncio
async def test_get_welcome_settings_defaults_to_enabled_when_file_missing(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/welcome-settings")
    assert resp.status == 200
    assert (await resp.json()) == {"channel_enabled": True, "dm_enabled": True}


@pytest.mark.asyncio
async def test_get_welcome_settings_returns_stored_values(aiohttp_client):
    bot_config.save_config({"WELCOME_CHANNEL_ENABLED": False, "WELCOME_DM_ENABLED": True})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/welcome-settings")
    assert (await resp.json()) == {"channel_enabled": False, "dm_enabled": True}


@pytest.mark.asyncio
async def test_get_welcome_settings_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/welcome-settings")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_update_welcome_settings_persists(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/welcome-settings", json={"channel_enabled": False, "dm_enabled": False}
    )
    assert resp.status == 200
    assert (await resp.json()) == {"channel_enabled": False, "dm_enabled": False}
    assert bot_config.load_config()["WELCOME_CHANNEL_ENABLED"] is False
    assert bot_config.load_config()["WELCOME_DM_ENABLED"] is False


@pytest.mark.asyncio
async def test_update_welcome_settings_rejects_non_boolean(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/welcome-settings", json={"channel_enabled": "yes", "dm_enabled": True}
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_update_welcome_settings_rejects_non_dict_body(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/welcome-settings", data="[]", headers={"Content-Type": "application/json"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_update_welcome_settings_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.put("/api/welcome-settings", json={"channel_enabled": True, "dm_enabled": True})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_welcome_settings_route_is_registered_in_the_real_app(aiohttp_client):
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
    resp = await client.get("/api/welcome-settings")
    assert resp.status == 401
