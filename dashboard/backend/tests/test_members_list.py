import pytest

from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)


def build_client_app(members):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator] + members)
    return make_moderation_app(FakeBot(guild), [moderation_routes])


@pytest.mark.asyncio
async def test_lists_members_with_pagination_fields(aiohttp_client):
    members = [FakeMember(100 + i, name=f"user{i}") for i in range(3)]
    client = await aiohttp_client(build_client_app(members))
    await force_login(client, 10)

    resp = await client.get("/api/members")
    assert resp.status == 200
    body = await resp.json()
    assert body["total"] == 4  # moderator + 3
    assert body["page"] == 1
    assert body["page_size"] == 20
    first = body["members"][0]
    assert set(first) == {"id", "username", "display_name", "avatar", "role_count", "joined_at", "is_bot"}


@pytest.mark.asyncio
async def test_search_matches_name_and_display_name_case_insensitive(aiohttp_client):
    named = FakeMember(101, name="SharpShooter")
    nicked = FakeMember(102, name="boring", display_name="ShArP_nick")
    other = FakeMember(103, name="unrelated")
    client = await aiohttp_client(build_client_app([named, nicked, other]))
    await force_login(client, 10)

    resp = await client.get("/api/members?search=sharp")
    body = await resp.json()
    assert body["total"] == 2
    assert {m["id"] for m in body["members"]} == {"101", "102"}


@pytest.mark.asyncio
async def test_pagination_slices_and_caps_page_size(aiohttp_client):
    members = [FakeMember(200 + i, name=f"m{i:03d}") for i in range(30)]
    client = await aiohttp_client(build_client_app(members))
    await force_login(client, 10)

    resp = await client.get("/api/members?page=2&page_size=10")
    body = await resp.json()
    assert body["page"] == 2
    assert len(body["members"]) == 10

    resp = await client.get("/api/members?page_size=5000")
    body = await resp.json()
    assert body["page_size"] == 100


@pytest.mark.asyncio
async def test_invalid_pagination_returns_400(aiohttp_client):
    client = await aiohttp_client(build_client_app([]))
    await force_login(client, 10)
    resp = await client.get("/api/members?page=abc")
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    client = await aiohttp_client(build_client_app([]))
    resp = await client.get("/api/members")
    assert resp.status == 401
