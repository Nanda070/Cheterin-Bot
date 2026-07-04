import discord
import pytest

import embed_builder
from dashboard.backend.routes.embed_builder import routes as embed_builder_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeComponentRow,
    FakeGuild,
    FakeMember,
    FakeMessage,
    FakeRole,
    force_login,
    make_moderation_app,
)


def build(roles=None, channels=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot_top = FakeRole(900, name="bot-role", position=50)
    me = FakeMember(1, name="bot", top_role=bot_top)
    guild = FakeGuild(members=[moderator], roles=roles or [], channels=channels or [], me=me)
    return guild, make_moderation_app(FakeBot(guild), [embed_builder_routes])


@pytest.mark.asyncio
async def test_create_embed_message_success(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    channel = FakeChannel(500, next_message_id=999)
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages",
        json={"channel_id": "500", "content": "Hello", "embed": {"title": "Title"}, "role_ids": ["7"]},
    )
    assert resp.status == 201
    body = await resp.json()
    assert body == {"message_id": "999", "channel_id": "500"}
    assert channel.send_calls[0]["content"] == "Hello"
    assert channel.send_calls[0]["embed"].title == "Title"
    assert channel.send_calls[0]["view"].children[0].custom_id == "btn_role_7"


@pytest.mark.asyncio
async def test_create_embed_message_rejects_empty_embed(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/embed-messages", json={"channel_id": "500", "embed": {}, "role_ids": []})
    assert resp.status == 400
    assert (await resp.json())["error"] == "empty_embed"


@pytest.mark.asyncio
async def test_create_embed_message_rejects_too_many_roles(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages",
        json={"channel_id": "500", "embed": {"title": "T"}, "role_ids": ["1", "2", "3", "4", "5", "6"]},
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "too_many_roles"


@pytest.mark.asyncio
async def test_create_embed_message_checks_channel_before_role_assignability(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    _, app = build(roles=[role], channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages", json={"channel_id": "500", "embed": {"title": "T"}, "role_ids": ["9"]}
    )
    assert resp.status == 404
    assert (await resp.json())["error"] == "channel_not_found"


@pytest.mark.asyncio
async def test_create_embed_message_rejects_role_above_bot(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    channel = FakeChannel(500)
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages", json={"channel_id": "500", "embed": {"title": "T"}, "role_ids": ["9"]}
    )
    assert resp.status == 403


@pytest.mark.asyncio
async def test_create_embed_message_channel_not_found(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/embed-messages", json={"channel_id": "500", "embed": {"title": "T"}})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_create_embed_message_discord_error_logged(aiohttp_client):
    channel = FakeChannel(500)
    channel.send_raises = discord.HTTPException.__new__(discord.HTTPException)
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/embed-messages", json={"channel_id": "500", "embed": {"title": "T"}})
    assert resp.status == 502


@pytest.mark.asyncio
async def test_create_embed_message_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/embed-messages", json={"channel_id": "500", "embed": {"title": "T"}})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_get_embed_message_returns_parsed_spec_and_roles(aiohttp_client):
    embed = embed_builder.build_embed({"title": "Existing", "description": "Desc"})
    row = FakeComponentRow([discord.ui.Button(label="VIP", custom_id="btn_role_7")])
    message = FakeMessage(999, embeds=[embed], components=[row], content="hi")
    channel = FakeChannel(500, messages={999: message})
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/embed-messages/500/999")
    assert resp.status == 200
    body = await resp.json()
    assert body["content"] == "hi"
    assert body["embed"]["title"] == "Existing"
    assert body["role_ids"] == ["7"]


@pytest.mark.asyncio
async def test_get_embed_message_404_when_message_missing(aiohttp_client):
    channel = FakeChannel(500, messages={})
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/embed-messages/500/999")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_get_embed_message_404_when_channel_missing(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/embed-messages/500/999")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_update_embed_message_success(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/embed-messages/500/999",
        json={"content": "updated", "embed": {"title": "Updated"}, "role_ids": ["7"]},
    )
    assert resp.status == 200
    assert message.edit_calls[0]["content"] == "updated"
    assert message.edit_calls[0]["embed"].title == "Updated"


@pytest.mark.asyncio
async def test_update_embed_message_checks_message_before_role_assignability(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    channel = FakeChannel(500, messages={})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/embed-messages/500/999", json={"embed": {"title": "T"}, "role_ids": ["9"]})
    assert resp.status == 404
    assert (await resp.json())["error"] == "message_not_found"


@pytest.mark.asyncio
async def test_update_embed_message_rejects_role_above_bot(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/embed-messages/500/999", json={"embed": {"title": "T"}, "role_ids": ["9"]})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_update_embed_message_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.put("/api/embed-messages/500/999", json={"embed": {"title": "T"}})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_create_embed_message_allows_content_only(aiohttp_client):
    channel = FakeChannel(500, next_message_id=999)
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages",
        json={"channel_id": "500", "content": "Just text", "embed": {}, "role_ids": []},
    )
    assert resp.status == 201
    assert channel.send_calls[0]["content"] == "Just text"
    assert channel.send_calls[0]["embed"] is None


@pytest.mark.asyncio
async def test_create_embed_message_rejects_blank_content_and_empty_embed(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages", json={"channel_id": "500", "content": "   ", "embed": {}, "role_ids": []}
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "empty_embed"


@pytest.mark.asyncio
async def test_update_embed_message_allows_content_only(aiohttp_client):
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/embed-messages/500/999",
        json={"content": "Just text", "embed": {}, "role_ids": []},
    )
    assert resp.status == 200
    assert message.edit_calls[0]["content"] == "Just text"
    assert message.edit_calls[0]["embed"] is None
