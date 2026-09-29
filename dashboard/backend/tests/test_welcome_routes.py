import pytest

import bot.config as bot_config
from dashboard.backend.routes.welcome import routes as welcome_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_settings_db(tmp_path, monkeypatch):
    import bot.core.settings_db as settings_db
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "test_settings.db"))
    settings_db._cache.clear()
    settings_db.init()


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
    data = await resp.json()
    assert data["channel_enabled"] is True
    assert data["dm_enabled"] is True
    assert data["goodbye_channel_enabled"] is False
    assert data["goodbye_channel_id"] == ""
    assert data["messages"]["channel_mode"] == "text"


@pytest.mark.asyncio
async def test_get_welcome_settings_returns_stored_values(aiohttp_client):
    bot_config.save_config(1, {"WELCOME_CHANNEL_ENABLED": False, "WELCOME_DM_ENABLED": True})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/welcome-settings")
    data = await resp.json()
    assert data["channel_enabled"] is False
    assert data["dm_enabled"] is True
    assert data["goodbye_channel_enabled"] is False


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
        "/api/welcome-settings",
        json={
            "channel_enabled": False,
            "dm_enabled": False,
            "goodbye_channel_enabled": True,
            "goodbye_channel_id": "",
        },
    )
    assert resp.status == 200
    data = await resp.json()
    assert data["channel_enabled"] is False
    assert data["dm_enabled"] is False
    assert data["goodbye_channel_enabled"] is True
    assert bot_config.load_config(1)["WELCOME_CHANNEL_ENABLED"] is False
    assert bot_config.load_config(1)["WELCOME_DM_ENABLED"] is False
    assert bot_config.load_config(1)["GOODBYE_CHANNEL_ENABLED"] is True


@pytest.mark.asyncio
async def test_update_welcome_settings_allows_empty_embeds_in_text_mode(aiohttp_client):
    """Saving toggles with empty channel/dm embed stubs must not fail as empty_embed."""
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/welcome-settings",
        json={
            "channel_enabled": True,
            "dm_enabled": True,
            "goodbye_channel_enabled": False,
            "goodbye_channel_id": "",
            "messages": {
                "channel_mode": "text",
                "channel_text": "hi {mention}",
                "channel_embed": {
                    "title": "",
                    "description": "",
                    "url": "",
                    "color": "#5865F2",
                    "author": {"name": "", "url": "", "icon_url": ""},
                    "footer": {"text": "", "icon_url": ""},
                    "image": {"url": ""},
                    "thumbnail": {"url": ""},
                    "timestamp": None,
                    "fields": [],
                },
                "dm_content": "",
                "dm_embed": {
                    "title": "",
                    "description": "",
                    "url": "",
                    "color": "#5865F2",
                    "author": {"name": "", "url": "", "icon_url": ""},
                    "footer": {"text": "", "icon_url": ""},
                    "image": {"url": ""},
                    "thumbnail": {"url": ""},
                    "timestamp": None,
                    "fields": [],
                },
                "dm_thumbnail_url": "",
                "dm_fallback_thumbnail_url": "",
                "dm_footer_text": "",
                "dm_use_guild_icon": True,
                "goodbye_text": "",
            },
        },
    )
    assert resp.status == 200, await resp.json()
    data = await resp.json()
    assert data["messages"]["channel_text"] == "hi {mention}"


@pytest.mark.asyncio
async def test_update_welcome_settings_rejects_oversized_dm_field(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/welcome-settings",
        json={
            "channel_enabled": True,
            "dm_enabled": True,
            "goodbye_channel_enabled": False,
            "goodbye_channel_id": "",
            "messages": {
                "channel_mode": "text",
                "channel_text": "",
                "channel_embed": {
                    "title": "",
                    "description": "",
                    "url": "",
                    "color": "#5865F2",
                    "author": {"name": "", "url": "", "icon_url": ""},
                    "footer": {"text": "", "icon_url": ""},
                    "image": {"url": ""},
                    "thumbnail": {"url": ""},
                    "timestamp": None,
                    "fields": [],
                },
                "dm_content": "",
                "dm_embed": {
                    "title": "Hi",
                    "description": "",
                    "url": "",
                    "color": "#5865F2",
                    "author": {"name": "", "url": "", "icon_url": ""},
                    "footer": {"text": "", "icon_url": ""},
                    "image": {"url": ""},
                    "thumbnail": {"url": ""},
                    "timestamp": None,
                    "fields": [{"name": "x", "value": "y" * 1025, "inline": False}],
                },
                "dm_thumbnail_url": "",
                "dm_fallback_thumbnail_url": "",
                "dm_footer_text": "",
                "dm_use_guild_icon": True,
                "goodbye_text": "",
            },
        },
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "field_value_too_long"
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/welcome-settings",
        json={
            "channel_enabled": "yes",
            "dm_enabled": True,
            "goodbye_channel_enabled": False,
            "goodbye_channel_id": "",
        },
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
    resp = await client.put(
        "/api/welcome-settings",
        json={
            "channel_enabled": True,
            "dm_enabled": True,
            "goodbye_channel_enabled": False,
            "goodbye_channel_id": "",
        },
    )
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
