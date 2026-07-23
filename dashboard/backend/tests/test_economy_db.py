"""Тесты economy_db: атомарные списания, переводы, топ, журнал, per-guild изоляция."""

import sqlite3
from contextlib import closing

import pytest

import economy_db

GUILD_ID = 1
OTHER = 777
MAIN = 404  # миграция легаси → мейн-сервер (как в stats_db)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("ECONOMY_DB_PATH", str(tmp_path / "economy.db"))
    economy_db.init()


def test_add_and_get_balance():
    assert economy_db.get_balance(GUILD_ID, 1) == 0
    assert economy_db.add(GUILD_ID, 1, 100, "test") == 100
    assert economy_db.add(GUILD_ID, 1, 50, "test") == 150
    assert economy_db.get_balance(GUILD_ID, 1) == 150


def test_add_ignores_non_positive():
    economy_db.add(GUILD_ID, 1, 100, "test")
    assert economy_db.add(GUILD_ID, 1, 0, "test") == 100
    assert economy_db.add(GUILD_ID, 1, -50, "test") == 100


def test_try_spend_success_and_insufficient():
    economy_db.add(GUILD_ID, 1, 100, "test")
    assert economy_db.try_spend(GUILD_ID, 1, 60, "buy") is True
    assert economy_db.get_balance(GUILD_ID, 1) == 40
    assert economy_db.try_spend(GUILD_ID, 1, 60, "buy") is False
    assert economy_db.get_balance(GUILD_ID, 1) == 40  # баланс не тронут


def test_try_spend_unknown_user():
    assert economy_db.try_spend(GUILD_ID, 999, 10, "buy") is False


def test_transfer_moves_amount_and_fee():
    economy_db.add(GUILD_ID, 1, 100, "test")
    assert economy_db.transfer(GUILD_ID, 1, 2, 50, 5) is True
    assert economy_db.get_balance(GUILD_ID, 1) == 45
    assert economy_db.get_balance(GUILD_ID, 2) == 50


def test_transfer_insufficient_with_fee():
    economy_db.add(GUILD_ID, 1, 50, "test")
    assert economy_db.transfer(GUILD_ID, 1, 2, 50, 5) is False
    assert economy_db.get_balance(GUILD_ID, 1) == 50
    assert economy_db.get_balance(GUILD_ID, 2) == 0


def test_set_balance_and_rank():
    economy_db.set_balance(GUILD_ID, 1, 500, "admin")
    economy_db.set_balance(GUILD_ID, 2, 300, "admin")
    economy_db.set_balance(GUILD_ID, 3, 700, "admin")
    assert economy_db.get_balance(GUILD_ID, 1) == 500
    assert economy_db.rank_of(GUILD_ID, 3) == 1
    assert economy_db.rank_of(GUILD_ID, 1) == 2
    assert economy_db.rank_of(GUILD_ID, 2) == 3
    assert economy_db.rank_of(GUILD_ID, 999) is None


def test_top_orders_and_skips_zero():
    economy_db.set_balance(GUILD_ID, 1, 100, "admin")
    economy_db.set_balance(GUILD_ID, 2, 0, "admin")
    economy_db.set_balance(GUILD_ID, 3, 300, "admin")
    top = economy_db.top(GUILD_ID, 10)
    assert [r["user_id"] for r in top] == [3, 1]


def test_balances_isolated_per_guild():
    economy_db.add(GUILD_ID, 1, 100, "test")
    economy_db.add(OTHER, 1, 50, "test")
    assert economy_db.get_balance(GUILD_ID, 1) == 100
    assert economy_db.get_balance(OTHER, 1) == 50
    assert economy_db.try_spend(GUILD_ID, 1, 40, "buy") is True
    assert economy_db.get_balance(GUILD_ID, 1) == 60
    assert economy_db.get_balance(OTHER, 1) == 50


def test_history_recorded():
    economy_db.add(GUILD_ID, 1, 100, "text_xp")
    economy_db.try_spend(GUILD_ID, 1, 30, "shop_abc")
    history = economy_db.recent_history(GUILD_ID, 1)
    assert [h["delta"] for h in history] == [-30, 100]
    assert history[0]["reason"] == "shop_abc"


