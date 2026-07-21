"""Тесты OAuth-логина и выбора сервера (Фаза 2.3, модель MEE6)."""

import pytest
from aiohttp import web

import dashboard.backend.auth as auth_module
from dashboard.backend.auth import routes
from dashboard.backend.config import DashboardConfig
from dashboard.backend.session import setup_session
from dashboard.backend.access import SUPER_ADMIN_ROLE_IDS
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember

CONFIG = DashboardConfig(
    port=8080,
    client_id="test-client-id",
    client_secret="test-client-secret",
    redirect_uri="http://localhost:8080/api/auth/discord/callback",
    session_secret="x" * 32,
    access_role_ids=frozenset(),
    frontend_url="http://localhost:5173",
)


def make_app(bot, config=CONFIG):
    app = web.Application()
    app["bot"] = bot
    app["dashboard_config"] = config
    app["guild_id"] = 1
    app["http_session"] = object()
    setup_session(app, config.session_secret)
    app.add_routes(routes)
    return app


def _patch_oauth(monkeypatch, user_id="111", guilds=None):
    async def fake_exchange(*args, **kwargs):
        return {"access_token": "tok", "refresh_token": "ref", "expires_in": 3600}

    async def fake_identity(*args, **kwargs):
        return {"id": user_id, "username": "tester"}

    async def fake_guilds(*args, **kwargs):
        return guilds if guilds is not None else []

    monkeypatch.setattr(auth_module, "exchange_code_for_token", fake_exchange)
    monkeypatch.setattr(auth_module, "fetch_discord_identity", fake_identity)
    monkeypatch.setattr(auth_module, "fetch_user_guilds", fake_guilds)


async def _login(client):
    resp = await client.get("/api/auth/login", allow_redirects=False)
    return resp.cookies["oauth_state"].value


# ────────────────────────── login / callback ──────────────────────────

@pytest.mark.asyncio
async def test_login_redirects_with_guilds_scope(aiohttp_client):
    app = make_app(FakeBot(FakeGuild()))
    client = await aiohttp_client(app)
    resp = await client.get("/api/auth/login", allow_redirects=False)
    assert resp.status == 302
    loc = resp.headers["Location"]
    assert "discord.com/api/oauth2/authorize" in loc
    assert "identify" in loc and "guilds" in loc
    assert "oauth_state" in resp.cookies


@pytest.mark.asyncio
async def test_callback_logs_in_anyone_and_redirects_to_servers(aiohttp_client, monkeypatch):
    _patch_oauth(monkeypatch, user_id="999")
    # Пользователь даже не участник — всё равно логинится (членство больше не проверяется).
    app = make_app(FakeBot(FakeGuild(members=[])))
    client = await aiohttp_client(app)
    state = await _login(client)

    resp = await client.get(f"/api/auth/discord/callback?code=abc&state={state}", allow_redirects=False)
    assert resp.status == 302
    assert resp.headers["Location"] == "http://localhost:5173/servers"


@pytest.mark.asyncio
async def test_callback_state_mismatch_redirects_to_login(aiohttp_client, monkeypatch):
    _patch_oauth(monkeypatch)
    app = make_app(FakeBot(FakeGuild()))
    client = await aiohttp_client(app)
    await _login(client)
    resp = await client.get("/api/auth/discord/callback?code=abc&state=wrong", allow_redirects=False)
    assert resp.status == 302
    assert "auth_error=state_mismatch" in resp.headers["Location"]


@pytest.mark.asyncio
async def test_callback_error_query_redirects_to_login(aiohttp_client):
    app = make_app(FakeBot(FakeGuild()))
    client = await aiohttp_client(app)
    resp = await client.get("/api/auth/discord/callback?error=access_denied", allow_redirects=False)
    assert resp.status == 302
    assert resp.headers["Location"] == "http://localhost:5173/login?auth_error=denied"


# ────────────────────────── me ──────────────────────────

@pytest.mark.asyncio
async def test_me_without_session_returns_401(aiohttp_client):
    app = make_app(FakeBot(FakeGuild()))
    client = await aiohttp_client(app)
    resp = await client.get("/api/auth/me")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_me_after_login_returns_identity(aiohttp_client, monkeypatch):
    _patch_oauth(monkeypatch, user_id="111")
    member = FakeMember(111, name="tester", administrator=True)
    app = make_app(FakeBot(FakeGuild(members=[member])))
    client = await aiohttp_client(app)
    state = await _login(client)
    await client.get(f"/api/auth/discord/callback?code=abc&state={state}", allow_redirects=False)

    resp = await client.get("/api/auth/me")
    assert resp.status == 200
    body = await resp.json()
    assert body["id"] == "111"
    assert body["active_guild_id"] is None


@pytest.mark.asyncio
async def test_me_is_super_admin_for_super_role_on_main_guild(aiohttp_client, monkeypatch):
    _patch_oauth(monkeypatch, user_id="111")
    super_role_id = int(next(iter(SUPER_ADMIN_ROLE_IDS)))
    member = FakeMember(111, name="boss", role_ids=[super_role_id])
    app = make_app(FakeBot(FakeGuild(members=[member])))
    client = await aiohttp_client(app)
    state = await _login(client)
    await client.get(f"/api/auth/discord/callback?code=abc&state={state}", allow_redirects=False)

    body = await (await client.get("/api/auth/me")).json()
    assert body["is_super_admin"] is True


