import pytest

import automod_core
import settings_db

GUILD_ID = 404


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


# ────────────────────────── Настройки ──────────────────────────

def test_get_settings_defaults():
    settings = automod_core.get_settings(GUILD_ID)
    assert settings["enabled"] is False
    assert set(settings["filters"].keys()) == set(automod_core.FILTER_KEYS)
    assert settings["escalation"] == []
    assert settings["manual_warn_duration_minutes"] == automod_core.DEFAULT_MANUAL_WARN_DURATION_MINUTES

    links = settings["filters"]["links"]
    assert links["enabled"] is False
    assert links["punishment"] == "warn"
    assert links["whitelist_domains"] == []
    assert links["label"] == "Ссылки"


def test_update_module_enabled():
    settings = automod_core.update_module_enabled(GUILD_ID, True)
    assert settings["enabled"] is True


def test_update_filter():
    updated = automod_core.update_filter(GUILD_ID, "bad_words", {"enabled": True, "words": ["плохое"]})
    assert updated["enabled"] is True
    assert updated["words"] == ["плохое"]
    # прочие фильтры не затронуты
    assert automod_core.get_settings(GUILD_ID)["filters"]["links"]["enabled"] is False


def test_update_filter_unknown_key_returns_none():
    assert automod_core.update_filter(GUILD_ID, "unknown", {"enabled": True}) is None


def test_update_manual_warn_duration():
    settings = automod_core.update_manual_warn_duration(GUILD_ID, 1440)
    assert settings["manual_warn_duration_minutes"] == 1440


# ────────────────────────── Эскалация ──────────────────────────

def test_escalation_crud():
    rule = automod_core.add_escalation_rule(GUILD_ID, 3, "mute", 1440)
    assert rule["id"] == "1"
    assert rule["count"] == 3

    updated = automod_core.update_escalation_rule(GUILD_ID, rule["id"], {"action": "kick"})
    assert updated["action"] == "kick"
    assert automod_core.update_escalation_rule(GUILD_ID, "999", {"action": "ban"}) is None

    assert automod_core.delete_escalation_rule(GUILD_ID, rule["id"]) is True
    assert automod_core.delete_escalation_rule(GUILD_ID, rule["id"]) is False


def test_find_escalation_rule_exact_match():
    automod_core.add_escalation_rule(GUILD_ID, 3, "mute", 1440)
    automod_core.add_escalation_rule(GUILD_ID, 5, "kick", 0)

    assert automod_core.find_escalation_rule(GUILD_ID, 3)["action"] == "mute"
    assert automod_core.find_escalation_rule(GUILD_ID, 5)["action"] == "kick"
    assert automod_core.find_escalation_rule(GUILD_ID, 4) is None


# ────────────────────────── Шаблон уведомления ──────────────────────────

def test_render_notify_template():
    text = automod_core.render_notify_template("Привет {{member}}! Причина: {{reason}}.", "@user", "флуд")
    assert text == "Привет @user! Причина: флуд."


# ────────────────────────── Детекторы ──────────────────────────

def test_detect_links():
    assert automod_core.detect_links("зайди на http://evil.example", []) is True
    assert automod_core.detect_links("зайди на http://good.example", ["good.example"]) is False
    assert automod_core.detect_links("просто текст без ссылок", []) is False


def test_detect_invites():
    own = "https://discord.gg/ownserver"
    assert automod_core.detect_invites("го в discord.gg/other", True, own) is True
    assert automod_core.detect_invites("го в discord.gg/ownserver", True, own) is False
    assert automod_core.detect_invites("го в discord.gg/ownserver", False, own) is True
    assert automod_core.detect_invites("просто текст", True, own) is False


def test_detect_scam_links():
    assert automod_core.detect_scam_links("зайди на discord-nitro-free.ru", ["discord-nitro"]) is True
    assert automod_core.detect_scam_links("обычная ссылка", ["discord-nitro"]) is False
    assert automod_core.detect_scam_links("что угодно", []) is False


def test_detect_bad_words():
    assert automod_core.detect_bad_words("ты плохой человек", ["плохой"]) is True
    assert automod_core.detect_bad_words("нормальный текст", ["плохой"]) is False
    assert automod_core.detect_bad_words("текст", []) is False


def test_detect_repeated_text():
    assert automod_core.detect_repeated_text(["x", "x", "x"], "x", 4) is True
    assert automod_core.detect_repeated_text(["x", "x"], "x", 4) is False
    assert automod_core.detect_repeated_text([], "x", 0) is False


def test_detect_caps_lock():
    assert automod_core.detect_caps_lock("HELLO WORLD LOUD TEXT", 70, 10) is True
    assert automod_core.detect_caps_lock("hello world quiet text", 70, 10) is False
    assert automod_core.detect_caps_lock("HI", 70, 10) is False  # короче min_length


def test_detect_emoji_spam():
    assert automod_core.detect_emoji_spam("<:a:1><:b:2><:c:3>", 3) is True
    assert automod_core.detect_emoji_spam("<:a:1>", 3) is False
    assert automod_core.detect_emoji_spam("текст", 0) is False


def test_detect_mentions():
    assert automod_core.detect_mentions(5, 5) is True
    assert automod_core.detect_mentions(4, 5) is False
    assert automod_core.detect_mentions(10, 0) is False


def test_detect_zalgo():
    zalgo_text = "Z̀́̂̃̄o"
    assert automod_core.detect_zalgo(zalgo_text, 5) is True
    assert automod_core.detect_zalgo("обычный текст", 5) is False
