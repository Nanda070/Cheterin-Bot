"""SQLite-хранилище Вордла: игры дня, статистика игроков, серия сервера.

Игры дня переживают перезапуск бота (догадки хранятся в БД), тренировочные
игры — только в памяти кога и в БД не попадают. Все таблицы per-guild.
"""

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

import bot.modules.games.wordle_core as wordle_core

MAIN_GUILD = int(os.getenv("GUILD_ID", "404"))


def get_db_path() -> str:
    return os.getenv("WORDLE_DB_PATH", "wordle.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def init():
    with closing(connect()) as conn, conn:
        # ── daily_games: (user_id, day_no) → (guild_id, user_id, day_no) ──
        cols = _table_columns(conn, "daily_games")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE daily_games RENAME TO daily_games_old")
            conn.execute("""
                CREATE TABLE daily_games (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    day_no INTEGER NOT NULL,
                    guesses TEXT NOT NULL DEFAULT '[]',
                    finished INTEGER NOT NULL DEFAULT 0,
                    won INTEGER NOT NULL DEFAULT 0,
                    live_channel_id INTEGER NOT NULL DEFAULT 0,
                    live_message_id INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id, day_no)
                )
            """)
            conn.execute(
                """INSERT INTO daily_games
                   (guild_id, user_id, day_no, guesses, finished, won,
                    live_channel_id, live_message_id, updated_at)
                   SELECT ?, user_id, day_no, guesses, finished, won,
                          live_channel_id, live_message_id, updated_at
                   FROM daily_games_old""",
                (MAIN_GUILD,),
            )
            conn.execute("DROP TABLE daily_games_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_games (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    day_no INTEGER NOT NULL,
                    guesses TEXT NOT NULL DEFAULT '[]',
                    finished INTEGER NOT NULL DEFAULT 0,
                    won INTEGER NOT NULL DEFAULT 0,
                    live_channel_id INTEGER NOT NULL DEFAULT 0,
                    live_message_id INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id, day_no)
                )
            """)

        # ── stats: user_id → (guild_id, user_id) ──
        cols = _table_columns(conn, "stats")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE stats RENAME TO stats_old")
            conn.execute("""
                CREATE TABLE stats (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    played INTEGER NOT NULL DEFAULT 0,
                    won INTEGER NOT NULL DEFAULT 0,
                    streak INTEGER NOT NULL DEFAULT 0,
                    max_streak INTEGER NOT NULL DEFAULT 0,
                    last_won_day INTEGER NOT NULL DEFAULT 0,
                    distribution TEXT NOT NULL DEFAULT '[0,0,0,0,0,0]',
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            conn.execute(
                """INSERT INTO stats
                   (guild_id, user_id, played, won, streak, max_streak, last_won_day, distribution)
                   SELECT ?, user_id, played, won, streak, max_streak, last_won_day, distribution
                   FROM stats_old""",
                (MAIN_GUILD,),
            )
            conn.execute("DROP TABLE stats_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    played INTEGER NOT NULL DEFAULT 0,
                    won INTEGER NOT NULL DEFAULT 0,
                    streak INTEGER NOT NULL DEFAULT 0,
                    max_streak INTEGER NOT NULL DEFAULT 0,
                    last_won_day INTEGER NOT NULL DEFAULT 0,
                    distribution TEXT NOT NULL DEFAULT '[0,0,0,0,0,0]',
                    PRIMARY KEY (guild_id, user_id)
                )
            """)

        # ── meta: key → (guild_id, key) ──
        cols = _table_columns(conn, "meta")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE meta RENAME TO meta_old")
            conn.execute("""
                CREATE TABLE meta (
                    guild_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY (guild_id, key)
                )
            """)
            conn.execute(
                "INSERT INTO meta (guild_id, key, value) SELECT ?, key, value FROM meta_old",
                (MAIN_GUILD,),
            )
            conn.execute("DROP TABLE meta_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS meta (
                    guild_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY (guild_id, key)
                )
            """)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ────────────────────────── Игры дня ──────────────────────────

def get_daily_game(guild_id: int, user_id: int, day_no: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM daily_games WHERE guild_id = ? AND user_id = ? AND day_no = ?",
            (guild_id, user_id, day_no),
        ).fetchone()
    if row is None:
        return None
    game = dict(row)
    game["guesses"] = json.loads(game["guesses"])
    return game


def start_daily_game(guild_id: int, user_id: int, day_no: int) -> dict:
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT OR IGNORE INTO daily_games (guild_id, user_id, day_no, updated_at) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, day_no, _now()),
        )
    return get_daily_game(guild_id, user_id, day_no)


