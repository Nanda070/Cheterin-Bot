import time

import pytest

import mafia_core
import mafia_db
from mafia import MafiaCog
from dashboard.backend.routes.mafia import routes as mafia_routes
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("MAFIA_DB_PATH", str(tmp_path / "mafia.db"))
    mafia_db.init()
    monkeypatch.setattr(mafia_core, "CONFIG_FILE", str(tmp_path / "mafia_config.json"))
    monkeypatch.setattr(mafia_core, "_cache", None, raising=False)
    monkeypatch.setattr(mafia_core, "_cache_mtime", None, raising=False)


def build(members=None):
    channel = FakeChannel(500, name="mafia-game")
    guild = FakeGuild(members=members or [], channels=[channel])
    bot = FakeBot(guild)
    return bot, guild, channel, make_moderation_app(bot, [mafia_routes])


def _setup_game(guild, channel, phase="night", round_number=1, players=None):
    game = mafia_db.create_game(guild.id, channel.id, 10, 5, 20, 60, 120, 60)
    mafia_db.update_game(
        game["id"], status="active", phase=phase, round_number=round_number,
        phase_deadline_ts=int(time.time()) + 60,
    )
    for user_id, role in (players or {}).items():
        mafia_db.add_player(game["id"], user_id)
        token = f"tok-{user_id}" if role in mafia_core.NIGHT_ACTION_ROLES else None
        mafia_db.assign_player_role(game["id"], user_id, role, token)
    return mafia_db.get_game(game["id"])


# ────────────────────────── GET публичное состояние ──────────────────────────

@pytest.mark.asyncio
async def test_public_state_unknown_token(aiohttp_client):
    _, _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/public/mafia/does-not-exist")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_public_state_mafia_sees_teammates_and_votes(aiohttp_client):
    mafia1 = FakeMember(20, name="mafia1")
    mafia2 = FakeMember(21, name="mafia2")
    citizen = FakeMember(22, name="citizen")
    bot, guild, channel, app = build(members=[mafia1, mafia2, citizen])
    game = _setup_game(guild, channel, players={20: "mafia", 21: "mafia", 22: "citizen"})
    mafia_db.upsert_night_action(game["id"], 1, 20, "mafia", 22)

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/mafia/tok-20")
    assert resp.status == 200
    body = await resp.json()
    assert body["your_role"] == "mafia"
    assert body["action_required"] is True
    assert body["your_action_submitted"] is True
    assert body["your_submitted_target"] == "22"
    assert {t["user_id"] for t in body["teammates"]} == {"21"}
    assert len(body["mafia_votes"]) == 1
    assert len(body["alive_players"]) == 3


@pytest.mark.asyncio
async def test_public_state_no_action_outside_night(aiohttp_client):
    doctor = FakeMember(20, name="doctor")
    bot, guild, channel, app = build(members=[doctor])
    _setup_game(guild, channel, phase="day_vote", players={20: "doctor"})

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()
    assert body["action_required"] is False


@pytest.mark.asyncio
async def test_public_state_dead_player_no_action(aiohttp_client):
    doctor = FakeMember(20, name="doctor")
    bot, guild, channel, app = build(members=[doctor])
    game = _setup_game(guild, channel, players={20: "doctor"})
    mafia_db.eliminate_player(game["id"], 20, 1, "killed")

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()
    assert body["your_alive"] is False
    assert body["action_required"] is False


# ────────────────────────── POST действие ──────────────────────────

@pytest.mark.asyncio
async def test_action_happy_path_and_resubmit(aiohttp_client):
    mafia1 = FakeMember(20, name="mafia1")
    citizen = FakeMember(22, name="citizen")
    bot, guild, channel, app = build(members=[mafia1, citizen])
    _setup_game(guild, channel, players={20: "mafia", 22: "citizen"})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/action", json={"target_user_id": "22"})
    assert resp.status == 200

    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()
    assert body["your_submitted_target"] == "22"

    resp = await client.post("/api/public/mafia/tok-20/action", json={"target_user_id": None})
    assert resp.status == 200
    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()
    assert body["your_action_submitted"] is True
    assert body["your_submitted_target"] is None


