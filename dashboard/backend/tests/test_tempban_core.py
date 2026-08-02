"""Tempban / honeypot settings: action modes, counter, templates."""

import tempban_core
import settings_db

GUILD_ID = 9202


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_default_action_softban(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    settings = tempban_core.get_settings(GUILD_ID)
    assert settings["action"] == "softban"
    assert settings["ban_count"] == 0
    assert tempban_core.should_process_trap(settings) is True


def test_action_modes(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    tempban_core.save_settings(
        GUILD_ID,
        {
            "action": "disabled",
            "dm_enabled": True,
            "dm_message": "",
            "log_enabled": True,
            "log_message": "",
            "unban_reason": "",
            "warning_message": "",
            "warning_thumbnail_url": "",
        },
    )
    settings = tempban_core.get_settings(GUILD_ID)
    assert settings["action"] == "disabled"
    assert tempban_core.should_process_trap(settings) is False

    tempban_core.save_settings(
        GUILD_ID,
        {**settings, "action": "ban", "dm_enabled": True, "log_enabled": True},
    )
    settings = tempban_core.get_settings(GUILD_ID)
    assert settings["action"] == "ban"
    assert tempban_core.should_process_trap(settings) is True
    assert tempban_core.ban_reason_for_api("ban") == tempban_core.PERMANENT_BAN_REASON_MARKER
    assert tempban_core.ban_reason_for_api("softban") == tempban_core.BAN_REASON_MARKER
    assert tempban_core.is_tempban_ban_reason(tempban_core.PERMANENT_BAN_REASON_MARKER) is False
    assert tempban_core.is_tempban_ban_reason(tempban_core.BAN_REASON_MARKER) is True


def test_increment_ban_count(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    assert tempban_core.increment_ban_count(GUILD_ID) == 1
    assert tempban_core.increment_ban_count(GUILD_ID) == 2
    assert tempban_core.get_settings(GUILD_ID)["ban_count"] == 2


def test_render_template_double_brace():
    vars_ = {"action": "permanent ban", "guild": "Test", "ban_count": "3"}
    assert tempban_core.render_template("Do not: {action}", vars_) == "Do not: permanent ban"
    assert tempban_core.render_template("Do not: {{action}}", vars_) == "Do not: permanent ban"
    assert tempban_core.render_template("Do not: {{action:text}}", vars_) == "Do not: permanent ban"
    assert tempban_core.render_template("{guild} / {ban_count}", vars_) == "Test / 3"


def test_save_preserves_ban_count_and_message_id(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    tempban_core.increment_ban_count(GUILD_ID)
    tempban_core.set_warning_message_id(GUILD_ID, 555)
    tempban_core.save_settings(
        GUILD_ID,
        {
            "action": "softban",
            "dm_enabled": False,
            "dm_message": "hi",
            "log_enabled": True,
            "log_message": "",
            "unban_reason": "",
            "warning_message": "Warn",
            "warning_thumbnail_url": "",
            "ban_count": 1,
            "warning_message_id": "555",
        },
    )
    settings = tempban_core.get_settings(GUILD_ID)
    assert settings["ban_count"] == 1
    assert settings["warning_message_id"] == "555"
    assert settings["dm_enabled"] is False
