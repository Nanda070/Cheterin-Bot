"""Relations pairs + cooldowns + daily action counters (guild-scoped)."""

from __future__ import annotations

import os
import sqlite3
import time
from contextlib import closing


def get_db_path() -> str:
    return os.getenv("RELATIONS_DB_PATH", "relations.db")


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
            CREATE TABLE IF NOT EXISTS relations_pairs (
                guild_id INTEGER NOT NULL,
                user_a INTEGER NOT NULL,
                user_b INTEGER NOT NULL,
                hp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                updated_at REAL NOT NULL,
                PRIMARY KEY (guild_id, user_a, user_b)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_relations_pairs_hp
            ON relations_pairs(guild_id, hp DESC)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS relations_cooldowns (
                guild_id INTEGER NOT NULL,
                user_a INTEGER NOT NULL,
                user_b INTEGER NOT NULL,
                action_id TEXT NOT NULL,
                available_at REAL NOT NULL,
                PRIMARY KEY (guild_id, user_a, user_b, action_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS relations_daily (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                day_key TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, day_key)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS relations_marriages (
                guild_id INTEGER NOT NULL,
                user_a INTEGER NOT NULL,
                user_b INTEGER NOT NULL,
                married_at REAL NOT NULL,
                PRIMARY KEY (guild_id, user_a, user_b)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_relations_marriages_guild
            ON relations_marriages(guild_id, married_at ASC)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS relations_proposals (
                guild_id INTEGER NOT NULL,
                proposer_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                PRIMARY KEY (guild_id, proposer_id, target_id)
            )
            """
        )


def get_pair(guild_id: int, user_a: int, user_b: int) -> dict | None:
    a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT user_a, user_b, hp, level, updated_at
            FROM relations_pairs
            WHERE guild_id = ? AND user_a = ? AND user_b = ?
            """,
            (guild_id, a, b),
        ).fetchone()
    if not row:
        return None
    return {
        "user_a": int(row["user_a"]),
        "user_b": int(row["user_b"]),
        "hp": int(row["hp"]),
        "level": int(row["level"]),
        "updated_at": float(row["updated_at"]),
    }


def ensure_pair(guild_id: int, user_a: int, user_b: int) -> dict:
    existing = get_pair(guild_id, user_a, user_b)
    if existing:
        return existing
    a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)
    now = time.time()
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO relations_pairs
                (guild_id, user_a, user_b, hp, level, updated_at)
            VALUES (?, ?, ?, 0, 1, ?)
            """,
            (guild_id, a, b, now),
        )
    return get_pair(guild_id, a, b) or {
        "user_a": a,
        "user_b": b,
        "hp": 0,
        "level": 1,
        "updated_at": now,
    }


def add_hp(guild_id: int, user_a: int, user_b: int, amount: int, *, level: int) -> dict:
    a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)
    now = time.time()
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO relations_pairs (guild_id, user_a, user_b, hp, level, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_a, user_b) DO UPDATE SET
                hp = relations_pairs.hp + excluded.hp,
                level = excluded.level,
                updated_at = excluded.updated_at
            """,
            (guild_id, a, b, max(0, amount), level, now),
        )
        # Recompute hp then set level from caller (level already computed after add)
        conn.execute(
            """
            UPDATE relations_pairs SET level = ?, updated_at = ?
            WHERE guild_id = ? AND user_a = ? AND user_b = ?
            """,
            (level, now, guild_id, a, b),
        )
    return get_pair(guild_id, a, b) or ensure_pair(guild_id, a, b)


def apply_action_hp(
    guild_id: int,
    user_a: int,
    user_b: int,
    hp_gain: int,
    level_for_hp_fn,
) -> tuple[dict, int, int]:
    """Add HP and sync level. Returns (pair, old_level, new_level)."""
    pair = ensure_pair(guild_id, user_a, user_b)
    old_level = int(pair["level"])
    new_hp = int(pair["hp"]) + max(0, hp_gain)
    new_level = int(level_for_hp_fn(new_hp))
    a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)
    now = time.time()
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            UPDATE relations_pairs
            SET hp = ?, level = ?, updated_at = ?
            WHERE guild_id = ? AND user_a = ? AND user_b = ?
            """,
            (new_hp, new_level, now, guild_id, a, b),
        )
    updated = get_pair(guild_id, a, b) or {
        "user_a": a,
        "user_b": b,
        "hp": new_hp,
        "level": new_level,
        "updated_at": now,
    }
    return updated, old_level, new_level


def top_pairs(guild_id: int, limit: int = 15) -> list[dict]:
    lim = max(1, min(50, limit))
    with closing(connect()) as conn:
        rows = conn.execute(
            """
            SELECT user_a, user_b, hp, level, updated_at
            FROM relations_pairs
            WHERE guild_id = ?
            ORDER BY hp DESC, updated_at DESC
            LIMIT ?
            """,
            (guild_id, lim),
        ).fetchall()
    return [
        {
            "user_a": int(r["user_a"]),
            "user_b": int(r["user_b"]),
            "hp": int(r["hp"]),
            "level": int(r["level"]),
            "updated_at": float(r["updated_at"]),
        }
        for r in rows
    ]


def max_level_for_user(guild_id: int, user_id: int) -> int:
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT MAX(level) AS mx FROM relations_pairs
            WHERE guild_id = ? AND (user_a = ? OR user_b = ?)
            """,
            (guild_id, user_id, user_id),
        ).fetchone()
    if not row or row["mx"] is None:
        return 1
    return int(row["mx"])


