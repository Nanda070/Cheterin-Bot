"""Per-member verification consent timestamps (rules agreement / re-verify)."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone


def get_db_path() -> str:
    return os.getenv("VERIFICATION_DB_PATH", "verification.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS verification_consent (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                verified_at TEXT NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_verification_consent_guild "
            "ON verification_consent(guild_id)"
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_consent(guild_id: int, user_id: int, verified_at: str | None = None) -> dict:
    verified_at = verified_at or _now()
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO verification_consent (guild_id, user_id, verified_at)
               VALUES (?, ?, ?)
               ON CONFLICT(guild_id, user_id) DO UPDATE SET
                 verified_at = excluded.verified_at""",
            (guild_id, user_id, verified_at),
        )
        row = conn.execute(
            "SELECT * FROM verification_consent WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
    return dict(row)


def get_consent(guild_id: int, user_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM verification_consent WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def clear_consent(guild_id: int, user_id: int) -> bool:
    with closing(connect()) as conn, conn:
        cur = conn.execute(
            "DELETE FROM verification_consent WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
        return cur.rowcount > 0


def list_consents(guild_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM verification_consent WHERE guild_id = ? ORDER BY verified_at",
            (guild_id,),
        ).fetchall()
    return [dict(r) for r in rows]
