import time

import pytest

import bot.modules.games.bunker_db as bunker_db
import bot.core.settings_db as settings_db
from bot.modules.games.bunker import BunkerCog
from dashboard.backend.routes.bunker import routes as bunker_routes
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("BUNKER_DB_PATH", str(tmp_path / "bunker.db"))
    bunker_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build(members=None):
    channel = FakeChannel(500, name="bunker-game")
    guild = FakeGuild(members=members or [], channels=[channel])
    bot = FakeBot(guild)
    return bot, guild, channel, make_moderation_app(bot, [bunker_routes])


def _character(name="Пожарный", used_1=False, used_2=False):
    return {
        "profession": {"name": name, "category": "МЧС", "experience_level": "Эксперт", "has_ability": True},
        "age": {"key": "adult", "label": "Взрослый (35-59 лет)"},
        "gender": "Мужской",
        "body_type": {"key": "strong", "name": "Крепкое"},
        "health": {"severity": "Здоров", "disease_name": None, "category": None},
        "hobby": {"name": "Рыбалка", "category": "Хобби", "experience_level": "Мастер (гуру)"},
        "phobia": {"name": "Без фобий", "type": "Нет"},
        "backpack_item": {"name": "Нож", "category": "Инструменты"},
        "large_item": {"name": "Генератор", "category": "Оборудование"},
        "trait": {"trait": "Альтруист", "category": "Моральная", "behavior_example": "...", "possible_bunker_behavior": "..."},
        "additional_info": {"name": "Бывший спасатель", "category": "Жизненный опыт", "linked_user_id": None},
        "special_abilities": [
            {"name": "Джокер", "category": "Защита", "effect": "эффект 1", "used": used_1},
            {"name": "Сейф", "category": "Защита", "effect": "эффект 2", "used": used_2},
        ],
    }


def _setup_game(guild, channel, phase="discussion", round_number=1, players=None, bunker_capacity=2):
    game = bunker_db.create_game(guild.id, channel.id, 10, 4, 12, 180, 90)
    bunker_db.update_game(
        game["id"], status="active", phase=phase, round_number=round_number,
        phase_deadline_ts=int(time.time()) + 60, bunker_capacity=bunker_capacity,
        catastrophe_name="Ядерная война", catastrophe_description="Ядерный удар накрыл города.",
        bunker_conditions_name="Тесное убежище", bunker_conditions_description="Места мало, запасов на месяц.",
    )
    for user_id, character in (players or {}).items():
        bunker_db.add_player(game["id"], user_id)
        bunker_db.assign_character(game["id"], user_id, character, f"tok-{user_id}")
    return bunker_db.get_game(game["id"])


# ────────────────────────── GET публичное состояние ──────────────────────────

@pytest.mark.asyncio
async def test_public_state_unknown_token(aiohttp_client):
    _, _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/public/bunker/does-not-exist")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_public_state_basic_fields_and_flavor_text(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    _setup_game(guild, channel, players={20: _character()})

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/bunker/tok-20")
    assert resp.status == 200
    body = await resp.json()

    assert body["language"] == "ru"
    assert body["phase"] == "discussion"
    assert body["round_number"] == 1
    assert body["bunker_capacity"] == 2
    assert body["catastrophe_name"] == "Ядерная война"
    assert body["bunker_conditions_name"] == "Тесное убежище"
    assert body["your_alive"] is True
    assert body["your_character"]["profession"]["name"] == "Пожарный"
    assert body["your_revealed_fields"] == []
    assert body["action_required"] is False
    assert body["roster"][0]["avatar_url"] == str(p1.display_avatar.url)
    assert body["alive_players"][0]["avatar_url"] == str(p1.display_avatar.url)


