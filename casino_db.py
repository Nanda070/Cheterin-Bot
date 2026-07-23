"""SQLite-хранилище статистики казино (победы/поражения), per-guild."""

import os
import sqlite3
from contextlib import closing

MAIN_GUILD = int(os.getenv("GUILD_ID", "404"))


def get_db_path() -> str:
    return os.getenv("CASINO_DB_PATH", "casino.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def init():
    with closing(connect()) as conn, conn:
        cols = _table_columns(conn, "casino_stats")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE casino_stats RENAME TO casino_stats_old")
            conn.execute("""
                CREATE TABLE casino_stats (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    slots_losses INTEGER NOT NULL DEFAULT 0,
                    slots_wins INTEGER NOT NULL DEFAULT 0,
                    bj_losses INTEGER NOT NULL DEFAULT 0,
                    bj_wins INTEGER NOT NULL DEFAULT 0,
                    bj_pushes INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            conn.execute(
                """INSERT INTO casino_stats
                   (guild_id, user_id, slots_losses, slots_wins, bj_losses, bj_wins, bj_pushes)
                   SELECT ?, user_id, slots_losses, slots_wins, bj_losses, bj_wins, bj_pushes
                   FROM casino_stats_old""",
                (MAIN_GUILD,),
            )
            conn.execute("DROP TABLE casino_stats_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS casino_stats (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    slots_losses INTEGER NOT NULL DEFAULT 0,
                    slots_wins INTEGER NOT NULL DEFAULT 0,
                    bj_losses INTEGER NOT NULL DEFAULT 0,
                    bj_wins INTEGER NOT NULL DEFAULT 0,
                    bj_pushes INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)


def _ensure_row(conn: sqlite3.Connection, guild_id: int, user_id: int):
    conn.execute(
        "INSERT OR IGNORE INTO casino_stats (guild_id, user_id) VALUES (?, ?)",
        (guild_id, user_id),
    )


def record_slots(guild_id: int, user_id: int, won: bool) -> None:
    with closing(connect()) as conn, conn:
        _ensure_row(conn, guild_id, user_id)
        if won:
            conn.execute(
                "UPDATE casino_stats SET slots_wins = slots_wins + 1 WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id),
            )
        else:
            conn.execute(
                "UPDATE casino_stats SET slots_losses = slots_losses + 1 WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id),
            )


def record_bj(guild_id: int, user_id: int, result: str) -> None:
    """result: 'win', 'lose', 'push'"""
    with closing(connect()) as conn, conn:
        _ensure_row(conn, guild_id, user_id)
        if result == "win":
            conn.execute(
                "UPDATE casino_stats SET bj_wins = bj_wins + 1 WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id),
            )
        elif result == "lose":
            conn.execute(
                "UPDATE casino_stats SET bj_losses = bj_losses + 1 WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id),
            )
        elif result == "push":
            conn.execute(
                "UPDATE casino_stats SET bj_pushes = bj_pushes + 1 WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id),
            )


def get_stats(guild_id: int, user_id: int) -> dict:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM casino_stats WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
    if row:
        return dict(row)
    return {
        "guild_id": guild_id,
        "user_id": user_id,
        "slots_losses": 0, "slots_wins": 0,
        "bj_losses": 0, "bj_wins": 0, "bj_pushes": 0
    }


def leaderboard(guild_id: int, mode: str, stat_type: str, limit: int = 1000) -> list[dict]:
    """mode: 'slots', 'bj', 'total'
       stat_type: 'wins', 'losses'
    """
    order_col = ""
    if mode == "slots":
        order_col = "slots_wins" if stat_type == "wins" else "slots_losses"
    elif mode == "bj":
        order_col = "bj_wins" if stat_type == "wins" else "bj_losses"
    elif mode == "total":
        order_col = "(slots_wins + bj_wins)" if stat_type == "wins" else "(slots_losses + bj_losses)"
    else:
        raise ValueError(f"Unknown mode: {mode}")

    where_clause = f"{order_col} > 0"

    query = f"""
        SELECT *
        FROM casino_stats
        WHERE guild_id = ? AND {where_clause}
        ORDER BY {order_col} DESC
        LIMIT ?
    """
    with closing(connect()) as conn:
        rows = conn.execute(query, (guild_id, limit)).fetchall()
    return [dict(r) for r in rows]
