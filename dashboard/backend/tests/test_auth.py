import pytest
from aiohttp import web
from aiohttp_session import get_session

from dashboard.backend.auth import routes
from dashboard.backend.config import DashboardConfig
from dashboard.backend.session import setup_session

CONFIG = DashboardConfig(
    port=8080,
    client_id="test-client-id",
    client_secret="test-client-secret",
    redirect_uri="http://localhost:8080/api/auth/discord/callback",
    session_secret="x" * 32,
    access_role_ids=frozenset({"111"}),
    frontend_url="",
)

CONFIG_WITH_FRONTEND_URL = DashboardConfig(
    port=8080,
    client_id="test-client-id",
    client_secret="test-client-secret",
    redirect_uri="http://localhost:8080/api/auth/discord/callback",
    session_secret="x" * 32,
    access_role_ids=frozenset({"111"}),
    frontend_url="http://localhost:5173",
)


class FakeRole:
    def __init__(self, role_id):
        self.id = role_id


class FakePermissions:
    def __init__(self, administrator=False):
        self.administrator = administrator


class FakeMember:
    def __init__(self, member_id, role_ids, administrator=False):
        self.id = member_id
        self.name = "tester"
        self.display_avatar = None
        self.roles = [FakeRole(r) for r in role_ids]
        self.guild_permissions = FakePermissions(administrator)


class FakeGuild:
    def __init__(self, member=None):
        self._member = member

    def get_member(self, user_id):
        return self._member

    async def fetch_member(self, user_id):
        return self._member


class FakeBot:
    def __init__(self, guild):
        self._guild = guild

    def get_guild(self, guild_id):
        return self._guild


def make_app(bot, http_session_stub, config=CONFIG):
    app = web.Application()
    app["bot"] = bot
    app["dashboard_config"] = config
    app["guild_id"] = 1
    app["http_session"] = http_session_stub
    setup_session(app, config.session_secret)
    app.add_routes(routes)
    return app


class _NullHttpSession:
    """Placeholder; overridden per-test via monkeypatch on discord_oauth functions."""


@pytest.mark.asyncio
async def test_login_redirects_to_discord_and_sets_state_cookie(aiohttp_client):
    app = make_app(FakeBot(FakeGuild()), _NullHttpSession())
    client = await aiohttp_client(app)
    resp = await client.get("/api/auth/login", allow_redirects=False)
    assert resp.status == 302
    assert "discord.com/api/oauth2/authorize" in resp.headers["Location"]
    assert "oauth_state" in resp.cookies


@pytest.mark.asyncio
async def test_me_without_session_returns_401(aiohttp_client):
    app = make_app(FakeBot(FakeGuild()), _NullHttpSession())
    client = await aiohttp_client(app)
    resp = await client.get("/api/auth/me")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_callback_denies_when_role_missing(aiohttp_client, monkeypatch):
    import dashboard.backend.auth as auth_module

    async def fake_exchange(*args, **kwargs):
        return {"access_token": "tok"}

    async def fake_identity(*args, **kwargs):
        return {"id": "999"}

    monkeypatch.setattr(auth_module, "exchange_code_for_token", fake_exchange)
    monkeypatch.setattr(auth_module, "fetch_discord_identity", fake_identity)

    member_without_role = FakeMember(999, role_ids=[])
    app = make_app(FakeBot(FakeGuild(member_without_role)), _NullHttpSession())
    client = await aiohttp_client(app)

    login_resp = await client.get("/api/auth/login", allow_redirects=False)
    state_cookie = login_resp.cookies["oauth_state"].value

    resp = await client.get(
        f"/api/auth/discord/callback?code=abc&state={state_cookie}",
        allow_redirects=False,
    )
    assert resp.status == 302
    assert "/access-denied" in resp.headers["Location"]


@pytest.mark.asyncio
async def test_callback_succeeds_and_me_returns_user(aiohttp_client, monkeypatch):
    import dashboard.backend.auth as auth_module

    async def fake_exchange(*args, **kwargs):
        return {"access_token": "tok"}

    async def fake_identity(*args, **kwargs):
        return {"id": "111"}

    monkeypatch.setattr(auth_module, "exchange_code_for_token", fake_exchange)
    monkeypatch.setattr(auth_module, "fetch_discord_identity", fake_identity)

    member_with_role = FakeMember(111, role_ids=[111])
    app = make_app(FakeBot(FakeGuild(member_with_role)), _NullHttpSession())
    client = await aiohttp_client(app)

    login_resp = await client.get("/api/auth/login", allow_redirects=False)
    state_cookie = login_resp.cookies["oauth_state"].value

    callback_resp = await client.get(
        f"/api/auth/discord/callback?code=abc&state={state_cookie}",
        allow_redirects=False,
    )
    assert callback_resp.status == 302
    assert callback_resp.headers["Location"] == "/"

    me_resp = await client.get("/api/auth/me")
    assert me_resp.status == 200
    body = await me_resp.json()
    assert body["id"] == "111"
    assert body["is_super_admin"] is False


