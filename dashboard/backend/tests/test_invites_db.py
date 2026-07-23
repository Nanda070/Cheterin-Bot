import pytest

import invites_db

GUILD_ID = 103


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("INVITES_DB_PATH", str(tmp_path / "invites.db"))
    invites_db.init()


def test_snapshot_and_stats():
    invites_db.upsert_snapshot(GUILD_ID, "abc", 10, 2)
    invites_db.record_join(GUILD_ID, 20, 10, "abc")
    invites_db.record_join(GUILD_ID, 21, 10, "abc")
    invites_db.record_join(GUILD_ID, 22, 11, "xyz")

    snap = invites_db.get_snapshot(GUILD_ID)
    assert snap["abc"]["uses"] == 2
    stats = {r["inviter_id"]: r["joins"] for r in invites_db.inviter_stats(GUILD_ID)}
    assert stats[10] == 2
    assert stats[11] == 1
