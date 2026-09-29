"""ValChecker SQLite store — schema mirrors ValChecker/src/db/database.js."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from typing import Any


def get_db_path() -> str:
    return os.getenv("VALCHECKER_DB_PATH", "valchecker.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    with closing(connect()) as conn, conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              discord_id TEXT PRIMARY KEY,
              puuid TEXT NOT NULL,
              name TEXT NOT NULL,
              tag TEXT NOT NULL,
              region TEXT NOT NULL DEFAULT 'eu',
              platform TEXT NOT NULL DEFAULT 'pc',
              track INTEGER NOT NULL DEFAULT 0,
              last_match_id TEXT,
              last_rr INTEGER,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS guild_settings (
              guild_id TEXT PRIMARY KEY,
              match_channel_id TEXT,
              digest_channel_id TEXT,
              alert_channel_id TEXT,
              roles_enabled INTEGER NOT NULL DEFAULT 0,
              locale TEXT NOT NULL DEFAULT 'en',
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS rank_roles (
              guild_id TEXT NOT NULL,
              rank_tier TEXT NOT NULL,
              role_id TEXT NOT NULL,
              PRIMARY KEY (guild_id, rank_tier)
            );

            CREATE TABLE IF NOT EXISTS match_cache (
              match_id TEXT NOT NULL,
              puuid TEXT NOT NULL,
              region TEXT,
              map TEXT,
              mode TEXT,
              agent TEXT,
              kills INTEGER,
              deaths INTEGER,
              assists INTEGER,
              acs REAL,
              hs_pct REAL,
              won INTEGER,
              rr_change INTEGER,
              played_at TEXT,
              raw_json TEXT,
              PRIMARY KEY (match_id, puuid)
            );

            CREATE TABLE IF NOT EXISTS status_state (
              region TEXT PRIMARY KEY,
              fingerprints TEXT NOT NULL DEFAULT '{}',
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_users_track ON users(track);
            CREATE INDEX IF NOT EXISTS idx_match_puuid ON match_cache(puuid);
            """
        )
        try:
            conn.execute("ALTER TABLE users ADD COLUMN last_rank TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute(
                "ALTER TABLE guild_settings ADD COLUMN locale TEXT NOT NULL DEFAULT 'en'"
            )
        except sqlite3.OperationalError:
            pass


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def link_user(
    *,
    discord_id: str,
    puuid: str,
    name: str,
    tag: str,
    region: str,
    platform: str,
) -> None:
    existing = get_user(discord_id)
    account_changed = existing is None or existing["puuid"] != puuid

    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO users (discord_id, puuid, name, tag, region, platform, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(discord_id) DO UPDATE SET
              puuid=excluded.puuid, name=excluded.name, tag=excluded.tag,
              region=excluded.region, platform=excluded.platform, updated_at=datetime('now')
            """,
            (discord_id, puuid, name, tag, region, platform),
        )
        if account_changed:
            conn.execute(
                """
                UPDATE users SET
                  last_match_id = NULL,
                  last_rr = NULL,
                  last_rank = NULL,
                  updated_at = datetime('now')
                WHERE discord_id = ?
                """,
                (discord_id,),
            )


def unlink_user(discord_id: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM users WHERE discord_id = ?", (discord_id,))


def get_user(discord_id: str) -> dict[str, Any] | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE discord_id = ?", (str(discord_id),)
        ).fetchone()
    return _row_to_dict(row)


def get_user_by_puuid(puuid: str) -> dict[str, Any] | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM users WHERE puuid = ?", (puuid,)).fetchone()
    return _row_to_dict(row)


def set_tracking(discord_id: str, track: bool) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE users SET track = ?, updated_at = datetime('now') WHERE discord_id = ?",
            (1 if track else 0, str(discord_id)),
        )


def get_tracked_users() -> list[dict[str, Any]]:
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM users WHERE track = 1").fetchall()
    return [dict(r) for r in rows]


def update_track_state(
    discord_id: str,
    *,
    last_match_id: str | None = None,
    last_rr: int | float | None = None,
    last_rank: str | None = None,
) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            UPDATE users SET
              last_match_id = COALESCE(?, last_match_id),
              last_rr = COALESCE(?, last_rr),
              last_rank = COALESCE(?, last_rank),
              updated_at = datetime('now')
            WHERE discord_id = ?
            """,
            (last_match_id, last_rr, last_rank, str(discord_id)),
        )


