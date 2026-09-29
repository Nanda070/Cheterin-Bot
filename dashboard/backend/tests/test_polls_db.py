from datetime import datetime, timedelta, timezone

import pytest

import bot.modules.community.polls_db as polls_db

GUILD_ID = 106


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("POLLS_DB_PATH", str(tmp_path / "polls.db"))
    polls_db.init()


def test_create_vote_tallies_end():
    ends = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    poll = polls_db.create(GUILD_ID, 50, "Q?", ["A", "B"], ends, created_by=1)
    assert polls_db.vote(poll["id"], 10, 0) is True
    assert polls_db.vote(poll["id"], 11, 1) is True
    assert polls_db.vote(poll["id"], 10, 1) is True  # change vote
    assert polls_db.tallies(poll["id"]) == [0, 2]
    polls_db.mark_ended(poll["id"])
    assert polls_db.get(poll["id"])["ended"] is True
    assert polls_db.vote(poll["id"], 12, 0) is False
