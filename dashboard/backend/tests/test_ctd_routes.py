"""CTD-настройки — привилегия мейна (Фаза 2b): роут доступен только когда активный
сервер == мейн-сервер приложения; иначе 403 not_main_guild."""

import pytest

import bot_config
import settings_db
from dashboard.backend.routes.ctd import routes as ctd_routes
from dashboard.backend.tests.fakes import (
    FakeChannel,
    FakeBot,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def isolated_settings_db(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build(channels=None, roles=None):
    moderator = FakeMember(10, name="mod", manage_guild=True)
    guild = FakeGuild(members=[moderator], channels=channels or [], roles=roles or [])
    return guild, make_moderation_app(FakeBot(guild), [ctd_routes])


@pytest.mark.asyncio
async def test_get_ctd_defaults_on_main_guild(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/ctd")
    assert resp.status == 200
    body = await resp.json()
    assert body == {"CTD_ROLE_ID": "", "CTD_CHANNEL_ID": ""}


@pytest.mark.asyncio
async def test_put_and_get_ctd_round_trip(aiohttp_client):
    role = FakeRole(200, name="Support")
    channel = FakeChannel(300, name="tickets")
    _, app = build(channels=[channel], roles=[role])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/ctd", json={"CTD_ROLE_ID": "200", "CTD_CHANNEL_ID": "300"})
    assert resp.status == 200
    assert (await resp.json()) == {"CTD_ROLE_ID": "200", "CTD_CHANNEL_ID": "300"}

    stored = bot_config.load_config(1)
    assert stored["CTD_ROLE_ID"] == "200"
    assert stored["CTD_CHANNEL_ID"] == "300"


@pytest.mark.asyncio
async def test_put_ctd_404_when_role_missing(aiohttp_client):
    _, app = build(channels=[], roles=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/ctd", json={"CTD_ROLE_ID": "200", "CTD_CHANNEL_ID": ""})
    assert resp.status == 404
    assert (await resp.json())["error"] == "ctd_role_id_not_found"


@pytest.mark.asyncio
async def test_ctd_forbidden_when_active_guild_not_main(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    # Активный сервер (2) отличается от мейна приложения (1) → not_main_guild.
    await force_login(client, 10, active_guild_id="2")

    resp = await client.get("/api/ctd")
    assert resp.status == 403
    assert (await resp.json())["error"] == "not_main_guild"

    resp = await client.put("/api/ctd", json={"CTD_ROLE_ID": "", "CTD_CHANNEL_ID": ""})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_ctd_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/ctd")
    assert resp.status == 401