def test_weekly_report_aggregates_earned_spent_net():
    economy_db.add(GUILD_ID, 1, 100, "earn")
    economy_db.try_spend(GUILD_ID, 1, 30, "spend")
    economy_db.add(GUILD_ID, 2, 50, "earn")
    economy_db.add(OTHER, 1, 999, "other_guild")  # чужой сервер

    report = {r["user_id"]: r for r in economy_db.weekly_report(GUILD_ID, days=7)}
    assert report[1]["earned"] == 100 and report[1]["spent"] == 30 and report[1]["net"] == 70
    assert report[2]["earned"] == 50 and report[2]["spent"] == 0 and report[2]["net"] == 50
    assert 999 not in report


def test_daily_bonus_default_when_missing():
    assert economy_db.get_daily_bonus(GUILD_ID, 1) == {"streak": 0, "last_claim_date": ""}


def test_daily_bonus_roundtrip_and_update():
    economy_db.set_daily_bonus(GUILD_ID, 1, 3, "2026-01-10")
    assert economy_db.get_daily_bonus(GUILD_ID, 1) == {"streak": 3, "last_claim_date": "2026-01-10"}
    economy_db.set_daily_bonus(GUILD_ID, 1, 4, "2026-01-11")
    assert economy_db.get_daily_bonus(GUILD_ID, 1) == {"streak": 4, "last_claim_date": "2026-01-11"}


# ────────────────────────── Косметика ──────────────────────────

def test_owns_cosmetic_false_when_not_granted():
    assert economy_db.owns_cosmetic(GUILD_ID, 1, "frame1") is False


def test_grant_and_own_cosmetic():
    economy_db.grant_cosmetic(GUILD_ID, 1, "frame1", "frame_color", "#FF00AA", "Розовая рамка")
    assert economy_db.owns_cosmetic(GUILD_ID, 1, "frame1") is True


def test_grant_cosmetic_is_idempotent():
    economy_db.grant_cosmetic(GUILD_ID, 1, "frame1", "frame_color", "#FF00AA", "Розовая рамка")
    economy_db.grant_cosmetic(GUILD_ID, 1, "frame1", "frame_color", "#000000", "Другой цвет")  # повторная покупка игнорится
    owned = economy_db.list_owned_cosmetics(GUILD_ID, 1, "frame_color")
    assert len(owned) == 1
    assert owned[0]["value"] == "#FF00AA"  # исходное значение не перезаписано


def test_list_owned_cosmetics_filters_by_kind():
    economy_db.grant_cosmetic(GUILD_ID, 1, "frame1", "frame_color", "#FF00AA", "Рамка")
    economy_db.grant_cosmetic(GUILD_ID, 1, "title1", "title", "VIP", "Титул VIP")
    assert [c["item_id"] for c in economy_db.list_owned_cosmetics(GUILD_ID, 1, "frame_color")] == ["frame1"]
    assert [c["item_id"] for c in economy_db.list_owned_cosmetics(GUILD_ID, 1, "title")] == ["title1"]


def test_equip_roundtrip_and_clear():
    economy_db.grant_cosmetic(GUILD_ID, 1, "frame1", "frame_color", "#FF00AA", "Рамка")
    assert economy_db.get_equipped(GUILD_ID, 1, "frame_color") is None

    economy_db.set_equipped(GUILD_ID, 1, "frame_color", "frame1")
    equipped = economy_db.get_equipped(GUILD_ID, 1, "frame_color")
    assert equipped["item_id"] == "frame1"
    assert equipped["value"] == "#FF00AA"

    economy_db.clear_equipped(GUILD_ID, 1, "frame_color")
    assert economy_db.get_equipped(GUILD_ID, 1, "frame_color") is None


