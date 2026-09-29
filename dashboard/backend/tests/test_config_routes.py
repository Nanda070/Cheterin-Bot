import pytest

import bot.config as bot_config
from dashboard.backend.routes.config import routes as config_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app
from dashboard.backend.tests.fakes import FakeChannel, FakeRole


@pytest.fixture(autouse=True)
def isolated_settings_db(tmp_path, monkeypatch):
    import bot.core.settings_db as settings_db
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "test_settings.db"))
    settings_db._cache.clear()
    settings_db.init()


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    return guild, make_moderation_app(FakeBot(guild), [config_routes])


@pytest.mark.asyncio
async def test_get_config_returns_defaults_when_file_missing(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/config")
    assert resp.status == 200
    body = await resp.json()
    assert body["LOG_CHANNEL_ID"] == ""
    assert body["SPAM_EXCEPTION_CHANNELS"] == []
    assert body["BUTTON_WEBHOOK_URL"] == ""


@pytest.mark.asyncio
async def test_get_config_returns_stored_values(aiohttp_client):
    bot_config.save_config(1,
        {
            "LOG_CHANNEL_ID": "500",
            "SPAM_EXCEPTION_CHANNELS": ["600", "700"],
            "SERVER_INVITE_LINK": "https://discord.gg/example",
        }
    )
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/config")
    body = await resp.json()
    assert body["LOG_CHANNEL_ID"] == "500"
    assert body["SPAM_EXCEPTION_CHANNELS"] == ["600", "700"]
    assert body["SERVER_INVITE_LINK"] == "https://discord.gg/example"


@pytest.mark.asyncio
async def test_get_config_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/config")
    assert resp.status == 401


def _full_config(**overrides):
    cfg = {
        "LOG_CHANNEL_ID": "",
        "SPAM_EXCEPTION_CHANNELS": [],
        "TEMPBAN_CHANNEL_ID": "",
        "TEMPBAN_LOG_CHANNEL_ID": "",
        "SPAM_LOG_CHANNEL_ID": "",
        "SPAM_LOG_ROLE_ID": "",
        "WELCOME_CHANNEL_ID": "",
        "INVITE_LOG_CHANNEL_ID": "",
        "ANNOUNCEMENTS_CHANNEL_ID": "",
        "RULES_CHANNEL_ID": "",
        "ROLES_CHANNEL_ID": "",
        "SEARCH_PLAYERS_CHANNEL_ID": "",
        "CTD_ROLE_ID": "",
        "CTD_CHANNEL_ID": "",
        "BUTTON_CREATE_ALLOWED_ROLES": [],
        "BUTTON_WEBHOOK_URL": "",
        "BUTTON_WEBHOOK_USERNAME": "",
        "BUTTON_WEBHOOK_AVATAR_URL": "",
        "SERVER_INVITE_LINK": "",
    }
    cfg.update(overrides)
    return cfg


def build_with_guild(channels=None, roles=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator], channels=channels or [], roles=roles or [])
    return guild, make_moderation_app(FakeBot(guild), [config_routes])


@pytest.mark.asyncio
async def test_update_config_success_updates_all_fields(aiohttp_client):
    channel = FakeChannel(500, name="logs")
    _, app = build_with_guild(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(LOG_CHANNEL_ID="500"))
    assert resp.status == 200
    assert (await resp.json())["LOG_CHANNEL_ID"] == "500"
    assert bot_config.load_config(1)["LOG_CHANNEL_ID"] == "500"


@pytest.mark.asyncio
async def test_update_config_checks_structure_before_channel_existence(aiohttp_client):
    _, app = build_with_guild(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(SPAM_EXCEPTION_CHANNELS="not-a-list", LOG_CHANNEL_ID="500"))
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_spam_exception_channels"


@pytest.mark.asyncio
async def test_update_config_404_when_channel_not_found(aiohttp_client):
    _, app = build_with_guild(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(LOG_CHANNEL_ID="500"))
    assert resp.status == 404
    assert (await resp.json())["error"] == "log_channel_id_not_found"


@pytest.mark.asyncio
async def test_update_config_404_when_role_not_found(aiohttp_client):
    _, app = build_with_guild(roles=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(SUPPLY_ROLE_ID="200"))
    assert resp.status == 404
    assert (await resp.json())["error"] == "supply_role_id_not_found"


@pytest.mark.asyncio
async def test_update_config_404_when_list_channel_not_found(aiohttp_client):
    _, app = build_with_guild(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(SPAM_EXCEPTION_CHANNELS=["500"]))
    assert resp.status == 404
    assert (await resp.json())["error"] == "spam_exception_channels_not_found"


@pytest.mark.asyncio
async def test_update_config_404_when_list_role_not_found(aiohttp_client):
    _, app = build_with_guild(roles=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(BUTTON_CREATE_ALLOWED_ROLES=["200"]))
    assert resp.status == 404
    assert (await resp.json())["error"] == "button_create_allowed_roles_not_found"


@pytest.mark.asyncio
async def test_update_config_allows_blank_optional_fields(aiohttp_client):
    _, app = build_with_guild(channels=[], roles=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config())
    assert resp.status == 200


@pytest.mark.asyncio
async def test_update_config_requires_auth(aiohttp_client):
    _, app = build_with_guild()
    client = await aiohttp_client(app)
    resp = await client.put("/api/config", json=_full_config())
    assert resp.status == 401


@pytest.mark.asyncio
async def test_update_config_round_trips_via_get(aiohttp_client):
    channel = FakeChannel(500, name="webhook-log")
    role = FakeRole(200, name="Supply")
    _, app = build_with_guild(channels=[channel], roles=[role])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.put("/api/config", json=_full_config(LOG_CHANNEL_ID="500", SUPPLY_ROLE_ID="200"))
    resp = await client.get("/api/config")
    body = await resp.json()
    assert body["LOG_CHANNEL_ID"] == "500"
    assert body["SUPPLY_ROLE_ID"] == "200"


@pytest.mark.asyncio
async def test_put_config_preserves_foreign_keys(aiohttp_client):
    """PUT /api/config не должен затирать ключи других разделов (авто-роли, приветствия)."""
    bot_config.save_config(1,
        {
            "AUTO_ROLE_IDS": ["42"],
            "WELCOME_CHANNEL_ENABLED": False,
            "WELCOME_DM_ENABLED": True,
        }
    )
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/config")
    body = await resp.json()

    resp = await client.put("/api/config", json=body)
    assert resp.status == 200

    stored = bot_config.load_config(1)
    assert stored["AUTO_ROLE_IDS"] == ["42"]
    assert stored["WELCOME_CHANNEL_ENABLED"] is False
    assert stored["WELCOME_DM_ENABLED"] is True
