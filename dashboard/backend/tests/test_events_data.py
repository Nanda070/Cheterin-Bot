import json
import os

import pytest

import events


@pytest.fixture(autouse=True)
def isolated_events_file(tmp_path, monkeypatch):
    monkeypatch.setattr(events, "EVENTS_FILE", str(tmp_path / "events_data.json"))


@pytest.mark.asyncio
async def test_load_events_returns_empty_events_dict_when_file_missing():
    data = await events.load_events()
    assert data == {"events": {}}


@pytest.mark.asyncio
async def test_save_then_load_roundtrips():
    await events.save_events({"events": {"123": {"title": "Test"}}})
    data = await events.load_events()
    assert data == {"events": {"123": {"title": "Test"}}}


@pytest.mark.asyncio
async def test_load_events_reads_fresh_after_external_write():
    await events.load_events()  # first read, populates any cache that might exist
    with open(events.EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"events": {"999": {"title": "Written externally"}}}, f)
    data = await events.load_events()
    assert data == {"events": {"999": {"title": "Written externally"}}}
