import time

import pytest
from aiohttp import web
from aiohttp_session import new_session

import stats_db
from dashboard.backend.audit_middleware import audit_middleware, describe_action
from dashboard.backend.routes.audit import routes as audit_routes
from dashboard.backend.access_middleware import require_dashboard_access
from dashboard.backend.session import setup_session
from dashboard.backend.tests.fakes import TEST_CONFIG, FakeBot, FakeGuild, FakeMember, force_login


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("STATS_DB_PATH", str(tmp_path / "stats.db"))
    stats_db.init()


def build_app():
    moderator = FakeMember(10, name="mod", display_name="Mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator]))

    app = web.Application(middlewares=[audit_middleware])
    app["bot"] = bot
    app["dashboard_config"] = TEST_CONFIG
    app["guild_id"] = 1
    setup_session(app, TEST_CONFIG.session_secret)
    app.add_routes(audit_routes)

    @require_dashboard_access
    async def mutate(request: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    @require_dashboard_access
    async def failing(request: web.Request) -> web.Response:
        return web.json_response({"error": "bad"}, status=400)

    app.router.add_put("/api/config", mutate)
    app.router.add_put("/api/failing", failing)

    async def test_login(request):
        session = await new_session(request)
        session["discord_user_id"] = request.query["user_id"]
        active_guild_id = request.query.get("active_guild_id")
        if active_guild_id:
            session["active_guild_id"] = active_guild_id
        return web.json_response({"ok": True})

    app.router.add_get("/test/login", test_login)
    return app


def test_describe_action_known_and_fallback():
    assert describe_action("PUT", "/api/config") == "audit.action.config"
    assert describe_action("POST", "/api/xp/reset-all") == "audit.action.xp_reset_all"
    assert describe_action("PUT", "/api/wordle") == "audit.action.wordle"
    assert describe_action("POST", "/api/unknown") == "audit.action.other"


def test_normalize_stored_action_maps_legacy_raw_paths():
    from dashboard.backend.audit_middleware import normalize_stored_action

    assert normalize_stored_action("PUT /api/wordle") == "audit.action.wordle"
    assert normalize_stored_action("audit.action.fun") == "audit.action.fun"
    assert normalize_stored_action("POST /api/something-new") == "audit.action.other"


@pytest.mark.asyncio
async def test_successful_mutation_is_audited(aiohttp_client):
    client = await aiohttp_client(build_app())
    await force_login(client, 10)

    resp = await client.put("/api/config", json={})
    assert resp.status == 200

    resp = await client.get("/api/audit")
    assert resp.status == 200
    body = await resp.json()
    assert body["total"] == 1
    entry = body["entries"][0]
    assert entry["action"] == "audit.action.config"
    assert entry["moderator_name"] == "Mod"
    assert entry["moderator_id"] == "10"
    assert abs(entry["ts"] - int(time.time())) < 60
    assert body["moderators"] == [{"id": "10", "name": "Mod"}]


@pytest.mark.asyncio
async def test_failed_mutation_not_audited(aiohttp_client):
    client = await aiohttp_client(build_app())
    await force_login(client, 10)

    resp = await client.put("/api/failing", json={})
    assert resp.status == 400

    resp = await client.get("/api/audit")
    body = await resp.json()
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_get_requests_not_audited(aiohttp_client):
    client = await aiohttp_client(build_app())
    await force_login(client, 10)

    await client.get("/api/audit")
    resp = await client.get("/api/audit")
    body = await resp.json()
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_filter_by_moderator(aiohttp_client):
    client = await aiohttp_client(build_app())
    await force_login(client, 10)
    await client.put("/api/config", json={})

    resp = await client.get("/api/audit?moderator=10")
    assert (await resp.json())["total"] == 1

    resp = await client.get("/api/audit?moderator=999")
    assert (await resp.json())["total"] == 0

    resp = await client.get("/api/audit?moderator=abc")
    assert resp.status == 400


@pytest.mark.asyncio
async def test_filter_by_search_q(aiohttp_client):
    client = await aiohttp_client(build_app())
    await force_login(client, 10)
    await client.put("/api/config", json={})

    resp = await client.get("/api/audit?q=config")
    body = await resp.json()
    assert resp.status == 200
    assert body["total"] == 1

    resp = await client.get("/api/audit?q=Mod")
    assert (await resp.json())["total"] == 1

    resp = await client.get("/api/audit?q=zzznomatch")
    assert (await resp.json())["total"] == 0