def cooldown_remaining(guild_id: int, user_a: int, user_b: int, action_id: str) -> float:
    a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT available_at FROM relations_cooldowns
            WHERE guild_id = ? AND user_a = ? AND user_b = ? AND action_id = ?
            """,
            (guild_id, a, b, action_id),
        ).fetchone()
    if not row:
        return 0.0
    return max(0.0, float(row["available_at"]) - time.time())


def set_cooldown(guild_id: int, user_a: int, user_b: int, action_id: str, cooldown_sec: int) -> None:
    if cooldown_sec <= 0:
        return
    a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)
    available = time.time() + cooldown_sec
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO relations_cooldowns
                (guild_id, user_a, user_b, action_id, available_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_a, user_b, action_id) DO UPDATE SET
                available_at = excluded.available_at
            """,
            (guild_id, a, b, action_id, available),
        )


def daily_count(guild_id: int, user_id: int, day_key: str) -> int:
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT count FROM relations_daily
            WHERE guild_id = ? AND user_id = ? AND day_key = ?
            """,
            (guild_id, user_id, day_key),
        ).fetchone()
    return int(row["count"]) if row else 0


def bump_daily(guild_id: int, user_id: int, day_key: str) -> int:
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO relations_daily (guild_id, user_id, day_key, count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(guild_id, user_id, day_key) DO UPDATE SET
                count = relations_daily.count + 1
            """,
            (guild_id, user_id, day_key),
        )
        row = conn.execute(
            """
            SELECT count FROM relations_daily
            WHERE guild_id = ? AND user_id = ? AND day_key = ?
            """,
            (guild_id, user_id, day_key),
        ).fetchone()
    return int(row["count"]) if row else 1


# ── Marriage / proposals ──


def _marriage_row(row: sqlite3.Row) -> dict:
    return {
        "user_a": int(row["user_a"]),
        "user_b": int(row["user_b"]),
        "married_at": float(row["married_at"]),
    }


def are_married(guild_id: int, user_a: int, user_b: int) -> bool:
    a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT 1 FROM relations_marriages
            WHERE guild_id = ? AND user_a = ? AND user_b = ?
            """,
            (guild_id, a, b),
        ).fetchone()
    return row is not None


def get_marriage(guild_id: int, user_a: int, user_b: int) -> dict | None:
    a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT user_a, user_b, married_at FROM relations_marriages
            WHERE guild_id = ? AND user_a = ? AND user_b = ?
            """,
            (guild_id, a, b),
        ).fetchone()
    return _marriage_row(row) if row else None


def get_spouses(guild_id: int, user_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            """
            SELECT user_a, user_b, married_at FROM relations_marriages
            WHERE guild_id = ? AND (user_a = ? OR user_b = ?)
            ORDER BY married_at ASC
            """,
            (guild_id, user_id, user_id),
        ).fetchall()
    out: list[dict] = []
    for row in rows:
        m = _marriage_row(row)
        other = m["user_b"] if m["user_a"] == user_id else m["user_a"]
        out.append({**m, "spouse_id": other})
    return out


def get_spouse(guild_id: int, user_id: int) -> dict | None:
    spouses = get_spouses(guild_id, user_id)
    return spouses[0] if spouses else None