def test_set_equipped_overwrites_previous():
    economy_db.grant_cosmetic(GUILD_ID, 1, "frame1", "frame_color", "#111111", "Рамка 1")
    economy_db.grant_cosmetic(GUILD_ID, 1, "frame2", "frame_color", "#222222", "Рамка 2")
    economy_db.set_equipped(GUILD_ID, 1, "frame_color", "frame1")
    economy_db.set_equipped(GUILD_ID, 1, "frame_color", "frame2")
    assert economy_db.get_equipped(GUILD_ID, 1, "frame_color")["item_id"] == "frame2"


def test_cosmetics_isolated_per_guild():
    economy_db.grant_cosmetic(GUILD_ID, 1, "frame1", "frame_color", "#FF00AA", "Рамка")
    economy_db.set_equipped(GUILD_ID, 1, "frame_color", "frame1")
    assert economy_db.owns_cosmetic(OTHER, 1, "frame1") is False
    assert economy_db.get_equipped(OTHER, 1, "frame_color") is None


# ────────────────────────── Миграция легаси-схемы ──────────────────────────

def _create_legacy_schema(path: str) -> None:
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("CREATE TABLE balances (user_id INTEGER PRIMARY KEY, balance INTEGER NOT NULL DEFAULT 0)")
        conn.execute("INSERT INTO balances VALUES (10, 500)")

        conn.execute("""
            CREATE TABLE history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                delta INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "INSERT INTO history (user_id, delta, reason, created_at) VALUES (?, ?, ?, ?)",
            (10, 100, "legacy", "2026-01-01T00:00:00+00:00"),
        )

        conn.execute("""
            CREATE TABLE daily_bonus (
                user_id INTEGER PRIMARY KEY,
                streak INTEGER NOT NULL DEFAULT 0,
                last_claim_date TEXT NOT NULL DEFAULT ''
            )
        """)
        conn.execute("INSERT INTO daily_bonus VALUES (10, 3, '2026-01-10')")

        conn.execute("""
            CREATE TABLE owned_cosmetics (
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                value TEXT NOT NULL,
                name TEXT NOT NULL,
                PRIMARY KEY (user_id, item_id)
            )
        """)
        conn.execute("INSERT INTO owned_cosmetics VALUES (10, 'frame1', 'frame_color', '#FF00AA', 'Рамка')")

        conn.execute("""
            CREATE TABLE equipped_cosmetics (
                user_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                item_id TEXT NOT NULL,
                PRIMARY KEY (user_id, kind)
            )
        """)
        conn.execute("INSERT INTO equipped_cosmetics VALUES (10, 'frame_color', 'frame1')")


def test_migration_assigns_legacy_rows_to_main_guild(tmp_path, monkeypatch):
    db_path = str(tmp_path / "legacy_economy.db")
    monkeypatch.setenv("ECONOMY_DB_PATH", db_path)
    _create_legacy_schema(db_path)

    economy_db.init()

    assert economy_db.get_balance(MAIN, 10) == 500
    assert economy_db.get_balance(GUILD_ID, 10) == 0
    assert economy_db.get_daily_bonus(MAIN, 10) == {"streak": 3, "last_claim_date": "2026-01-10"}
    assert economy_db.owns_cosmetic(MAIN, 10, "frame1") is True
    assert economy_db.get_equipped(MAIN, 10, "frame_color")["item_id"] == "frame1"
    history = economy_db.recent_history(MAIN, 10)
    assert len(history) == 1 and history[0]["delta"] == 100


def test_migration_is_idempotent(tmp_path, monkeypatch):
    db_path = str(tmp_path / "legacy_economy2.db")
    monkeypatch.setenv("ECONOMY_DB_PATH", db_path)
    _create_legacy_schema(db_path)

    economy_db.init()
    economy_db.init()

    assert economy_db.get_balance(MAIN, 10) == 500
    assert len(economy_db.recent_history(MAIN, 10)) == 1

    # композитный PK: тот же user_id на другом сервере
    economy_db.add(OTHER, 10, 77, "new")
    assert economy_db.get_balance(MAIN, 10) == 500
    assert economy_db.get_balance(OTHER, 10) == 77
