import discord
import pytest

import bot.modules.community.reaction_roles as reaction_roles
import bot.core.settings_db as settings_db
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
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


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
    assert reaction_roles.load_config(1)["999"]["channel_id"] == "500"


@pytest.mark.asyncio
async def test_create_reaction_role_succeeds_even_if_add_reaction_fails(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    message = FakeMessage(999)
    message.add_reaction_raises = discord.HTTPException.__new__(discord.HTTPException)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    assert resp.status == 201
    assert reaction_roles.load_config(1)["999"]["channel_id"] == "500"


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


@pytest.mark.asyncio
async def test_create_reaction_role_checks_channel_before_role_assignability(aiohttp_client):
    # Role is not assignable AND channel doesn't exist. Must get 404 channel_not_found,
    # not 403 role_not_assignable -- proves channel existence is checked before role
    # assignability, per the plan's binding validation order.
    role = FakeRole(9, name="TooHigh", position=60)
    _, app = build(roles=[role], channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "9"}]},
    )
    assert resp.status == 404
    assert (await resp.json())["error"] == "channel_not_found"


@pytest.mark.asyncio
async def test_update_reaction_role_syncs_reactions(aiohttp_client):
    role_a = FakeRole(7, name="A", position=5)
    role_b = FakeRole(8, name="B", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role_a, role_b], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    message.reaction_calls.clear()

    resp = await client.put(
        "/api/reaction-roles/999", json={"pairs": [{"emoji": "✅", "role_id": "8"}]}
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["pairs"] == [{"emoji": "✅", "role_id": "8"}]
    assert ("remove", "📖") in message.reaction_calls
    assert ("add", "✅") in message.reaction_calls


@pytest.mark.asyncio
async def test_update_reaction_role_404_when_unknown(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    _, app = build(roles=[role])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/reaction-roles/999", json={"pairs": [{"emoji": "📖", "role_id": "7"}]})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_update_reaction_role_resets_binding_when_message_gone(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    del channel._messages[999]  # simulate the message being deleted in Discord

    resp = await client.put("/api/reaction-roles/999", json={"pairs": [{"emoji": "✅", "role_id": "7"}]})
    assert resp.status == 404
    assert reaction_roles.load_config(1) == {}


@pytest.mark.asyncio
async def test_update_reaction_role_checks_message_before_role_assignability(aiohttp_client):
    # Message no longer exists AND the new pairs include a non-assignable role.
    # Must get 404 message_not_found, not 403 role_not_assignable -- proves
    # message existence is checked before role assignability on PUT too.
    role = FakeRole(7, name="VIP", position=5)
    too_high_role = FakeRole(9, name="TooHigh", position=60)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role, too_high_role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    del channel._messages[999]

    resp = await client.put("/api/reaction-roles/999", json={"pairs": [{"emoji": "✅", "role_id": "9"}]})
    assert resp.status == 404
    assert (await resp.json())["error"] == "message_not_found"


@pytest.mark.asyncio
async def test_delete_reaction_role_removes_config_and_reactions(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    resp = await client.delete("/api/reaction-roles/999")
    assert resp.status == 200
    assert reaction_roles.load_config(1) == {}
    assert ("remove", "📖") in message.reaction_calls


@pytest.mark.asyncio
async def test_delete_reaction_role_404_when_unknown(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.delete("/api/reaction-roles/999")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_list_emojis(aiohttp_client):
    from dashboard.backend.tests.fakes import FakeCustomEmoji

    emoji = FakeCustomEmoji(20, "wave")
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator], emojis=[emoji])
    app = make_moderation_app(FakeBot(guild), [reaction_roles_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/emojis")
    assert resp.status == 200
    body = await resp.json()
    assert body["emojis"] == [{"id": "20", "name": "wave", "url": "https://cdn.example/emojis/20.png"}]


@pytest.mark.asyncio
async def test_list_channels(aiohttp_client):
    channel = FakeChannel(500, name="general")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/channels")
    assert resp.status == 200
    body = await resp.json()
    assert body["channels"] == [
        {
            "id": "500",
            "name": "general",
            "category": "",
            "bot_can_view": True,
            "bot_can_send": True,
        }
    ]


@pytest.mark.asyncio
async def test_list_channels_marks_dead_when_bot_cannot_send(aiohttp_client):
    from dashboard.backend.tests.fakes import FakePermissions

    dead = FakeChannel(
        501,
        name="locked",
        permissions=FakePermissions(view_channel=True, send_messages=False),
    )
    hidden = FakeChannel(
        502,
        name="hidden",
        permissions=FakePermissions(view_channel=False, send_messages=False),
    )
    _, app = build(channels=[dead, hidden])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/channels")
    assert resp.status == 200
    body = await resp.json()
    by_id = {c["id"]: c for c in body["channels"]}
    assert by_id["501"]["bot_can_view"] is True
    assert by_id["501"]["bot_can_send"] is False
    assert by_id["502"]["bot_can_view"] is False
    assert by_id["502"]["bot_can_send"] is False
