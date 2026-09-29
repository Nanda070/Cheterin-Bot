import bot.core.settings_db as settings_db
import json
import os
from datetime import datetime, timezone

LOG_FILE = "moderation_log.json"
MAX_ENTRIES = 200


def load_events(guild_id: int) -> list[dict]:
    events = settings_db.get(guild_id, "moderation_log", [])
    return list(reversed(events))

def save_events(guild_id: int, events: list[dict]) -> None:
    settings_db.put(guild_id, "moderation_log", events)

def append_event(
    guild_id: int,
    event_type: str,
    user_id: int,
    user_display: str,
    reason: str,
    moderator_id: int | None = None,
    moderator_display: str | None = None,
    extra: str = "",
) -> None:
    events = settings_db.get(guild_id, "moderation_log", [])

    events.append(
        {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": str(user_id),
            "user_display": user_display,
            "moderator_id": str(moderator_id) if moderator_id is not None else None,
            "moderator_display": moderator_display,
            "reason": reason,
            "extra": extra,
        }
    )

    if len(events) > MAX_ENTRIES:
        events = events[-MAX_ENTRIES:]

    save_events(guild_id, events)
