"""SQLite-хранилище игры «Мафия»: лобби/игры, игроки, ночные действия, дневные голоса.

Синхронный sqlite3 (не aiosqlite) — тот же стиль хранения, что и family_db.py/voice_db.py.
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

ACTIVE_STATUSES = ("lobby", "active")


def get_db_path() -> str:
    return os.getenv("MAFIA_DB_PATH", "mafia.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                voice_channel_id INTEGER,
                lobby_message_id INTEGER,
                vote_message_id INTEGER,
                status TEXT NOT NULL DEFAULT 'lobby',
                phase TEXT NOT NULL DEFAULT 'lobby',
                round_number INTEGER NOT NULL DEFAULT 0,
                phase_deadline_ts INTEGER,
                vote_page INTEGER NOT NULL DEFAULT 0,
                min_players INTEGER NOT NULL,
                max_players INTEGER NOT NULL,
                night_timer_sec INTEGER NOT NULL,
                day_discussion_timer_sec INTEGER NOT NULL,
                day_vote_timer_sec INTEGER NOT NULL,
                winner TEXT,
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                ended_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT,
                token TEXT UNIQUE,
                alive INTEGER NOT NULL DEFAULT 1,
                eliminated_round INTEGER,
                eliminated_reason TEXT,
                joined_at TEXT NOT NULL,
                UNIQUE(game_id, user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS night_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                actor_user_id INTEGER NOT NULL,
                actor_role TEXT NOT NULL,
                target_user_id INTEGER,
                result TEXT,
                submitted_at TEXT NOT NULL,
                UNIQUE(game_id, round_number, actor_user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS day_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                voter_user_id INTEGER NOT NULL,
                target_user_id INTEGER,
                submitted_at TEXT NOT NULL,
                UNIQUE(game_id, round_number, voter_user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS round_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL
            )
        """)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ────────────────────────── Игры ──────────────────────────

