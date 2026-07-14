import pytest

import family_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("FAMILY_DB_PATH", str(tmp_path / "family.db"))
    family_db.init()


def test_roster_message_roundtrip():
    assert family_db.get_roster_data() is None
    family_db.save_roster_data(500, 999)
    row = family_db.get_roster_data()
    assert row["channel_id"] == 500
    assert row["message_id"] == 999
    family_db.clear_roster_data()
    assert family_db.get_roster_data() is None


def test_pending_form_roundtrip():
    assert family_db.get_pending_form(1) is None
    family_db.save_pending_form(1, "Nick", "Lvl99", "Gov", "24/7 MSK")
    data = family_db.get_pending_form(1)
    assert data == {"nickname": "Nick", "game_level": "Lvl99", "faction_pref": "Gov", "online_timezone": "24/7 MSK"}
    family_db.delete_pending_form(1)
    assert family_db.get_pending_form(1) is None


TICKET_DATA = {
    "nickname": "Nick", "game_level": "99", "faction_pref": "Gov", "online_timezone": "MSK",
    "real_name": "Ivan", "real_age": "20", "about_text": "about", "why_join": "why",
    "inviter_nickname": None,
}


def test_ticket_lifecycle():
    family_db.create_ticket_record(1, 100, TICKET_DATA)
    ticket = family_db.get_ticket_by_user(1)
    assert ticket["status"] == "open"
    assert ticket["nickname"] == "Nick"
    assert ticket["guild_id"] == 100

    family_db.update_ticket_indexes(1, mini_message_id=200, thread_id=300)
    ticket = family_db.get_ticket_by_user(1)
    assert ticket["mini_message_id"] == 200
    assert ticket["thread_id"] == 300

    by_thread = family_db.get_ticket_by_thread(300)
    assert by_thread["user_id"] == 1

    family_db.update_ticket_status(1, "approved", handled_by=42)
    ticket = family_db.get_ticket_by_user(1)
    assert ticket["status"] == "approved"
    assert ticket["handled_by"] == 42


def test_ticket_recreate_replaces_previous_open_ticket():
    family_db.create_ticket_record(1, 100, TICKET_DATA)
    family_db.update_ticket_status(1, "denied", handled_by=42)
    family_db.create_ticket_record(1, 100, TICKET_DATA)
    ticket = family_db.get_ticket_by_user(1)
    assert ticket["status"] == "open"
    assert ticket["handled_by"] is None


def test_list_and_count_tickets_filters_by_status():
    family_db.create_ticket_record(1, 100, TICKET_DATA)
    family_db.create_ticket_record(2, 100, TICKET_DATA)
    family_db.update_ticket_status(2, "approved", handled_by=1)

    assert family_db.count_tickets() == 2
    assert family_db.count_tickets(status="open") == 1
    assert family_db.count_tickets(status="approved") == 1

    open_tickets = family_db.list_tickets(status="open")
    assert len(open_tickets) == 1
    assert open_tickets[0]["user_id"] == 1


def test_birthday_roundtrip_and_queries():
    family_db.save_birthday(1, 100, 5, 1, "05.01")
    family_db.save_birthday(2, 100, 5, 1, "05.01.1999")
    family_db.save_birthday(3, 100, 6, 2, "06.02")

    all_rows = family_db.get_all_birthdays(100)
    assert [r["user_id"] for r in all_rows] == [1, 2, 3]  # сортировка по месяцу/дню/user_id

    jan5 = family_db.get_birthdays_for_date(100, 5, 1)
    assert {r["user_id"] for r in jan5} == {1, 2}

    assert family_db.delete_birthday(1) is True
    assert family_db.delete_birthday(1) is False
    assert len(family_db.get_all_birthdays(100)) == 2


def test_birthday_message_roundtrip():
    assert family_db.get_birthday_message_data() is None
    family_db.save_birthday_message_data(500, 999)
    row = family_db.get_birthday_message_data()
    assert row["channel_id"] == 500
    family_db.clear_birthday_message_data()
    assert family_db.get_birthday_message_data() is None
