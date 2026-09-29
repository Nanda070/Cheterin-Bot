import pytest

import bot.modules.community.giveaway_core as giveaway_core
from dashboard.backend.routes.giveaways import routes as giveaways_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)


GUILD = 1


class FakeGiveawayCog:
    def __init__(self):
        self.published = []
        self.rerolled = []
        self.finalized = []

    async def publish_giveaway(self, guild_id, channel, initiator_id, prize, duration_str, winners_count):
        giveaway = giveaway_core.create_giveaway(guild_id, initiator_id, prize, duration_str, winners_count)
        giveaway = giveaway_core.update_giveaway(guild_id, giveaway["id"], channel_id=str(channel.id), message_id="555")
        self.published.append(giveaway["id"])
        return giveaway

    async def reroll_and_announce(self, guild_id, giveaway_id):
        winners = giveaway_core.reroll_giveaway(guild_id, giveaway_id)
        if winners is not None:
            self.rerolled.append(giveaway_id)
        return winners

    async def finalize_giveaway(self, guild_id, giveaway_id, status="finished"):
        giveaway = giveaway_core.close_giveaway(guild_id, giveaway_id, status=status)
        if giveaway is None:
            return False
        self.finalized.append((giveaway_id, status))
        return True


def build(with_cog=True):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    member = FakeMember(100, name="fighter", display_name="Fighter")
    channel = FakeChannel(500, name="general")
    bot = FakeBot(FakeGuild(members=[moderator, member], channels=[channel]))
    cog = FakeGiveawayCog() if with_cog else None
    bot.get_cog = lambda name: cog
    return bot, cog, make_moderation_app(bot, [giveaways_routes])


@pytest.mark.asyncio
async def test_overview_empty(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/giveaways")
    assert resp.status == 200
    assert await resp.json() == {"active": [], "history": []}


@pytest.mark.asyncio
async def test_overview_with_data(aiohttp_client):
    _, _, app = build()
    giveaway = giveaway_core.create_giveaway(GUILD, 10, "Nitro", "10m", 1)
    giveaway_core.join_giveaway(GUILD, giveaway["id"], 100)
    giveaway_core.join_giveaway(GUILD, giveaway["id"], 100500)  # не участник гильдии

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/giveaways")
    body = await resp.json()
    assert len(body["active"]) == 1
    active = body["active"][0]
    assert active["prize"] == "Nitro"
    assert active["entrants"][0] == {"id": "100", "display": "Fighter"}
    assert active["entrants"][1] == {"id": "100500", "display": "100500"}


@pytest.mark.asyncio
async def test_create_giveaway(aiohttp_client):
    _, cog, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/giveaways",
        json={"channel_id": "500", "prize": "Discord Nitro", "duration_str": "10m", "winners_count": 1},
    )
    assert resp.status == 201
    body = await resp.json()
    assert body["prize"] == "Discord Nitro"
    assert body["initiator_id"] == "10"
    assert cog.published == [body["id"]]


@pytest.mark.asyncio
async def test_create_giveaway_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    base = {"channel_id": "500", "prize": "Приз", "duration_str": "10m", "winners_count": 1}

    resp = await client.post("/api/giveaways", json={**base, "prize": " "})
    assert resp.status == 400
    resp = await client.post("/api/giveaways", json={**base, "duration_str": "не время"})
    assert resp.status == 400
    resp = await client.post("/api/giveaways", json={**base, "winners_count": 0})
    assert resp.status == 400
    resp = await client.post("/api/giveaways", json={**base, "winners_count": 21})
    assert resp.status == 400
    resp = await client.post("/api/giveaways", json={**base, "channel_id": "999"})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_end_giveaway(aiohttp_client):
    _, cog, app = build()
    giveaway = giveaway_core.create_giveaway(GUILD, 10, "Приз", "10m", 1)

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(f"/api/giveaways/{giveaway['id']}/end")
    assert resp.status == 200
    assert giveaway_core.get_giveaway(GUILD, giveaway["id"])["status"] == "finished"

    # Повторное завершение -> 409, несуществующий -> 404
    resp = await client.post(f"/api/giveaways/{giveaway['id']}/end")
    assert resp.status == 409
    resp = await client.post("/api/giveaways/999/end")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_reroll_giveaway(aiohttp_client):
    _, cog, app = build()
    giveaway = giveaway_core.create_giveaway(GUILD, 10, "Приз", "10m", 1)
    giveaway_core.join_giveaway(GUILD, giveaway["id"], 100)
    giveaway_core.join_giveaway(GUILD, giveaway["id"], 200)
    giveaway_core.close_giveaway(GUILD, giveaway["id"], status="finished")

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(f"/api/giveaways/{giveaway['id']}/reroll")
    assert resp.status == 200
    body = await resp.json()
    assert len(body["winners"]) == 1
    assert cog.rerolled == [giveaway["id"]]


@pytest.mark.asyncio
async def test_reroll_not_finished_returns_409(aiohttp_client):
    _, _, app = build()
    giveaway = giveaway_core.create_giveaway(GUILD, 10, "Приз", "10m", 1)

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(f"/api/giveaways/{giveaway['id']}/reroll")
    assert resp.status == 409


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/giveaways")
    assert resp.status == 401
