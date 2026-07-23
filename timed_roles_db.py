"""Timed roles: assign a role until expires_at, then auto-remove."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone


def get_db_path() -> str:
    return os.getenv("TIMED_ROLES_DB_PATH", "timed_roles.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS timed_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(guild_id, user_id, role_id)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_timed_roles_expires ON timed_roles(expires_at)"
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add(guild_id: int, user_id: int, role_id: int, expires_at: str) -> dict:
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO timed_roles (guild_id, user_id, role_id, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(guild_id, user_id, role_id) DO UPDATE SET
                 expires_at = excluded.expires_at""",
            (guild_id, user_id, role_id, expires_at, _now()),
        )
        row = conn.execute(
            """SELECT * FROM timed_roles
               WHERE guild_id = ? AND user_id = ? AND role_id = ?""",
            (guild_id, user_id, role_id),
        ).fetchone()
    return dict(row)


def remove(row_id: int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM timed_roles WHERE id = ?", (row_id,))


def remove_by_keys(guild_id: int, user_id: int, role_id: int) -> bool:
    with closing(connect()) as conn, conn:
        cur = conn.execute(
            "DELETE FROM timed_roles WHERE guild_id = ? AND user_id = ? AND role_id = ?",
            (guild_id, user_id, role_id),
        )
        return cur.rowcount > 0


def list_for_guild(guild_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM timed_roles WHERE guild_id = ? ORDER BY expires_at",
            (guild_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def expired(now_iso: str | None = None) -> list[dict]:
    now_iso = now_iso or _now()
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM timed_roles WHERE expires_at <= ? ORDER BY expires_at",
            (now_iso,),
        ).fetchall()
    return [dict(r) for r in rows]
