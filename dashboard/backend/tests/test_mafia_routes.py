import pytest

import mafia_core
import mafia_db
import settings_db
from dashboard.backend.routes.mafia import routes as mafia_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("MAFIA_DB_PATH", str(tmp_path / "mafia.db"))
    mafia_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    bot = FakeBot(guild)
    return bot, guild, make_moderation_app(bot, [mafia_routes])


# ────────────────────────── Настройки ──────────────────────────

@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/mafia")
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is False
    assert body["default_min_players"] == mafia_core.DEFAULT_MIN_PLAYERS
    assert body["default_max_players"] == mafia_core.DEFAULT_MAX_PLAYERS


@pytest.mark.asyncio
async def test_put_then_get(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    payload = mafia_core.get_settings(1)
    payload["enabled"] = True
    payload["default_min_players"] = 6
    payload["log_channel_id"] = "42"

    resp = await client.put("/api/mafia", json=payload)
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is True
    assert body["default_min_players"] == 6

    resp = await client.get("/api/mafia")
    assert (await resp.json())["log_channel_id"] == "42"


@pytest.mark.asyncio
async def test_put_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    payload = mafia_core.get_settings(1)
    payload["enabled"] = "yes"
    resp = await client.put("/api/mafia", json=payload)
    assert resp.status == 400

    payload = mafia_core.get_settings(1)
    payload["default_min_players"] = 4
    resp = await client.put("/api/mafia", json=payload)
    assert resp.status == 400

    payload = mafia_core.get_settings(1)
    payload["default_max_players"] = 100
    resp = await client.put("/api/mafia", json=payload)
    assert resp.status == 400

    payload = mafia_core.get_settings(1)
    payload["default_min_players"] = 50
    payload["default_max_players"] = 10
    resp = await client.put("/api/mafia", json=payload)
    assert resp.status == 400

    payload = mafia_core.get_settings(1)
    payload["default_night_timer_sec"] = 5
    resp = await client.put("/api/mafia", json=payload)
    assert resp.status == 400

    payload = mafia_core.get_settings(1)
    payload["log_channel_id"] = "abc"
    resp = await client.put("/api/mafia", json=payload)
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/mafia")
    assert resp.status == 401


# ────────────────────────── Активные игры ──────────────────────────

@pytest.mark.asyncio
async def test_games_list(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = mafia_db.create_game(guild.id, 500, 10, 5, 20, 60, 120, 60)
    mafia_db.add_player(game["id"], 20)
    mafia_db.add_player(game["id"], 21)
    finished = mafia_db.create_game(guild.id, 501, 10, 5, 20, 60, 120, 60)
    mafia_db.update_game(finished["id"], status="finished")

    resp = await client.get("/api/mafia/games")
    assert resp.status == 200
    body = await resp.json()
    ids = {g["id"] for g in body["games"]}
    assert game["id"] in ids
    assert finished["id"] not in ids
    entry = next(g for g in body["games"] if g["id"] == game["id"])
    assert entry["player_count"] == 2
    assert entry["status"] == "lobby"
