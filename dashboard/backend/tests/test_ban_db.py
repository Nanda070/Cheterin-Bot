import pytest

import bot.modules.moderation.ban_db as ban_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("BAN_DB_PATH", str(tmp_path / "moderation_bans.db"))
    ban_db.init()


def test_add_and_get_by_user():
    row_id = ban_db.add(guild_id=1, user_id=20, unban_at_ts=1000)
    row = ban_db.get_by_user(1, 20)
    assert row["id"] == row_id
    assert row["guild_id"] == 1
    assert row["user_id"] == 20
    assert row["unban_at_ts"] == 1000


def test_get_by_user_unknown_returns_none():
    assert ban_db.get_by_user(1, 999) is None


def test_add_replaces_existing_row_for_same_user():
    first_id = ban_db.add(guild_id=1, user_id=20, unban_at_ts=1000)
    second_id = ban_db.add(guild_id=1, user_id=20, unban_at_ts=2000)
    row = ban_db.get_by_user(1, 20)
    assert row["id"] == second_id
    assert row["unban_at_ts"] == 2000
    assert len(ban_db.list_all()) == 1
    assert first_id != second_id


def test_remove():
    row_id = ban_db.add(guild_id=1, user_id=20, unban_at_ts=1000)
    ban_db.remove(row_id)
    assert ban_db.get_by_user(1, 20) is None


def test_list_all_ordered_by_unban_at():
    ban_db.add(guild_id=1, user_id=20, unban_at_ts=3000)
    ban_db.add(guild_id=1, user_id=21, unban_at_ts=1000)
    ban_db.add(guild_id=1, user_id=22, unban_at_ts=2000)

    rows = ban_db.list_all()
    assert [r["user_id"] for r in rows] == [21, 22, 20]


def test_different_guilds_are_independent():
    ban_db.add(guild_id=1, user_id=20, unban_at_ts=1000)
    ban_db.add(guild_id=2, user_id=20, unban_at_ts=2000)
    assert ban_db.get_by_user(1, 20)["unban_at_ts"] == 1000
    assert ban_db.get_by_user(2, 20)["unban_at_ts"] == 2000
    assert len(ban_db.list_all()) == 2
