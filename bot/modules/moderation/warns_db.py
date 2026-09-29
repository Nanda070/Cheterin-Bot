import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone


def get_db_path() -> str:
    return os.getenv("WARNS_DB_PATH", "warns.db")


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def db_init():
    with closing(db_connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                moderator_id INTEGER,
                source TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL,
                expires_at TEXT,
                removed INTEGER NOT NULL DEFAULT 0,
                removed_by INTEGER,
                removed_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_warns_user ON warns (guild_id, user_id)")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_warn(guild_id: int, user_id: int, reason: str, moderator_id: int | None, source: str, expires_at: str | None) -> sqlite3.Row:
    with closing(db_connect()) as conn, conn:
        cursor = conn.execute(
            """
            INSERT INTO warns (guild_id, user_id, reason, moderator_id, source, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (guild_id, user_id, reason, moderator_id, source, _now_iso(), expires_at),
        )
        warn_id = cursor.lastrowid
    with closing(db_connect()) as conn:
        return conn.execute("SELECT * FROM warns WHERE id = ?", (warn_id,)).fetchone()


def remove_warn(warn_id: int, removed_by: int | None) -> bool:
    with closing(db_connect()) as conn, conn:
        cursor = conn.execute(
            "UPDATE warns SET removed = 1, removed_by = ?, removed_at = ? WHERE id = ? AND removed = 0",
            (removed_by, _now_iso(), warn_id),
        )
        return cursor.rowcount > 0


def get_warn(warn_id: int) -> sqlite3.Row | None:
    with closing(db_connect()) as conn:
        return conn.execute("SELECT * FROM warns WHERE id = ?", (warn_id,)).fetchone()


def get_warns(guild_id: int, user_id: int) -> list[sqlite3.Row]:
    """История варнов участника, новые первыми."""
    with closing(db_connect()) as conn:
        return conn.execute(
            "SELECT * FROM warns WHERE guild_id = ? AND user_id = ? ORDER BY created_at DESC",
            (guild_id, user_id),
        ).fetchall()


def get_active_warn_count(guild_id: int, user_id: int) -> int:
    now = _now_iso()
    with closing(db_connect()) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM warns
            WHERE guild_id = ? AND user_id = ? AND removed = 0
              AND (expires_at IS NULL OR expires_at > ?)
            """,
            (guild_id, user_id, now),
        ).fetchone()
        return row["cnt"] if row else 0
