"""Тесты ядра экономики: курс от XP, комиссии, валидация ставок, хук award_for_xp."""

import pytest

import economy_core
import economy_db
import language_core
import settings_db

GUILD_ID = 404


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("ECONOMY_DB_PATH", str(tmp_path / "economy.db"))
    economy_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_settings_defaults():
    settings = economy_core.get_settings(GUILD_ID)
    assert settings["enabled"] is False
    assert settings["currency_name"] == "монеты"
    assert settings["text_rate_percent"] == 50
    assert settings["transfer_enabled"] is True
    assert settings["roulette_bets_enabled"] is True
    assert settings["shop_items"] == []


def test_settings_defaults_respect_guild_language():
    language_core.set_language(GUILD_ID, "en")
    settings = economy_core.get_settings(GUILD_ID)
    assert settings["currency_name"] == "coins"


def test_settings_custom_currency_name_preserved():
    economy_core.save_config(GUILD_ID, {"currency_name": "кредиты"})
    assert economy_core.get_settings(GUILD_ID)["currency_name"] == "кредиты"


def test_coins_from_xp():
    assert economy_core.coins_from_xp(10, 50) == 5
    assert economy_core.coins_from_xp(10, 100) == 10
    assert economy_core.coins_from_xp(3, 50) == 1  # округление вниз
    assert economy_core.coins_from_xp(0, 100) == 0
    assert economy_core.coins_from_xp(10, 0) == 0
    assert economy_core.coins_from_xp(-5, 100) == 0


def test_award_for_xp_disabled_gives_nothing():
    assert economy_core.award_for_xp(GUILD_ID, 1, 100, "text") == 0
    assert economy_db.get_balance(GUILD_ID, 1) == 0


def test_award_for_xp_uses_kind_rate():
    economy_core.save_config(GUILD_ID, {"enabled": True, "text_rate_percent": 100, "voice_rate_percent": 10})
    assert economy_core.award_for_xp(GUILD_ID, 1, 10, "text") == 10
    assert economy_core.award_for_xp(GUILD_ID, 1, 10, "voice") == 1
    assert economy_db.get_balance(GUILD_ID, 1) == 11


def test_transfer_fee_rounds_up():
    assert economy_core.transfer_fee(100, 5) == 5
    assert economy_core.transfer_fee(50, 1) == 1  # 0.5 -> вверх
    assert economy_core.transfer_fee(100, 0) == 0


def test_bet_error_cases():
    economy_core.save_config(GUILD_ID, {"enabled": True, "roulette_max_bet": 100})
    settings = economy_core.get_settings(GUILD_ID)
    assert economy_core.bet_error(0, 1000, settings) is not None
    assert "Максимальная" in economy_core.bet_error(101, 1000, settings)
    assert "Недостаточно" in economy_core.bet_error(50, 10, settings)
    assert economy_core.bet_error(50, 100, settings) is None

    economy_core.save_config(GUILD_ID, {"enabled": True, "roulette_bets_enabled": False})
    settings = economy_core.get_settings(GUILD_ID)
    assert "отключены" in economy_core.bet_error(10, 1000, settings)


def test_bet_error_unlimited_when_max_zero():
    economy_core.save_config(GUILD_ID, {"enabled": True, "roulette_max_bet": 0})
    settings = economy_core.get_settings(GUILD_ID)
    assert economy_core.bet_error(999999, 1000000, settings) is None


def test_find_shop_item():
    economy_core.save_config(GUILD_ID, {
        "enabled": True,
        "shop_items": [{"id": "abc", "role_id": "5", "price": 100, "name": "VIP"}],
    })
    settings = economy_core.get_settings(GUILD_ID)
    assert economy_core.find_shop_item(settings, "abc")["role_id"] == "5"
    assert economy_core.find_shop_item(settings, "nope") is None


def test_format_amount():
    economy_core.save_config(GUILD_ID, {"enabled": True, "currency_emoji": "💎"})
    settings = economy_core.get_settings(GUILD_ID)
    assert economy_core.format_amount(42, settings) == "42 💎"


# ────────────────────────── /daily ──────────────────────────

def test_daily_bonus_defaults():
    settings = economy_core.get_settings(GUILD_ID)
    assert settings["daily_bonus_enabled"] is True
    assert settings["daily_base_amount"] == 50
    assert settings["daily_growth_per_day"] == 25
    assert settings["daily_max_streak_days"] == 7


def test_daily_bonus_amount_grows_linearly():
    settings = economy_core.get_settings(GUILD_ID)
    assert economy_core.daily_bonus_amount(1, settings) == 50
    assert economy_core.daily_bonus_amount(4, settings) == 125
    assert economy_core.daily_bonus_amount(7, settings) == 200


def test_daily_bonus_amount_plateaus_after_max_days():
    settings = economy_core.get_settings(GUILD_ID)
    assert economy_core.daily_bonus_amount(7, settings) == economy_core.daily_bonus_amount(30, settings)


def test_claim_daily_bonus_first_time():
    result = economy_core.claim_daily_bonus(GUILD_ID, 1, today="2026-01-10")
    assert result == {"claimed": True, "already_claimed": False, "streak": 1, "amount": 50, "balance": 50}


def test_claim_daily_bonus_same_day_rejected():
    economy_core.claim_daily_bonus(GUILD_ID, 1, today="2026-01-10")
    result = economy_core.claim_daily_bonus(GUILD_ID, 1, today="2026-01-10")
    assert result["already_claimed"] is True
    assert result["claimed"] is False
    assert result["amount"] == 0
    assert result["streak"] == 1  # стрик не потерян, просто не растёт повторно


def test_claim_daily_bonus_consecutive_day_extends_streak():
    economy_core.claim_daily_bonus(GUILD_ID, 1, today="2026-01-10")
    result = economy_core.claim_daily_bonus(GUILD_ID, 1, today="2026-01-11")
    assert result["streak"] == 2
    assert result["amount"] == 75  # 50 + 25*(2-1)
    assert result["balance"] == 125


def test_claim_daily_bonus_gap_resets_streak():
    economy_core.claim_daily_bonus(GUILD_ID, 1, today="2026-01-10")
    result = economy_core.claim_daily_bonus(GUILD_ID, 1, today="2026-01-13")
    assert result["streak"] == 1
    assert result["amount"] == 50


def test_claim_daily_bonus_uses_real_date_by_default(monkeypatch):
    monkeypatch.setattr(economy_core, "today_msk_date", lambda *_a, **_k: "2026-02-01")
    result = economy_core.claim_daily_bonus(GUILD_ID, 1)
    assert result["claimed"] is True

    result_again = economy_core.claim_daily_bonus(GUILD_ID, 1)
    assert result_again["already_claimed"] is True
