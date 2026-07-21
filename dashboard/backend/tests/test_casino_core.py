"""Тесты ядра казино: настройки, лимиты ставок, выплаты слотов/монетки с house edge."""

import pytest

import casino_core
import settings_db


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_settings_defaults():
    settings = casino_core.get_settings(404)
    assert settings == {
        "enabled": False,
        "house_edge_percent": 5,
        "cooldown_sec": 5,
        "min_bet": 10,
        "max_bet": 5000,
        "loss_roles": [],
    }


def test_settings_roundtrip():
    casino_core.save_config(404,{"enabled": True, "house_edge_percent": 10, "min_bet": 50, "max_bet": 0})
    settings = casino_core.get_settings(404)
    assert settings["enabled"] is True
    assert settings["house_edge_percent"] == 10
    assert settings["max_bet"] == 0  # 0 — без лимита


def test_bet_error_below_min():
    settings = casino_core.get_settings(404)
    assert "Минимальная" in casino_core.bet_error(1, 1000, settings)


def test_bet_error_above_max():
    casino_core.save_config(404,{"enabled": True, "max_bet": 100})
    settings = casino_core.get_settings(404)
    assert "Максимальная" in casino_core.bet_error(200, 1000, settings)


def test_bet_error_unlimited_when_max_zero():
    casino_core.save_config(404,{"enabled": True, "max_bet": 0})
    settings = casino_core.get_settings(404)
    assert casino_core.bet_error(999999, 1000000, settings) is None


def test_bet_error_insufficient_funds():
    settings = casino_core.get_settings(404)
    assert "Недостаточно" in casino_core.bet_error(50, 10, settings)


def test_bet_error_ok():
    settings = casino_core.get_settings(404)
    assert casino_core.bet_error(50, 1000, settings) is None


def test_payout_amount_applies_edge():
    assert casino_core.payout_amount(100, 2, 5) == 190  # 200 * 0.95
    assert casino_core.payout_amount(100, 2, 0) == 200
    assert casino_core.payout_amount(100, 0, 5) == 0
    assert casino_core.payout_amount(100, 1.5, 5) == 142  # 150*0.95=142.5 -> floor


# ────────────────────────── Слоты ──────────────────────────

def test_slot_multiplier_triple_uses_table():
    assert casino_core.slot_multiplier(("💎", "💎", "💎")) == casino_core.SLOT_TRIPLE_MULTIPLIERS["💎"]
    assert casino_core.slot_multiplier(("7️⃣", "7️⃣", "7️⃣")) == 50


def test_slot_multiplier_pair():
    assert casino_core.slot_multiplier(("🍒", "🍒", "🔔")) == casino_core.SLOT_PAIR_MULTIPLIER
    assert casino_core.slot_multiplier(("🍒", "🔔", "🍒")) == casino_core.SLOT_PAIR_MULTIPLIER


def test_slot_multiplier_no_match():
    assert casino_core.slot_multiplier(("🍒", "🔔", "⭐")) == 0


def test_roll_slots_returns_known_symbols():
    reels = casino_core.roll_slots()
    assert len(reels) == 3
    assert all(r in casino_core.SLOT_SYMBOLS for r in reels)


# ────────────────────────── Монетка ──────────────────────────

def test_flip_coin_returns_valid_side():
    assert casino_core.flip_coin() in casino_core.COINFLIP_SIDES


def test_flip_coin_distribution(monkeypatch):
    monkeypatch.setattr(casino_core.random, "choice", lambda seq: seq[0])
    assert casino_core.flip_coin() == casino_core.COINFLIP_SIDES[0]