@pytest.mark.asyncio
async def test_action_unknown_token(aiohttp_client):
    _, _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/nope/action", json={"target_user_id": None})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_action_wrong_phase(aiohttp_client):
    mafia1 = FakeMember(20, name="mafia1")
    bot, guild, channel, app = build(members=[mafia1])
    _setup_game(guild, channel, phase="day_discussion", players={20: "mafia"})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/action", json={"target_user_id": None})
    assert resp.status == 400
    assert (await resp.json())["error"] == "wrong_phase"


@pytest.mark.asyncio
async def test_action_dead_player(aiohttp_client):
    mafia1 = FakeMember(20, name="mafia1")
    bot, guild, channel, app = build(members=[mafia1])
    game = _setup_game(guild, channel, players={20: "mafia"})
    mafia_db.eliminate_player(game["id"], 20, 1, "killed")

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/action", json={"target_user_id": None})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_action_game_not_active(aiohttp_client):
    mafia1 = FakeMember(20, name="mafia1")
    bot, guild, channel, app = build(members=[mafia1])
    game = _setup_game(guild, channel, players={20: "mafia"})
    mafia_db.update_game(game["id"], status="finished")

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/action", json={"target_user_id": None})
    assert resp.status == 410


@pytest.mark.asyncio
async def test_action_invalid_target_not_alive(aiohttp_client):
    mafia1 = FakeMember(20, name="mafia1")
    bot, guild, channel, app = build(members=[mafia1])
    _setup_game(guild, channel, players={20: "mafia"})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/action", json={"target_user_id": "999"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_target"


@pytest.mark.asyncio
async def test_action_self_target_forbidden_for_mafia_and_sheriff(aiohttp_client):
    mafia1 = FakeMember(20, name="mafia1")
    sheriff = FakeMember(21, name="sheriff")
    bot, guild, channel, app = build(members=[mafia1, sheriff])
    _setup_game(guild, channel, players={20: "mafia", 21: "sheriff"})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/action", json={"target_user_id": "20"})
    assert resp.status == 400
    resp = await client.post("/api/public/mafia/tok-21/action", json={"target_user_id": "21"})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_action_self_target_allowed_for_doctor(aiohttp_client):
    doctor = FakeMember(20, name="doctor")
    bot, guild, channel, app = build(members=[doctor])
    _setup_game(guild, channel, players={20: "doctor"})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/action", json={"target_user_id": "20"})
    assert resp.status == 200


@pytest.mark.asyncio
async def test_action_deadline_passed(aiohttp_client):
    mafia1 = FakeMember(20, name="mafia1")
    bot, guild, channel, app = build(members=[mafia1])
    game = _setup_game(guild, channel, players={20: "mafia"})
    mafia_db.update_game(game["id"], phase_deadline_ts=int(time.time()) - 10)

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/action", json={"target_user_id": None})
    assert resp.status == 409


# ────────────────────────── Досрочное завершение ночи ──────────────────────────

@pytest.mark.asyncio
async def test_action_triggers_early_night_resolution(aiohttp_client):
    # Двое мирных остаются живы после убийства одного из трёх -- мафия ещё не в паритете, игра продолжается.
    mafia1 = FakeMember(20, name="mafia1")
    citizen = FakeMember(22, name="citizen")
    citizen2 = FakeMember(23, name="citizen2")
    citizen3 = FakeMember(24, name="citizen3")
    bot, guild, channel, app = build(members=[mafia1, citizen, citizen2, citizen3])
    game = _setup_game(
        guild, channel, players={20: "mafia", 22: "citizen", 23: "citizen", 24: "citizen"}
    )

    client = await aiohttp_client(app)

    cog = MafiaCog(bot)
    bot.get_cog = lambda name: cog if name == "MafiaCog" else None

    resp = await client.post("/api/public/mafia/tok-20/action", json={"target_user_id": "22"})
    assert resp.status == 200

    updated = mafia_db.get_game(game["id"])
    assert updated["phase"] == "day_discussion"

    victim = mafia_db.get_player(game["id"], 22)
    assert victim["alive"] == 0
    assert victim["eliminated_reason"] == "killed"

    assert len(channel.send_calls) >= 1

    task = cog._timers.get(game["id"])
    if task:
        task.cancel()
