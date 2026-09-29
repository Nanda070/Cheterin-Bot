import pytest

import bot.modules.games.bunker_db as bunker_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("BUNKER_DB_PATH", str(tmp_path / "bunker.db"))
    bunker_db.init()


def _make_game(**overrides):
    defaults = dict(
        guild_id=1, channel_id=100, created_by=10,
        min_players=4, max_players=12, discussion_timer_sec=180, vote_timer_sec=90,
    )
    defaults.update(overrides)
    return bunker_db.create_game(**defaults)


def _sample_character(name="Пожарный"):
    return {
        "profession": {"name": name, "category": "МЧС", "experience_level": "Эксперт", "has_ability": True},
        "age": {"key": "adult", "label": "Взрослый (35-59 лет)"},
        "gender": "Мужской",
        "special_abilities": [
            {"name": "Джокер", "category": "Защита", "effect": "...", "used": False},
            {"name": "Сейф", "category": "Защита", "effect": "...", "used": False},
        ],
    }


def test_create_and_get_game():
    game = _make_game()
    assert game["status"] == "lobby"
    assert game["phase"] == "lobby"
    assert game["unique_cards"] == 1  # без повторов по умолчанию
    assert game["voice_channel_id"] is None
    assert bunker_db.get_game(game["id"]) == game


def test_create_game_with_repeats_allowed():
    game = _make_game(unique_cards=False)
    assert game["unique_cards"] == 0


def test_update_game_stores_voice_channel_id():
    game = _make_game()
    updated = bunker_db.update_game(game["id"], voice_channel_id=999)
    assert updated["voice_channel_id"] == 999


def test_init_migrates_old_schema_without_new_columns(tmp_path, monkeypatch):
    """База, созданная до появления voice_channel_id/vote_message_id/unique_cards,
    должна дополняться колонками при init(), а не падать на INSERT."""
    import sqlite3
    from contextlib import closing

    db_path = str(tmp_path / "old_bunker.db")
    monkeypatch.setenv("BUNKER_DB_PATH", db_path)
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute("""
            CREATE TABLE games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                lobby_message_id INTEGER,
                status TEXT NOT NULL DEFAULT 'lobby',
                phase TEXT NOT NULL DEFAULT 'lobby',
                round_number INTEGER NOT NULL DEFAULT 0,
                phase_deadline_ts INTEGER,
                min_players INTEGER NOT NULL,
                max_players INTEGER NOT NULL,
                bunker_capacity INTEGER,
                discussion_timer_sec INTEGER NOT NULL,
                vote_timer_sec INTEGER NOT NULL,
                catastrophe_name TEXT,
                catastrophe_description TEXT,
                bunker_conditions_name TEXT,
                bunker_conditions_description TEXT,
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                ended_at TEXT
            )
        """)

    bunker_db.init()
    game = _make_game()
    assert game["unique_cards"] == 1
    assert game["voice_channel_id"] is None
    assert game["vote_message_id"] is None


def test_get_game_by_lobby_message():
    game = _make_game()
    bunker_db.update_game(game["id"], lobby_message_id=555)
    assert bunker_db.get_game_by_lobby_message(555)["id"] == game["id"]
    assert bunker_db.get_game_by_lobby_message(999) is None


def test_get_active_game_in_channel_filters_by_status():
    game = _make_game(channel_id=200)
    assert bunker_db.get_active_game_in_channel(200)["id"] == game["id"]
    bunker_db.update_game(game["id"], status="finished")
    assert bunker_db.get_active_game_in_channel(200) is None


def test_update_game_generic_fields():
    game = _make_game()
    updated = bunker_db.update_game(game["id"], phase="vote", round_number=2, bunker_capacity=3)
    assert updated["phase"] == "vote"
    assert updated["round_number"] == 2
    assert updated["bunker_capacity"] == 3


def test_list_active_games_excludes_finished_and_cancelled():
    a = _make_game(channel_id=300)
    b = _make_game(channel_id=301)
    bunker_db.update_game(b["id"], status="finished")
    active_ids = {g["id"] for g in bunker_db.list_active_games()}
    assert a["id"] in active_ids
    assert b["id"] not in active_ids


def test_list_active_games_filters_by_guild():
    a = _make_game(channel_id=300)
    foreign = bunker_db.create_game(999, 400, 10, 4, 12, 180, 90)
    ids = {g["id"] for g in bunker_db.list_active_games(guild_id=a["guild_id"])}
    assert a["id"] in ids
    assert foreign["id"] not in ids


