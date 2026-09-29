"""SQLite-хранилище модуля «Семья» (портировано из FamQ): ростер, заявки, дни рождения.

Все таблицы per-guild (Фаза 2.2б MULTIGUILD_PLAN.md): ростер и список ДР — по одному
сообщению на сервер, заявки/черновики/дни рождения изолированы между серверами.
При миграции старой (одно-серверной) схемы существующие строки присваиваются
мейн-серверу (GUILD_ID / MAIN_GUILD_ID) — тот же приём, что в economy_db.py.
Ранний sentinel 404 ремонтируется при init().
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

# Ошибочный sentinel первой per-guild миграции (легаси уезжало на guild_id=404).
_MISATTRIBUTED_GUILD = 404


def get_main_guild_id() -> int:
    """Мейн-сервер для миграции легаси-строк без guild_id."""
    return int(os.getenv("GUILD_ID") or os.getenv("MAIN_GUILD_ID") or "1324239354154975252")


def __getattr__(name: str):
    if name == "MAIN_GUILD":
        return get_main_guild_id()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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


def _move_or_drop_user_rows(conn: sqlite3.Connection, table: str, key_cols: tuple[str, ...], real_main: int) -> None:
    if table not in {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")} \
            or "guild_id" not in _table_columns(conn, table):
        return
    rows = conn.execute(f"SELECT * FROM {table} WHERE guild_id = ?", (_MISATTRIBUTED_GUILD,)).fetchall()
    for row in rows:
        where = " AND ".join(f"{c} = ?" for c in key_cols)
        key_vals = [row[c] for c in key_cols]
        exists = conn.execute(
            f"SELECT 1 FROM {table} WHERE guild_id = ? AND {where}",
            [real_main] + key_vals,
        ).fetchone()
        if exists is None:
            conn.execute(
                f"UPDATE {table} SET guild_id = ? WHERE guild_id = ? AND {where}",
                [real_main, _MISATTRIBUTED_GUILD] + key_vals,
            )
        else:
            conn.execute(
                f"DELETE FROM {table} WHERE guild_id = ? AND {where}",
                [_MISATTRIBUTED_GUILD] + key_vals,
            )


def _move_or_drop_singleton(conn: sqlite3.Connection, table: str, real_main: int) -> None:
    if table not in {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")} \
            or "guild_id" not in _table_columns(conn, table):
        return
    row = conn.execute(f"SELECT * FROM {table} WHERE guild_id = ?", (_MISATTRIBUTED_GUILD,)).fetchone()
    if row is None:
        return
    exists = conn.execute(f"SELECT 1 FROM {table} WHERE guild_id = ?", (real_main,)).fetchone()
    if exists is None:
        conn.execute(
            f"UPDATE {table} SET guild_id = ? WHERE guild_id = ?",
            (real_main, _MISATTRIBUTED_GUILD),
        )
    else:
        conn.execute(f"DELETE FROM {table} WHERE guild_id = ?", (_MISATTRIBUTED_GUILD,))


def _repair_misattributed_guild(conn: sqlite3.Connection) -> None:
    real_main = get_main_guild_id()
    if real_main == _MISATTRIBUTED_GUILD:
        return
    _move_or_drop_singleton(conn, "roster_msg", real_main)
    _move_or_drop_singleton(conn, "birthday_msg", real_main)
    _move_or_drop_user_rows(conn, "pending_forms", ("user_id",), real_main)
    _move_or_drop_user_rows(conn, "tickets", ("user_id",), real_main)
    _move_or_drop_user_rows(conn, "birthdays", ("user_id",), real_main)


def init():
    with closing(connect()) as conn, conn:
        main_guild = get_main_guild_id()
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
                (main_guild,),
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
                (main_guild,),
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
            gid_expr = "guild_id" if "guild_id" in cols else str(main_guild)
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
            gid_expr = "guild_id" if "guild_id" in cols else str(main_guild)
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
                (main_guild,),
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

        _repair_misattributed_guild(conn)


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
