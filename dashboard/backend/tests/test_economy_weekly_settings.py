import pytest

import bot.modules.games.economy_core as economy_core
import bot.core.settings_db as settings_db

GUILD_ID = 109


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_weekly_report_settings_defaults_and_mark():
    s = economy_core.get_settings(GUILD_ID)
    assert s["weekly_report_enabled"] is False
    assert s["weekly_report_channel_id"] == ""
    economy_core.save_config(
        GUILD_ID,
        {**s, "enabled": True, "weekly_report_enabled": True, "weekly_report_channel_id": "55"},
    )
    economy_core.mark_weekly_report_posted(GUILD_ID, "2026-W30")
    assert economy_core.get_settings(GUILD_ID)["last_weekly_report_date"] == "2026-W30"
