import sqlite3
from contextlib import closing

import casino_db


def test_legacy_migration_assigns_hardcoded_main_guild(tmp_path, monkeypatch):
    db_path = tmp_path / "casino.db"
    monkeypatch.setenv("CASINO_DB_PATH", str(db_path))
    monkeypatch.setenv("GUILD_ID", "999999")  # must not affect migration target

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
    assert casino_db.MAIN_GUILD == 404
    stats = casino_db.get_stats(404, 42)
    assert stats["slots_wins"] == 3
    assert casino_db.get_stats(999999, 42)["slots_wins"] == 0
