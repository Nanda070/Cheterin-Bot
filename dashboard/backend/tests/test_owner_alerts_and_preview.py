from datetime import datetime, timezone

import pytest

import bot.modules.community.birthdays_core as birthdays_core
import bot.modules.utility.owner_alerts_core as owner_alerts_core
import bot.core.preview_core as preview_core
import bot.core.settings_db as settings_db
import bot.modules.community.starboard_core as starboard_core
import bot.modules.moderation.verification_core as verification_core
from dashboard.backend.tests.fakes import FakeChannel, FakeGuild, FakeRole

GUILD_ID = 108


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    owner_alerts_core._ban_events.clear()
    owner_alerts_core._module_errors.clear()


def test_owner_alerts_mass_ban_threshold():
    owner_alerts_core.save_settings(
        GUILD_ID,
        {
            "enabled": True,
            "alert_mass_ban": True,
            "mass_ban_threshold": 3,
            "mass_ban_window_sec": 60,
        },
    )
    assert owner_alerts_core.register_ban(GUILD_ID) is False
    assert owner_alerts_core.register_ban(GUILD_ID) is False
    assert owner_alerts_core.register_ban(GUILD_ID) is True


# ────────────────────────── Setup health: module checks ──────────────────────────

def test_check_module_health_flags_dead_channel():
    guild = FakeGuild(guild_id=GUILD_ID, channels=[])
    starboard_core.save_config(GUILD_ID, {"enabled": True, "channel_id": "999", "emoji": "⭐", "threshold": 3})

    issues = owner_alerts_core.check_module_health(guild)
    assert {"module": "starboard", "kind": "missing_channel", "detail": "999"} in issues


def test_check_module_health_ok_when_channel_exists():
    channel = FakeChannel(999)
    guild = FakeGuild(guild_id=GUILD_ID, channels=[channel])
    starboard_core.save_config(GUILD_ID, {"enabled": True, "channel_id": "999", "emoji": "⭐", "threshold": 3})

    issues = owner_alerts_core.check_module_health(guild)
    assert issues == []


def test_check_module_health_ignores_disabled_module():
    guild = FakeGuild(guild_id=GUILD_ID, channels=[])
    birthdays_core.save_settings(GUILD_ID, enabled=False, channel_id="999")

    issues = owner_alerts_core.check_module_health(guild)
    assert issues == []


def test_check_module_health_flags_missing_verified_role():
    guild = FakeGuild(guild_id=GUILD_ID, roles=[])
    verification_core.save_config(GUILD_ID, {"enabled": True, "verified_role_id": "555"})

    issues = owner_alerts_core.check_module_health(guild)
    assert {"module": "verification", "kind": "missing_role", "detail": "555"} in issues


def test_check_module_health_ok_when_verified_role_exists():
    role = FakeRole(555, name="Verified")
    guild = FakeGuild(guild_id=GUILD_ID, roles=[role])
    verification_core.save_config(GUILD_ID, {"enabled": True, "verified_role_id": "555"})

    issues = owner_alerts_core.check_module_health(guild)
    assert issues == []


def test_check_module_health_flags_valchecker_missing_match_channel(tmp_path, monkeypatch):
    import bot.modules.valorant.valchecker_core as valchecker_core
    import bot.modules.valorant.valchecker_db as valchecker_db

    monkeypatch.setenv("VALCHECKER_DB_PATH", str(tmp_path / "valchecker.db"))
    valchecker_db.init()
    guild = FakeGuild(guild_id=GUILD_ID, channels=[])
    valchecker_core.save_settings(
        GUILD_ID,
        {
            "enabled": True,
            "match_channel_id": "",
            "alert_channel_id": "",
            "poll_interval_sec": 90,
        },
    )

    issues = owner_alerts_core.check_module_health(guild)
    assert {
        "module": "valchecker",
        "kind": "missing_channel",
        "detail": "match_channel_id",
    } in issues


