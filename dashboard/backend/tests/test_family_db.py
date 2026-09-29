"""Тесты family_db: per-guild ростер/заявки/дни рождения + миграция старой схемы.

Фаза 2.2б MULTIGUILD_PLAN.md: «Семья» стала полноценно мультигилдовой. Старые
(одно-серверные) строки при миграции присваиваются мейн-серверу
(GUILD_ID / MAIN_GUILD_ID). Ошибочный sentinel 404 ремонтируется при init().
"""

import sqlite3
from contextlib import closing

import pytest

import bot.modules.games.family_db as family_db

G = 100
G2 = 200


def _main() -> int:
    return family_db.get_main_guild_id()


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("FAMILY_DB_PATH", str(tmp_path / "family.db"))
    monkeypatch.delenv("GUILD_ID", raising=False)
    monkeypatch.delenv("MAIN_GUILD_ID", raising=False)
    family_db.init()


TICKET_DATA = {
    "nickname": "Nick", "game_level": "99", "faction_pref": "Gov", "online_timezone": "MSK",
    "real_name": "Ivan", "real_age": "20", "about_text": "about", "why_join": "why",
    "inviter_nickname": None,
}


# ────────────────────────── Ростер ──────────────────────────

def test_roster_message_roundtrip_and_isolation():
    assert family_db.get_roster_data(G) is None
    family_db.save_roster_data(G, 500, 999)
    family_db.save_roster_data(G2, 501, 1000)

    row = family_db.get_roster_data(G)
    assert row["channel_id"] == 500 and row["message_id"] == 999
    assert family_db.get_roster_data(G2)["channel_id"] == 501

    family_db.clear_roster_data(G)
    assert family_db.get_roster_data(G) is None
    # соседний сервер не затронут
    assert family_db.get_roster_data(G2) is not None


# ────────────────────────── Черновики ──────────────────────────

def test_pending_form_roundtrip_and_isolation():
    assert family_db.get_pending_form(G, 1) is None
    family_db.save_pending_form(G, 1, "Nick", "Lvl99", "Gov", "24/7 MSK")
    data = family_db.get_pending_form(G, 1)
    assert data == {"nickname": "Nick", "game_level": "Lvl99", "faction_pref": "Gov", "online_timezone": "24/7 MSK"}
    # тот же user на другом сервере — отдельный (отсутствующий) черновик
    assert family_db.get_pending_form(G2, 1) is None

    family_db.delete_pending_form(G, 1)
    assert family_db.get_pending_form(G, 1) is None


# ────────────────────────── Заявки ──────────────────────────

def test_ticket_lifecycle():
    family_db.create_ticket_record(1, G, TICKET_DATA)
    ticket = family_db.get_ticket_by_user(G, 1)
    assert ticket["status"] == "open"
    assert ticket["nickname"] == "Nick"
    assert ticket["guild_id"] == G

    family_db.update_ticket_indexes(G, 1, mini_message_id=200, thread_id=300)
    ticket = family_db.get_ticket_by_user(G, 1)
    assert ticket["mini_message_id"] == 200
    assert ticket["thread_id"] == 300

    by_thread = family_db.get_ticket_by_thread(G, 300)
    assert by_thread["user_id"] == 1

    family_db.update_ticket_status(G, 1, "approved", handled_by=42)
    ticket = family_db.get_ticket_by_user(G, 1)
    assert ticket["status"] == "approved"
    assert ticket["handled_by"] == 42


def test_ticket_same_user_isolated_per_guild():
    family_db.create_ticket_record(1, G, TICKET_DATA)
    family_db.create_ticket_record(1, G2, {**TICKET_DATA, "nickname": "Other"})
    # композитный PK (guild_id, user_id): один user_id живёт на двух серверах
    assert family_db.get_ticket_by_user(G, 1)["nickname"] == "Nick"
    assert family_db.get_ticket_by_user(G2, 1)["nickname"] == "Other"
    family_db.update_ticket_status(G, 1, "denied", handled_by=5)
    assert family_db.get_ticket_by_user(G, 1)["status"] == "denied"
    assert family_db.get_ticket_by_user(G2, 1)["status"] == "open"


def test_ticket_recreate_replaces_previous_open_ticket():
    family_db.create_ticket_record(1, G, TICKET_DATA)
    family_db.update_ticket_status(G, 1, "denied", handled_by=42)
    family_db.create_ticket_record(1, G, TICKET_DATA)
    ticket = family_db.get_ticket_by_user(G, 1)
    assert ticket["status"] == "open"
    assert ticket["handled_by"] is None


def test_list_and_count_tickets_scoped_and_filtered():
    family_db.create_ticket_record(1, G, TICKET_DATA)
    family_db.create_ticket_record(2, G, TICKET_DATA)
    family_db.update_ticket_status(G, 2, "approved", handled_by=1)
    family_db.create_ticket_record(3, G2, TICKET_DATA)  # чужой сервер

    assert family_db.count_tickets(G) == 2
    assert family_db.count_tickets(G, status="open") == 1
    assert family_db.count_tickets(G, status="approved") == 1
    assert family_db.count_tickets(G2) == 1

    open_tickets = family_db.list_tickets(G, status="open")
    assert len(open_tickets) == 1
    assert open_tickets[0]["user_id"] == 1


# ────────────────────────── Дни рождения ──────────────────────────

