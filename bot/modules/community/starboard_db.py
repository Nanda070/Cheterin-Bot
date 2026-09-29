"""Starboard message mapping: original message_id → starboard message_id."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing


def get_db_path() -> str:
    return os.getenv("STARBOARD_DB_PATH", "starboard.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS starboard_messages (
                guild_id INTEGER NOT NULL,
                original_message_id INTEGER NOT NULL,
                starboard_message_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, original_message_id)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_starboard_sb_msg
            ON starboard_messages(guild_id, starboard_message_id)
            """
        )


def get_starboard_message(guild_id: int, original_message_id: int) -> int | None:
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT starboard_message_id FROM starboard_messages
            WHERE guild_id = ? AND original_message_id = ?
            """,
            (guild_id, original_message_id),
        ).fetchone()
    return int(row["starboard_message_id"]) if row else None


def upsert(
    guild_id: int,
    original_message_id: int,
    starboard_message_id: int,
    channel_id: int,
) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO starboard_messages
                (guild_id, original_message_id, starboard_message_id, channel_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, original_message_id) DO UPDATE SET
                starboard_message_id = excluded.starboard_message_id,
                channel_id = excluded.channel_id
            """,
            (guild_id, original_message_id, starboard_message_id, channel_id),
        )


def delete(guild_id: int, original_message_id: int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            DELETE FROM starboard_messages
            WHERE guild_id = ? AND original_message_id = ?
            """,
            (guild_id, original_message_id),
        )


def find_by_starboard_message(guild_id: int, starboard_message_id: int) -> int | None:
    """Return original_message_id if this starboard post is tracked."""
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT original_message_id FROM starboard_messages
            WHERE guild_id = ? AND starboard_message_id = ?
            """,
            (guild_id, starboard_message_id),
        ).fetchone()
    return int(row["original_message_id"]) if row else None
