import json
import os

import pytest

import bot.modules.community.events as events


@pytest.fixture(autouse=True)
def isolated_events_file(tmp_path, monkeypatch):
    monkeypatch.setattr(events, "EVENTS_FILE", str(tmp_path / "events_data.json"))


@pytest.mark.asyncio
async def test_load_events_returns_empty_events_dict_when_file_missing():
    data = events.load_events(1)
    assert data == {"events": {}}


@pytest.mark.asyncio
async def test_save_then_load_roundtrips():
    events.save_events(1, {"events": {"123": {"title": "Test"}}})
    data = events.load_events(1)
    assert data == {"events": {"123": {"title": "Test"}}}


@pytest.mark.asyncio
async def test_load_events_reads_fresh_after_external_write():
    events.load_events(1)  # first read, populates any cache that might exist
    import bot.core.settings_db as settings_db
    settings_db.put(1, "events", {"events": {"999": {"title": "Written externally"}}})
    data = events.load_events(1)
    assert data == {"events": {"999": {"title": "Written externally"}}}