def test_birthday_roundtrip_and_queries():
    family_db.save_birthday(1, G, 5, 1, "05.01")
    family_db.save_birthday(2, G, 5, 1, "05.01.1999")
    family_db.save_birthday(3, G, 6, 2, "06.02")
    family_db.save_birthday(1, G2, 9, 9, "09.09")  # тот же user на другом сервере

    all_rows = family_db.get_all_birthdays(G)
    assert [r["user_id"] for r in all_rows] == [1, 2, 3]

    jan5 = family_db.get_birthdays_for_date(G, 5, 1)
    assert {r["user_id"] for r in jan5} == {1, 2}

    assert family_db.delete_birthday(G, 1) is True
    assert family_db.delete_birthday(G, 1) is False
    assert len(family_db.get_all_birthdays(G)) == 2
    # запись того же user на другом сервере не тронута
    assert len(family_db.get_all_birthdays(G2)) == 1


def test_birthday_message_roundtrip_and_isolation():
    assert family_db.get_birthday_message_data(G) is None
    family_db.save_birthday_message_data(G, 500, 999)
    family_db.save_birthday_message_data(G2, 600, 1000)
    row = family_db.get_birthday_message_data(G)
    assert row["channel_id"] == 500
    assert family_db.get_birthday_message_data(G2)["channel_id"] == 600
    family_db.clear_birthday_message_data(G)
    assert family_db.get_birthday_message_data(G) is None
    assert family_db.get_birthday_message_data(G2) is not None


# ────────────────────────── Миграция старой (одно-серверной) схемы ──────────────────────────

def _create_legacy_schema(path: str):
    """Схема до Фазы 2.2б: синглтоны roster_msg/birthday_msg (id=1), single-PK
    pending_forms/tickets/birthdays (tickets/birthdays уже с колонкой guild_id).

    Исторически колонка guild_id в tickets/birthdays писалась sentinel'ом 404 —
    repair при init переносит их на реальный мейн.
    """
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("CREATE TABLE roster_msg (id INTEGER PRIMARY KEY CHECK (id = 1), channel_id INTEGER, message_id INTEGER)")
        conn.execute("INSERT INTO roster_msg (id, channel_id, message_id) VALUES (1, 500, 999)")

        conn.execute("CREATE TABLE pending_forms (user_id INTEGER PRIMARY KEY, nickname TEXT, game_level TEXT, faction_pref TEXT, online_timezone TEXT)")
        conn.execute("INSERT INTO pending_forms VALUES (7, 'Leg', 'L1', 'Gov', 'MSK')")

        conn.execute("""
            CREATE TABLE tickets (
                user_id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, mini_message_id INTEGER,
                thread_id INTEGER, status TEXT NOT NULL, nickname TEXT, game_level TEXT,
                faction_pref TEXT, online_timezone TEXT, real_name TEXT, real_age TEXT,
                about_text TEXT, why_join TEXT, inviter_nickname TEXT, created_at TEXT NOT NULL, handled_by INTEGER
            )
        """)
        conn.execute(
            "INSERT INTO tickets (user_id, guild_id, status, nickname, created_at) VALUES (7, 404, 'open', 'Leg', '01.01.2026 00:00 UTC')",
        )

        conn.execute("CREATE TABLE birthdays (user_id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, day INTEGER NOT NULL, month INTEGER NOT NULL, date_display TEXT NOT NULL)")
        conn.execute("INSERT INTO birthdays VALUES (7, 404, 5, 1, '05.01')")

        conn.execute("CREATE TABLE birthday_msg (id INTEGER PRIMARY KEY CHECK (id = 1), channel_id INTEGER, message_id INTEGER)")
        conn.execute("INSERT INTO birthday_msg (id, channel_id, message_id) VALUES (1, 700, 800)")


def test_migration_assigns_legacy_rows_to_main_guild(tmp_path, monkeypatch):
    db_path = str(tmp_path / "legacy_family.db")
    monkeypatch.setenv("FAMILY_DB_PATH", db_path)
    monkeypatch.setenv("GUILD_ID", "1324239354154975252")
    _create_legacy_schema(db_path)

    family_db.init()
    main = _main()

    assert family_db.get_roster_data(main)["channel_id"] == 500
    assert family_db.get_pending_form(main, 7)["nickname"] == "Leg"
    assert family_db.get_ticket_by_user(main, 7)["status"] == "open"
    assert family_db.get_all_birthdays(main)[0]["user_id"] == 7
    assert family_db.get_birthday_message_data(main)["channel_id"] == 700


def test_migration_is_idempotent(tmp_path, monkeypatch):
    db_path = str(tmp_path / "legacy_family2.db")
    monkeypatch.setenv("FAMILY_DB_PATH", db_path)
    monkeypatch.setenv("GUILD_ID", "1324239354154975252")
    _create_legacy_schema(db_path)

    family_db.init()
    family_db.init()  # повторный вызов не должен падать/дублировать
    main = _main()

    assert family_db.count_tickets(main) == 1
    assert len(family_db.get_all_birthdays(main)) == 1
    assert family_db.get_roster_data(main)["channel_id"] == 500

    # композитный PK после миграции: тот же user_id может жить на другом сервере
    family_db.create_ticket_record(7, G2, TICKET_DATA)
    assert family_db.get_ticket_by_user(main, 7)["nickname"] == "Leg"
    assert family_db.get_ticket_by_user(G2, 7)["nickname"] == "Nick"
