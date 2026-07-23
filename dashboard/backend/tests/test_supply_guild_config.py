import bot_config
import settings_db
from supply import _config_int, get_reminder_minutes


def test_supply_config_is_per_guild(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setenv("GUILD_ID", "999")  # must not leak into lookups
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()

    bot_config.save_config(1, {
        "SUPPLY_ROLE_ID": "111",
        "SUPPLY_VOICE_CHANNEL_ID": "222",
        "SUPPLY_LOG_CHANNEL_ID": "333",
        "SUPPLY_REMINDER_MINUTES": "5",
    })
    bot_config.save_config(2, {
        "SUPPLY_ROLE_ID": "444",
        "SUPPLY_VOICE_CHANNEL_ID": "555",
        "SUPPLY_LOG_CHANNEL_ID": "666",
        "SUPPLY_REMINDER_MINUTES": "15",
    })

    assert _config_int(1, "SUPPLY_ROLE_ID") == 111
    assert _config_int(2, "SUPPLY_ROLE_ID") == 444
    assert get_reminder_minutes(1) == 5
    assert get_reminder_minutes(2) == 15
    assert _config_int(3, "SUPPLY_ROLE_ID") == 0
    assert get_reminder_minutes(3) == 10  # default when unset
