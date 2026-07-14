"""Общее SQLite-хранилище для системы уровней, войс-статистики и аудита дашборда.

Отдельный файл от private_rooms.db: здесь высокочастотные данные (XP, сессии,
записи аудита), которые нельзя держать в JSON.
"""

import os
import sqlite3
from contextlib import closing


def get_db_path() -> str:
    return os.getenv("STATS_DB_PATH", "stats.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS xp_members (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 0,
                messages INTEGER NOT NULL DEFAULT 0,
                voice_seconds INTEGER NOT NULL DEFAULT 0,
                last_text_xp_ts INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS voice_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                channel_name TEXT NOT NULL DEFAULT '',
                joined_ts INTEGER NOT NULL,
                left_ts INTEGER NOT NULL,
                active_seconds INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_voice_sessions_joined ON voice_sessions(joined_ts)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_voice_sessions_user ON voice_sessions(user_id)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                moderator_name TEXT NOT NULL,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                action TEXT NOT NULL,
                status INTEGER NOT NULL,
                details TEXT NOT NULL DEFAULT ''
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts)")


# ────────────────────────── XP ──────────────────────────

def xp_get_member(user_id: int):
    with closing(connect()) as conn:
        return conn.execute("SELECT * FROM xp_members WHERE user_id = ?", (user_id,)).fetchone()


def xp_upsert_member(user_id: int):
    with closing(connect()) as conn, conn:
        conn.execute("INSERT OR IGNORE INTO xp_members (user_id) VALUES (?)", (user_id,))


def xp_add_text(user_id: int, amount: int, now_ts: int):
    with closing(connect()) as conn, conn:
        conn.execute("INSERT OR IGNORE INTO xp_members (user_id) VALUES (?)", (user_id,))
        conn.execute(
            "UPDATE xp_members SET xp = xp + ?, messages = messages + 1, last_text_xp_ts = ? WHERE user_id = ?",
            (amount, now_ts, user_id),
        )


def xp_add_voice(user_id: int, xp_amount: int, active_seconds: int):
    with closing(connect()) as conn, conn:
        conn.execute("INSERT OR IGNORE INTO xp_members (user_id) VALUES (?)", (user_id,))
        conn.execute(
            "UPDATE xp_members SET xp = xp + ?, voice_seconds = voice_seconds + ? WHERE user_id = ?",
            (xp_amount, active_seconds, user_id),
        )


def xp_set_level(user_id: int, level: int):
    with closing(connect()) as conn, conn:
        conn.execute("UPDATE xp_members SET level = ? WHERE user_id = ?", (level, user_id))


def xp_set_xp(user_id: int, xp: int, level: int):
    with closing(connect()) as conn, conn:
        conn.execute("INSERT OR IGNORE INTO xp_members (user_id) VALUES (?)", (user_id,))
        conn.execute("UPDATE xp_members SET xp = ?, level = ? WHERE user_id = ?", (xp, level, user_id))


def xp_reset_member(user_id: int):
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM xp_members WHERE user_id = ?", (user_id,))


def xp_reset_all():
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM xp_members")


def xp_leaderboard(limit: int = 100, offset: int = 0):
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT * FROM xp_members ORDER BY xp DESC LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()


def xp_all_members():
    """Все строки xp_members без пагинации — для мёржа с полным ростером гильдии."""
    with closing(connect()) as conn:
        return conn.execute("SELECT * FROM xp_members").fetchall()


def xp_member_count() -> int:
    with closing(connect()) as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM xp_members").fetchone()["c"]


def xp_rank_of(user_id: int) -> int | None:
    """Позиция участника в рейтинге (1-based) или None."""
    with closing(connect()) as conn:
        row = conn.execute("SELECT xp FROM xp_members WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            return None
        higher = conn.execute("SELECT COUNT(*) AS c FROM xp_members WHERE xp > ?", (row["xp"],)).fetchone()["c"]
        return higher + 1


# ────────────────────────── Войс-сессии ──────────────────────────

def voice_session_add(user_id: int, channel_id: int, channel_name: str, joined_ts: int, left_ts: int, active_seconds: int):
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT INTO voice_sessions (user_id, channel_id, channel_name, joined_ts, left_ts, active_seconds) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, channel_id, channel_name, joined_ts, left_ts, active_seconds),
        )


def voice_sessions_since(since_ts: int):
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT * FROM voice_sessions WHERE left_ts >= ? ORDER BY joined_ts", (since_ts,)
        ).fetchall()


def voice_sessions_prune(before_ts: int):
    """Удаляет сессии старше указанного времени (ретенция сырых данных)."""
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM voice_sessions WHERE left_ts < ?", (before_ts,))


# ────────────────────────── Аудит ──────────────────────────

def audit_add(ts: int, moderator_id: int, moderator_name: str, method: str, path: str, action: str, status: int, details: str = ""):
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT INTO audit_log (ts, moderator_id, moderator_name, method, path, action, status, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ts, moderator_id, moderator_name, method, path, action, status, details),
        )


def audit_list(limit: int = 50, offset: int = 0, moderator_id: int | None = None):
    query = "SELECT * FROM audit_log"
    params: list = []
    if moderator_id is not None:
        query += " WHERE moderator_id = ?"
        params.append(moderator_id)
    query += " ORDER BY ts DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with closing(connect()) as conn:
        return conn.execute(query, params).fetchall()


def audit_count(moderator_id: int | None = None) -> int:
    with closing(connect()) as conn:
        if moderator_id is not None:
            return conn.execute("SELECT COUNT(*) AS c FROM audit_log WHERE moderator_id = ?", (moderator_id,)).fetchone()["c"]
        return conn.execute("SELECT COUNT(*) AS c FROM audit_log").fetchone()["c"]
