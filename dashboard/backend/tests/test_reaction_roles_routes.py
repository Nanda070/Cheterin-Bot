import pytest

import reaction_roles
from dashboard.backend.routes.reaction_roles import routes as reaction_roles_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    FakeMessage,
    FakeRole,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(reaction_roles, "CONFIG_FILE", str(tmp_path / "reaction_roles.json"))


def build(roles=None, channels=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot_top = FakeRole(900, name="bot-role", position=50)
    me = FakeMember(1, name="bot", top_role=bot_top)
    guild = FakeGuild(members=[moderator], roles=roles or [], channels=channels or [], me=me)
    return guild, make_moderation_app(FakeBot(guild), [reaction_roles_routes])


@pytest.mark.asyncio
async def test_list_reaction_roles_empty(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/reaction-roles")
    assert resp.status == 200
    assert (await resp.json()) == {"reaction_roles": []}


@pytest.mark.asyncio
async def test_create_reaction_role_success(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    assert resp.status == 201
    body = await resp.json()
    assert body["message_id"] == "999"
    assert body["pairs"] == [{"emoji": "📖", "role_id": "7"}]
    assert message.reaction_calls == [("add", "📖")]
    assert reaction_roles.load_config()["999"]["channel_id"] == "500"


@pytest.mark.asyncio
async def test_create_reaction_role_rejects_duplicate_emoji(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    other_role = FakeRole(8, name="Other", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role, other_role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={
            "channel_id": "500",
            "message_id": "999",
            "pairs": [{"emoji": "📖", "role_id": "7"}, {"emoji": "📖", "role_id": "8"}],
        },
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "duplicate_emoji"


@pytest.mark.asyncio
async def test_create_reaction_role_rejects_role_above_bot(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "9"}]},
    )
    assert resp.status == 403


@pytest.mark.asyncio
async def test_create_reaction_role_channel_not_found(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    _, app = build(roles=[role], channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    assert resp.status == 404


@pytest.mark.asyncio
async def test_create_reaction_role_message_not_found(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    channel = FakeChannel(500, messages={})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    assert resp.status == 404


@pytest.mark.asyncio
async def test_create_reaction_role_empty_pairs_rejected(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles", json={"channel_id": "500", "message_id": "999", "pairs": []}
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/reaction-roles")
    assert resp.status == 401
