from datetime import datetime, timedelta, timezone

import pytest

import bot.modules.community.timed_roles_db as timed_roles_db

GUILD_ID = 104


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("TIMED_ROLES_DB_PATH", str(tmp_path / "timed_roles.db"))
    timed_roles_db.init()


def test_add_and_expired():
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    timed_roles_db.add(GUILD_ID, 1, 2, past)
    timed_roles_db.add(GUILD_ID, 1, 3, future)
    expired = timed_roles_db.expired()
    assert len(expired) == 1
    assert expired[0]["role_id"] == 2
    timed_roles_db.remove(expired[0]["id"])
    assert timed_roles_db.expired() == []