def add_guess(guild_id: int, user_id: int, day_no: int, guess: str, finished: bool, won: bool) -> dict:
    game = get_daily_game(guild_id, user_id, day_no)
    guesses = (game["guesses"] if game else []) + [guess]
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO daily_games (guild_id, user_id, day_no, guesses, finished, won, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(guild_id, user_id, day_no) DO UPDATE SET
                 guesses = excluded.guesses, finished = excluded.finished,
                 won = excluded.won, updated_at = excluded.updated_at""",
            (guild_id, user_id, day_no, json.dumps(guesses, ensure_ascii=False), int(finished), int(won), _now()),
        )
    return get_daily_game(guild_id, user_id, day_no)


def set_live_message(guild_id: int, user_id: int, day_no: int, channel_id: int, message_id: int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """UPDATE daily_games SET live_channel_id = ?, live_message_id = ?
               WHERE guild_id = ? AND user_id = ? AND day_no = ?""",
            (channel_id, message_id, guild_id, user_id, day_no),
        )


def list_day_games(guild_id: int, day_no: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM daily_games WHERE guild_id = ? AND day_no = ? ORDER BY updated_at",
            (guild_id, day_no),
        ).fetchall()
    games = []
    for row in rows:
        game = dict(row)
        game["guesses"] = json.loads(game["guesses"])
        games.append(game)
    return games


# ────────────────────────── Статистика ──────────────────────────

def get_stats(guild_id: int, user_id: int) -> dict:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM stats WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
    if row is None:
        return {
            "guild_id": guild_id,
            "user_id": user_id, "played": 0, "won": 0, "streak": 0,
            "max_streak": 0, "last_won_day": 0,
            "distribution": [0] * wordle_core.MAX_ATTEMPTS,
        }
    stats = dict(row)
    stats["distribution"] = json.loads(stats["distribution"])
    return stats


def record_result(guild_id: int, user_id: int, day_no: int, won: bool, attempts: int) -> dict:
    """Обновить статистику после завершённой игры дня.

    Стрик продолжается, если предыдущая победа была вчера (day_no - 1).
    """
    stats = get_stats(guild_id, user_id)
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
            """INSERT INTO stats (guild_id, user_id, played, won, streak, max_streak, last_won_day, distribution)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(guild_id, user_id) DO UPDATE SET
                 played = excluded.played, won = excluded.won, streak = excluded.streak,
                 max_streak = excluded.max_streak, last_won_day = excluded.last_won_day,
                 distribution = excluded.distribution""",
            (guild_id, user_id, stats["played"], stats["won"], stats["streak"],
             stats["max_streak"], stats["last_won_day"], json.dumps(stats["distribution"])),
        )
    return stats


def top_players(guild_id: int, limit: int = 10) -> list[dict]:
    """Топ по победам, при равенстве — по максимальному стрику."""
    with closing(connect()) as conn:
        rows = conn.execute(
            """SELECT * FROM stats WHERE guild_id = ? AND played > 0
               ORDER BY won DESC, max_streak DESC, played ASC LIMIT ?""",
            (guild_id, limit),
        ).fetchall()
    result = []
    for row in rows:
        stats = dict(row)
        stats["distribution"] = json.loads(stats["distribution"])
        result.append(stats)
    return result


# ────────────────────────── Мета: анонсы и серия сервера ──────────────────────────

def _get_meta(guild_id: int, key: str, default: str) -> str:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT value FROM meta WHERE guild_id = ? AND key = ?",
            (guild_id, key),
        ).fetchone()
    return row["value"] if row else default


def _set_meta(guild_id: int, key: str, value: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO meta (guild_id, key, value) VALUES (?, ?, ?)
               ON CONFLICT(guild_id, key) DO UPDATE SET value = excluded.value""",
            (guild_id, key, value),
        )


def get_last_announced_day(guild_id: int) -> int:
    return int(_get_meta(guild_id, "last_announced_day", "0"))


def set_last_announced_day(guild_id: int, day_no: int) -> None:
    _set_meta(guild_id, "last_announced_day", str(day_no))


def get_group_streak(guild_id: int) -> int:
    return int(_get_meta(guild_id, "group_streak", "0"))


def update_group_streak(guild_id: int, day_no: int, anyone_won: bool) -> int:
    """Серия сервера: подряд идущие дни, когда хоть кто-то отгадал слово."""
    last_win_day = int(_get_meta(guild_id, "group_last_win_day", "0"))
    if anyone_won:
        streak = get_group_streak(guild_id) + 1 if last_win_day == day_no - 1 else 1
        _set_meta(guild_id, "group_last_win_day", str(day_no))
    else:
        streak = 0
    _set_meta(guild_id, "group_streak", str(streak))
    return streak
