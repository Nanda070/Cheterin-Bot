"""ValChecker settings / poll validation."""

from __future__ import annotations

import bot.core.settings_db as settings_db
import bot.modules.valorant.valchecker_core as core


def test_validate_poll_interval_bounds():
    assert core.validate_poll_interval(29) is None
    assert core.validate_poll_interval(30) == 30
    assert core.validate_poll_interval(3600) == 3600
    assert core.validate_poll_interval(3601) is None
    assert core.validate_poll_interval(90.0) == 90
    assert core.validate_poll_interval(90.5) is None
    assert core.validate_poll_interval(True) is None
    assert core.validate_poll_interval("90") is None


def test_clamp_poll_via_get_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    settings_db.put(1, core.MODULE_NAME, {"enabled": True, "poll_interval_sec": 10})
    s = core.get_settings(1)
    assert s["poll_interval_sec"] == core.POLL_INTERVAL_MIN

    settings_db.put(1, core.MODULE_NAME, {"enabled": True, "poll_interval_sec": 99999})
    s = core.get_settings(1)
    assert s["poll_interval_sec"] == core.POLL_INTERVAL_MAX


def test_any_enabled_match_guild(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    assert core.any_enabled_match_guild([1]) is False

    settings_db.put(
        1,
        core.MODULE_NAME,
        {"enabled": True, "match_channel_id": "", "poll_interval_sec": 90},
    )
    assert core.any_enabled_match_guild([1]) is False

    settings_db.put(
        1,
        core.MODULE_NAME,
        {"enabled": True, "match_channel_id": "123", "poll_interval_sec": 90},
    )
    assert core.any_enabled_match_guild([1]) is True
