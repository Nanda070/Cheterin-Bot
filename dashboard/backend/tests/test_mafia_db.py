import pytest

import mafia_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MAFIA_DB_PATH", str(tmp_path / "mafia.db"))
    mafia_db.init()


def _make_game(**overrides):
    defaults = dict(
        guild_id=1, channel_id=100, created_by=10,
        min_players=5, max_players=20, night_timer_sec=60,
        day_discussion_timer_sec=120, day_vote_timer_sec=60,
    )
    defaults.update(overrides)
    return mafia_db.create_game(**defaults)


def test_create_and_get_game():
    game = _make_game()
    assert game["status"] == "lobby"
    assert game["phase"] == "lobby"
    assert mafia_db.get_game(game["id"]) == game


def test_get_game_by_lobby_and_vote_message():
    game = _make_game()
    mafia_db.update_game(game["id"], lobby_message_id=555, vote_message_id=777)
    assert mafia_db.get_game_by_lobby_message(555)["id"] == game["id"]
    assert mafia_db.get_game_by_vote_message(777)["id"] == game["id"]
    assert mafia_db.get_game_by_lobby_message(999) is None


def test_get_active_game_in_channel_filters_by_status():
    game = _make_game(channel_id=200)
    assert mafia_db.get_active_game_in_channel(200)["id"] == game["id"]
    mafia_db.update_game(game["id"], status="finished")
    assert mafia_db.get_active_game_in_channel(200) is None


def test_update_game_generic_fields():
    game = _make_game()
    updated = mafia_db.update_game(game["id"], phase="night", round_number=2)
    assert updated["phase"] == "night"
    assert updated["round_number"] == 2


def test_list_active_games_excludes_finished_and_cancelled():
    a = _make_game(channel_id=300)
    b = _make_game(channel_id=301)
    mafia_db.update_game(b["id"], status="finished")
    active_ids = {g["id"] for g in mafia_db.list_active_games()}
    assert a["id"] in active_ids
    assert b["id"] not in active_ids


def test_add_player_rejects_duplicate():
    game = _make_game()
    assert mafia_db.add_player(game["id"], 20) is True
    assert mafia_db.add_player(game["id"], 20) is False
    assert mafia_db.count_players(game["id"]) == 1


def test_remove_player():
    game = _make_game()
    mafia_db.add_player(game["id"], 20)
    assert mafia_db.remove_player(game["id"], 20) is True
    assert mafia_db.remove_player(game["id"], 20) is False
    assert mafia_db.list_players(game["id"]) == []


def test_list_alive_players_excludes_eliminated():
    game = _make_game()
    mafia_db.add_player(game["id"], 20)
    mafia_db.add_player(game["id"], 21)
    mafia_db.eliminate_player(game["id"], 20, 1, "killed")
    alive_ids = {p["user_id"] for p in mafia_db.list_alive_players(game["id"])}
    assert alive_ids == {21}
    eliminated = mafia_db.get_player(game["id"], 20)
    assert eliminated["alive"] == 0
    assert eliminated["eliminated_round"] == 1
    assert eliminated["eliminated_reason"] == "killed"


def test_assign_player_role_and_get_by_token():
    game = _make_game()
    mafia_db.add_player(game["id"], 20)
    mafia_db.assign_player_role(game["id"], 20, "mafia", "tok-abc")
    player = mafia_db.get_player(game["id"], 20)
    assert player["role"] == "mafia"
    assert player["token"] == "tok-abc"

    by_token = mafia_db.get_player_by_token("tok-abc")
    assert by_token["user_id"] == 20
    assert mafia_db.get_player_by_token("unknown") is None


def test_upsert_night_action_overwrites():
    game = _make_game()
    mafia_db.upsert_night_action(game["id"], 1, 20, "mafia", 30)
    mafia_db.upsert_night_action(game["id"], 1, 20, "mafia", 31)
    action = mafia_db.get_night_action(game["id"], 1, 20)
    assert action["target_user_id"] == 31
    assert len(mafia_db.get_night_actions(game["id"], 1)) == 1


def test_get_night_actions_filters_by_role():
    game = _make_game()
    mafia_db.upsert_night_action(game["id"], 1, 20, "mafia", 30)
    mafia_db.upsert_night_action(game["id"], 1, 21, "doctor", 20)
    assert len(mafia_db.get_night_actions(game["id"], 1, role="mafia")) == 1
    assert len(mafia_db.get_night_actions(game["id"], 1)) == 2


def test_set_night_action_result():
    game = _make_game()
    mafia_db.upsert_night_action(game["id"], 1, 20, "sheriff", 30)
    mafia_db.set_night_action_result(game["id"], 1, 20, "mafia")
    action = mafia_db.get_night_action(game["id"], 1, 20)
    assert action["result"] == "mafia"


def test_upsert_day_vote_overwrites():
    game = _make_game()
    mafia_db.upsert_day_vote(game["id"], 1, 20, 30)
    mafia_db.upsert_day_vote(game["id"], 1, 20, 31)
    votes = mafia_db.get_day_votes(game["id"], 1)
    assert len(votes) == 1
    assert votes[0]["target_user_id"] == 31


def test_round_events_roundtrip():
    game = _make_game()
    mafia_db.add_round_event(game["id"], 1, "game_started", "Игроков: 5.")
    events = mafia_db.list_round_events(game["id"])
    assert len(events) == 1
    assert events[0]["event_type"] == "game_started"
