import os
import sqlite3
from contextlib import closing

user_owned_channels: dict[int, int] = {}


def get_db_path() -> str:
    return os.getenv("VOICE_DB_PATH", "private_rooms.db")


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def db_init():
    with closing(db_connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS private_rooms (
                guild_id INTEGER NOT NULL,
                channel_id INTEGER PRIMARY KEY,
                owner_id INTEGER NOT NULL,
                room_name TEXT NOT NULL,
                is_closed INTEGER NOT NULL DEFAULT 0,
                user_limit INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS room_access (
                channel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                access_type TEXT NOT NULL CHECK(access_type IN ('allow', 'deny')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(channel_id, user_id)
            )
        """)


def db_upsert_room(guild_id: int, channel_id: int, owner_id: int, room_name: str, is_closed: bool = False, user_limit: int = 0):
    with closing(db_connect()) as conn, conn:
        conn.execute("""
            INSERT INTO private_rooms (guild_id, channel_id, owner_id, room_name, is_closed, user_limit)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET
                guild_id=excluded.guild_id,
                owner_id=excluded.owner_id,
                room_name=excluded.room_name,
                is_closed=excluded.is_closed,
                user_limit=excluded.user_limit
        """, (guild_id, channel_id, owner_id, room_name, int(is_closed), user_limit))


def db_delete_room(channel_id: int):
    with closing(db_connect()) as conn, conn:
        conn.execute("DELETE FROM room_access WHERE channel_id = ?", (channel_id,))
        conn.execute("DELETE FROM private_rooms WHERE channel_id = ?", (channel_id,))


def db_get_room(channel_id: int):
    with closing(db_connect()) as conn:
        return conn.execute("SELECT * FROM private_rooms WHERE channel_id = ?", (channel_id,)).fetchone()


def db_get_all_rooms():
    with closing(db_connect()) as conn:
        return conn.execute("SELECT * FROM private_rooms").fetchall()


def db_update_room_name(channel_id: int, room_name: str):
    with closing(db_connect()) as conn, conn:
        conn.execute("UPDATE private_rooms SET room_name = ? WHERE channel_id = ?", (room_name, channel_id))


def db_update_room_limit(channel_id: int, user_limit: int):
    with closing(db_connect()) as conn, conn:
        conn.execute("UPDATE private_rooms SET user_limit = ? WHERE channel_id = ?", (user_limit, channel_id))


def db_update_room_closed(channel_id: int, is_closed: bool):
    with closing(db_connect()) as conn, conn:
        conn.execute("UPDATE private_rooms SET is_closed = ? WHERE channel_id = ?", (int(is_closed), channel_id))


def db_update_room_owner(channel_id: int, new_owner_id: int):
    with closing(db_connect()) as conn, conn:
        conn.execute("UPDATE private_rooms SET owner_id = ? WHERE channel_id = ?", (new_owner_id, channel_id))


def db_set_access(channel_id: int, user_id: int, access_type: str):
    with closing(db_connect()) as conn, conn:
        conn.execute("""
            INSERT INTO room_access (channel_id, user_id, access_type)
            VALUES (?, ?, ?)
            ON CONFLICT(channel_id, user_id) DO UPDATE SET
                access_type=excluded.access_type
        """, (channel_id, user_id, access_type))


def db_remove_access(channel_id: int, user_id: int):
    with closing(db_connect()) as conn, conn:
        conn.execute("DELETE FROM room_access WHERE channel_id = ? AND user_id = ?", (channel_id, user_id))


def db_get_access(channel_id: int, user_id: int):
    with closing(db_connect()) as conn:
        row = conn.execute("SELECT access_type FROM room_access WHERE channel_id = ? AND user_id = ?", (channel_id, user_id)).fetchone()
        return row["access_type"] if row else None


def db_get_all_access(channel_id: int):
    with closing(db_connect()) as conn:
        return conn.execute("SELECT user_id, access_type FROM room_access WHERE channel_id = ?", (channel_id,)).fetchall()
