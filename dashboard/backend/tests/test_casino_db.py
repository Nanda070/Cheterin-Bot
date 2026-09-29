import sqlite3
from contextlib import closing

import bot.modules.games.casino_db as casino_db


def test_legacy_migration_assigns_env_main_guild(tmp_path, monkeypatch):
    db_path = tmp_path / "casino.db"
    monkeypatch.setenv("CASINO_DB_PATH", str(db_path))
    monkeypatch.setenv("GUILD_ID", "999999")

    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute("""
            CREATE TABLE casino_stats (
                user_id INTEGER PRIMARY KEY,
                slots_losses INTEGER NOT NULL DEFAULT 0,
                slots_wins INTEGER NOT NULL DEFAULT 0,
                bj_losses INTEGER NOT NULL DEFAULT 0,
                bj_wins INTEGER NOT NULL DEFAULT 0,
                bj_pushes INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute(
            "INSERT INTO casino_stats (user_id, slots_wins) VALUES (42, 3)",
        )

    casino_db.init()
    assert casino_db.MAIN_GUILD == 999999
    stats = casino_db.get_stats(999999, 42)
    assert stats["slots_wins"] == 3
    assert casino_db.get_stats(404, 42)["slots_wins"] == 0


def test_repair_moves_misattributed_404_to_main_guild(tmp_path, monkeypatch):
    db_path = tmp_path / "casino_repair.db"
    monkeypatch.setenv("CASINO_DB_PATH", str(db_path))
    monkeypatch.setenv("GUILD_ID", "999999")

    with closing(sqlite3.connect(db_path)) as conn, conn:
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
            "INSERT INTO casino_stats (guild_id, user_id, slots_wins) VALUES (404, 42, 3)",
        )
        conn.execute(
            "INSERT INTO casino_stats (guild_id, user_id, slots_wins) VALUES (999999, 42, 2)",
        )

    casino_db.init()
    assert casino_db.get_stats(999999, 42)["slots_wins"] == 5
    assert casino_db.get_stats(404, 42)["slots_wins"] == 0
