import pytest

import owner_alerts_core
import preview_core
import settings_db

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


def test_preview_text_and_slash():
    out = preview_core.preview_text("Hi {name} on {guild}")
    assert "User" in out["content"]
    assert "Example Server" in out["content"]
    slash = preview_core.preview_slash_help("rank", "Show rank", [{"name": "member", "required": False}])
    assert slash["usage"] == "/rank [member]"
