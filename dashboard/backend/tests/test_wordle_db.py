"""Тесты wordle_db: игры дня, статистика со стриками, мета сервера (per-guild)."""

import os
import sqlite3
from contextlib import closing

import pytest

import wordle_db

GUILD = 1
OTHER = 2
MAIN = int(os.getenv("GUILD_ID", "404"))


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("WORDLE_DB_PATH", str(tmp_path / "wordle.db"))
    wordle_db.init()


# ────────────────────────── Игры дня ──────────────────────────

def test_start_and_get_daily_game():
    assert wordle_db.get_daily_game(GUILD, 1, 10) is None
    game = wordle_db.start_daily_game(GUILD, 1, 10)
    assert game["guesses"] == []
    assert game["finished"] == 0
    # повторный старт не сбрасывает игру
    wordle_db.add_guess(GUILD, 1, 10, "школа", False, False)
    game = wordle_db.start_daily_game(GUILD, 1, 10)
    assert game["guesses"] == ["школа"]


def test_add_guess_accumulates_and_finishes():
    wordle_db.start_daily_game(GUILD, 1, 10)
    wordle_db.add_guess(GUILD, 1, 10, "катер", False, False)
    game = wordle_db.add_guess(GUILD, 1, 10, "канат", True, True)
    assert game["guesses"] == ["катер", "канат"]
    assert game["finished"] == 1
    assert game["won"] == 1


def test_live_message_roundtrip():
    wordle_db.start_daily_game(GUILD, 1, 10)
    wordle_db.set_live_message(GUILD, 1, 10, 555, 777)
    game = wordle_db.get_daily_game(GUILD, 1, 10)
    assert game["live_channel_id"] == 555
    assert game["live_message_id"] == 777


def test_list_day_games_filters_by_day():
    wordle_db.add_guess(GUILD, 1, 10, "школа", True, True)
    wordle_db.add_guess(GUILD, 2, 10, "канат", True, False)
    wordle_db.add_guess(GUILD, 3, 11, "катер", False, False)
    games = wordle_db.list_day_games(GUILD, 10)
    assert {g["user_id"] for g in games} == {1, 2}


def test_daily_games_isolated_per_guild():
    wordle_db.add_guess(GUILD, 1, 10, "школа", True, True)
    wordle_db.add_guess(OTHER, 1, 10, "канат", True, False)
    assert wordle_db.get_daily_game(GUILD, 1, 10)["guesses"] == ["школа"]
    assert wordle_db.get_daily_game(OTHER, 1, 10)["guesses"] == ["канат"]
    assert {g["user_id"] for g in wordle_db.list_day_games(GUILD, 10)} == {1}
    assert {g["user_id"] for g in wordle_db.list_day_games(OTHER, 10)} == {1}


# ────────────────────────── Статистика ──────────────────────────

def test_record_result_win_starts_streak_and_distribution():
    stats = wordle_db.record_result(GUILD, 1, 10, won=True, attempts=4)
    assert stats["played"] == 1
    assert stats["won"] == 1
    assert stats["streak"] == 1
    assert stats["max_streak"] == 1
    assert stats["distribution"][3] == 1


def test_record_result_consecutive_days_extend_streak():
    wordle_db.record_result(GUILD, 1, 10, won=True, attempts=3)
    stats = wordle_db.record_result(GUILD, 1, 11, won=True, attempts=5)
    assert stats["streak"] == 2
    assert stats["max_streak"] == 2


def test_record_result_gap_resets_streak():
    wordle_db.record_result(GUILD, 1, 10, won=True, attempts=3)
    stats = wordle_db.record_result(GUILD, 1, 13, won=True, attempts=3)
    assert stats["streak"] == 1
    assert stats["max_streak"] == 1


def test_record_result_loss_resets_streak_but_counts_played():
    wordle_db.record_result(GUILD, 1, 10, won=True, attempts=3)
    stats = wordle_db.record_result(GUILD, 1, 11, won=False, attempts=6)
    assert stats["played"] == 2
    assert stats["won"] == 1
    assert stats["streak"] == 0
    assert stats["max_streak"] == 1
    assert sum(stats["distribution"]) == 1  # поражение в распределение не попадает


