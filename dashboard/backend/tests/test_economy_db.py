"""Тесты economy_db: атомарные списания, переводы, топ, журнал."""

import pytest

import economy_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("ECONOMY_DB_PATH", str(tmp_path / "economy.db"))
    economy_db.init()


def test_add_and_get_balance():
    assert economy_db.get_balance(1) == 0
    assert economy_db.add(1, 100, "test") == 100
    assert economy_db.add(1, 50, "test") == 150
    assert economy_db.get_balance(1) == 150


def test_add_ignores_non_positive():
    economy_db.add(1, 100, "test")
    assert economy_db.add(1, 0, "test") == 100
    assert economy_db.add(1, -50, "test") == 100


def test_try_spend_success_and_insufficient():
    economy_db.add(1, 100, "test")
    assert economy_db.try_spend(1, 60, "buy") is True
    assert economy_db.get_balance(1) == 40
    assert economy_db.try_spend(1, 60, "buy") is False
    assert economy_db.get_balance(1) == 40  # баланс не тронут


def test_try_spend_unknown_user():
    assert economy_db.try_spend(999, 10, "buy") is False


def test_transfer_moves_amount_and_fee():
    economy_db.add(1, 100, "test")
    assert economy_db.transfer(1, 2, 50, 5) is True
    assert economy_db.get_balance(1) == 45
    assert economy_db.get_balance(2) == 50


def test_transfer_insufficient_with_fee():
    economy_db.add(1, 50, "test")
    assert economy_db.transfer(1, 2, 50, 5) is False
    assert economy_db.get_balance(1) == 50
    assert economy_db.get_balance(2) == 0


def test_set_balance_and_rank():
    economy_db.set_balance(1, 500, "admin")
    economy_db.set_balance(2, 300, "admin")
    economy_db.set_balance(3, 700, "admin")
    assert economy_db.get_balance(1) == 500
    assert economy_db.rank_of(3) == 1
    assert economy_db.rank_of(1) == 2
    assert economy_db.rank_of(2) == 3
    assert economy_db.rank_of(999) is None


def test_top_orders_and_skips_zero():
    economy_db.set_balance(1, 100, "admin")
    economy_db.set_balance(2, 0, "admin")
    economy_db.set_balance(3, 300, "admin")
    top = economy_db.top(10)
    assert [r["user_id"] for r in top] == [3, 1]


def test_history_recorded():
    economy_db.add(1, 100, "text_xp")
    economy_db.try_spend(1, 30, "shop_abc")
    history = economy_db.recent_history(1)
    assert [h["delta"] for h in history] == [-30, 100]
    assert history[0]["reason"] == "shop_abc"


def test_daily_bonus_default_when_missing():
    assert economy_db.get_daily_bonus(1) == {"streak": 0, "last_claim_date": ""}


def test_daily_bonus_roundtrip_and_update():
    economy_db.set_daily_bonus(1, 3, "2026-01-10")
    assert economy_db.get_daily_bonus(1) == {"streak": 3, "last_claim_date": "2026-01-10"}
    economy_db.set_daily_bonus(1, 4, "2026-01-11")
    assert economy_db.get_daily_bonus(1) == {"streak": 4, "last_claim_date": "2026-01-11"}


# ────────────────────────── Косметика ──────────────────────────

def test_owns_cosmetic_false_when_not_granted():
    assert economy_db.owns_cosmetic(1, "frame1") is False


def test_grant_and_own_cosmetic():
    economy_db.grant_cosmetic(1, "frame1", "frame_color", "#FF00AA", "Розовая рамка")
    assert economy_db.owns_cosmetic(1, "frame1") is True


def test_grant_cosmetic_is_idempotent():
    economy_db.grant_cosmetic(1, "frame1", "frame_color", "#FF00AA", "Розовая рамка")
    economy_db.grant_cosmetic(1, "frame1", "frame_color", "#000000", "Другой цвет")  # повторная покупка игнорится
    owned = economy_db.list_owned_cosmetics(1, "frame_color")
    assert len(owned) == 1
    assert owned[0]["value"] == "#FF00AA"  # исходное значение не перезаписано


def test_list_owned_cosmetics_filters_by_kind():
    economy_db.grant_cosmetic(1, "frame1", "frame_color", "#FF00AA", "Рамка")
    economy_db.grant_cosmetic(1, "title1", "title", "VIP", "Титул VIP")
    assert [c["item_id"] for c in economy_db.list_owned_cosmetics(1, "frame_color")] == ["frame1"]
    assert [c["item_id"] for c in economy_db.list_owned_cosmetics(1, "title")] == ["title1"]


def test_equip_roundtrip_and_clear():
    economy_db.grant_cosmetic(1, "frame1", "frame_color", "#FF00AA", "Рамка")
    assert economy_db.get_equipped(1, "frame_color") is None

    economy_db.set_equipped(1, "frame_color", "frame1")
    equipped = economy_db.get_equipped(1, "frame_color")
    assert equipped["item_id"] == "frame1"
    assert equipped["value"] == "#FF00AA"

    economy_db.clear_equipped(1, "frame_color")
    assert economy_db.get_equipped(1, "frame_color") is None


def test_set_equipped_overwrites_previous():
    economy_db.grant_cosmetic(1, "frame1", "frame_color", "#111111", "Рамка 1")
    economy_db.grant_cosmetic(1, "frame2", "frame_color", "#222222", "Рамка 2")
    economy_db.set_equipped(1, "frame_color", "frame1")
    economy_db.set_equipped(1, "frame_color", "frame2")
    assert economy_db.get_equipped(1, "frame_color")["item_id"] == "frame2"
