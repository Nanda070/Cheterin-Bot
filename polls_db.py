"""Polls: create, vote via buttons, end and announce results."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone


def get_db_path() -> str:
    return os.getenv("POLLS_DB_PATH", "polls.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER,
                question TEXT NOT NULL,
                options_json TEXT NOT NULL,
                ends_at TEXT NOT NULL,
                ended INTEGER NOT NULL DEFAULT 0,
                created_by INTEGER,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS poll_votes (
                poll_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                option_index INTEGER NOT NULL,
                PRIMARY KEY (poll_id, user_id)
            )
        """)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create(
    guild_id: int,
    channel_id: int,
    question: str,
    options: list[str],
    ends_at: str,
    created_by: int | None = None,
) -> dict:
    import json

    with closing(connect()) as conn, conn:
        cur = conn.execute(
            """INSERT INTO polls
               (guild_id, channel_id, message_id, question, options_json, ends_at, ended, created_by, created_at)
               VALUES (?, ?, NULL, ?, ?, ?, 0, ?, ?)""",
            (guild_id, channel_id, question, json.dumps(options, ensure_ascii=False), ends_at, created_by, _now()),
        )
        poll_id = cur.lastrowid
    return get(poll_id)


def get(poll_id: int) -> dict | None:
    import json

    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM polls WHERE id = ?", (poll_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["options"] = json.loads(d.pop("options_json"))
        d["ended"] = bool(d["ended"])
        return d


def set_message_id(poll_id: int, message_id: int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute("UPDATE polls SET message_id = ? WHERE id = ?", (message_id, poll_id))


def vote(poll_id: int, user_id: int, option_index: int) -> bool:
    poll = get(poll_id)
    if not poll or poll["ended"]:
        return False
    if option_index < 0 or option_index >= len(poll["options"]):
        return False
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO poll_votes (poll_id, user_id, option_index) VALUES (?, ?, ?)
               ON CONFLICT(poll_id, user_id) DO UPDATE SET option_index = excluded.option_index""",
            (poll_id, user_id, option_index),
        )
    return True


def tallies(poll_id: int) -> list[int]:
    poll = get(poll_id)
    if not poll:
        return []
    counts = [0] * len(poll["options"])
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT option_index, COUNT(*) AS c FROM poll_votes WHERE poll_id = ? GROUP BY option_index",
            (poll_id,),
        ).fetchall()
    for r in rows:
        idx = r["option_index"]
        if 0 <= idx < len(counts):
            counts[idx] = r["c"]
    return counts


def mark_ended(poll_id: int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute("UPDATE polls SET ended = 1 WHERE id = ?", (poll_id,))


def due_to_end(now_iso: str | None = None) -> list[dict]:
    now_iso = now_iso or _now()
    import json

    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM polls WHERE ended = 0 AND ends_at <= ?",
            (now_iso,),
        ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["options"] = json.loads(d.pop("options_json"))
        d["ended"] = bool(d["ended"])
        result.append(d)
    return result


def list_for_guild(guild_id: int, limit: int = 50) -> list[dict]:
    import json

    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM polls WHERE guild_id = ? ORDER BY id DESC LIMIT ?",
            (guild_id, limit),
        ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["options"] = json.loads(d.pop("options_json"))
        d["ended"] = bool(d["ended"])
        result.append(d)
    return result
