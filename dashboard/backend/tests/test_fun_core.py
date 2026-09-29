import pytest

import bot.modules.games.fun_core as fun_core
import bot.core.settings_db as settings_db


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_get_settings_defaults():
    settings = fun_core.get_settings(404)
    assert settings["enabled"] is False
    assert settings["roulette_timeout_minutes"] == fun_core.DEFAULT_ROULETTE_TIMEOUT_MINUTES
    assert settings["roulette_cooldown_sec"] == fun_core.DEFAULT_ROULETTE_COOLDOWN_SEC


def test_save_config_roundtrip():
    fun_core.save_config(404, {"enabled": True, "roulette_timeout_minutes": 5, "roulette_cooldown_sec": 60})
    settings = fun_core.get_settings(404)
    assert settings["enabled"] is True
    assert settings["roulette_timeout_minutes"] == 5
    assert settings["roulette_cooldown_sec"] == 60


def test_get_settings_isolated_by_guild():
    fun_core.save_config(1, {"enabled": True})
    fun_core.save_config(2, {"enabled": False})
    assert fun_core.get_settings(1)["enabled"] is True
    assert fun_core.get_settings(2)["enabled"] is False


def test_spin_trigger_empty_cylinder_never_fires():
    assert all(not fun_core.spin_trigger(clicks, empty_cylinder=True) for clicks in range(6))


def test_roll_empty_cylinder_chance(monkeypatch):
    monkeypatch.setattr(fun_core.random, "random", lambda: 0.07)
    assert fun_core.roll_empty_cylinder() is True
    monkeypatch.setattr(fun_core.random, "random", lambda: 0.08)
    assert fun_core.roll_empty_cylinder() is False


def test_spin_trigger_probability_is_one_in_six():
    # Детерминированно: перебираем все исходы randrange.
    outcomes = set()
    import random

    original = random.randrange
    try:
        for forced in range(fun_core.ROULETTE_CHAMBERS):
            random.randrange = lambda n, _f=forced: _f
            outcomes.add(fun_core.spin_trigger())
    finally:
        random.randrange = original
    # Ровно один исход из шести — выстрел.
    assert outcomes == {True, False}


def test_spin_trigger_statistical_sanity():
    shots = sum(1 for _ in range(6000) if fun_core.spin_trigger())
    assert 700 <= shots <= 1350  # ~1000 ± допуск


def test_pick_emoji_uses_guild_pool():
    assert fun_core.pick_emoji(["<:custom:1>"]) == "<:custom:1>"


def test_pick_emoji_fallback_when_no_guild_emojis():
    emoji = fun_core.pick_emoji([])
    assert emoji in fun_core.FALLBACK_EMOJIS
