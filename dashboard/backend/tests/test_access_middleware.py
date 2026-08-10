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
async def test_no_active_guild_returns_400(aiohttp_client):
    moderator = FakeMember(10, role_ids=[111])
    app = make_client_app(FakeBot(FakeGuild(members=[moderator])))
    client = await aiohttp_client(app)
    await force_login(client, 10, active_guild_id=None)
    resp = await client.get("/test/protected")
    assert resp.status == 400
    assert (await resp.json())["error"] == "no_guild_selected"


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


@pytest.mark.asyncio
async def test_super_admin_bypasses_manage_server_on_other_guild(aiohttp_client):
    from dashboard.backend.access import SUPER_ADMIN_ROLE_IDS

    super_role = int(next(iter(SUPER_ADMIN_ROLE_IDS)))
    main_member = FakeMember(10, name="boss", role_ids=[super_role])
    # On the active (other) guild: member without manage / legacy role.
    other_member = FakeMember(10, name="boss")
    main = FakeGuild(members=[main_member], guild_id=1)
    other = FakeGuild(members=[other_member], guild_id=2)
    bot = FakeBot(main, guilds=[main, other])
    app = make_client_app(bot)
    client = await aiohttp_client(app)
    await force_login(client, 10, active_guild_id=2)

    resp = await client.get("/test/protected")
    assert resp.status == 200
    assert (await resp.json())["moderator_id"] == 10


@pytest.mark.asyncio
async def test_super_admin_not_in_target_guild_still_allowed(aiohttp_client):
    from dashboard.backend.access import SUPER_ADMIN_ROLE_IDS

    super_role = int(next(iter(SUPER_ADMIN_ROLE_IDS)))
    main_member = FakeMember(10, name="boss", role_ids=[super_role])
    main = FakeGuild(members=[main_member], guild_id=1)
    other = FakeGuild(members=[], guild_id=2)
    bot = FakeBot(main, guilds=[main, other])
    app = make_client_app(bot)
    client = await aiohttp_client(app)
    await force_login(client, 10, active_guild_id=2)

    resp = await client.get("/test/protected")
    assert resp.status == 200
    assert (await resp.json())["moderator_id"] == 10