# ────────────────────────── guilds ──────────────────────────

@pytest.mark.asyncio
async def test_guilds_requires_login(aiohttp_client):
    app = make_app(FakeBot(FakeGuild()))
    client = await aiohttp_client(app)
    resp = await client.get("/api/auth/guilds")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_guilds_returns_manageable_annotated_with_has_bot(aiohttp_client, monkeypatch):
    guilds = [
        {"id": "1", "name": "Managed", "permissions": "32"},   # MANAGE_GUILD → включён
        {"id": "5", "name": "NoPerms", "permissions": "0"},    # без прав → отфильтрован
    ]
    _patch_oauth(monkeypatch, user_id="111", guilds=guilds)
    app = make_app(FakeBot(FakeGuild(members=[FakeMember(111)])))
    client = await aiohttp_client(app)
    state = await _login(client)
    await client.get(f"/api/auth/discord/callback?code=abc&state={state}", allow_redirects=False)

    resp = await client.get("/api/auth/guilds")
    assert resp.status == 200
    body = await resp.json()
    ids = {g["id"] for g in body["guilds"]}
    assert ids == {"1"}
    assert body["guilds"][0]["has_bot"] is True  # FakeBot.get_guild всегда возвращает гильдию


# ────────────────────────── select-guild ──────────────────────────

async def _login_and_callback(client, monkeypatch, user_id, member):
    _patch_oauth(monkeypatch, user_id=user_id)
    state = await _login(client)
    await client.get(f"/api/auth/discord/callback?code=abc&state={state}", allow_redirects=False)


@pytest.mark.asyncio
async def test_select_guild_sets_active_when_manage_server(aiohttp_client, monkeypatch):
    member = FakeMember(111, name="mod", manage_guild=True)
    app = make_app(FakeBot(FakeGuild(members=[member], guild_id=2)))
    client = await aiohttp_client(app)
    await _login_and_callback(client, monkeypatch, "111", member)

    resp = await client.post("/api/auth/select-guild", json={"guild_id": 2})
    assert resp.status == 200
    assert (await resp.json())["guild_id"] == "2"

    body = await (await client.get("/api/auth/me")).json()
    assert body["active_guild_id"] == "2"
    assert body["is_main_guild"] is False  # активен сервер 2, мейн приложения — 1


@pytest.mark.asyncio
async def test_me_is_main_guild_true_when_active_is_main(aiohttp_client, monkeypatch):
    member = FakeMember(111, name="mod", manage_guild=True)
    app = make_app(FakeBot(FakeGuild(members=[member], guild_id=1)))  # app["guild_id"] == 1
    client = await aiohttp_client(app)
    await _login_and_callback(client, monkeypatch, "111", member)

    resp = await client.post("/api/auth/select-guild", json={"guild_id": 1})
    assert resp.status == 200

    body = await (await client.get("/api/auth/me")).json()
    assert body["active_guild_id"] == "1"
    assert body["is_main_guild"] is True


@pytest.mark.asyncio
async def test_select_guild_forbidden_without_manage_server(aiohttp_client, monkeypatch):
    member = FakeMember(111, name="plain")  # без manage_guild/admin
    app = make_app(FakeBot(FakeGuild(members=[member], guild_id=2)))
    client = await aiohttp_client(app)
    await _login_and_callback(client, monkeypatch, "111", member)

    resp = await client.post("/api/auth/select-guild", json={"guild_id": 2})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_select_guild_requires_login(aiohttp_client):
    app = make_app(FakeBot(FakeGuild()))
    client = await aiohttp_client(app)
    resp = await client.post("/api/auth/select-guild", json={"guild_id": 2})
    assert resp.status == 401


# ────────────────────────── invite-url ──────────────────────────

@pytest.mark.asyncio
async def test_invite_url_contains_client_and_permissions(aiohttp_client):
    app = make_app(FakeBot(FakeGuild()))
    client = await aiohttp_client(app)
    resp = await client.get("/api/auth/invite-url?guild_id=2")
    assert resp.status == 200
    url = (await resp.json())["url"]
    assert "client_id=test-client-id" in url
    assert "permissions=" in url
    assert "guild_id=2" in url
    assert "scope=bot" in url


# ────────────────────────── logout ──────────────────────────

@pytest.mark.asyncio
async def test_logout_clears_session(aiohttp_client, monkeypatch):
    _patch_oauth(monkeypatch, user_id="111")
    member = FakeMember(111, name="tester")
    app = make_app(FakeBot(FakeGuild(members=[member])))
    client = await aiohttp_client(app)
    state = await _login(client)
    await client.get(f"/api/auth/discord/callback?code=abc&state={state}", allow_redirects=False)

    assert (await client.post("/api/auth/logout")).status == 200
    assert (await client.get("/api/auth/me")).status == 401
