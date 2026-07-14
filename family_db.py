"""SQLite-хранилище модуля «Семья» (портировано из FamQ): ростер, заявки, дни рождения.

Схема 1:1 с оригиналом FamQ, только синхронный sqlite3 вместо aiosqlite —
единый стиль хранения с voice_db.py/private_rooms.db.
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone


def get_db_path() -> str:
    return os.getenv("FAMILY_DB_PATH", "family.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS roster_msg (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                channel_id INTEGER,
                message_id INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_forms (
                user_id INTEGER PRIMARY KEY,
                nickname TEXT,
                game_level TEXT,
                faction_pref TEXT,
                online_timezone TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
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
                handled_by INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS birthdays (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                day INTEGER NOT NULL,
                month INTEGER NOT NULL,
                date_display TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS birthday_msg (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                channel_id INTEGER,
                message_id INTEGER
            )
        """)


# ────────────────────────── Live-ростер ──────────────────────────

def get_roster_data():
    with closing(connect()) as conn:
        return conn.execute("SELECT channel_id, message_id FROM roster_msg WHERE id = 1").fetchone()


def save_roster_data(channel_id: int, message_id: int):
    with closing(connect()) as conn, conn:
        conn.execute("INSERT OR REPLACE INTO roster_msg (id, channel_id, message_id) VALUES (1, ?, ?)", (channel_id, message_id))


def clear_roster_data():
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM roster_msg WHERE id = 1")


# ────────────────────────── Черновик анкеты (между 1/2 и 2/2) ──────────────────────────

def save_pending_form(user_id: int, nickname: str, game_level: str, faction_pref: str, online_timezone: str):
    with closing(connect()) as conn, conn:
        conn.execute("""
            INSERT OR REPLACE INTO pending_forms (user_id, nickname, game_level, faction_pref, online_timezone)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, nickname, game_level, faction_pref, online_timezone))


def get_pending_form(user_id: int):
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT nickname, game_level, faction_pref, online_timezone FROM pending_forms WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def delete_pending_form(user_id: int):
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM pending_forms WHERE user_id = ?", (user_id,))


# ────────────────────────── Заявки (тикеты) ──────────────────────────

def get_ticket_by_user(user_id: int):
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM tickets WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_ticket_by_thread(thread_id: int):
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM tickets WHERE thread_id = ?", (thread_id,)).fetchone()
        return dict(row) if row else None


def list_tickets(status: str | None = None, limit: int = 50, offset: int = 0):
    with closing(connect()) as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (status, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tickets ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()
        return [dict(r) for r in rows]


def count_tickets(status: str | None = None) -> int:
    with closing(connect()) as conn:
        if status:
            return conn.execute("SELECT COUNT(*) AS c FROM tickets WHERE status = ?", (status,)).fetchone()["c"]
        return conn.execute("SELECT COUNT(*) AS c FROM tickets").fetchone()["c"]


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


def update_ticket_indexes(user_id: int, mini_message_id: int | None = None, thread_id: int | None = None):
    with closing(connect()) as conn, conn:
        if mini_message_id is not None:
            conn.execute("UPDATE tickets SET mini_message_id = ? WHERE user_id = ?", (mini_message_id, user_id))
        if thread_id is not None:
            conn.execute("UPDATE tickets SET thread_id = ? WHERE user_id = ?", (thread_id, user_id))


def update_ticket_status(user_id: int, status: str, handled_by: int):
    with closing(connect()) as conn, conn:
        conn.execute("UPDATE tickets SET status = ?, handled_by = ? WHERE user_id = ?", (status, handled_by, user_id))


# ────────────────────────── Дни рождения ──────────────────────────

def save_birthday(user_id: int, guild_id: int, day: int, month: int, date_display: str):
    with closing(connect()) as conn, conn:
        conn.execute("""
            INSERT OR REPLACE INTO birthdays (user_id, guild_id, day, month, date_display)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, guild_id, day, month, date_display))


def delete_birthday(user_id: int) -> bool:
    with closing(connect()) as conn, conn:
        cursor = conn.execute("DELETE FROM birthdays WHERE user_id = ?", (user_id,))
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


def get_birthday_message_data():
    with closing(connect()) as conn:
        return conn.execute("SELECT channel_id, message_id FROM birthday_msg WHERE id = 1").fetchone()


def save_birthday_message_data(channel_id: int, message_id: int):
    with closing(connect()) as conn, conn:
        conn.execute("INSERT OR REPLACE INTO birthday_msg (id, channel_id, message_id) VALUES (1, ?, ?)", (channel_id, message_id))


def clear_birthday_message_data():
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM birthday_msg WHERE id = 1")
