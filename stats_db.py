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
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        # 1. xp_members schema & migration
        cur = conn.execute("PRAGMA table_info(xp_members)")
        cols = [r["name"] for r in cur.fetchall()]
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE xp_members RENAME TO xp_members_old")
            conn.execute("""
                CREATE TABLE xp_members (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    xp INTEGER NOT NULL DEFAULT 0,
                    level INTEGER NOT NULL DEFAULT 0,
                    messages INTEGER NOT NULL DEFAULT 0,
                    voice_seconds INTEGER NOT NULL DEFAULT 0,
                    last_text_xp_ts INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            conn.execute("INSERT INTO xp_members (guild_id, user_id, xp, level, messages, voice_seconds, last_text_xp_ts) SELECT 404, user_id, xp, level, messages, voice_seconds, last_text_xp_ts FROM xp_members_old")
            conn.execute("DROP TABLE xp_members_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS xp_members (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    xp INTEGER NOT NULL DEFAULT 0,
                    level INTEGER NOT NULL DEFAULT 0,
                    messages INTEGER NOT NULL DEFAULT 0,
                    voice_seconds INTEGER NOT NULL DEFAULT 0,
                    last_text_xp_ts INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)

        # 2. voice_sessions schema & migration
        cur = conn.execute("PRAGMA table_info(voice_sessions)")
        cols = [r["name"] for r in cur.fetchall()]
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE voice_sessions ADD COLUMN guild_id INTEGER NOT NULL DEFAULT 404")
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS voice_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_voice_sessions_guild ON voice_sessions(guild_id)")

        # 3. audit_log schema & migration
        cur = conn.execute("PRAGMA table_info(audit_log)")
        cols = [r["name"] for r in cur.fetchall()]
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE audit_log ADD COLUMN guild_id INTEGER NOT NULL DEFAULT 404")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_guild ON audit_log(guild_id)")


# ────────────────────────── XP ──────────────────────────

def xp_get_member(guild_id: int, user_id: int):
    with closing(connect()) as conn:
        return conn.execute("SELECT * FROM xp_members WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()


def xp_upsert_member(guild_id: int, user_id: int):
    with closing(connect()) as conn, conn:
        conn.execute("INSERT OR IGNORE INTO xp_members (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))


def xp_add_text(guild_id: int, user_id: int, amount: int, now_ts: int):
    with closing(connect()) as conn, conn:
        conn.execute("INSERT OR IGNORE INTO xp_members (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        conn.execute(
            "UPDATE xp_members SET xp = xp + ?, messages = messages + 1, last_text_xp_ts = ? WHERE guild_id = ? AND user_id = ?",
            (amount, now_ts, guild_id, user_id),
        )


def xp_add_voice(guild_id: int, user_id: int, xp_amount: int, active_seconds: int):
    with closing(connect()) as conn, conn:
        conn.execute("INSERT OR IGNORE INTO xp_members (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        conn.execute(
            "UPDATE xp_members SET xp = xp + ?, voice_seconds = voice_seconds + ? WHERE guild_id = ? AND user_id = ?",
            (xp_amount, active_seconds, guild_id, user_id),
        )


def xp_set_level(guild_id: int, user_id: int, level: int):
    with closing(connect()) as conn, conn:
        conn.execute("UPDATE xp_members SET level = ? WHERE guild_id = ? AND user_id = ?", (level, guild_id, user_id))


def xp_set_xp(guild_id: int, user_id: int, xp: int, level: int):
    with closing(connect()) as conn, conn:
        conn.execute("INSERT OR IGNORE INTO xp_members (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        conn.execute("UPDATE xp_members SET xp = ?, level = ? WHERE guild_id = ? AND user_id = ?", (xp, level, guild_id, user_id))


def xp_reset_member(guild_id: int, user_id: int):
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM xp_members WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))


def xp_reset_all(guild_id: int):
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM xp_members WHERE guild_id = ?", (guild_id,))


def xp_leaderboard(guild_id: int, limit: int = 100, offset: int = 0):
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT * FROM xp_members WHERE guild_id = ? ORDER BY xp DESC LIMIT ? OFFSET ?", (guild_id, limit, offset)
        ).fetchall()


def voice_leaderboard(guild_id: int, limit: int = 1000, offset: int = 0):
    """Лидеры по суммарному времени в голосовых каналах."""
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT * FROM xp_members WHERE guild_id = ? ORDER BY voice_seconds DESC LIMIT ? OFFSET ?", (guild_id, limit, offset)
        ).fetchall()


def xp_all_members(guild_id: int):
    """Все строки xp_members без пагинации — для мёржа с полным ростером гильдии."""
    with closing(connect()) as conn:
        return conn.execute("SELECT * FROM xp_members WHERE guild_id = ?", (guild_id,)).fetchall()


def xp_member_count(guild_id: int) -> int:
    with closing(connect()) as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM xp_members WHERE guild_id = ?", (guild_id,)).fetchone()["c"]


def xp_rank_of(guild_id: int, user_id: int) -> int | None:
    """Позиция участника в рейтинге (1-based) или None."""
    with closing(connect()) as conn:
        row = conn.execute("SELECT xp FROM xp_members WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)).fetchone()
        if row is None:
            return None
        higher = conn.execute("SELECT COUNT(*) AS c FROM xp_members WHERE guild_id = ? AND xp > ?", (guild_id, row["xp"])).fetchone()["c"]
        return higher + 1


# ────────────────────────── Войс-сессии ──────────────────────────

def voice_session_add(guild_id: int, user_id: int, channel_id: int, channel_name: str, joined_ts: int, left_ts: int, active_seconds: int):
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT INTO voice_sessions (guild_id, user_id, channel_id, channel_name, joined_ts, left_ts, active_seconds) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (guild_id, user_id, channel_id, channel_name, joined_ts, left_ts, active_seconds),
        )


def voice_sessions_since(guild_id: int, since_ts: int):
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT * FROM voice_sessions WHERE guild_id = ? AND left_ts >= ? ORDER BY joined_ts", (guild_id, since_ts)
        ).fetchall()


def voice_sessions_prune(before_ts: int):
    """Удаляет сессии старше указанного времени (ретенция сырых данных) глобально для всех серверов."""
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM voice_sessions WHERE left_ts < ?", (before_ts,))


# ────────────────────────── Аудит ──────────────────────────

def audit_add(guild_id: int, ts: int, moderator_id: int, moderator_name: str, method: str, path: str, action: str, status: int, details: str = ""):
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT INTO audit_log (guild_id, ts, moderator_id, moderator_name, method, path, action, status, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (guild_id, ts, moderator_id, moderator_name, method, path, action, status, details),
        )


def audit_list(
    guild_id: int,
    limit: int = 50,
    offset: int = 0,
    moderator_id: int | None = None,
    search: str | None = None,
):
    query = "SELECT * FROM audit_log WHERE guild_id = ?"
    params: list = [guild_id]
    if moderator_id is not None:
        query += " AND moderator_id = ?"
        params.append(moderator_id)
    if search:
        like = f"%{search}%"
        query += " AND (moderator_name LIKE ? OR action LIKE ? OR details LIKE ? OR path LIKE ?)"
        params.extend([like, like, like, like])
    query += " ORDER BY ts DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with closing(connect()) as conn:
        return conn.execute(query, params).fetchall()


def audit_count(guild_id: int, moderator_id: int | None = None, search: str | None = None) -> int:
    query = "SELECT COUNT(*) AS c FROM audit_log WHERE guild_id = ?"
    params: list = [guild_id]
    if moderator_id is not None:
        query += " AND moderator_id = ?"
        params.append(moderator_id)
    if search:
        like = f"%{search}%"
        query += " AND (moderator_name LIKE ? OR action LIKE ? OR details LIKE ? OR path LIKE ?)"
        params.extend([like, like, like, like])
    with closing(connect()) as conn:
        return conn.execute(query, params).fetchone()["c"]


def audit_moderators(guild_id: int) -> list:
    """Distinct moderators who have audit entries for this guild (newest name wins)."""
    with closing(connect()) as conn:
        return conn.execute(
            """
            SELECT moderator_id, moderator_name
            FROM audit_log
            WHERE guild_id = ? AND id IN (
                SELECT MAX(id) FROM audit_log WHERE guild_id = ? GROUP BY moderator_id
            )
            ORDER BY moderator_name COLLATE NOCASE
            """,
            (guild_id, guild_id),
        ).fetchall()
