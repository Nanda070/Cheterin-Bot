import discord
import pytest

from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)


class _StubForbidden(discord.Forbidden):
    def __init__(self):
        pass


def build(members=None, roles=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot_top = FakeRole(900, name="bot-role", position=50)
    me = FakeMember(1, name="bot", top_role=bot_top)
    guild = FakeGuild(members=[moderator] + (members or []), roles=roles or [], me=me)
    return make_moderation_app(FakeBot(guild), [moderation_routes])


@pytest.mark.asyncio
async def test_roles_lists_only_assignable_sorted(aiohttp_client):
    roles = [
        FakeRole(0, name="@everyone", position=0, default=True),
        FakeRole(2, name="Low", position=5),
        FakeRole(3, name="High", position=40),
        FakeRole(4, name="AboveBot", position=60),
        FakeRole(5, name="Integration", position=10, managed=True),
    ]
    client = await aiohttp_client(build(roles=roles))
    await force_login(client, 10)

    resp = await client.get("/api/roles")
    assert resp.status == 200
    body = await resp.json()
    assert [r["name"] for r in body["roles"]] == ["High", "Low"]


@pytest.mark.asyncio
async def test_grant_role_calls_add_roles(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    target = FakeMember(70, name="lucky")
    client = await aiohttp_client(build(members=[target], roles=[role]))
    await force_login(client, 10)

    resp = await client.post("/api/members/70/roles", json={"role_id": "7"})
    assert resp.status == 200
    action, kwargs = target.action_calls[0]
    assert action == "add_roles"
    assert kwargs["role"].id == 7


@pytest.mark.asyncio
async def test_revoke_role_calls_remove_roles(aiohttp_client):
    role = FakeRole(8, name="Temp", position=5)
    target = FakeMember(71, name="temp")
    client = await aiohttp_client(build(members=[target], roles=[role]))
    await force_login(client, 10)

    resp = await client.delete("/api/members/71/roles/8")
    assert resp.status == 200
    action, kwargs = target.action_calls[0]
    assert action == "remove_roles"
    assert kwargs["role"].id == 8


@pytest.mark.asyncio
async def test_grant_unknown_or_unassignable_role_404(aiohttp_client):
    above_bot = FakeRole(9, name="AboveBot", position=60)
    target = FakeMember(72)
    client = await aiohttp_client(build(members=[target], roles=[above_bot]))
    await force_login(client, 10)

    resp = await client.post("/api/members/72/roles", json={"role_id": "12345"})
    assert resp.status == 404
    resp = await client.post("/api/members/72/roles", json={"role_id": "9"})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_grant_forbidden_maps_to_403(aiohttp_client):
    role = FakeRole(11, name="Race", position=5)
    target = FakeMember(73)
    target.action_raises = _StubForbidden()
    client = await aiohttp_client(build(members=[target], roles=[role]))
    await force_login(client, 10)

    resp = await client.post("/api/members/73/roles", json={"role_id": "11"})
    assert resp.status == 403