def update_riot_name(discord_id: str, name: str, tag: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE users SET name = ?, tag = ?, updated_at = datetime('now') WHERE discord_id = ?",
            (name, tag, str(discord_id)),
        )


def get_guild_settings(guild_id: str | int) -> dict[str, Any]:
    gid = str(guild_id)
    with closing(connect()) as conn, conn:
        row = conn.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?", (gid,)
        ).fetchone()
        if row is None:
            conn.execute("INSERT INTO guild_settings (guild_id) VALUES (?)", (gid,))
            row = conn.execute(
                "SELECT * FROM guild_settings WHERE guild_id = ?", (gid,)
            ).fetchone()
    return dict(row)


def set_guild_settings(guild_id: str | int, patch: dict[str, Any]) -> None:
    gid = str(guild_id)
    get_guild_settings(gid)
    if not patch:
        return
    allowed = {
        "match_channel_id",
        "digest_channel_id",
        "alert_channel_id",
        "roles_enabled",
        "locale",
    }
    fields: list[str] = []
    values: list[Any] = []
    for key, value in patch.items():
        if key not in allowed:
            continue
        fields.append(f"{key} = ?")
        values.append(value)
    if not fields:
        return
    fields.append("updated_at = datetime('now')")
    values.append(gid)
    with closing(connect()) as conn, conn:
        conn.execute(
            f"UPDATE guild_settings SET {', '.join(fields)} WHERE guild_id = ?",
            values,
        )


def set_rank_role(guild_id: str | int, rank_tier: str, role_id: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO rank_roles (guild_id, rank_tier, role_id) VALUES (?, ?, ?)
            ON CONFLICT(guild_id, rank_tier) DO UPDATE SET role_id = excluded.role_id
            """,
            (str(guild_id), rank_tier, role_id),
        )


def get_rank_roles(guild_id: str | int) -> list[dict[str, Any]]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM rank_roles WHERE guild_id = ?", (str(guild_id),)
        ).fetchall()
    return [dict(r) for r in rows]


def clear_rank_roles(guild_id: str | int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM rank_roles WHERE guild_id = ?", (str(guild_id),))


def upsert_match_cache(row: dict[str, Any]) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO match_cache (
              match_id, puuid, region, map, mode, agent, kills, deaths, assists,
              acs, hs_pct, won, rr_change, played_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(match_id, puuid) DO UPDATE SET
              kills=excluded.kills, deaths=excluded.deaths, assists=excluded.assists,
              acs=excluded.acs, hs_pct=excluded.hs_pct, won=excluded.won,
              rr_change=excluded.rr_change, raw_json=excluded.raw_json
            """,
            (
                row["match_id"],
                row["puuid"],
                row.get("region"),
                row.get("map"),
                row.get("mode"),
                row.get("agent"),
                row.get("kills"),
                row.get("deaths"),
                row.get("assists"),
                row.get("acs"),
                row.get("hs_pct"),
                row.get("won"),
                row.get("rr_change"),
                row.get("played_at"),
                row.get("raw_json"),
            ),
        )


def get_cached_matches(puuid: str, limit: int = 20) -> list[dict[str, Any]]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM match_cache WHERE puuid = ? ORDER BY played_at DESC LIMIT ?",
            (puuid, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_linked_users() -> list[dict[str, Any]]:
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM users").fetchall()
    return [dict(r) for r in rows]


def get_linked_in_guild(member_ids: list[str] | list[int]) -> list[dict[str, Any]]:
    if not member_ids:
        return []
    ids = [str(m) for m in member_ids]
    placeholders = ",".join("?" for _ in ids)
    with closing(connect()) as conn:
        rows = conn.execute(
            f"SELECT * FROM users WHERE discord_id IN ({placeholders})",
            ids,
        ).fetchall()
    return [dict(r) for r in rows]


def get_status_fingerprints(region: str) -> dict[str, Any] | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT fingerprints FROM status_state WHERE region = ?",
            (region,),
        ).fetchone()
    if row is None:
        return None
    raw = row["fingerprints"]
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        # Corrupt row — treat as missing so the next poll seeds without spam alerts.
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def set_status_fingerprints(region: str, fingerprints: dict[str, Any] | None) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """
            INSERT INTO status_state (region, fingerprints, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(region) DO UPDATE SET
              fingerprints = excluded.fingerprints,
              updated_at = datetime('now')
            """,
            (region, json.dumps(fingerprints or {})),
        )
