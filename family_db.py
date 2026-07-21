"""SQLite-хранилище модуля «Семья» (портировано из FamQ): ростер, заявки, дни рождения.

Все таблицы per-guild (Фаза 2.2б MULTIGUILD_PLAN.md): ростер и список ДР — по одному
сообщению на сервер, заявки/черновики/дни рождения изолированы между серверами.
При миграции старой (одно-серверной) схемы существующие строки присваиваются
мейн-серверу (guild 404) — тот же приём, что в stats_db.py.
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

MAIN_GUILD = 404  # легаси-строки без guild_id при миграции достаются мейн-серверу


def get_db_path() -> str:
    return os.getenv("FAMILY_DB_PATH", "family.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _guild_id_in_pk(conn, table: str) -> bool:
    """True, если столбец guild_id существует и входит в первичный ключ."""
    for r in conn.execute(f"PRAGMA table_info({table})").fetchall():
        if r["name"] == "guild_id":
            return r["pk"] > 0
    return False


def init():
    with closing(connect()) as conn, conn:
        # ── roster_msg: id=1 (синглтон) → guild_id (per-guild) ──
        cols = _table_columns(conn, "roster_msg")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE roster_msg RENAME TO roster_msg_old")
            conn.execute("""
                CREATE TABLE roster_msg (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    message_id INTEGER
                )
            """)
            conn.execute(
                "INSERT INTO roster_msg (guild_id, channel_id, message_id) SELECT ?, channel_id, message_id FROM roster_msg_old",
                (MAIN_GUILD,),
            )
            conn.execute("DROP TABLE roster_msg_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS roster_msg (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    message_id INTEGER
                )
            """)

        # ── pending_forms: user_id PK → (guild_id, user_id) PK ──
        cols = _table_columns(conn, "pending_forms")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE pending_forms RENAME TO pending_forms_old")
            conn.execute("""
                CREATE TABLE pending_forms (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    nickname TEXT,
                    game_level TEXT,
                    faction_pref TEXT,
                    online_timezone TEXT,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            conn.execute(
                "INSERT INTO pending_forms (guild_id, user_id, nickname, game_level, faction_pref, online_timezone) "
                "SELECT ?, user_id, nickname, game_level, faction_pref, online_timezone FROM pending_forms_old",
                (MAIN_GUILD,),
            )
            conn.execute("DROP TABLE pending_forms_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_forms (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    nickname TEXT,
                    game_level TEXT,
                    faction_pref TEXT,
                    online_timezone TEXT,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)

        # ── tickets: user_id PK (guild_id уже есть колонкой) → (guild_id, user_id) PK ──
        cols = _table_columns(conn, "tickets")
        if cols and not _guild_id_in_pk(conn, "tickets"):
            gid_expr = "guild_id" if "guild_id" in cols else str(MAIN_GUILD)
            conn.execute("ALTER TABLE tickets RENAME TO tickets_old")
            conn.execute("""
                CREATE TABLE tickets (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    mini_message_id INTEGER,
                    thread_id INTEGER,
                    status TEXT NOT NULL,
                    nickname TEXT,
                    game_level TEXT,
                    faction_pref TEXT,
                    online_timezone TEXT,
                    real_name TEXT,
                    real_age TEXT,
                    about_text TEXT,
                    why_join TEXT,
                    inviter_nickname TEXT,
                    created_at TEXT NOT NULL,
                    handled_by INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            conn.execute(f"""
                INSERT INTO tickets
                (guild_id, user_id, mini_message_id, thread_id, status, nickname, game_level,
                 faction_pref, online_timezone, real_name, real_age, about_text, why_join,
                 inviter_nickname, created_at, handled_by)
                SELECT {gid_expr}, user_id, mini_message_id, thread_id, status, nickname, game_level,
                       faction_pref, online_timezone, real_name, real_age, about_text, why_join,
                       inviter_nickname, created_at, handled_by
                FROM tickets_old
            """)
            conn.execute("DROP TABLE tickets_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    mini_message_id INTEGER,
                    thread_id INTEGER,
                    status TEXT NOT NULL,
                    nickname TEXT,
                    game_level TEXT,
                    faction_pref TEXT,
                    online_timezone TEXT,
                    real_name TEXT,
                    real_age TEXT,
                    about_text TEXT,
                    why_join TEXT,
                    inviter_nickname TEXT,
                    created_at TEXT NOT NULL,
                    handled_by INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)

        # ── birthdays: user_id PK (guild_id уже есть колонкой) → (guild_id, user_id) PK ──
        cols = _table_columns(conn, "birthdays")
        if cols and not _guild_id_in_pk(conn, "birthdays"):
            gid_expr = "guild_id" if "guild_id" in cols else str(MAIN_GUILD)
            conn.execute("ALTER TABLE birthdays RENAME TO birthdays_old")
            conn.execute("""
                CREATE TABLE birthdays (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    day INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    date_display TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            conn.execute(
                f"INSERT INTO birthdays (guild_id, user_id, day, month, date_display) "
                f"SELECT {gid_expr}, user_id, day, month, date_display FROM birthdays_old"
            )
            conn.execute("DROP TABLE birthdays_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS birthdays (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    day INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    date_display TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)

        # ── birthday_msg: id=1 (синглтон) → guild_id (per-guild) ──
        cols = _table_columns(conn, "birthday_msg")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE birthday_msg RENAME TO birthday_msg_old")
            conn.execute("""
                CREATE TABLE birthday_msg (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    message_id INTEGER
                )
            """)
            conn.execute(
                "INSERT INTO birthday_msg (guild_id, channel_id, message_id) SELECT ?, channel_id, message_id FROM birthday_msg_old",
                (MAIN_GUILD,),
            )
            conn.execute("DROP TABLE birthday_msg_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS birthday_msg (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    message_id INTEGER
                )
            """)


# ────────────────────────── Live-ростер ──────────────────────────

def get_roster_data(guild_id: int):
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT channel_id, message_id FROM roster_msg WHERE guild_id = ?", (guild_id,)
        ).fetchone()


def save_roster_data(guild_id: int, channel_id: int, message_id: int):
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT OR REPLACE INTO roster_msg (guild_id, channel_id, message_id) VALUES (?, ?, ?)",
            (guild_id, channel_id, message_id),
        )


