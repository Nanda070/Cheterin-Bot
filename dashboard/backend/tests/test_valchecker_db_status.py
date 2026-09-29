"""ValChecker status fingerprint edge cases."""

from __future__ import annotations

import sqlite3

import bot.modules.valorant.valchecker_db as db


def test_corrupt_fingerprints_return_none(tmp_path, monkeypatch):
    path = tmp_path / "vc.db"
    monkeypatch.setenv("VALCHECKER_DB_PATH", str(path))
    db.init()
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO status_state (region, fingerprints, updated_at) VALUES (?, ?, datetime('now'))",
            ("eu", "{not-json"),
        )
        conn.commit()
    assert db.get_status_fingerprints("eu") is None
