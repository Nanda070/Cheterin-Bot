import pytest

import birthdays_db

GUILD_ID = 105


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("BIRTHDAYS_DB_PATH", str(tmp_path / "birthdays.db"))
    birthdays_db.init()


def test_set_list_for_date():
    assert birthdays_db.is_valid_mm_dd("07-23")
    assert not birthdays_db.is_valid_mm_dd("13-01")
    birthdays_db.set_birthday(GUILD_ID, 1, "07-23")
    birthdays_db.set_birthday(GUILD_ID, 2, "01-01")
    assert [r["user_id"] for r in birthdays_db.for_date(GUILD_ID, "07-23")] == [1]
    assert birthdays_db.delete_birthday(GUILD_ID, 1) is True