@pytest.mark.asyncio
async def test_public_state_roster_hides_unrevealed_fields_for_others(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    p2 = FakeMember(21, name="p2")
    bot, guild, channel, app = build(members=[p1, p2])
    game = _setup_game(guild, channel, players={20: _character(), 21: _character("Врач")})
    bunker_db.reveal_fields(game["id"], 21, ["profession"])

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/bunker/tok-20")
    body = await resp.json()

    roster_by_id = {p["user_id"]: p for p in body["roster"]}
    assert roster_by_id["20"]["character"]["profession"]["name"] == "Пожарный"  # своя карточка — полностью видна
    assert set(roster_by_id["21"]["character"].keys()) == {"profession"}  # только раскрытое
    assert roster_by_id["21"]["character"]["profession"]["name"] == "Врач"


@pytest.mark.asyncio
async def test_public_state_roster_shows_full_card_for_eliminated_players(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    p2 = FakeMember(21, name="p2")
    bot, guild, channel, app = build(members=[p1, p2])
    game = _setup_game(guild, channel, players={20: _character(), 21: _character("Врач")})
    bunker_db.eliminate_player(game["id"], 21, 1)

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/bunker/tok-20")
    body = await resp.json()

    roster_by_id = {p["user_id"]: p for p in body["roster"]}
    assert roster_by_id["21"]["alive"] is False
    assert roster_by_id["21"]["character"]["profession"]["name"] == "Врач"  # выбывший раскрыт полностью


@pytest.mark.asyncio
async def test_public_state_action_required_only_during_vote(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    game = _setup_game(guild, channel, phase="discussion", players={20: _character()})

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/bunker/tok-20")
    assert (await resp.json())["action_required"] is False

    bunker_db.update_game(game["id"], phase="vote")
    resp = await client.get("/api/public/bunker/tok-20")
    assert (await resp.json())["action_required"] is True


@pytest.mark.asyncio
async def test_public_state_vote_tally_during_vote(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    p2 = FakeMember(22, name="p2")
    bot, guild, channel, app = build(members=[p1, p2])
    game = _setup_game(guild, channel, phase="vote", players={20: _character(), 22: _character("Врач")})
    bunker_db.upsert_vote(game["id"], 1, 20, 22)
    bunker_db.upsert_vote(game["id"], 1, 22, 22)

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/bunker/tok-20")
    body = await resp.json()
    assert body["vote_tally"] == [{"target": "22", "target_display": "p2", "count": 2}]


@pytest.mark.asyncio
async def test_public_state_dead_player_no_action(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    game = _setup_game(guild, channel, phase="vote", players={20: _character()})
    bunker_db.eliminate_player(game["id"], 20, 1)

    client = await aiohttp_client(app)
    resp = await client.get("/api/public/bunker/tok-20")
    body = await resp.json()
    assert body["your_alive"] is False
    assert body["action_required"] is False


# ────────────────────────── POST раскрытие характеристики ──────────────────────────

@pytest.mark.asyncio
async def test_reveal_happy_path_visible_to_others(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    p2 = FakeMember(21, name="p2")
    bot, guild, channel, app = build(members=[p1, p2])
    _setup_game(guild, channel, phase="discussion", players={20: _character(), 21: _character("Врач")})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/reveal", json={"field_keys": ["profession", "age"]})
    assert resp.status == 200

    resp = await client.get("/api/public/bunker/tok-21")
    body = await resp.json()
    roster_by_id = {p["user_id"]: p for p in body["roster"]}
    assert set(roster_by_id["20"]["character"].keys()) == {"profession", "age"}


@pytest.mark.asyncio
async def test_reveal_unknown_token(aiohttp_client):
    _, _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/nope/reveal", json={"field_keys": ["profession"]})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_reveal_wrong_phase(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    _setup_game(guild, channel, phase="vote", players={20: _character()})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/reveal", json={"field_keys": ["profession"]})
    assert resp.status == 400
    assert (await resp.json())["error"] == "wrong_phase"


@pytest.mark.asyncio
async def test_reveal_invalid_field_key(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    _setup_game(guild, channel, phase="discussion", players={20: _character()})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/reveal", json={"field_keys": ["special_abilities"]})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_field_keys"


@pytest.mark.asyncio
async def test_reveal_dead_player(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    game = _setup_game(guild, channel, phase="discussion", players={20: _character()})
    bunker_db.eliminate_player(game["id"], 20, 1)

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/reveal", json={"field_keys": ["profession"]})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_reveal_game_not_active(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    game = _setup_game(guild, channel, phase="discussion", players={20: _character()})
    bunker_db.update_game(game["id"], status="finished")

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/reveal", json={"field_keys": ["profession"]})
    assert resp.status == 410


# ────────────────────────── POST голос за исключение ──────────────────────────

@pytest.mark.asyncio
async def test_vote_happy_path_and_resubmit(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    p2 = FakeMember(22, name="p2")
    bot, guild, channel, app = build(members=[p1, p2])
    _setup_game(guild, channel, phase="vote", players={20: _character(), 22: _character("Врач")})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/vote", json={"target_user_id": "22"})
    assert resp.status == 200

    resp = await client.get("/api/public/bunker/tok-20")
    assert (await resp.json())["your_submitted_target"] == "22"

    resp = await client.post("/api/public/bunker/tok-20/vote", json={"target_user_id": None})
    assert resp.status == 200
    resp = await client.get("/api/public/bunker/tok-20")
    body = await resp.json()
    assert body["your_vote_submitted"] is True
    assert body["your_submitted_target"] is None


@pytest.mark.asyncio
async def test_vote_unknown_token(aiohttp_client):
    _, _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/nope/vote", json={"target_user_id": None})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_vote_wrong_phase(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    _setup_game(guild, channel, phase="discussion", players={20: _character()})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/vote", json={"target_user_id": None})
    assert resp.status == 400
    assert (await resp.json())["error"] == "wrong_phase"


@pytest.mark.asyncio
async def test_vote_dead_player(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    game = _setup_game(guild, channel, phase="vote", players={20: _character()})
    bunker_db.eliminate_player(game["id"], 20, 1)

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/vote", json={"target_user_id": None})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_vote_game_not_active(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    game = _setup_game(guild, channel, phase="vote", players={20: _character()})
    bunker_db.update_game(game["id"], status="finished")

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/vote", json={"target_user_id": None})
    assert resp.status == 410


@pytest.mark.asyncio
async def test_vote_invalid_target_not_alive(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    _setup_game(guild, channel, phase="vote", players={20: _character()})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/vote", json={"target_user_id": "999"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_target"


@pytest.mark.asyncio
async def test_vote_self_target_allowed(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    _setup_game(guild, channel, phase="vote", players={20: _character()})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/vote", json={"target_user_id": "20"})
    assert resp.status == 200


@pytest.mark.asyncio
async def test_vote_negative_bot_target_and_stored_display_name(aiohttp_client):
    """Fake-lobby bots use negative user ids; vote + roster must accept them."""
    from bot.modules.games.game_test_lobby import fake_avatar_url, fake_user_id

    host = FakeMember(20, name="host", display_name="Host")
    bot_id = fake_user_id(0)
    _, guild, channel, app = build(members=[host])
    game = bunker_db.create_game(guild.id, channel.id, 10, 4, 12, 180, 90)
    bunker_db.update_game(
        game["id"], status="active", phase="vote", round_number=1,
        phase_deadline_ts=int(time.time()) + 60, bunker_capacity=2,
    )
    bunker_db.add_player(game["id"], 20, display_name="Host")
    bunker_db.assign_character(game["id"], 20, _character(), "tok-20")
    bunker_db.add_player(
        game["id"], bot_id, display_name="Alex Bot", avatar_url=fake_avatar_url("Alex Bot"),
    )
    bunker_db.assign_character(game["id"], bot_id, _character("Врач"), f"tok-{bot_id}")

    client = await aiohttp_client(app)

    resp = await client.get("/api/public/bunker/tok-20")
    assert resp.status == 200
    body = await resp.json()
    alive_by_id = {p["user_id"]: p for p in body["alive_players"]}
    assert alive_by_id[str(bot_id)]["display_name"] == "Alex Bot"
    roster_by_id = {p["user_id"]: p for p in body["roster"]}
    assert roster_by_id[str(bot_id)]["display_name"] == "Alex Bot"

    resp = await client.post(
        "/api/public/bunker/tok-20/vote",
        json={"target_user_id": str(bot_id)},
    )
    assert resp.status == 200

    resp = await client.get("/api/public/bunker/tok-20")
    body = await resp.json()
    assert body["your_submitted_target"] == str(bot_id)
    assert any(
        entry["target"] == str(bot_id) and entry["target_display"] == "Alex Bot"
        for entry in body["vote_tally"]
    )


@pytest.mark.asyncio
async def test_vote_deadline_passed(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    game = _setup_game(guild, channel, phase="vote", players={20: _character()})
    bunker_db.update_game(game["id"], phase_deadline_ts=int(time.time()) - 10)

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/vote", json={"target_user_id": None})
    assert resp.status == 409


@pytest.mark.asyncio
async def test_vote_triggers_early_resolution_and_continues_when_above_capacity(aiohttp_client):
    members = [FakeMember(uid, name=f"p{uid}") for uid in (20, 21, 22, 23)]
    bot, guild, channel, app = build(members=members)
    game = _setup_game(
        guild, channel, phase="vote", bunker_capacity=2,
        players={uid: _character(f"prof-{uid}") for uid in (20, 21, 22, 23)},
    )

    client = await aiohttp_client(app)
    cog = BunkerCog(bot)
    bot.get_cog = lambda name: cog if name == "BunkerCog" else None

    for uid in (20, 21, 22):
        resp = await client.post(f"/api/public/bunker/tok-{uid}/vote", json={"target_user_id": "23"})
        assert resp.status == 200
    assert bunker_db.get_game(game["id"])["phase"] == "vote"  # ещё не все проголосовали

    resp = await client.post("/api/public/bunker/tok-23/vote", json={"target_user_id": "23"})
    assert resp.status == 200

    updated = bunker_db.get_game(game["id"])
    assert updated["phase"] == "discussion"
    assert updated["round_number"] == 2

    victim = bunker_db.get_player(game["id"], 23)
    assert victim["alive"] == 0

    task = cog._timers.get(game["id"])
    if task:
        task.cancel()


# ────────────────────────── POST заявка на спец. возможность ──────────────────────────

@pytest.mark.asyncio
async def test_ability_happy_path_marks_card_used_and_announces(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    p2 = FakeMember(21, name="p2")
    bot, guild, channel, app = build(members=[p1, p2])
    game = _setup_game(guild, channel, phase="discussion", players={20: _character(), 21: _character("Врач")})

    client = await aiohttp_client(app)
    cog = BunkerCog(bot)
    bot.get_cog = lambda name: cog if name == "BunkerCog" else None

    resp = await client.post(
        "/api/public/bunker/tok-20/ability",
        json={"card_index": 1, "target_user_id": "21", "note": "меняю профессию"},
    )
    assert resp.status == 200

    player = bunker_db.get_player(game["id"], 20)
    assert player["character"]["special_abilities"][0]["used"] is True
    assert player["character"]["special_abilities"][1]["used"] is False

    announcements = bunker_db.list_ability_announcements(game["id"])
    assert len(announcements) == 1
    assert announcements[0]["card_name"] == "Джокер"
    assert announcements[0]["target_user_id"] == 21
    assert len(channel.send_calls) >= 1  # cog.announce_ability отправил сообщение в канал


@pytest.mark.asyncio
async def test_ability_unknown_token(aiohttp_client):
    _, _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/nope/ability", json={"card_index": 1})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_ability_dead_player(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    game = _setup_game(guild, channel, phase="discussion", players={20: _character()})
    bunker_db.eliminate_player(game["id"], 20, 1)

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/ability", json={"card_index": 1})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_ability_game_not_active(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    game = _setup_game(guild, channel, phase="discussion", players={20: _character()})
    bunker_db.update_game(game["id"], status="finished")

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/ability", json={"card_index": 1})
    assert resp.status == 410


@pytest.mark.asyncio
async def test_ability_wrong_phase_during_vote(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    _setup_game(guild, channel, phase="vote", players={20: _character()})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/ability", json={"card_index": 1})
    assert resp.status == 400
    assert (await resp.json())["error"] == "wrong_phase"


@pytest.mark.asyncio
async def test_ability_invalid_card_index(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    _setup_game(guild, channel, phase="discussion", players={20: _character()})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/ability", json={"card_index": 3})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_card_index"


@pytest.mark.asyncio
async def test_ability_already_used(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    _setup_game(guild, channel, phase="discussion", players={20: _character(used_1=True)})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/ability", json={"card_index": 1})
    assert resp.status == 409
    assert (await resp.json())["error"] == "card_already_used"


@pytest.mark.asyncio
async def test_ability_invalid_target(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    bot, guild, channel, app = build(members=[p1])
    _setup_game(guild, channel, phase="discussion", players={20: _character()})

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/ability", json={"card_index": 1, "target_user_id": "999"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_target"


@pytest.mark.asyncio
async def test_ability_target_can_be_eliminated_player(aiohttp_client):
    p1 = FakeMember(20, name="p1")
    p2 = FakeMember(21, name="p2")
    bot, guild, channel, app = build(members=[p1, p2])
    game = _setup_game(guild, channel, phase="discussion", players={20: _character(), 21: _character("Врач")})
    bunker_db.eliminate_player(game["id"], 21, 1)

    client = await aiohttp_client(app)
    resp = await client.post("/api/public/bunker/tok-20/ability", json={"card_index": 2, "target_user_id": "21"})
    assert resp.status == 200