@pytest.mark.asyncio
async def test_me_returns_is_super_admin_true_for_super_admin_role(aiohttp_client, monkeypatch):
    import dashboard.backend.auth as auth_module
    from dashboard.backend.access import SUPER_ADMIN_ROLE_IDS

    async def fake_exchange(*args, **kwargs):
        return {"access_token": "tok"}

    async def fake_identity(*args, **kwargs):
        return {"id": "111"}

    monkeypatch.setattr(auth_module, "exchange_code_for_token", fake_exchange)
    monkeypatch.setattr(auth_module, "fetch_discord_identity", fake_identity)

    super_admin_role_id = int(next(iter(SUPER_ADMIN_ROLE_IDS)))
    member = FakeMember(111, role_ids=[111, super_admin_role_id])
    app = make_app(FakeBot(FakeGuild(member)), _NullHttpSession())
    client = await aiohttp_client(app)

    login_resp = await client.get("/api/auth/login", allow_redirects=False)
    state_cookie = login_resp.cookies["oauth_state"].value
    await client.get(f"/api/auth/discord/callback?code=abc&state={state_cookie}", allow_redirects=False)

    me_resp = await client.get("/api/auth/me")
    body = await me_resp.json()
    assert body["is_super_admin"] is True


@pytest.mark.asyncio
async def test_callback_error_query_redirects_to_login_with_frontend_url(aiohttp_client):
    app = make_app(FakeBot(FakeGuild()), _NullHttpSession(), config=CONFIG_WITH_FRONTEND_URL)
    client = await aiohttp_client(app)

    resp = await client.get(
        "/api/auth/discord/callback?error=access_denied",
        allow_redirects=False,
    )
    assert resp.status == 302
    assert resp.headers["Location"] == "http://localhost:5173/login?auth_error=denied"


@pytest.mark.asyncio
async def test_callback_access_denied_uses_frontend_url(aiohttp_client, monkeypatch):
    import dashboard.backend.auth as auth_module

    async def fake_exchange(*args, **kwargs):
        return {"access_token": "tok"}

    async def fake_identity(*args, **kwargs):
        return {"id": "999"}

    monkeypatch.setattr(auth_module, "exchange_code_for_token", fake_exchange)
    monkeypatch.setattr(auth_module, "fetch_discord_identity", fake_identity)

    member_without_role = FakeMember(999, role_ids=[])
    app = make_app(
        FakeBot(FakeGuild(member_without_role)),
        _NullHttpSession(),
        config=CONFIG_WITH_FRONTEND_URL,
    )
    client = await aiohttp_client(app)

    login_resp = await client.get("/api/auth/login", allow_redirects=False)
    state_cookie = login_resp.cookies["oauth_state"].value

    resp = await client.get(
        f"/api/auth/discord/callback?code=abc&state={state_cookie}",
        allow_redirects=False,
    )
    assert resp.status == 302
    assert resp.headers["Location"] == "http://localhost:5173/access-denied?reason=insufficient_role"


@pytest.mark.asyncio
async def test_callback_succeeds_redirects_to_frontend_url(aiohttp_client, monkeypatch):
    import dashboard.backend.auth as auth_module

    async def fake_exchange(*args, **kwargs):
        return {"access_token": "tok"}

    async def fake_identity(*args, **kwargs):
        return {"id": "111"}

    monkeypatch.setattr(auth_module, "exchange_code_for_token", fake_exchange)
    monkeypatch.setattr(auth_module, "fetch_discord_identity", fake_identity)

    member_with_role = FakeMember(111, role_ids=[111])
    app = make_app(
        FakeBot(FakeGuild(member_with_role)),
        _NullHttpSession(),
        config=CONFIG_WITH_FRONTEND_URL,
    )
    client = await aiohttp_client(app)

    login_resp = await client.get("/api/auth/login", allow_redirects=False)
    state_cookie = login_resp.cookies["oauth_state"].value

    callback_resp = await client.get(
        f"/api/auth/discord/callback?code=abc&state={state_cookie}",
        allow_redirects=False,
    )
    assert callback_resp.status == 302
    assert callback_resp.headers["Location"] == "http://localhost:5173/"


@pytest.mark.asyncio
async def test_logout_clears_session(aiohttp_client, monkeypatch):
    import dashboard.backend.auth as auth_module

    async def fake_exchange(*args, **kwargs):
        return {"access_token": "tok"}

    async def fake_identity(*args, **kwargs):
        return {"id": "111"}

    monkeypatch.setattr(auth_module, "exchange_code_for_token", fake_exchange)
    monkeypatch.setattr(auth_module, "fetch_discord_identity", fake_identity)

    member_with_role = FakeMember(111, role_ids=[111])
    app = make_app(FakeBot(FakeGuild(member_with_role)), _NullHttpSession())
    client = await aiohttp_client(app)

    login_resp = await client.get("/api/auth/login", allow_redirects=False)
    state_cookie = login_resp.cookies["oauth_state"].value
    await client.get(
        f"/api/auth/discord/callback?code=abc&state={state_cookie}",
        allow_redirects=False,
    )

    logout_resp = await client.post("/api/auth/logout")
    assert logout_resp.status == 200

    me_resp = await client.get("/api/auth/me")
    assert me_resp.status == 401
