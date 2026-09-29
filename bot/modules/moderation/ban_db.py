"""SQLite-хранилище временных банов из команды /ban (параметр time): переживает
перезапуск бота — на старте все ещё не наступившие разбаны планируются заново
(тот же recover-паттерн, что у mafia.py/bunker.py для игровых таймеров).
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone


def get_db_path() -> str:
    return os.getenv("BAN_DB_PATH", "moderation_bans.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_unbans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                unban_at_ts INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(guild_id, user_id)
            )
        """)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add(guild_id: int, user_id: int, unban_at_ts: int) -> int:
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM scheduled_unbans WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        cursor = conn.execute(
            "INSERT INTO scheduled_unbans (guild_id, user_id, unban_at_ts, created_at) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, unban_at_ts, _now()),
        )
        return cursor.lastrowid


def remove(row_id: int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM scheduled_unbans WHERE id = ?", (row_id,))


def get_by_user(guild_id: int, user_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM scheduled_unbans WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def list_all() -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM scheduled_unbans ORDER BY unban_at_ts").fetchall()
        return [dict(r) for r in rows]