def marriage_count(guild_id: int, user_id: int) -> int:
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM relations_marriages
            WHERE guild_id = ? AND (user_a = ? OR user_b = ?)
            """,
            (guild_id, user_id, user_id),
        ).fetchone()
    return int(row["c"]) if row else 0


def create_marriage(guild_id: int, user_a: int, user_b: int) -> dict:
    a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)
    now = time.time()
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO relations_marriages
                (guild_id, user_a, user_b, married_at)
            VALUES (?, ?, ?, ?)
            """,
            (guild_id, a, b, now),
        )
        # Clear any proposals involving either user with each other
        conn.execute(
            """
            DELETE FROM relations_proposals
            WHERE guild_id = ?
              AND (
                (proposer_id = ? AND target_id = ?)
                OR (proposer_id = ? AND target_id = ?)
              )
            """,
            (guild_id, a, b, b, a),
        )
    return get_marriage(guild_id, a, b) or {
        "user_a": a,
        "user_b": b,
        "married_at": now,
    }


def dissolve_marriage(guild_id: int, user_a: int, user_b: int) -> bool:
    a, b = (user_a, user_b) if user_a < user_b else (user_b, user_a)
    with closing(connect()) as conn, conn:
        cur = conn.execute(
            """
            DELETE FROM relations_marriages
            WHERE guild_id = ? AND user_a = ? AND user_b = ?
            """,
            (guild_id, a, b),
        )
    return cur.rowcount > 0


def top_marriages(guild_id: int, limit: int = 15) -> list[dict]:
    lim = max(1, min(50, limit))
    with closing(connect()) as conn:
        rows = conn.execute(
            """
            SELECT m.user_a, m.user_b, m.married_at, p.hp, p.level
            FROM relations_marriages m
            LEFT JOIN relations_pairs p
              ON p.guild_id = m.guild_id AND p.user_a = m.user_a AND p.user_b = m.user_b
            WHERE m.guild_id = ?
            ORDER BY m.married_at ASC
            LIMIT ?
            """,
            (guild_id, lim),
        ).fetchall()
    return [
        {
            "user_a": int(r["user_a"]),
            "user_b": int(r["user_b"]),
            "married_at": float(r["married_at"]),
            "hp": int(r["hp"] or 0),
            "level": int(r["level"] or 1),
        }
        for r in rows
    ]


def upsert_proposal(
    guild_id: int, proposer_id: int, target_id: int, timeout_sec: int
) -> dict:
    now = time.time()
    expires = now + max(1, timeout_sec)
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO relations_proposals
                (guild_id, proposer_id, target_id, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, proposer_id, target_id) DO UPDATE SET
                created_at = excluded.created_at,
                expires_at = excluded.expires_at
            """,
            (guild_id, proposer_id, target_id, now, expires),
        )
    return {
        "proposer_id": proposer_id,
        "target_id": target_id,
        "created_at": now,
        "expires_at": expires,
    }


def get_proposal(guild_id: int, proposer_id: int, target_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT proposer_id, target_id, created_at, expires_at
            FROM relations_proposals
            WHERE guild_id = ? AND proposer_id = ? AND target_id = ?
            """,
            (guild_id, proposer_id, target_id),
        ).fetchone()
    if not row:
        return None
    return {
        "proposer_id": int(row["proposer_id"]),
        "target_id": int(row["target_id"]),
        "created_at": float(row["created_at"]),
        "expires_at": float(row["expires_at"]),
    }


def clear_proposal(guild_id: int, proposer_id: int, target_id: int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            DELETE FROM relations_proposals
            WHERE guild_id = ? AND proposer_id = ? AND target_id = ?
            """,
            (guild_id, proposer_id, target_id),
        )


def clear_expired_proposals(guild_id: int | None = None) -> int:
    now = time.time()
    with closing(connect()) as conn, conn:
        if guild_id is None:
            cur = conn.execute(
                "DELETE FROM relations_proposals WHERE expires_at < ?",
                (now,),
            )
        else:
            cur = conn.execute(
                "DELETE FROM relations_proposals WHERE guild_id = ? AND expires_at < ?",
                (guild_id, now),
            )
    return int(cur.rowcount)


def has_outgoing_proposal(guild_id: int, proposer_id: int) -> bool:
    now = time.time()
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT 1 FROM relations_proposals
            WHERE guild_id = ? AND proposer_id = ? AND expires_at >= ?
            LIMIT 1
            """,
            (guild_id, proposer_id, now),
        ).fetchone()
    return row is not None


def has_incoming_proposal(guild_id: int, target_id: int) -> bool:
    now = time.time()
    with closing(connect()) as conn:
        row = conn.execute(
            """
            SELECT 1 FROM relations_proposals
            WHERE guild_id = ? AND target_id = ? AND expires_at >= ?
            LIMIT 1
            """,
            (guild_id, target_id, now),
        ).fetchone()
    return row is not None
