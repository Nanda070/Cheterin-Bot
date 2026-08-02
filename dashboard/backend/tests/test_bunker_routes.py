import pytest

import bunker_core
import bunker_db
import settings_db
from dashboard.backend.routes.bunker import routes as bunker_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("BUNKER_DB_PATH", str(tmp_path / "bunker.db"))
    bunker_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    bot = FakeBot(guild)
    return bot, guild, make_moderation_app(bot, [bunker_routes])


def _sample_character():
    return {
        "profession": {"name": "Пожарный", "category": "МЧС", "experience_level": "Эксперт", "has_ability": True},
        "age": {"key": "adult", "label": "Взрослый (35-59 лет)"},
        "gender": "Мужской",
        "special_abilities": [
            {"name": "Джокер", "category": "Защита", "effect": "...", "used": False},
            {"name": "Сейф", "category": "Защита", "effect": "...", "used": False},
        ],
    }


# ────────────────────────── Настройки ──────────────────────────

@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/bunker")
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is False
    assert body["default_min_players"] == bunker_core.DEFAULT_MIN_PLAYERS
    assert body["default_max_players"] == bunker_core.DEFAULT_MAX_PLAYERS
    assert body["default_unique_cards"] == bunker_core.DEFAULT_UNIQUE_CARDS


