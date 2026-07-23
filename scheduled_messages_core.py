"""Per-guild scheduled messages: one-shot datetime or cron-like HH:MM interval."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import settings_db

MODULE_NAME = "scheduled_messages"
MAX_MESSAGES = 30
MAX_CONTENT_LEN = 2000
TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
MOSCOW_TZ = timezone(timedelta(hours=3), name="MSK")


def is_valid_time(value: str) -> bool:
    return bool(TIME_RE.match(value or ""))


def _normalized(data: dict) -> dict:
    data.setdefault("enabled", False)
    data.setdefault("seq", 0)
    data.setdefault("messages", [])
    return data


def get_settings(guild_id: int) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    return {
        "enabled": bool(data["enabled"]),
        "messages": [_public(m) for m in data["messages"] if isinstance(m, dict)],
    }


def _public(m: dict) -> dict:
    return {
        "id": str(m.get("id") or ""),
        "channel_id": str(m.get("channel_id") or ""),
        "content": str(m.get("content") or ""),
        "schedule_type": m.get("schedule_type") if m.get("schedule_type") in ("once", "daily") else "once",
        "run_at": str(m.get("run_at") or ""),  # ISO UTC for once
        "daily_time": str(m.get("daily_time") or ""),  # HH:MM MSK for daily
        "enabled": bool(m.get("enabled", True)),
        "last_posted_date": str(m.get("last_posted_date") or ""),
        "posted": bool(m.get("posted", False)),
    }


def update_enabled(guild_id: int, enabled: bool) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    data["enabled"] = bool(enabled)
    settings_db.put(guild_id, MODULE_NAME, data)
    return get_settings(guild_id)


def add_message(
    guild_id: int,
    *,
    channel_id: str,
    content: str,
    schedule_type: str = "once",
    run_at: str = "",
    daily_time: str = "",
    enabled: bool = True,
) -> dict | None:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    if len(data["messages"]) >= MAX_MESSAGES:
        return None
    data["seq"] += 1
    msg = {
        "id": str(data["seq"]),
        "channel_id": channel_id,
        "content": content,
        "schedule_type": schedule_type if schedule_type in ("once", "daily") else "once",
        "run_at": run_at,
        "daily_time": daily_time,
        "enabled": bool(enabled),
        "last_posted_date": "",
        "posted": False,
    }
    data["messages"].append(msg)
    settings_db.put(guild_id, MODULE_NAME, data)
    return _public(msg)


def update_message(guild_id: int, msg_id: str, **fields) -> dict | None:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    for msg in data["messages"]:
        if str(msg.get("id")) == str(msg_id):
            for key in ("channel_id", "content", "run_at", "daily_time"):
                if key in fields:
                    msg[key] = str(fields[key])
            if "schedule_type" in fields and fields["schedule_type"] in ("once", "daily"):
                msg["schedule_type"] = fields["schedule_type"]
            if "enabled" in fields:
                msg["enabled"] = bool(fields["enabled"])
            settings_db.put(guild_id, MODULE_NAME, data)
            return _public(msg)
    return None


def delete_message(guild_id: int, msg_id: str) -> bool:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    before = len(data["messages"])
    data["messages"] = [m for m in data["messages"] if str(m.get("id")) != str(msg_id)]
    if len(data["messages"]) == before:
        return False
    settings_db.put(guild_id, MODULE_NAME, data)
    return True


def mark_posted(guild_id: int, msg_id: str, *, once: bool = False) -> None:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    today = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")
    for msg in data["messages"]:
        if str(msg.get("id")) == str(msg_id):
            msg["last_posted_date"] = today
            if once:
                msg["posted"] = True
                msg["enabled"] = False
            settings_db.put(guild_id, MODULE_NAME, data)
            return


def due_messages(guild_id: int, now: datetime | None = None) -> list[dict]:
    """Messages that should post now (caller posts then mark_posted)."""
    settings = get_settings(guild_id)
    if not settings["enabled"]:
        return []
    now = now or datetime.now(timezone.utc)
    now_msk = now.astimezone(MOSCOW_TZ)
    today = now_msk.strftime("%Y-%m-%d")
    hhmm = now_msk.strftime("%H:%M")
    due = []
    for msg in settings["messages"]:
        if not msg["enabled"] or not msg["channel_id"] or not msg["content"]:
            continue
        if msg["schedule_type"] == "once":
            if msg["posted"] or not msg["run_at"]:
                continue
            try:
                run_at = datetime.fromisoformat(msg["run_at"].replace("Z", "+00:00"))
            except ValueError:
                continue
            if run_at.tzinfo is None:
                run_at = run_at.replace(tzinfo=timezone.utc)
            if now >= run_at:
                due.append(msg)
        else:  # daily
            if not is_valid_time(msg["daily_time"]):
                continue
            if msg["last_posted_date"] == today:
                continue
            if hhmm >= msg["daily_time"]:
                due.append(msg)
    return due
