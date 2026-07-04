import pytest

import moderation_log


@pytest.fixture(autouse=True)
def isolated_log(tmp_path, monkeypatch):
    monkeypatch.setattr(moderation_log, "LOG_FILE", str(tmp_path / "moderation_log.json"))


def test_load_events_returns_empty_list_when_file_missing():
    assert moderation_log.load_events() == []


def test_load_events_returns_empty_list_on_corrupt_json():
    with open(moderation_log.LOG_FILE, "w", encoding="utf-8") as f:
        f.write("{not valid json")
    assert moderation_log.load_events() == []


def test_append_then_load_returns_newest_first():
    moderation_log.append_event("spam_punish", 1, "userA", "reason1")
    moderation_log.append_event("tempban", 2, "userB", "reason2")
    events = moderation_log.load_events()
    assert len(events) == 2
    assert events[0]["type"] == "tempban"
    assert events[1]["type"] == "spam_punish"


def test_append_event_stores_all_fields():
    moderation_log.append_event(
        "manual_ban", 100, "target", "spam", moderator_id=10, moderator_display="mod", extra="7 дн."
    )
    event = moderation_log.load_events()[0]
    assert event["type"] == "manual_ban"
    assert event["user_id"] == "100"
    assert event["user_display"] == "target"
    assert event["moderator_id"] == "10"
    assert event["moderator_display"] == "mod"
    assert event["reason"] == "spam"
    assert event["extra"] == "7 дн."
    assert "timestamp" in event


def test_append_event_defaults_moderator_to_none_for_automatic_events():
    moderation_log.append_event("tempban", 5, "userC", "auto reason")
    event = moderation_log.load_events()[0]
    assert event["moderator_id"] is None
    assert event["moderator_display"] is None


def test_append_event_trims_to_max_entries(monkeypatch):
    monkeypatch.setattr(moderation_log, "MAX_ENTRIES", 3)
    for i in range(5):
        moderation_log.append_event("spam_punish", i, f"user{i}", "reason")
    events = moderation_log.load_events()
    assert len(events) == 3
    assert events[0]["user_id"] == "4"
    assert events[-1]["user_id"] == "2"