def create_game(
    guild_id: int, channel_id: int, created_by: int,
    min_players: int, max_players: int,
    night_timer_sec: int, day_discussion_timer_sec: int, day_vote_timer_sec: int,
) -> dict:
    with closing(connect()) as conn, conn:
        cursor = conn.execute("""
            INSERT INTO games (
                guild_id, channel_id, min_players, max_players,
                night_timer_sec, day_discussion_timer_sec, day_vote_timer_sec,
                created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guild_id, channel_id, min_players, max_players,
            night_timer_sec, day_discussion_timer_sec, day_vote_timer_sec,
            created_by, _now(),
        ))
        game_id = cursor.lastrowid
    return get_game(game_id)


def get_game(game_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        return dict(row) if row else None


def get_game_by_lobby_message(message_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM games WHERE lobby_message_id = ?", (message_id,)).fetchone()
        return dict(row) if row else None


def get_game_by_vote_message(message_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM games WHERE vote_message_id = ?", (message_id,)).fetchone()
        return dict(row) if row else None


def get_active_game_in_channel(channel_id: int) -> dict | None:
    with closing(connect()) as conn:
        placeholders = ",".join("?" * len(ACTIVE_STATUSES))
        row = conn.execute(
            f"SELECT * FROM games WHERE channel_id = ? AND status IN ({placeholders})",
            (channel_id, *ACTIVE_STATUSES),
        ).fetchone()
        return dict(row) if row else None


def update_game(game_id: int, **fields) -> dict | None:
    if not fields:
        return get_game(game_id)
    columns = ", ".join(f"{key} = ?" for key in fields)
    with closing(connect()) as conn, conn:
        conn.execute(f"UPDATE games SET {columns} WHERE id = ?", (*fields.values(), game_id))
    return get_game(game_id)


def list_active_games() -> list[dict]:
    with closing(connect()) as conn:
        placeholders = ",".join("?" * len(ACTIVE_STATUSES))
        rows = conn.execute(
            f"SELECT * FROM games WHERE status IN ({placeholders}) ORDER BY created_at DESC",
            ACTIVE_STATUSES,
        ).fetchall()
        return [dict(r) for r in rows]


# ────────────────────────── Игроки ──────────────────────────

def add_player(game_id: int, user_id: int) -> bool:
    with closing(connect()) as conn, conn:
        try:
            conn.execute(
                "INSERT INTO players (game_id, user_id, joined_at) VALUES (?, ?, ?)",
                (game_id, user_id, _now()),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def remove_player(game_id: int, user_id: int) -> bool:
    with closing(connect()) as conn, conn:
        cursor = conn.execute("DELETE FROM players WHERE game_id = ? AND user_id = ?", (game_id, user_id))
        return cursor.rowcount > 0


def list_players(game_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM players WHERE game_id = ? ORDER BY joined_at", (game_id,)).fetchall()
        return [dict(r) for r in rows]


def list_alive_players(game_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM players WHERE game_id = ? AND alive = 1 ORDER BY joined_at", (game_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def count_players(game_id: int) -> int:
    with closing(connect()) as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM players WHERE game_id = ?", (game_id,)).fetchone()["c"]


def get_player(game_id: int, user_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM players WHERE game_id = ? AND user_id = ?", (game_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def get_player_by_token(token: str) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM players WHERE token = ?", (token,)).fetchone()
        return dict(row) if row else None


def assign_player_role(game_id: int, user_id: int, role: str, token: str | None) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE players SET role = ?, token = ? WHERE game_id = ? AND user_id = ?",
            (role, token, game_id, user_id),
        )


def eliminate_player(game_id: int, user_id: int, round_number: int, reason: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE players SET alive = 0, eliminated_round = ?, eliminated_reason = ? WHERE game_id = ? AND user_id = ?",
            (round_number, reason, game_id, user_id),
        )


# ────────────────────────── Ночные действия ──────────────────────────

def upsert_night_action(game_id: int, round_number: int, actor_user_id: int, actor_role: str, target_user_id: int | None) -> None:
    with closing(connect()) as conn, conn:
        conn.execute("""
            INSERT OR REPLACE INTO night_actions
            (game_id, round_number, actor_user_id, actor_role, target_user_id, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (game_id, round_number, actor_user_id, actor_role, target_user_id, _now()))


def get_night_action(game_id: int, round_number: int, actor_user_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM night_actions WHERE game_id = ? AND round_number = ? AND actor_user_id = ?",
            (game_id, round_number, actor_user_id),
        ).fetchone()
        return dict(row) if row else None


def get_night_actions(game_id: int, round_number: int, role: str | None = None) -> list[dict]:
    with closing(connect()) as conn:
        if role:
            rows = conn.execute(
                "SELECT * FROM night_actions WHERE game_id = ? AND round_number = ? AND actor_role = ?",
                (game_id, round_number, role),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM night_actions WHERE game_id = ? AND round_number = ?", (game_id, round_number)
            ).fetchall()
        return [dict(r) for r in rows]


def set_night_action_result(game_id: int, round_number: int, actor_user_id: int, result: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE night_actions SET result = ? WHERE game_id = ? AND round_number = ? AND actor_user_id = ?",
            (result, game_id, round_number, actor_user_id),
        )


# ────────────────────────── Дневные голоса ──────────────────────────

def upsert_day_vote(game_id: int, round_number: int, voter_user_id: int, target_user_id: int | None) -> None:
    with closing(connect()) as conn, conn:
        conn.execute("""
            INSERT OR REPLACE INTO day_votes (game_id, round_number, voter_user_id, target_user_id, submitted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (game_id, round_number, voter_user_id, target_user_id, _now()))


def get_day_votes(game_id: int, round_number: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM day_votes WHERE game_id = ? AND round_number = ?", (game_id, round_number)
        ).fetchall()
        return [dict(r) for r in rows]


def get_day_vote(game_id: int, round_number: int, voter_user_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM day_votes WHERE game_id = ? AND round_number = ? AND voter_user_id = ?",
            (game_id, round_number, voter_user_id),
        ).fetchone()
        return dict(row) if row else None


# ────────────────────────── События раунда ──────────────────────────

def add_round_event(game_id: int, round_number: int, event_type: str, payload: str = "") -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT INTO round_events (game_id, round_number, event_type, payload, created_at) VALUES (?, ?, ?, ?, ?)",
            (game_id, round_number, event_type, payload, _now()),
        )


def list_round_events(game_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM round_events WHERE game_id = ? ORDER BY id", (game_id,)
        ).fetchall()
        return [dict(r) for r in rows]
