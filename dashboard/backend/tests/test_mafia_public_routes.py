import time

import pytest

import bot.modules.games.mafia_db as mafia_db
import bot.core.settings_db as settings_db
from bot.modules.games.mafia import MafiaCog
from dashboard.backend.routes.mafia import routes as mafia_routes
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("MAFIA_DB_PATH", str(tmp_path / "mafia.db"))
    mafia_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


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
        mafia_db.assign_player_role(game["id"], user_id, role, f"tok-{user_id}")
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
    assert body["language"] == "ru"
    assert body["your_role"] == "mafia"
    assert body["action_required"] is True
    assert body["your_action_submitted"] is True
    assert body["your_submitted_target"] == "22"
    assert {t["user_id"] for t in body["teammates"]} == {"21"}
    assert len(body["mafia_votes"]) == 1
    assert len(body["alive_players"]) == 3
    assert body["roster"][0]["avatar_url"] == str(mafia1.display_avatar.url)
    assert body["teammates"][0]["avatar_url"] == str(mafia2.display_avatar.url)


@pytest.mark.asyncio
async def test_public_state_no_action_during_discussion(aiohttp_client):
    doctor = FakeMember(20, name="doctor")
    bot, guild, channel, app = build(members=[doctor])
    _setup_game(guild, channel, phase="day_discussion", players={20: "doctor"})

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()
    assert body["action_required"] is False


@pytest.mark.asyncio
async def test_public_state_citizen_no_night_action_but_day_vote_required(aiohttp_client):
    citizen = FakeMember(20, name="citizen")
    bot, guild, channel, app = build(members=[citizen])
    game = _setup_game(guild, channel, phase="night", players={20: "citizen"})

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()
    assert body["action_required"] is False

    mafia_db.update_game(game["id"], phase="day_vote")

    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()
    assert body["action_required"] is True


@pytest.mark.asyncio
async def test_public_state_includes_roster_with_hidden_alive_roles(aiohttp_client):
    mafia1 = FakeMember(20, name="mafia1")
    citizen = FakeMember(22, name="citizen")
    bot, guild, channel, app = build(members=[mafia1, citizen])
    game = _setup_game(guild, channel, players={20: "mafia", 22: "citizen"})
    mafia_db.eliminate_player(game["id"], 22, 1, "lynched")

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()

    roster_by_id = {p["user_id"]: p for p in body["roster"]}
    assert roster_by_id["20"]["alive"] is True
    assert roster_by_id["20"]["role"] == "mafia"  # видит свою роль
    assert roster_by_id["22"]["alive"] is False
    assert roster_by_id["22"]["role"] == "citizen"  # роль погибшего раскрыта всем


@pytest.mark.asyncio
async def test_public_state_hides_other_alive_player_roles(aiohttp_client):
    mafia1 = FakeMember(20, name="mafia1")
    doctor = FakeMember(21, name="doctor")
    bot, guild, channel, app = build(members=[mafia1, doctor])
    _setup_game(guild, channel, players={20: "mafia", 21: "doctor"})

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()

    roster_by_id = {p["user_id"]: p for p in body["roster"]}
    assert "role" not in roster_by_id["21"]  # доктор жив и не ты — роль скрыта


@pytest.mark.asyncio
async def test_public_state_vote_tally_during_day_vote(aiohttp_client):
    mafia1 = FakeMember(20, name="mafia1")
    citizen = FakeMember(22, name="citizen")
    bot, guild, channel, app = build(members=[mafia1, citizen])
    game = _setup_game(guild, channel, phase="day_vote", players={20: "mafia", 22: "citizen"})
    mafia_db.upsert_day_vote(game["id"], 1, 20, 22)
    mafia_db.upsert_day_vote(game["id"], 1, 22, 22)

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()

    assert body["vote_tally"] == [{"target": "22", "target_display": "citizen", "count": 2}]


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


# ────────────────────────── POST дневной голос ──────────────────────────

