"""Unit tests for relations_core helpers."""

from __future__ import annotations

import relations_core as rc


def test_pair_ids_ordered():
    assert rc.pair_ids(5, 2) == (2, 5)
    assert rc.pair_ids(2, 5) == (2, 5)


def test_level_for_hp_defaults():
    assert rc.level_for_hp(0) == 1
    assert rc.level_for_hp(rc.DEFAULT_LEVEL_THRESHOLDS[0]) == 1
    assert rc.level_for_hp(rc.DEFAULT_LEVEL_THRESHOLDS[1]) == 2
    assert rc.level_for_hp(rc.DEFAULT_LEVEL_THRESHOLDS[-1]) == 11
    assert rc.level_for_hp(99999) == 11


def test_progress_to_next():
    th = rc.DEFAULT_LEVEL_THRESHOLDS
    hp = th[1]  # exactly at level 2
    level, into, need = rc.progress_to_next(hp)
    assert level == 2
    assert into == 0
    assert need == th[2] - th[1]


def test_normalize_actions_filters_junk():
    actions = rc._normalize_actions(
        [
            {"id": "hug", "emoji": "🤗", "hp_gain": 10, "cooldown_sec": 60, "enabled": True},
            {"id": "hug", "emoji": "x", "hp_gain": 1, "cooldown_sec": 1, "enabled": True},  # dup
            {"id": "", "emoji": "x"},
            "nope",
        ]
    )
    assert len(actions) == 1
    assert actions[0]["id"] == "hug"


def test_deserved_reward_roles():
    settings = {
        "reward_roles": {"2": "111", "5": "222", "11": "333"},
    }
    assert rc.deserved_reward_role_ids(settings, 1) == set()
    assert rc.deserved_reward_role_ids(settings, 2) == {111}
    assert rc.deserved_reward_role_ids(settings, 5) == {111, 222}
    assert rc.deserved_reward_role_ids(settings, 11) == {111, 222, 333}


def test_ship_score_stable_and_bounded():
    a = rc.ship_score(100, 200)
    b = rc.ship_score(200, 100)
    assert a == b
    assert 0 <= a <= 100
    assert rc.ship_label_key(95).endswith("soulmates")
    assert rc.ship_label_key(10).endswith("awkward")


def test_apply_married_bonus():
    assert rc.apply_married_bonus(10, 25) == 12
    assert rc.apply_married_bonus(10, 0) == 10
    assert rc.apply_married_bonus(8, 25) == 10


def test_days_together():
    assert rc.days_together(1_000_000.0, now=1_000_000.0 + 86400 * 3 + 10) == 3


def test_marriage_settings_defaults(tmp_path, monkeypatch):
    import settings_db

    db = tmp_path / "settings.db"
    monkeypatch.setenv("SETTINGS_DB_PATH", str(db))
    settings_db._cache.clear()
    settings_db.init()
    s = rc.get_settings(42)
    assert s["marriage_enabled"] is True
    assert s["min_level_to_marry"] == rc.DEFAULT_MIN_LEVEL_TO_MARRY
    assert s["divorce_requires_accept"] is True
    saved = rc.save_config(
        42,
        {
            **s,
            "marriage_enabled": False,
            "min_level_to_marry": 5,
            "married_hp_bonus_percent": 50,
            "allow_polygamy": True,
        },
    )
    assert saved["marriage_enabled"] is False
    assert saved["min_level_to_marry"] == 5
    assert saved["married_hp_bonus_percent"] == 50
    assert saved["allow_polygamy"] is True


def test_level_thresholds_roundtrip(tmp_path, monkeypatch):
    """save_config persists custom level_thresholds; reload from DB returns same values."""
    import settings_db

    db = tmp_path / "settings.db"
    monkeypatch.setenv("SETTINGS_DB_PATH", str(db))
    settings_db._cache.clear()
    settings_db.init()

    guild_id = 99
    custom = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    base = rc.get_settings(guild_id)
    assert base["level_thresholds"] == list(rc.DEFAULT_LEVEL_THRESHOLDS)

    saved = rc.save_config(guild_id, {**base, "level_thresholds": custom})
    assert saved["level_thresholds"] == custom

    # Simulate page refresh: clear in-memory cache, re-read from SQLite
    settings_db._cache.clear()
    reloaded = rc.get_settings(guild_id)
    assert reloaded["level_thresholds"] == custom, (
        f"Level thresholds did not persist across cache clear: "
        f"expected {custom}, got {reloaded['level_thresholds']}"
    )


def test_normalize_thresholds_rejects_non_monotonic():
    bad = [0, 50, 40, 300, 400, 500, 600, 700, 800, 900, 1000]
    result = rc._normalize_thresholds(bad)
    assert result == list(rc.DEFAULT_LEVEL_THRESHOLDS), "non-monotonic thresholds must fall back to defaults"


def test_default_level_thresholds_values():
    th = rc.DEFAULT_LEVEL_THRESHOLDS
    assert len(th) == rc.LEVEL_COUNT
    assert th[0] == 0
    assert th[1] == 1150
    assert th[-1] == 5400
    # Must be strictly increasing
    for i in range(1, len(th)):
        assert th[i] > th[i - 1], f"threshold[{i}]={th[i]} not > threshold[{i-1}]={th[i-1]}"

