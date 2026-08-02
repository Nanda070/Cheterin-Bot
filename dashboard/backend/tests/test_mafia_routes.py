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


@pytest.mark.asyncio
async def test_games_list_filters_by_guild(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    ours = mafia_db.create_game(guild.id, 500, 10, 5, 20, 60, 120, 60)
    foreign = mafia_db.create_game(999, 600, 10, 5, 20, 60, 120, 60)

    resp = await client.get("/api/mafia/games")
    assert resp.status == 200
    ids = {g["id"] for g in (await resp.json())["games"]}
    assert ours["id"] in ids
    assert foreign["id"] not in ids


# ────────────────────────── Управление ведущего ──────────────────────────

class _FakeMafiaCog:
    def __init__(self):
        self.advance_calls = []
        self.end_calls = []
        self.advance_returns = True
        self.end_returns = True

    async def force_advance_phase(self, game_id):
        self.advance_calls.append(game_id)
        return self.advance_returns

    async def force_end_game(self, game_id):
        self.end_calls.append(game_id)
        return self.end_returns


@pytest.mark.asyncio
async def test_game_detail_includes_roster_and_events(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    player = FakeMember(20, name="player20")
    guild.members.append(player)

    game = mafia_db.create_game(guild.id, 500, 10, 5, 20, 60, 120, 60)
    mafia_db.add_player(game["id"], 20)
    mafia_db.assign_player_role(game["id"], 20, "citizen", "tok-20")
    mafia_db.update_game(game["id"], status="active", phase="night", round_number=1)
    mafia_db.add_round_event(game["id"], 1, "game_started", "started")

    resp = await client.get(f"/api/mafia/games/{game['id']}")
    assert resp.status == 200
    body = await resp.json()
    assert body["game"]["id"] == game["id"]
    assert len(body["players"]) == 1
    assert body["players"][0]["display_name"] == "player20"
    assert body["players"][0]["role"] == "citizen"
    assert body["players"][0]["action_submitted"] is False
    assert len(body["events"]) == 1
    assert body["events"][0]["event_type"] == "game_started"


@pytest.mark.asyncio
async def test_game_detail_marks_night_action_submitted(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = mafia_db.create_game(guild.id, 500, 10, 5, 20, 60, 120, 60)
    mafia_db.add_player(game["id"], 20)
    mafia_db.assign_player_role(game["id"], 20, "mafia", "tok-20")
    mafia_db.update_game(game["id"], status="active", phase="night", round_number=1)
    mafia_db.upsert_night_action(game["id"], 1, 20, "mafia", None)

    resp = await client.get(f"/api/mafia/games/{game['id']}")
    assert resp.status == 200
    body = await resp.json()
    assert body["players"][0]["action_submitted"] is True


@pytest.mark.asyncio
async def test_game_detail_rejects_other_guild(aiohttp_client):
    _, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    foreign = mafia_db.create_game(999, 600, 10, 5, 20, 60, 120, 60)
    resp = await client.get(f"/api/mafia/games/{foreign['id']}")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_game_detail_not_found(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.get("/api/mafia/games/999")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_advance_phase_calls_cog(aiohttp_client):
    bot, guild, app = build()
    cog = _FakeMafiaCog()
    bot.get_cog = lambda name: cog if name == "MafiaCog" else None
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = mafia_db.create_game(guild.id, 500, 10, 5, 20, 60, 120, 60)
    resp = await client.post(f"/api/mafia/games/{game['id']}/advance-phase")
    assert resp.status == 200
    assert cog.advance_calls == [game["id"]]


@pytest.mark.asyncio
async def test_advance_phase_rejects_other_guild(aiohttp_client):
    bot, guild, app = build()
    cog = _FakeMafiaCog()
    bot.get_cog = lambda name: cog if name == "MafiaCog" else None
    client = await aiohttp_client(app)
    await force_login(client, 10)

    foreign = mafia_db.create_game(999, 600, 10, 5, 20, 60, 120, 60)
    resp = await client.post(f"/api/mafia/games/{foreign['id']}/advance-phase")
    assert resp.status == 404
    assert cog.advance_calls == []


@pytest.mark.asyncio
async def test_advance_phase_returns_409_when_game_not_active(aiohttp_client):
    bot, guild, app = build()
    cog = _FakeMafiaCog()
    cog.advance_returns = False
    bot.get_cog = lambda name: cog if name == "MafiaCog" else None
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = mafia_db.create_game(guild.id, 500, 10, 5, 20, 60, 120, 60)
    resp = await client.post(f"/api/mafia/games/{game['id']}/advance-phase")
    assert resp.status == 409


@pytest.mark.asyncio
async def test_advance_phase_service_unavailable_without_cog(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = mafia_db.create_game(guild.id, 500, 10, 5, 20, 60, 120, 60)
    resp = await client.post(f"/api/mafia/games/{game['id']}/advance-phase")
    assert resp.status == 503


@pytest.mark.asyncio
async def test_end_game_calls_cog(aiohttp_client):
    bot, guild, app = build()
    cog = _FakeMafiaCog()
    bot.get_cog = lambda name: cog if name == "MafiaCog" else None
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = mafia_db.create_game(guild.id, 500, 10, 5, 20, 60, 120, 60)
    resp = await client.post(f"/api/mafia/games/{game['id']}/end")
    assert resp.status == 200
    assert cog.end_calls == [game["id"]]


@pytest.mark.asyncio
async def test_end_game_rejects_other_guild(aiohttp_client):
    bot, guild, app = build()
    cog = _FakeMafiaCog()
    bot.get_cog = lambda name: cog if name == "MafiaCog" else None
    client = await aiohttp_client(app)
    await force_login(client, 10)

    foreign = mafia_db.create_game(999, 600, 10, 5, 20, 60, 120, 60)
    resp = await client.post(f"/api/mafia/games/{foreign['id']}/end")
    assert resp.status == 404
    assert cog.end_calls == []
