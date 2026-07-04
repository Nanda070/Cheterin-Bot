import json
import os
from datetime import datetime, timezone

LOG_FILE = "moderation_log.json"
MAX_ENTRIES = 200


def load_events() -> list[dict]:
    """Returns stored events newest-first."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            events = json.load(f)
        except json.JSONDecodeError:
            return []
    return list(reversed(events))


def append_event(
    event_type: str,
    user_id: int,
    user_display: str,
    reason: str,
    moderator_id: int | None = None,
    moderator_display: str | None = None,
    extra: str = "",
) -> None:
    events = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                events = json.load(f)
            except json.JSONDecodeError:
                events = []

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

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
