from datetime import datetime, timedelta, timezone

import pytest

import bot.modules.community.scheduled_messages_core as scheduled_messages_core
import bot.core.settings_db as settings_db

GUILD_ID = 102


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_daily_due_and_mark():
    scheduled_messages_core.update_enabled(GUILD_ID, True)
    scheduled_messages_core.add_message(
        GUILD_ID,
        channel_id="1",
        content="hello",
        schedule_type="daily",
        daily_time="00:00",
    )
    now = datetime.now(timezone.utc)
    due = scheduled_messages_core.due_messages(GUILD_ID, now=now)
    assert len(due) == 1
    scheduled_messages_core.mark_posted(GUILD_ID, due[0]["id"])
    assert scheduled_messages_core.due_messages(GUILD_ID, now=now) == []


def test_once_not_due_before_run_at():
    scheduled_messages_core.update_enabled(GUILD_ID, True)
    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    scheduled_messages_core.add_message(
        GUILD_ID,
        channel_id="1",
        content="later",
        schedule_type="once",
        run_at=future,
    )
    assert scheduled_messages_core.due_messages(GUILD_ID) == []
