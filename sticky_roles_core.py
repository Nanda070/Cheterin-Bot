"""Sticky (rejoin) roles: remember selected roles on leave and restore on rejoin."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing

import settings_db

MODULE_NAME = "sticky_roles"


def get_db_path() -> str:
    return os.getenv("STICKY_ROLES_DB_PATH", "sticky_roles.db")


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
            CREATE TABLE IF NOT EXISTS sticky_role_snapshots (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role_ids TEXT NOT NULL DEFAULT '[]',
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )


def get_settings(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "enabled": bool(data.get("enabled", False)),
        # Empty list = track all assignable member roles (except @everyone / managed).
        "tracked_role_ids": [str(x) for x in (data.get("tracked_role_ids") or []) if str(x).isdigit()],
        "ignored_role_ids": [str(x) for x in (data.get("ignored_role_ids") or []) if str(x).isdigit()],
    }


def save_settings(
    guild_id: int,
    *,
    enabled: bool,
    tracked_role_ids: list[str] | None = None,
    ignored_role_ids: list[str] | None = None,
) -> dict:
    current = get_settings(guild_id)
    payload = {
        "enabled": bool(enabled),
        "tracked_role_ids": (
            [str(x) for x in tracked_role_ids if str(x).isdigit()]
            if tracked_role_ids is not None
            else current["tracked_role_ids"]
        ),
        "ignored_role_ids": (
            [str(x) for x in ignored_role_ids if str(x).isdigit()]
            if ignored_role_ids is not None
            else current["ignored_role_ids"]
        ),
    }
    settings_db.put(guild_id, MODULE_NAME, payload)
    return get_settings(guild_id)


def save_snapshot(guild_id: int, user_id: int, role_ids: list[int]) -> None:
    init()
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO sticky_role_snapshots (guild_id, user_id, role_ids)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, user_id) DO UPDATE SET role_ids = excluded.role_ids
            """,
            (guild_id, user_id, json.dumps([int(r) for r in role_ids])),
        )


def pop_snapshot(guild_id: int, user_id: int) -> list[int]:
    init()
    with closing(connect()) as conn, conn:
        row = conn.execute(
            "SELECT role_ids FROM sticky_role_snapshots WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
        if row is None:
            return []
        conn.execute(
            "DELETE FROM sticky_role_snapshots WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        )
    try:
        data = json.loads(row["role_ids"] or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    return [int(x) for x in data if str(x).isdigit()]


def filter_member_roles(member, settings: dict | None = None) -> list[int]:
    """Pick roles worth restoring for this member given guild settings."""
    settings = settings or get_settings(member.guild.id)
    ignored = {int(x) for x in settings["ignored_role_ids"]}
    tracked = {int(x) for x in settings["tracked_role_ids"]}
    result = []
    for role in member.roles:
        if role.is_default() or role.managed or role.id in ignored:
            continue
        if tracked and role.id not in tracked:
            continue
        result.append(role.id)
    return result
