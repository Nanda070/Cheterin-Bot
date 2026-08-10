import pytest

from dashboard.backend.access import SUPER_ADMIN_ROLE_IDS
from dashboard.backend.routes.superadmin import routes as superadmin_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


def build(members=None, guilds=None):
    guild = FakeGuild(members=members or [], guild_id=1)
    bot = FakeBot(guild, guilds=guilds)
    return bot, guild, make_moderation_app(bot, [superadmin_routes])


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/superadmin/guilds")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_forbidden_without_super_admin_role(aiohttp_client):
    member = FakeMember(10, name="mod", role_ids=[111])
    _, _, app = build(members=[member])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/superadmin/guilds")
    assert resp.status == 403


@pytest.mark.asyncio
async def test_administrator_has_access(aiohttp_client):
    member = FakeMember(10, name="admin", administrator=True)
    _, _, app = build(members=[member])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/superadmin/guilds")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_returns_all_bot_guilds(aiohttp_client):
    super_admin_role_id = int(next(iter(SUPER_ADMIN_ROLE_IDS)))
    member = FakeMember(10, name="mod", role_ids=[super_admin_role_id])
    guild1 = FakeGuild(members=[member], guild_id=1, name="Основной сервер", member_count=42, owner_id=999)
    guild2 = FakeGuild(members=[], guild_id=2, name="Другой сервер", member_count=7)
    bot = FakeBot(guild1, guilds=[guild1, guild2])
    app = make_moderation_app(bot, [superadmin_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/superadmin/guilds")
    assert resp.status == 200
    body = await resp.json()
    assert len(body["guilds"]) == 2

    first = next(g for g in body["guilds"] if g["id"] == "1")
    assert first["name"] == "Основной сервер"
    assert first["member_count"] == 42
    assert first["owner_id"] == "999"
    assert first["icon"] is None

    second = next(g for g in body["guilds"] if g["id"] == "2")
    assert second["name"] == "Другой сервер"
    assert second["member_count"] == 7
    assert second["owner_id"] is None


@pytest.mark.asyncio
async def test_host_health_requires_super_admin(aiohttp_client):
    member = FakeMember(10, name="mod", role_ids=[111])
    _, _, app = build(members=[member])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/superadmin/host-health")
    assert resp.status == 403


@pytest.mark.asyncio
async def test_host_health_returns_metrics_for_super_admin(aiohttp_client):
    super_admin_role_id = int(next(iter(SUPER_ADMIN_ROLE_IDS)))
    member = FakeMember(10, name="mod", role_ids=[super_admin_role_id])
    _, _, app = build(members=[member])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/superadmin/host-health")
    assert resp.status == 200
    body = await resp.json()
    assert "ram" in body and "disk" in body
    assert "used_bytes" in body["ram"] and "total_bytes" in body["ram"]
    assert "percent" in body["ram"]
    assert "used_bytes" in body["disk"] and "total_bytes" in body["disk"]
    assert "platform" in body
    assert "process" in body
    assert "collected_at" in body
