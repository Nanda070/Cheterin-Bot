import pytest

import settings_db
import xp_core


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_level_formula_monotonic():
    assert xp_core.total_xp_for_level(0) == 0
    assert xp_core.total_xp_for_level(1) == 100
    assert xp_core.total_xp_for_level(2) == 100 + 155
    prev = -1
    for level in (0, 1, 5, 10, 50, 100):
        total = xp_core.total_xp_for_level(level)
        assert total > prev
        prev = total


def test_level_from_xp_roundtrip():
    for level in (0, 1, 3, 10, 42):
        total = xp_core.total_xp_for_level(level)
        assert xp_core.level_from_xp(total) == level
        assert xp_core.level_from_xp(total - 1 if total else 0) == max(0, level - 1)


def test_level_progress():
    level, into, step = xp_core.level_progress(150)
    assert level == 1
    assert into == 50
    assert step == xp_core.xp_for_level_step(1)


def test_roll_text_xp_respects_multiplier():
    assert xp_core.roll_text_xp(0) == 0
    for _ in range(20):
        value = xp_core.roll_text_xp(100)
        assert xp_core.TEXT_XP_MIN <= value <= xp_core.TEXT_XP_MAX
        doubled = xp_core.roll_text_xp(200)
        assert doubled >= xp_core.TEXT_XP_MIN * 2 - 1


def test_voice_xp_requires_two_active():
    assert xp_core.voice_xp_per_minute(1, 5, 100) == 0
    assert xp_core.voice_xp_per_minute(2, 5, 100) > 0
    # Накопительный: больше активных — больше XP
    assert xp_core.voice_xp_per_minute(3, 5, 100) > xp_core.voice_xp_per_minute(2, 5, 100)
    # Кап участников ограничивает фарм
    assert xp_core.voice_xp_per_minute(10, 5, 100) == xp_core.voice_xp_per_minute(5, 5, 100)


def test_voice_xp_juniper_formula_exact():
    # база × активные × множитель/100: 6 × 3 × 1.0 = 18
    assert xp_core.voice_xp_per_minute(3, 5, 100, base_per_minute=6) == 18
    assert xp_core.voice_xp_per_minute(3, 5, 200, base_per_minute=6) == 36


def test_voice_xp_configurable_base():
    assert xp_core.voice_xp_per_minute(2, 5, 100, base_per_minute=10) == 20
    assert xp_core.voice_xp_per_minute(2, 5, 100, base_per_minute=1) == 2


def test_voice_xp_member_multiplier():
    base = xp_core.voice_xp_per_minute(2, 5, 100, base_per_minute=6)
    assert xp_core.voice_xp_per_minute(2, 5, 100, base_per_minute=6, member_multiplier=200) == base * 2
    assert xp_core.voice_xp_per_minute(2, 5, 100, base_per_minute=6, member_multiplier=0) == 0


def test_voice_member_multiplier_lookup():
    scope = {"member_multipliers": {"42": 150}}
    assert xp_core.voice_member_multiplier(scope, 42) == 150
    assert xp_core.voice_member_multiplier(scope, 99) == 100
    assert xp_core.voice_member_multiplier({}, 42) == 100


def test_get_settings_voice_new_fields_defaults():
    settings = xp_core.get_settings(404)
    assert settings["voice"]["base_per_minute"] == xp_core.VOICE_XP_PER_ACTIVE_MINUTE
    assert settings["voice"]["member_multipliers"] == {}


def test_deserved_roles():
    settings = {
        "level_rewards": [
            {"level": 5, "role_ids": ["100"]},
            {"level": 15, "role_ids": ["200"]},
        ],
        "voice_rewards": [
            {"minutes": 60, "role_ids": ["300"]},
        ],
    }
    assert xp_core.deserved_level_roles(settings, 4) == set()
    assert xp_core.deserved_level_roles(settings, 5) == {"100"}
    assert xp_core.deserved_level_roles(settings, 20) == {"100", "200"}
    assert xp_core.deserved_voice_roles(settings, 59 * 60) == set()
    assert xp_core.deserved_voice_roles(settings, 60 * 60) == {"300"}
    assert xp_core.all_reward_role_ids(settings) == {"100", "200", "300"}


def test_render_announce():
    text = xp_core.render_announce(
        "Поздравляю {{member}}! Уровень {{member.rank.level}}. +{{roles_added}}",
        "@user", 10, ["Homie"], [],
    )
    assert "@user" in text
    assert "10" in text
    assert "Homie" in text


def test_format_voice_time():
    assert xp_core.format_voice_time(0) == "0 мин."
    assert "нед." in xp_core.format_voice_time(2 * 7 * 24 * 3600)
    assert "ч." in xp_core.format_voice_time(3 * 3600)


def test_settings_defaults():
    settings = xp_core.get_settings(404)
    assert settings["enabled"] is False  # выключено по умолчанию
    assert settings["text"]["multiplier"] == 100
    assert settings["voice"]["multiplier"] == 100
    assert settings["level_rewards"] == []
    assert settings["voice_rewards"] == []