@pytest.mark.asyncio
async def test_vote_happy_path_and_resubmit(aiohttp_client):
    citizen = FakeMember(20, name="citizen")
    target = FakeMember(22, name="target")
    bot, guild, channel, app = build(members=[citizen, target])
    _setup_game(guild, channel, phase="day_vote", players={20: "citizen", 22: "citizen"})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/vote", json={"target_user_id": "22"})
    assert resp.status == 200

    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()
    assert body["your_submitted_target"] == "22"

    resp = await client.post("/api/public/mafia/tok-20/vote", json={"target_user_id": None})
    assert resp.status == 200
    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()
    assert body["your_action_submitted"] is True
    assert body["your_submitted_target"] is None


@pytest.mark.asyncio
async def test_vote_unknown_token(aiohttp_client):
    _, _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/nope/vote", json={"target_user_id": None})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_vote_wrong_phase(aiohttp_client):
    citizen = FakeMember(20, name="citizen")
    bot, guild, channel, app = build(members=[citizen])
    _setup_game(guild, channel, phase="night", players={20: "citizen"})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/vote", json={"target_user_id": None})
    assert resp.status == 400
    assert (await resp.json())["error"] == "wrong_phase"


@pytest.mark.asyncio
async def test_vote_dead_player(aiohttp_client):
    citizen = FakeMember(20, name="citizen")
    bot, guild, channel, app = build(members=[citizen])
    game = _setup_game(guild, channel, phase="day_vote", players={20: "citizen"})
    mafia_db.eliminate_player(game["id"], 20, 1, "killed")

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/vote", json={"target_user_id": None})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_vote_game_not_active(aiohttp_client):
    citizen = FakeMember(20, name="citizen")
    bot, guild, channel, app = build(members=[citizen])
    game = _setup_game(guild, channel, phase="day_vote", players={20: "citizen"})
    mafia_db.update_game(game["id"], status="finished")

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/vote", json={"target_user_id": None})
    assert resp.status == 410


@pytest.mark.asyncio
async def test_vote_invalid_target_not_alive(aiohttp_client):
    citizen = FakeMember(20, name="citizen")
    bot, guild, channel, app = build(members=[citizen])
    _setup_game(guild, channel, phase="day_vote", players={20: "citizen"})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/vote", json={"target_user_id": "999"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_target"


@pytest.mark.asyncio
async def test_vote_self_target_allowed(aiohttp_client):
    citizen = FakeMember(20, name="citizen")
    bot, guild, channel, app = build(members=[citizen])
    _setup_game(guild, channel, phase="day_vote", players={20: "citizen"})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/vote", json={"target_user_id": "20"})
    assert resp.status == 200


@pytest.mark.asyncio
async def test_vote_deadline_passed(aiohttp_client):
    citizen = FakeMember(20, name="citizen")
    bot, guild, channel, app = build(members=[citizen])
    game = _setup_game(guild, channel, phase="day_vote", players={20: "citizen"})
    mafia_db.update_game(game["id"], phase_deadline_ts=int(time.time()) - 10)

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/mafia/tok-20/vote", json={"target_user_id": None})
    assert resp.status == 409


@pytest.mark.asyncio
async def test_vote_triggers_early_day_vote_resolution(aiohttp_client):
    # 1 мафия + 3 мирных: после казни одного мирного паритет ещё не наступает, игра продолжается.
    mafia1 = FakeMember(20, name="mafia1")
    citizen1 = FakeMember(21, name="citizen1")
    citizen2 = FakeMember(22, name="citizen2")
    citizen3 = FakeMember(23, name="citizen3")
    bot, guild, channel, app = build(members=[mafia1, citizen1, citizen2, citizen3])
    game = _setup_game(
        guild, channel, phase="day_vote",
        players={20: "mafia", 21: "citizen", 22: "citizen", 23: "citizen"},
    )

    client = await aiohttp_client(app)

    cog = MafiaCog(bot)
    bot.get_cog = lambda name: cog if name == "MafiaCog" else None

    for uid in (20, 21, 22):
        resp = await client.post(f"/api/public/mafia/tok-{uid}/vote", json={"target_user_id": "22"})
        assert resp.status == 200
    # Ещё не все проголосовали -- фаза не должна смениться.
    assert mafia_db.get_game(game["id"])["phase"] == "day_vote"

    resp = await client.post("/api/public/mafia/tok-23/vote", json={"target_user_id": "22"})
    assert resp.status == 200

    updated = mafia_db.get_game(game["id"])
    assert updated["phase"] == "night"
    assert updated["round_number"] == 2

    victim = mafia_db.get_player(game["id"], 22)
    assert victim["alive"] == 0
    assert victim["eliminated_reason"] == "lynched"

    task = cog._timers.get(game["id"])
    if task:
        task.cancel()


