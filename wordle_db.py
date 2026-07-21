"""SQLite-хранилище Вордла: игры дня, статистика игроков, серия сервера.

Игры дня переживают перезапуск бота (догадки хранятся в БД), тренировочные
игры — только в памяти кога и в БД не попадают.
"""

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

import wordle_core


def get_db_path() -> str:
    return os.getenv("WORDLE_DB_PATH", "wordle.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_games (
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                user_id INTEGER PRIMARY KEY,
                played INTEGER NOT NULL DEFAULT 0,
                won INTEGER NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                max_streak INTEGER NOT NULL DEFAULT 0,
                last_won_day INTEGER NOT NULL DEFAULT 0,
                distribution TEXT NOT NULL DEFAULT '[0,0,0,0,0,0]'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ────────────────────────── Игры дня ──────────────────────────

def get_daily_game(user_id: int, day_no: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM daily_games WHERE user_id = ? AND day_no = ?", (user_id, day_no)
        ).fetchone()
    if row is None:
        return None
    game = dict(row)
    game["guesses"] = json.loads(game["guesses"])
    return game


def start_daily_game(user_id: int, day_no: int) -> dict:
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT OR IGNORE INTO daily_games (user_id, day_no, updated_at) VALUES (?, ?, ?)",
            (user_id, day_no, _now()),
        )
    return get_daily_game(user_id, day_no)


def add_guess(user_id: int, day_no: int, guess: str, finished: bool, won: bool) -> dict:
    game = get_daily_game(user_id, day_no)
    guesses = (game["guesses"] if game else []) + [guess]
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO daily_games (user_id, day_no, guesses, finished, won, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, day_no) DO UPDATE SET
                 guesses = excluded.guesses, finished = excluded.finished,
                 won = excluded.won, updated_at = excluded.updated_at""",
            (user_id, day_no, json.dumps(guesses, ensure_ascii=False), int(finished), int(won), _now()),
        )
    return get_daily_game(user_id, day_no)


def set_live_message(user_id: int, day_no: int, channel_id: int, message_id: int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE daily_games SET live_channel_id = ?, live_message_id = ? WHERE user_id = ? AND day_no = ?",
            (channel_id, message_id, user_id, day_no),
        )


def list_day_games(day_no: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM daily_games WHERE day_no = ? ORDER BY updated_at", (day_no,)
        ).fetchall()
    games = []
    for row in rows:
        game = dict(row)
        game["guesses"] = json.loads(game["guesses"])
        games.append(game)
    return games


# ────────────────────────── Статистика ──────────────────────────

def get_stats(user_id: int) -> dict:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM stats WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return {
            "user_id": user_id, "played": 0, "won": 0, "streak": 0,
            "max_streak": 0, "last_won_day": 0,
            "distribution": [0] * wordle_core.MAX_ATTEMPTS,
        }
    stats = dict(row)
    stats["distribution"] = json.loads(stats["distribution"])
    return stats


def record_result(user_id: int, day_no: int, won: bool, attempts: int) -> dict:
    """Обновить статистику после завершённой игры дня.

    Стрик продолжается, если предыдущая победа была вчера (day_no - 1).
    """
    stats = get_stats(user_id)
    stats["played"] += 1
    if won:
        stats["won"] += 1
        stats["streak"] = stats["streak"] + 1 if stats["last_won_day"] == day_no - 1 else 1
        stats["max_streak"] = max(stats["max_streak"], stats["streak"])
        stats["last_won_day"] = day_no
        if 1 <= attempts <= wordle_core.MAX_ATTEMPTS:
            stats["distribution"][attempts - 1] += 1
    else:
        stats["streak"] = 0

    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO stats (user_id, played, won, streak, max_streak, last_won_day, distribution)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 played = excluded.played, won = excluded.won, streak = excluded.streak,
                 max_streak = excluded.max_streak, last_won_day = excluded.last_won_day,
                 distribution = excluded.distribution""",
            (user_id, stats["played"], stats["won"], stats["streak"],
             stats["max_streak"], stats["last_won_day"], json.dumps(stats["distribution"])),
        )
    return stats


def top_players(limit: int = 10) -> list[dict]:
    """Топ по победам, при равенстве — по максимальному стрику."""
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM stats WHERE played > 0 ORDER BY won DESC, max_streak DESC, played ASC LIMIT ?",
            (limit,),
        ).fetchall()
    result = []
    for row in rows:
        stats = dict(row)
        stats["distribution"] = json.loads(stats["distribution"])
        result.append(stats)
    return result


# ────────────────────────── Мета: анонсы и серия сервера ──────────────────────────

def _get_meta(key: str, default: str) -> str:
    with closing(connect()) as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def _set_meta(key: str, value: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_last_announced_day() -> int:
    return int(_get_meta("last_announced_day", "0"))


def set_last_announced_day(day_no: int) -> None:
    _set_meta("last_announced_day", str(day_no))


def get_group_streak() -> int:
    return int(_get_meta("group_streak", "0"))


def update_group_streak(day_no: int, anyone_won: bool) -> int:
    """Серия сервера: подряд идущие дни, когда хоть кто-то отгадал слово."""
    last_win_day = int(_get_meta("group_last_win_day", "0"))
    if anyone_won:
        streak = get_group_streak() + 1 if last_win_day == day_no - 1 else 1
        _set_meta("group_last_win_day", str(day_no))
    else:
        streak = 0
    _set_meta("group_streak", str(streak))
    return streak
