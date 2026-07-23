"""Invite tracker: snapshot of invite uses + join attribution per guild."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone


def get_db_path() -> str:
    return os.getenv("INVITES_DB_PATH", "invites.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invite_snapshot (
                guild_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                inviter_id INTEGER,
                uses INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, code)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invite_joins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                invitee_id INTEGER NOT NULL,
                inviter_id INTEGER,
                code TEXT,
                joined_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_invite_joins_guild ON invite_joins(guild_id, inviter_id)"
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_snapshot(guild_id: int, code: str, inviter_id: int | None, uses: int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO invite_snapshot (guild_id, code, inviter_id, uses)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(guild_id, code) DO UPDATE SET
                 inviter_id = excluded.inviter_id, uses = excluded.uses""",
            (guild_id, code, inviter_id, uses),
        )


def get_snapshot(guild_id: int) -> dict[str, dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT code, inviter_id, uses FROM invite_snapshot WHERE guild_id = ?",
            (guild_id,),
        ).fetchall()
    return {r["code"]: {"inviter_id": r["inviter_id"], "uses": r["uses"]} for r in rows}


def record_join(guild_id: int, invitee_id: int, inviter_id: int | None, code: str | None) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO invite_joins (guild_id, invitee_id, inviter_id, code, joined_at)
               VALUES (?, ?, ?, ?, ?)""",
            (guild_id, invitee_id, inviter_id, code, _now()),
        )


def inviter_stats(guild_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            """SELECT inviter_id, COUNT(*) AS joins
               FROM invite_joins
               WHERE guild_id = ? AND inviter_id IS NOT NULL
               GROUP BY inviter_id
               ORDER BY joins DESC""",
            (guild_id,),
        ).fetchall()
    return [{"inviter_id": r["inviter_id"], "joins": r["joins"]} for r in rows]


def recent_joins(guild_id: int, limit: int = 50) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            """SELECT invitee_id, inviter_id, code, joined_at
               FROM invite_joins WHERE guild_id = ?
               ORDER BY id DESC LIMIT ?""",
            (guild_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]
