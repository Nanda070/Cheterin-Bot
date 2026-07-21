"""Тесты синглтона состояния панели голосовых комнат (voice_rooms, Фаза 2.2б).

Раньше состояние жило в плоском voice_panel.json; после миграции модуль в карте
settings_migration, поэтому load/save обязаны ходить в settings_db (иначе после
переименования файла панель «теряется» и переспамливается при рестарте).
"""

import pytest

import voice_rooms


@pytest.fixture(autouse=True)
def main_guild(monkeypatch):
    monkeypatch.setenv("GUILD_ID", "404")


def test_panel_state_defaults_empty():
    assert voice_rooms.load_panel_state() == {}


def test_panel_state_round_trip():
    voice_rooms.save_panel_state({"message_id": 123, "channel_id": 456})
    state = voice_rooms.load_panel_state()
    assert state["message_id"] == 123
    assert state["channel_id"] == 456