def test_top_players_orders_by_wins_then_max_streak():
    wordle_db.record_result(GUILD, 1, 10, won=True, attempts=3)
    wordle_db.record_result(GUILD, 2, 10, won=True, attempts=2)
    wordle_db.record_result(GUILD, 2, 11, won=True, attempts=4)
    wordle_db.record_result(GUILD, 3, 10, won=False, attempts=6)
    top = wordle_db.top_players(GUILD, 10)
    assert [s["user_id"] for s in top][:2] == [2, 1]
    assert top[-1]["user_id"] == 3


def test_stats_isolated_per_guild():
    wordle_db.record_result(GUILD, 1, 10, won=True, attempts=3)
    wordle_db.record_result(OTHER, 1, 10, won=False, attempts=6)
    assert wordle_db.get_stats(GUILD, 1)["won"] == 1
    assert wordle_db.get_stats(OTHER, 1)["won"] == 0
    assert wordle_db.top_players(OTHER, 10)[0]["won"] == 0


# ────────────────────────── Мета ──────────────────────────

def test_last_announced_day_roundtrip():
    assert wordle_db.get_last_announced_day(GUILD) == 0
    wordle_db.set_last_announced_day(GUILD, 12)
    assert wordle_db.get_last_announced_day(GUILD) == 12
    assert wordle_db.get_last_announced_day(OTHER) == 0


def test_group_streak_grows_and_resets():
    assert wordle_db.update_group_streak(GUILD, 10, anyone_won=True) == 1
    assert wordle_db.update_group_streak(GUILD, 11, anyone_won=True) == 2
    assert wordle_db.update_group_streak(GUILD, 12, anyone_won=False) == 0
    assert wordle_db.update_group_streak(GUILD, 13, anyone_won=True) == 1


def test_group_streak_gap_resets():
    wordle_db.update_group_streak(GUILD, 10, anyone_won=True)
    assert wordle_db.update_group_streak(GUILD, 15, anyone_won=True) == 1


def test_group_streak_isolated_per_guild():
    wordle_db.update_group_streak(GUILD, 10, anyone_won=True)
    wordle_db.update_group_streak(GUILD, 11, anyone_won=True)
    assert wordle_db.get_group_streak(GUILD) == 2
    assert wordle_db.get_group_streak(OTHER) == 0
    assert wordle_db.update_group_streak(OTHER, 10, anyone_won=True) == 1


# ────────────────────────── Миграция ──────────────────────────

def test_migration_assigns_legacy_rows_to_main_guild(tmp_path, monkeypatch):
    db_path = str(tmp_path / "legacy_wordle.db")
    monkeypatch.setenv("WORDLE_DB_PATH", db_path)
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute("""
            CREATE TABLE daily_games (
                user_id INTEGER NOT NULL,
                day_no INTEGER NOT NULL,
                guesses TEXT NOT NULL DEFAULT '[]',
                finished INTEGER NOT NULL DEFAULT 0,
                won INTEGER NOT NULL DEFAULT 0,
                live_channel_id INTEGER NOT NULL DEFAULT 0,
                live_message_id INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, day_no)
            )
        """)
        conn.execute(
            "INSERT INTO daily_games (user_id, day_no, guesses, finished, won, updated_at) VALUES (1, 5, '[\"школа\"]', 1, 1, 't')"
        )
        conn.execute("""
            CREATE TABLE stats (
                user_id INTEGER PRIMARY KEY,
                played INTEGER NOT NULL DEFAULT 0,
                won INTEGER NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                max_streak INTEGER NOT NULL DEFAULT 0,
                last_won_day INTEGER NOT NULL DEFAULT 0,
                distribution TEXT NOT NULL DEFAULT '[0,0,0,0,0,0]'
            )
        """)
        conn.execute(
            "INSERT INTO stats (user_id, played, won, streak, max_streak, last_won_day) VALUES (1, 2, 1, 1, 1, 5)"
        )
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO meta (key, value) VALUES ('last_announced_day', '5')")
        conn.execute("INSERT INTO meta (key, value) VALUES ('group_streak', '3')")

    wordle_db.init()
    wordle_db.init()  # идемпотентность

    game = wordle_db.get_daily_game(MAIN, 1, 5)
    assert game is not None and game["guesses"] == ["школа"]
    assert wordle_db.get_daily_game(OTHER, 1, 5) is None
    assert wordle_db.get_stats(MAIN, 1)["played"] == 2
    assert wordle_db.get_last_announced_day(MAIN) == 5
    assert wordle_db.get_group_streak(MAIN) == 3