@pytest.mark.asyncio
async def test_put_then_get(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    payload = bunker_core.get_settings(1)
    payload["enabled"] = True
    payload["default_min_players"] = 5
    payload["log_channel_id"] = "42"

    resp = await client.put("/api/bunker", json=payload)
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is True
    assert body["default_min_players"] == 5

    resp = await client.get("/api/bunker")
    assert (await resp.json())["log_channel_id"] == "42"


@pytest.mark.asyncio
async def test_put_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    payload = bunker_core.get_settings(1)
    payload["enabled"] = "yes"
    resp = await client.put("/api/bunker", json=payload)
    assert resp.status == 400

    payload = bunker_core.get_settings(1)
    payload["default_min_players"] = 50
    payload["default_max_players"] = 10
    resp = await client.put("/api/bunker", json=payload)
    assert resp.status == 400

    payload = bunker_core.get_settings(1)
    payload["default_discussion_timer_sec"] = 5
    resp = await client.put("/api/bunker", json=payload)
    assert resp.status == 400

    payload = bunker_core.get_settings(1)
    payload["log_channel_id"] = "abc"
    resp = await client.put("/api/bunker", json=payload)
    assert resp.status == 400

    payload = bunker_core.get_settings(1)
    payload["default_unique_cards"] = "yes"
    resp = await client.put("/api/bunker", json=payload)
    assert resp.status == 400


@pytest.mark.asyncio
async def test_put_unique_cards_roundtrip(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    payload = bunker_core.get_settings(1)
    payload["default_unique_cards"] = False
    resp = await client.put("/api/bunker", json=payload)
    assert resp.status == 200
    assert (await resp.json())["default_unique_cards"] is False


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/bunker")
    assert resp.status == 401


# ────────────────────────── Активные игры ──────────────────────────

@pytest.mark.asyncio
async def test_games_list(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    bunker_db.add_player(game["id"], 20)
    bunker_db.add_player(game["id"], 21)
    finished = bunker_db.create_game(guild.id, 501, 10, 4, 12, 180, 90)
    bunker_db.update_game(finished["id"], status="finished")

    resp = await client.get("/api/bunker/games")
    assert resp.status == 200
    body = await resp.json()
    ids = {g["id"] for g in body["games"]}
    assert game["id"] in ids
    assert finished["id"] not in ids
    entry = next(g for g in body["games"] if g["id"] == game["id"])
    assert entry["player_count"] == 2
    assert entry["status"] == "lobby"
    assert entry["unique_cards"] is True


@pytest.mark.asyncio
async def test_games_list_filters_by_guild(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    ours = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    foreign = bunker_db.create_game(999, 600, 10, 4, 12, 180, 90)

    resp = await client.get("/api/bunker/games")
    assert resp.status == 200
    ids = {g["id"] for g in (await resp.json())["games"]}
    assert ours["id"] in ids
    assert foreign["id"] not in ids


@pytest.mark.asyncio
async def test_game_detail_rejects_other_guild(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    foreign = bunker_db.create_game(999, 600, 10, 4, 12, 180, 90)
    resp = await client.get(f"/api/bunker/games/{foreign['id']}")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_patch_player_rejects_other_guild(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    foreign = bunker_db.create_game(999, 600, 10, 4, 12, 180, 90)
    bunker_db.add_player(foreign["id"], 20)
    bunker_db.assign_character(foreign["id"], 20, _sample_character(), "tok-20")

    resp = await client.patch(
        f"/api/bunker/games/{foreign['id']}/players/20",
        json={"character": {"gender": "Женский"}},
    )
    assert resp.status == 404


@pytest.mark.asyncio
async def test_apply_ability_rejects_other_guild(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    foreign = bunker_db.create_game(999, 600, 10, 4, 12, 180, 90)
    announcement = bunker_db.create_ability_announcement(foreign["id"], 1, 20, 1, "Джокер", None, "")

    resp = await client.post(f"/api/bunker/games/{foreign['id']}/ability/{announcement['id']}/apply")
    assert resp.status == 404
    assert bunker_db.get_ability_announcement(announcement["id"])["applied"] == 0


@pytest.mark.asyncio
async def test_card_pools_endpoint_returns_reference_data(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/bunker/card-pools")
    assert resp.status == 200
    body = await resp.json()
    assert len(body["professions"]) == 100
    assert len(body["special_abilities"]) == 80
    assert len(body["genders"]) == 2
    assert body["health_severities"][0] == "Здоров"


@pytest.mark.asyncio
async def test_card_pools_endpoint_requires_auth(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/bunker/card-pools")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_game_detail_includes_players_and_announcements(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    player = FakeMember(20, name="player20")
    guild.members.append(player)

    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    bunker_db.add_player(game["id"], 20)
    bunker_db.assign_character(game["id"], 20, _sample_character(), "tok-20")
    bunker_db.reveal_fields(game["id"], 20, ["profession"])
    bunker_db.create_ability_announcement(game["id"], 1, 20, 1, "Джокер", None, "тестовая заявка")

    resp = await client.get(f"/api/bunker/games/{game['id']}")
    assert resp.status == 200
    body = await resp.json()

    assert body["game"]["id"] == game["id"]
    assert len(body["players"]) == 1
    assert body["players"][0]["display_name"] == "player20"
    assert body["players"][0]["revealed_fields"] == ["profession"]
    assert len(body["ability_announcements"]) == 1
    assert body["ability_announcements"][0]["card_name"] == "Джокер"
    assert body["ability_announcements"][0]["applied"] is False


@pytest.mark.asyncio
async def test_game_detail_uses_stored_display_name_for_bot_players(aiohttp_client):
    from game_test_lobby import fake_user_id

    _, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    bot_id = fake_user_id(0)
    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    bunker_db.add_player(game["id"], bot_id, display_name="Alex Bot")
    bunker_db.assign_character(game["id"], bot_id, _sample_character(), f"tok-{bot_id}")

    resp = await client.get(f"/api/bunker/games/{game['id']}")
    assert resp.status == 200
    body = await resp.json()
    assert body["players"][0]["user_id"] == str(bot_id)
    assert body["players"][0]["display_name"] == "Alex Bot"


@pytest.mark.asyncio
async def test_game_detail_not_found(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.get("/api/bunker/games/999")
    assert resp.status == 404


# ────────────────────────── Ручное редактирование карточки ──────────────────────────

@pytest.mark.asyncio
async def test_patch_player_character_merges_fields(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    bunker_db.add_player(game["id"], 20)
    bunker_db.assign_character(game["id"], 20, _sample_character(), "tok-20")

    resp = await client.patch(
        f"/api/bunker/games/{game['id']}/players/20",
        json={"character": {"gender": "Женский"}},
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["character"]["gender"] == "Женский"
    assert body["character"]["profession"]["name"] == "Пожарный"  # остальные поля не тронуты

    player = bunker_db.get_player(game["id"], 20)
    assert player["character"]["gender"] == "Женский"


@pytest.mark.asyncio
async def test_patch_player_character_rejects_unknown_keys(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    bunker_db.add_player(game["id"], 20)
    bunker_db.assign_character(game["id"], 20, _sample_character(), "tok-20")

    resp = await client.patch(
        f"/api/bunker/games/{game['id']}/players/20",
        json={"character": {"not_a_real_field": 1}},
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_patch_player_character_not_found(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    resp = await client.patch(
        f"/api/bunker/games/{game['id']}/players/999",
        json={"character": {"gender": "Женский"}},
    )
    assert resp.status == 404


@pytest.mark.asyncio
async def test_apply_ability_announcement(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    announcement = bunker_db.create_ability_announcement(game["id"], 1, 20, 1, "Джокер", None, "")

    resp = await client.post(f"/api/bunker/games/{game['id']}/ability/{announcement['id']}/apply")
    assert resp.status == 200

    applied = bunker_db.get_ability_announcement(announcement["id"])
    assert applied["applied"] == 1


@pytest.mark.asyncio
async def test_apply_ability_announcement_not_found(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    resp = await client.post(f"/api/bunker/games/{game['id']}/ability/999/apply")
    assert resp.status == 404


# ────────────────────────── Управление ведущего ──────────────────────────

class _FakeBunkerCog:
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
async def test_advance_phase_calls_cog(aiohttp_client):
    bot, guild, app = build()
    cog = _FakeBunkerCog()
    bot.get_cog = lambda name: cog if name == "BunkerCog" else None
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    resp = await client.post(f"/api/bunker/games/{game['id']}/advance-phase")
    assert resp.status == 200
    assert cog.advance_calls == [game["id"]]


@pytest.mark.asyncio
async def test_advance_phase_rejects_other_guild(aiohttp_client):
    bot, guild, app = build()
    cog = _FakeBunkerCog()
    bot.get_cog = lambda name: cog if name == "BunkerCog" else None
    client = await aiohttp_client(app)
    await force_login(client, 10)

    foreign = bunker_db.create_game(999, 600, 10, 4, 12, 180, 90)
    resp = await client.post(f"/api/bunker/games/{foreign['id']}/advance-phase")
    assert resp.status == 404
    assert cog.advance_calls == []


@pytest.mark.asyncio
async def test_advance_phase_returns_409_when_game_not_active(aiohttp_client):
    bot, guild, app = build()
    cog = _FakeBunkerCog()
    cog.advance_returns = False
    bot.get_cog = lambda name: cog if name == "BunkerCog" else None
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    resp = await client.post(f"/api/bunker/games/{game['id']}/advance-phase")
    assert resp.status == 409


@pytest.mark.asyncio
async def test_advance_phase_service_unavailable_without_cog(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    resp = await client.post(f"/api/bunker/games/{game['id']}/advance-phase")
    assert resp.status == 503


@pytest.mark.asyncio
async def test_end_game_calls_cog(aiohttp_client):
    bot, guild, app = build()
    cog = _FakeBunkerCog()
    bot.get_cog = lambda name: cog if name == "BunkerCog" else None
    client = await aiohttp_client(app)
    await force_login(client, 10)

    game = bunker_db.create_game(guild.id, 500, 10, 4, 12, 180, 90)
    resp = await client.post(f"/api/bunker/games/{game['id']}/end")
    assert resp.status == 200
    assert cog.end_calls == [game["id"]]


@pytest.mark.asyncio
async def test_end_game_rejects_other_guild(aiohttp_client):
    bot, guild, app = build()
    cog = _FakeBunkerCog()
    bot.get_cog = lambda name: cog if name == "BunkerCog" else None
    client = await aiohttp_client(app)
    await force_login(client, 10)

    foreign = bunker_db.create_game(999, 600, 10, 4, 12, 180, 90)
    resp = await client.post(f"/api/bunker/games/{foreign['id']}/end")
    assert resp.status == 404
    assert cog.end_calls == []
