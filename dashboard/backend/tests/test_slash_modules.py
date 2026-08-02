"""Tests for per-guild slash module filtering."""

from __future__ import annotations

import slash_modules as sm


def test_disabled_roots_only_when_explicitly_off(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    import settings_db
    import relations_core

    settings_db._cache.clear()
    settings_db.init()

    assert sm.disabled_root_names(7) == set()

    relations_core.save_config(
        7, {**relations_core.get_settings(7), "enabled": False}
    )
    assert sm.disabled_root_names(7) == {"relations"}

    relations_core.save_config(
        7, {**relations_core.get_settings(7), "enabled": True}
    )
    assert sm.disabled_root_names(7) == set()