def test_check_module_health_flags_valchecker_dead_match_channel(tmp_path, monkeypatch):
    import bot.modules.valorant.valchecker_core as valchecker_core
    import bot.modules.valorant.valchecker_db as valchecker_db

    monkeypatch.setenv("VALCHECKER_DB_PATH", str(tmp_path / "valchecker.db"))
    valchecker_db.init()
    guild = FakeGuild(guild_id=GUILD_ID, channels=[])
    valchecker_core.save_settings(
        GUILD_ID,
        {
            "enabled": True,
            "match_channel_id": "777",
            "alert_channel_id": "",
            "poll_interval_sec": 90,
        },
    )

    issues = owner_alerts_core.check_module_health(guild)
    assert {"module": "valchecker", "kind": "missing_channel", "detail": "777"} in issues


# ────────────────────────── Weekly settings digest ──────────────────────────

def test_weekly_digest_settings_roundtrip():
    saved = owner_alerts_core.save_settings(
        GUILD_ID,
        {"enabled": True, "weekly_digest_enabled": True, "weekly_digest_channel_id": "444", "channel_id": "111"},
    )
    assert saved["weekly_digest_enabled"] is True
    assert saved["weekly_digest_channel_id"] == "444"
    assert owner_alerts_core.weekly_digest_channel_id(saved) == "444"


def test_weekly_digest_channel_falls_back_to_alert_channel():
    settings = owner_alerts_core.save_settings(
        GUILD_ID, {"enabled": True, "weekly_digest_enabled": True, "channel_id": "111"}
    )
    assert settings["weekly_digest_channel_id"] == ""
    assert owner_alerts_core.weekly_digest_channel_id(settings) == "111"


def test_should_post_weekly_digest_requires_monday_and_channel(monkeypatch):
    import bot.core.timezone_core as timezone_core

    owner_alerts_core.save_settings(
        GUILD_ID, {"enabled": True, "weekly_digest_enabled": True, "channel_id": "111"}
    )

    monkeypatch.setattr(
        timezone_core, "now_local", lambda guild_id: datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)  # Monday
    )
    assert owner_alerts_core.should_post_weekly_digest(GUILD_ID) is True

    monkeypatch.setattr(
        timezone_core, "now_local", lambda guild_id: datetime(2026, 8, 4, 9, 0, tzinfo=timezone.utc)  # Tuesday
    )
    assert owner_alerts_core.should_post_weekly_digest(GUILD_ID) is False


def test_should_post_weekly_digest_false_when_already_posted(monkeypatch):
    import bot.core.timezone_core as timezone_core

    owner_alerts_core.save_settings(
        GUILD_ID, {"enabled": True, "weekly_digest_enabled": True, "channel_id": "111"}
    )
    monkeypatch.setattr(
        timezone_core, "now_local", lambda guild_id: datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)  # Monday
    )
    owner_alerts_core.mark_weekly_digest_posted(GUILD_ID, "2026-W32")
    assert owner_alerts_core.should_post_weekly_digest(GUILD_ID) is False


def test_should_post_weekly_digest_false_when_disabled(monkeypatch):
    import bot.core.timezone_core as timezone_core

    owner_alerts_core.save_settings(
        GUILD_ID, {"enabled": True, "weekly_digest_enabled": False, "channel_id": "111"}
    )
    monkeypatch.setattr(
        timezone_core, "now_local", lambda guild_id: datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)
    )
    assert owner_alerts_core.should_post_weekly_digest(GUILD_ID) is False


def test_summarize_audit_actions_groups_and_sorts():
    rows = [
        {"action": "audit.action.economy_balance"},
        {"action": "audit.action.economy_balance"},
        {"action": "audit.action.wordle"},
        {"action": "audit.action.economy_balance"},
    ]
    summary = owner_alerts_core.summarize_audit_actions(rows)
    assert summary[0] == {"action": "audit.action.economy_balance", "label": "Economy balance", "count": 3}
    assert summary[1] == {"action": "audit.action.wordle", "label": "Wordle", "count": 1}


def test_summarize_audit_actions_empty():
    assert owner_alerts_core.summarize_audit_actions([]) == []


def test_prettify_action():
    assert owner_alerts_core.prettify_action("audit.action.economy_balance") == "Economy balance"
    assert owner_alerts_core.prettify_action("") == "Unknown"


def test_preview_text_and_slash():
    out = preview_core.preview_text("Hi {name} on {guild}")
    assert "User" in out["content"]
    assert "Example Server" in out["content"]
    slash = preview_core.preview_slash_help("rank", "Show rank", [{"name": "member", "required": False}])
    assert slash["usage"] == "/rank [member]"