def test_add_player_rejects_duplicate():
    game = _make_game()
    assert bunker_db.add_player(game["id"], 20) is True
    assert bunker_db.add_player(game["id"], 20) is False
    assert bunker_db.count_players(game["id"]) == 1


def test_remove_player():
    game = _make_game()
    bunker_db.add_player(game["id"], 20)
    assert bunker_db.remove_player(game["id"], 20) is True
    assert bunker_db.remove_player(game["id"], 20) is False
    assert bunker_db.list_players(game["id"]) == []


def test_list_alive_players_excludes_eliminated():
    game = _make_game()
    bunker_db.add_player(game["id"], 20)
    bunker_db.add_player(game["id"], 21)
    bunker_db.eliminate_player(game["id"], 20, 1)
    alive_ids = {p["user_id"] for p in bunker_db.list_alive_players(game["id"])}
    assert alive_ids == {21}
    eliminated = bunker_db.get_player(game["id"], 20)
    assert eliminated["alive"] == 0
    assert eliminated["eliminated_round"] == 1


def test_assign_character_and_get_by_token():
    game = _make_game()
    bunker_db.add_player(game["id"], 20)
    character = _sample_character()
    bunker_db.assign_character(game["id"], 20, character, "tok-abc")

    player = bunker_db.get_player(game["id"], 20)
    assert player["character"] == character
    assert player["token"] == "tok-abc"
    assert player["revealed_fields"] == []

    by_token = bunker_db.get_player_by_token("tok-abc")
    assert by_token["user_id"] == 20
    assert bunker_db.get_player_by_token("unknown") is None


def test_set_player_character_full_replace():
    game = _make_game()
    bunker_db.add_player(game["id"], 20)
    bunker_db.assign_character(game["id"], 20, _sample_character(), "tok-abc")

    replaced = _sample_character(name="Врач")
    bunker_db.set_player_character(game["id"], 20, replaced)
    player = bunker_db.get_player(game["id"], 20)
    assert player["character"]["profession"]["name"] == "Врач"
    assert player["token"] == "tok-abc"  # токен не сбрасывается при перезаписи карточки


def test_reveal_fields_accumulates():
    game = _make_game()
    bunker_db.add_player(game["id"], 20)
    bunker_db.assign_character(game["id"], 20, _sample_character(), "tok-abc")

    bunker_db.reveal_fields(game["id"], 20, ["profession"])
    bunker_db.reveal_fields(game["id"], 20, ["age", "profession"])

    player = bunker_db.get_player(game["id"], 20)
    assert player["revealed_fields"] == ["age", "profession"]


def test_upsert_vote_overwrites():
    game = _make_game()
    bunker_db.upsert_vote(game["id"], 1, 20, 30)
    bunker_db.upsert_vote(game["id"], 1, 20, 31)
    votes = bunker_db.get_votes(game["id"], 1)
    assert len(votes) == 1
    assert votes[0]["target_user_id"] == 31


def test_get_vote_single_row():
    game = _make_game()
    bunker_db.upsert_vote(game["id"], 1, 20, 30)
    vote = bunker_db.get_vote(game["id"], 1, 20)
    assert vote["target_user_id"] == 30
    assert bunker_db.get_vote(game["id"], 1, 999) is None


def test_ability_announcement_create_list_get_apply():
    game = _make_game()
    announcement = bunker_db.create_ability_announcement(
        game["id"], 1, 20, 1, "Джокер", target_user_id=30, note="на игрока 30",
    )
    assert announcement["applied"] == 0

    fetched = bunker_db.get_ability_announcement(announcement["id"])
    assert fetched["card_name"] == "Джокер"
    assert fetched["note"] == "на игрока 30"

    listed = bunker_db.list_ability_announcements(game["id"])
    assert len(listed) == 1

    bunker_db.mark_ability_announcement_applied(announcement["id"])
    applied = bunker_db.get_ability_announcement(announcement["id"])
    assert applied["applied"] == 1
    assert applied["applied_at"] is not None


def test_round_events_roundtrip():
    game = _make_game()
    bunker_db.add_round_event(game["id"], 1, "game_started", "Игроков: 5.")
    events = bunker_db.list_round_events(game["id"])
    assert len(events) == 1
    assert events[0]["event_type"] == "game_started"