@pytest.mark.asyncio
async def test_vote_negative_bot_target_and_stored_display_name(aiohttp_client):
    """Fake-lobby bots use negative user ids; vote + roster must accept them."""
    from bot.modules.games.game_test_lobby import fake_avatar_url, fake_user_id

    host = FakeMember(20, name="host", display_name="Host")
    bot_id = fake_user_id(0)
    _, guild, channel, app = build(members=[host])
    game = mafia_db.create_game(guild.id, channel.id, 10, 5, 20, 60, 120, 60)
    mafia_db.update_game(
        game["id"], status="active", phase="day_vote", round_number=1,
        phase_deadline_ts=int(time.time()) + 60,
    )
    mafia_db.add_player(game["id"], 20, display_name="Host")
    mafia_db.assign_player_role(game["id"], 20, "citizen", "tok-20")
    mafia_db.add_player(
        game["id"], bot_id, display_name="Alex Bot", avatar_url=fake_avatar_url("Alex Bot"),
    )
    mafia_db.assign_player_role(game["id"], bot_id, "citizen", f"tok-{bot_id}")

    client = await aiohttp_client(app)

    resp = await client.get("/api/public/mafia/tok-20")
    assert resp.status == 200
    body = await resp.json()
    alive_by_id = {p["user_id"]: p for p in body["alive_players"]}
    assert alive_by_id[str(bot_id)]["display_name"] == "Alex Bot"
    roster_by_id = {p["user_id"]: p for p in body["roster"]}
    assert roster_by_id[str(bot_id)]["display_name"] == "Alex Bot"

    resp = await client.post(
        "/api/public/mafia/tok-20/vote",
        json={"target_user_id": str(bot_id)},
    )
    assert resp.status == 200

    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()
    assert body["your_submitted_target"] == str(bot_id)
    assert any(
        entry["target"] == str(bot_id) and entry["target_display"] == "Alex Bot"
        for entry in body["vote_tally"]
    )


@pytest.mark.asyncio
async def test_night_action_negative_bot_target(aiohttp_client):
    """Night actions must accept synthetic negative bot seat ids."""
    from bot.modules.games.game_test_lobby import fake_user_id

    mafia1 = FakeMember(20, name="mafia1")
    bot_id = fake_user_id(0)
    _, guild, channel, app = build(members=[mafia1])
    game = mafia_db.create_game(guild.id, channel.id, 10, 5, 20, 60, 120, 60)
    mafia_db.update_game(
        game["id"], status="active", phase="night", round_number=1,
        phase_deadline_ts=int(time.time()) + 60,
    )
    mafia_db.add_player(game["id"], 20, display_name="Mafia")
    mafia_db.assign_player_role(game["id"], 20, "mafia", "tok-20")
    mafia_db.add_player(game["id"], bot_id, display_name="Alex Bot")
    mafia_db.assign_player_role(game["id"], bot_id, "citizen", f"tok-{bot_id}")

    client = await aiohttp_client(app)
    resp = await client.post(
        "/api/public/mafia/tok-20/action",
        json={"target_user_id": str(bot_id)},
    )
    assert resp.status == 200

    resp = await client.get("/api/public/mafia/tok-20")
    body = await resp.json()
    assert body["your_action_submitted"] is True
    assert body["your_submitted_target"] == str(bot_id)
