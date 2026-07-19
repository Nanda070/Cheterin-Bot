"""Тесты wordle_db: игры дня, статистика со стриками, мета сервера."""

import pytest

import wordle_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("WORDLE_DB_PATH", str(tmp_path / "wordle.db"))
    wordle_db.init()


# ────────────────────────── Игры дня ──────────────────────────

def test_start_and_get_daily_game():
    assert wordle_db.get_daily_game(1, 10) is None
    game = wordle_db.start_daily_game(1, 10)
    assert game["guesses"] == []
    assert game["finished"] == 0
    # повторный старт не сбрасывает игру
    wordle_db.add_guess(1, 10, "школа", False, False)
    game = wordle_db.start_daily_game(1, 10)
    assert game["guesses"] == ["школа"]


def test_add_guess_accumulates_and_finishes():
    wordle_db.start_daily_game(1, 10)
    wordle_db.add_guess(1, 10, "катер", False, False)
    game = wordle_db.add_guess(1, 10, "канат", True, True)
    assert game["guesses"] == ["катер", "канат"]
    assert game["finished"] == 1
    assert game["won"] == 1


def test_live_message_roundtrip():
    wordle_db.start_daily_game(1, 10)
    wordle_db.set_live_message(1, 10, 555, 777)
    game = wordle_db.get_daily_game(1, 10)
    assert game["live_channel_id"] == 555
    assert game["live_message_id"] == 777


def test_list_day_games_filters_by_day():
    wordle_db.add_guess(1, 10, "школа", True, True)
    wordle_db.add_guess(2, 10, "канат", True, False)
    wordle_db.add_guess(3, 11, "катер", False, False)
    games = wordle_db.list_day_games(10)
    assert {g["user_id"] for g in games} == {1, 2}


# ────────────────────────── Статистика ──────────────────────────

def test_record_result_win_starts_streak_and_distribution():
    stats = wordle_db.record_result(1, 10, won=True, attempts=4)
    assert stats["played"] == 1
    assert stats["won"] == 1
    assert stats["streak"] == 1
    assert stats["max_streak"] == 1
    assert stats["distribution"][3] == 1


def test_record_result_consecutive_days_extend_streak():
    wordle_db.record_result(1, 10, won=True, attempts=3)
    stats = wordle_db.record_result(1, 11, won=True, attempts=5)
    assert stats["streak"] == 2
    assert stats["max_streak"] == 2


def test_record_result_gap_resets_streak():
    wordle_db.record_result(1, 10, won=True, attempts=3)
    stats = wordle_db.record_result(1, 13, won=True, attempts=3)
    assert stats["streak"] == 1
    assert stats["max_streak"] == 1


def test_record_result_loss_resets_streak_but_counts_played():
    wordle_db.record_result(1, 10, won=True, attempts=3)
    stats = wordle_db.record_result(1, 11, won=False, attempts=6)
    assert stats["played"] == 2
    assert stats["won"] == 1
    assert stats["streak"] == 0
    assert stats["max_streak"] == 1
    assert sum(stats["distribution"]) == 1  # поражение в распределение не попадает


def test_top_players_orders_by_wins_then_max_streak():
    wordle_db.record_result(1, 10, won=True, attempts=3)
    wordle_db.record_result(2, 10, won=True, attempts=2)
    wordle_db.record_result(2, 11, won=True, attempts=4)
    wordle_db.record_result(3, 10, won=False, attempts=6)
    top = wordle_db.top_players(10)
    assert [s["user_id"] for s in top][:2] == [2, 1]
    assert top[-1]["user_id"] == 3


# ────────────────────────── Мета ──────────────────────────

def test_last_announced_day_roundtrip():
    assert wordle_db.get_last_announced_day() == 0
    wordle_db.set_last_announced_day(12)
    assert wordle_db.get_last_announced_day() == 12


def test_group_streak_grows_and_resets():
    assert wordle_db.update_group_streak(10, anyone_won=True) == 1
    assert wordle_db.update_group_streak(11, anyone_won=True) == 2
    assert wordle_db.update_group_streak(12, anyone_won=False) == 0
    assert wordle_db.update_group_streak(13, anyone_won=True) == 1


def test_group_streak_gap_resets():
    wordle_db.update_group_streak(10, anyone_won=True)
    assert wordle_db.update_group_streak(15, anyone_won=True) == 1
