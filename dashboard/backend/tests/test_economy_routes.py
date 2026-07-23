import pytest

import economy_db
import settings_db
from dashboard.backend.routes.economy import routes as economy_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app

GUILD_ID = 1


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("ECONOMY_DB_PATH", str(tmp_path / "economy.db"))
    economy_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    member = FakeMember(20, name="rich", display_name="Rich")
    guild = FakeGuild(members=[moderator, member])
    bot = FakeBot(guild)
    return bot, guild, make_moderation_app(bot, [economy_routes])


@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/economy")
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is False
    assert body["currency_name"] == "монеты"
    assert body["shop_items"] == []


@pytest.mark.asyncio
async def test_put_roundtrip_with_shop(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/economy", json={
        "enabled": True,
        "currency_name": "кредиты",
        "currency_emoji": "💎",
        "text_rate_percent": 100,
        "voice_rate_percent": 25,
        "transfer_enabled": True,
        "transfer_fee_percent": 5,
        "roulette_bets_enabled": True,
        "roulette_max_bet": 500,
        "daily_bonus_enabled": False,
        "daily_base_amount": 100,
        "daily_growth_per_day": 50,
        "daily_max_streak_days": 14,
        "shop_items": [{"role_id": "777", "price": 1000, "name": "VIP"}],
    })
    assert resp.status == 200
    body = await resp.json()
    assert body["currency_name"] == "кредиты"
    assert body["daily_bonus_enabled"] is False
    assert body["daily_max_streak_days"] == 14
    assert len(body["shop_items"]) == 1
    assert body["shop_items"][0]["id"]  # id сгенерирован

    resp = await client.get("/api/economy")
    assert (await resp.json())["roulette_max_bet"] == 500


@pytest.mark.asyncio
async def test_put_roundtrip_with_cosmetic_items(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/economy", json={
        "enabled": True,
        "shop_items": [
            {"type": "frame_color", "color_hex": "#FF00AA", "price": 200, "name": "Розовая рамка"},
            {"type": "title", "title_text": "Легенда", "price": 300, "name": "Титул"},
        ],
    })
    assert resp.status == 200
    body = await resp.json()
    items = {item["type"]: item for item in body["shop_items"]}
    assert items["frame_color"]["color_hex"] == "#FF00AA"
    assert items["title"]["title_text"] == "Легенда"


@pytest.mark.asyncio
async def test_put_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    cases = [
        {"enabled": "да"},
        {"enabled": True, "currency_name": ""},
        {"enabled": True, "text_rate_percent": 5000},
        {"enabled": True, "transfer_fee_percent": 90},
        {"enabled": True, "shop_items": [{"role_id": 0, "price": 100}]},
        {"enabled": True, "shop_items": [{"role_id": 777, "price": 0}]},
        {"enabled": True, "shop_items": "не список"},
        {"enabled": True, "daily_bonus_enabled": "да"},
        {"enabled": True, "daily_max_streak_days": 0},
        {"enabled": True, "daily_base_amount": -1},
        {"enabled": True, "shop_items": [{"type": "unknown", "price": 100}]},
        {"enabled": True, "shop_items": [{"type": "frame_color", "color_hex": "not-a-color", "price": 100}]},
        {"enabled": True, "shop_items": [{"type": "frame_color", "color_hex": "#FFF", "price": 100}]},  # короткий hex
        {"enabled": True, "shop_items": [{"type": "title", "title_text": "", "price": 100}]},
        {"enabled": True, "shop_items": [{"type": "title", "title_text": "x" * 31, "price": 100}]},
        {"enabled": True, "weekly_report_days": "seven"},
        {"enabled": True, "weekly_report_days": 0},
        {"enabled": True, "weekly_report_days": 31},
    ]
    for body in cases:
        resp = await client.put("/api/economy", json=body)
        assert resp.status == 400, body


@pytest.mark.asyncio
async def test_top_returns_names(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    economy_db.add(GUILD_ID, 20, 300, "seed")
    resp = await client.get("/api/economy/top")
    assert resp.status == 200
    body = await resp.json()
    assert body == [{"user_id": "20", "display_name": "Rich", "balance": 300}]


@pytest.mark.asyncio
async def test_set_balance(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/economy/balance", json={"user_id": "20", "balance": 5000})
    assert resp.status == 200
    assert economy_db.get_balance(GUILD_ID, 20) == 5000

    resp = await client.put("/api/economy/balance", json={"user_id": "20", "balance": -5})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_login(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/economy")
    assert resp.status in (401, 403)
