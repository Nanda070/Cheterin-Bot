import pytest
from datetime import datetime, timedelta, timezone

import bot.modules.games.supply_core as supply_core
import bot.core.timezone_core as timezone_core
from dashboard.backend.routes.supply import routes as supply_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)


GUILD = 1
FIXED_TZ = timezone(timedelta(hours=3), name="MSK")
FIXED_NOW = datetime(2026, 7, 24, 12, 0, tzinfo=FIXED_TZ)


@pytest.fixture(autouse=True)
def stub_timezone(monkeypatch):
    # Avoid ZoneInfo/tzdata dependency on Windows CI/dev hosts.
    monkeypatch.setattr(timezone_core, "now_local", lambda _gid: FIXED_NOW)
    monkeypatch.setattr(timezone_core, "today_local", lambda _gid: "2026-07-24")
    monkeypatch.setattr(timezone_core, "get_tz", lambda _gid: FIXED_TZ)


class FakeSupplyCog:
    def __init__(self):
        self.published = []
        self.finalized = []

    async def publish_supply(self, guild_id, channel, initiator_id, opponent, limit, time_str):
        supply = supply_core.create_supply(guild_id, initiator_id, opponent, limit, time_str)
        supply = supply_core.update_supply(guild_id, supply["id"], channel_id=str(channel.id), message_id="555")
        self.published.append(supply["id"])
        return supply

    async def finalize_supply(self, guild_id, supply_id, reason, status="finished"):
        supply = supply_core.close_supply(guild_id, supply_id, status=status)
        if supply is None:
            return False
        self.finalized.append((supply_id, status))
        return True


def build(with_cog=True):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    member = FakeMember(100, name="fighter", display_name="Fighter")
    channel = FakeChannel(500, name="general")
    bot = FakeBot(FakeGuild(members=[moderator, member], channels=[channel]))
    cog = FakeSupplyCog() if with_cog else None
    bot.get_cog = lambda name: cog
    return bot, cog, make_moderation_app(bot, [supply_routes])


@pytest.mark.asyncio
async def test_overview_empty(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/supply")
    assert resp.status == 200
    assert await resp.json() == {"active": [], "history": [], "stats": []}


@pytest.mark.asyncio
async def test_overview_with_data(aiohttp_client):
    _, _, app = build()
    supply = supply_core.create_supply(GUILD, 10, "Ballas", 2, "15:10")
    supply_core.join_supply(GUILD, supply["id"], 100)
    supply_core.join_supply(GUILD, supply["id"], 100500)  # не участник гильдии

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/supply")
    body = await resp.json()
    assert len(body["active"]) == 1
    active = body["active"][0]
    assert active["opponent"] == "Ballas"
    assert active["participants"][0] == {"id": "100", "display": "Fighter"}
    # Неизвестный участник отображается по ID
    assert active["participants"][1] == {"id": "100500", "display": "100500"}


@pytest.mark.asyncio
async def test_create_supply(aiohttp_client):
    _, cog, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/supply",
        json={"channel_id": "500", "opponent": "Vagos", "limit": 5, "time_str": "15:10"},
    )
    assert resp.status == 201
    body = await resp.json()
    assert body["opponent"] == "Vagos"
    assert body["initiator_id"] == "10"
    assert cog.published == [body["id"]]


@pytest.mark.asyncio
async def test_create_supply_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    base = {"channel_id": "500", "opponent": "Vagos", "limit": 5, "time_str": "15:10"}

    resp = await client.post("/api/supply", json={**base, "opponent": " "})
    assert resp.status == 400
    resp = await client.post("/api/supply", json={**base, "time_str": "25:10"})
    assert resp.status == 400
    resp = await client.post("/api/supply", json={**base, "limit": 0})
    assert resp.status == 400
    resp = await client.post("/api/supply", json={**base, "channel_id": "999"})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_close_and_cancel(aiohttp_client):
    _, cog, app = build()
    supply = supply_core.create_supply(GUILD, 10, "Ballas", 2, "15:10")
    other = supply_core.create_supply(GUILD, 10, "Vagos", 2, "16:10")

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(f"/api/supply/{supply['id']}/close")
    assert resp.status == 200
    assert supply_core.get_supply(GUILD, supply["id"])["status"] == "finished"

    resp = await client.post(f"/api/supply/{other['id']}/cancel")
    assert resp.status == 200
    assert supply_core.get_supply(GUILD, other["id"])["status"] == "cancelled"

    # Повторное закрытие -> 409, несуществующий -> 404
    resp = await client.post(f"/api/supply/{supply['id']}/close")
    assert resp.status == 409
    resp = await client.post("/api/supply/999/close")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/supply")
    assert resp.status == 401
