import pytest
from aiohttp import web

from dashboard.backend.access_middleware import require_dashboard_access
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)

routes = web.RouteTableDef()


@routes.get("/test/protected")
@require_dashboard_access
async def protected(request):
    return web.json_response({"moderator_id": request["moderator"].id})


def make_client_app(bot):
    return make_moderation_app(bot, [routes])


@pytest.mark.asyncio
async def test_no_session_returns_401(aiohttp_client):
    moderator = FakeMember(10, role_ids=[111])
    app = make_client_app(FakeBot(FakeGuild(members=[moderator])))
    client = await aiohttp_client(app)
    resp = await client.get("/test/protected")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_member_with_access_reaches_handler(aiohttp_client):
    moderator = FakeMember(10, role_ids=[111])
    app = make_client_app(FakeBot(FakeGuild(members=[moderator])))
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.get("/test/protected")
    assert resp.status == 200
    assert (await resp.json())["moderator_id"] == 10


@pytest.mark.asyncio
async def test_member_without_access_role_gets_403(aiohttp_client):
    intruder = FakeMember(20, role_ids=[999])
    app = make_client_app(FakeBot(FakeGuild(members=[intruder])))
    client = await aiohttp_client(app)
    await force_login(client, 20)
    resp = await client.get("/test/protected")
    assert resp.status == 403


@pytest.mark.asyncio
async def test_member_not_in_guild_gets_403(aiohttp_client):
    app = make_client_app(FakeBot(FakeGuild(members=[])))
    client = await aiohttp_client(app)
    await force_login(client, 30)
    resp = await client.get("/test/protected")
    assert resp.status == 403


@pytest.mark.asyncio
async def test_guild_unavailable_gets_503(aiohttp_client):
    class NoGuildBot(FakeBot):
        def get_guild(self, guild_id):
            return None

    app = make_client_app(NoGuildBot(FakeGuild()))
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.get("/test/protected")
    assert resp.status == 503