def clear_roster_data(guild_id: int):
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM roster_msg WHERE guild_id = ?", (guild_id,))


# ────────────────────────── Черновик анкеты (между 1/2 и 2/2) ──────────────────────────

def save_pending_form(guild_id: int, user_id: int, nickname: str, game_level: str, faction_pref: str, online_timezone: str):
    with closing(connect()) as conn, conn:
        conn.execute("""
            INSERT OR REPLACE INTO pending_forms (guild_id, user_id, nickname, game_level, faction_pref, online_timezone)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (guild_id, user_id, nickname, game_level, faction_pref, online_timezone))


def get_pending_form(guild_id: int, user_id: int):
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT nickname, game_level, faction_pref, online_timezone FROM pending_forms WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def delete_pending_form(guild_id: int, user_id: int):
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM pending_forms WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))


# ────────────────────────── Заявки (тикеты) ──────────────────────────

def get_ticket_by_user(guild_id: int, user_id: int):
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM tickets WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def get_ticket_by_thread(guild_id: int, thread_id: int):
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM tickets WHERE guild_id = ? AND thread_id = ?", (guild_id, thread_id)
        ).fetchone()
        return dict(row) if row else None


def list_tickets(guild_id: int, status: str | None = None, limit: int = 50, offset: int = 0):
    with closing(connect()) as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM tickets WHERE guild_id = ? AND status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (guild_id, status, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tickets WHERE guild_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (guild_id, limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]


def count_tickets(guild_id: int, status: str | None = None) -> int:
    with closing(connect()) as conn:
        if status:
            return conn.execute(
                "SELECT COUNT(*) AS c FROM tickets WHERE guild_id = ? AND status = ?", (guild_id, status)
            ).fetchone()["c"]
        return conn.execute(
            "SELECT COUNT(*) AS c FROM tickets WHERE guild_id = ?", (guild_id,)
        ).fetchone()["c"]


def create_ticket_record(user_id: int, guild_id: int, data: dict):
    created_at = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    with closing(connect()) as conn, conn:
        conn.execute("""
            INSERT OR REPLACE INTO tickets
            (user_id, guild_id, status, nickname, game_level, faction_pref, online_timezone,
             real_name, real_age, about_text, why_join, inviter_nickname, created_at)
            VALUES (?, ?, 'open', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, guild_id, data["nickname"], data["game_level"], data["faction_pref"], data["online_timezone"],
            data["real_name"], data["real_age"], data["about_text"], data["why_join"], data["inviter_nickname"],
            created_at,
        ))


def update_ticket_indexes(guild_id: int, user_id: int, mini_message_id: int | None = None, thread_id: int | None = None):
    with closing(connect()) as conn, conn:
        if mini_message_id is not None:
            conn.execute(
                "UPDATE tickets SET mini_message_id = ? WHERE guild_id = ? AND user_id = ?",
                (mini_message_id, guild_id, user_id),
            )
        if thread_id is not None:
            conn.execute(
                "UPDATE tickets SET thread_id = ? WHERE guild_id = ? AND user_id = ?",
                (thread_id, guild_id, user_id),
            )


def update_ticket_status(guild_id: int, user_id: int, status: str, handled_by: int):
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE tickets SET status = ?, handled_by = ? WHERE guild_id = ? AND user_id = ?",
            (status, handled_by, guild_id, user_id),
        )


# ────────────────────────── Дни рождения ──────────────────────────

def save_birthday(user_id: int, guild_id: int, day: int, month: int, date_display: str):
    with closing(connect()) as conn, conn:
        conn.execute("""
            INSERT OR REPLACE INTO birthdays (user_id, guild_id, day, month, date_display)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, guild_id, day, month, date_display))


def delete_birthday(guild_id: int, user_id: int) -> bool:
    with closing(connect()) as conn, conn:
        cursor = conn.execute(
            "DELETE FROM birthdays WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
        )
        return cursor.rowcount > 0


def get_all_birthdays(guild_id: int):
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM birthdays WHERE guild_id = ? ORDER BY month, day, user_id", (guild_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_birthdays_for_date(guild_id: int, day: int, month: int):
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM birthdays WHERE guild_id = ? AND day = ? AND month = ? ORDER BY user_id",
            (guild_id, day, month),
        ).fetchall()
        return [dict(r) for r in rows]


def get_birthday_message_data(guild_id: int):
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT channel_id, message_id FROM birthday_msg WHERE guild_id = ?", (guild_id,)
        ).fetchone()


def save_birthday_message_data(guild_id: int, channel_id: int, message_id: int):
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT OR REPLACE INTO birthday_msg (guild_id, channel_id, message_id) VALUES (?, ?, ?)",
            (guild_id, channel_id, message_id),
        )


def clear_birthday_message_data(guild_id: int):
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM birthday_msg WHERE guild_id = ?", (guild_id,))
