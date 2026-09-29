"""Guild-wide birthday calendar (MM-DD), separate from family_birthdays."""

from __future__ import annotations

import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

MMDD_RE = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")


def get_db_path() -> str:
    return os.getenv("BIRTHDAYS_DB_PATH", "birthdays.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS birthdays (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                mm_dd TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
        """)


def is_valid_mm_dd(value: str) -> bool:
    return bool(MMDD_RE.match(value or ""))


def set_birthday(guild_id: int, user_id: int, mm_dd: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO birthdays (guild_id, user_id, mm_dd, updated_at) VALUES (?, ?, ?, ?)
               ON CONFLICT(guild_id, user_id) DO UPDATE SET
                 mm_dd = excluded.mm_dd, updated_at = excluded.updated_at""",
            (guild_id, user_id, mm_dd, now),
        )
    return {"guild_id": guild_id, "user_id": user_id, "mm_dd": mm_dd}


def delete_birthday(guild_id: int, user_id: int) -> bool:
    with closing(connect()) as conn, conn:
        cur = conn.execute(
            "DELETE FROM birthdays WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
        return cur.rowcount > 0


def get_birthday(guild_id: int, user_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT user_id, mm_dd FROM birthdays WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def list_birthdays(guild_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT user_id, mm_dd FROM birthdays WHERE guild_id = ? ORDER BY mm_dd",
            (guild_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def for_date(guild_id: int, mm_dd: str) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT user_id, mm_dd FROM birthdays WHERE guild_id = ? AND mm_dd = ?",
            (guild_id, mm_dd),
        ).fetchall()
    return [dict(r) for r in rows]
