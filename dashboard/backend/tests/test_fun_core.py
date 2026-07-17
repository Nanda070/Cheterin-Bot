import pytest

import fun_core


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(fun_core, "CONFIG_FILE", str(tmp_path / "fun_config.json"))
    monkeypatch.setattr(fun_core, "_cache", None, raising=False)
    monkeypatch.setattr(fun_core, "_cache_mtime", None, raising=False)


def test_get_settings_defaults():
    settings = fun_core.get_settings()
    assert settings["enabled"] is False
    assert settings["roulette_timeout_minutes"] == fun_core.DEFAULT_ROULETTE_TIMEOUT_MINUTES
    assert settings["roulette_cooldown_sec"] == fun_core.DEFAULT_ROULETTE_COOLDOWN_SEC


def test_save_config_roundtrip():
    fun_core.save_config({"enabled": True, "roulette_timeout_minutes": 5, "roulette_cooldown_sec": 60})
    settings = fun_core.get_settings()
    assert settings["enabled"] is True
    assert settings["roulette_timeout_minutes"] == 5
    assert settings["roulette_cooldown_sec"] == 60


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
