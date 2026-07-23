"""Sticky messages: keep one message at the bottom of a channel."""

from __future__ import annotations

import settings_db

MODULE_NAME = "sticky"
MAX_STICKIES = 25
MAX_CONTENT_LEN = 2000


def _normalized(data: dict) -> dict:
    data.setdefault("enabled", False)
    data.setdefault("seq", 0)
    data.setdefault("stickies", [])
    return data


def get_settings(guild_id: int) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    return {
        "enabled": bool(data["enabled"]),
        "stickies": [
            {
                "id": str(s.get("id") or ""),
                "channel_id": str(s.get("channel_id") or ""),
                "content": str(s.get("content") or ""),
                "message_id": str(s.get("message_id") or ""),
                "enabled": bool(s.get("enabled", True)),
            }
            for s in data["stickies"]
            if isinstance(s, dict)
        ],
    }


def update_enabled(guild_id: int, enabled: bool) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    data["enabled"] = bool(enabled)
    settings_db.put(guild_id, MODULE_NAME, data)
    return get_settings(guild_id)


def upsert_sticky(
    guild_id: int,
    *,
    channel_id: str,
    content: str,
    enabled: bool = True,
    sticky_id: str | None = None,
) -> dict | None:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    if sticky_id:
        for s in data["stickies"]:
            if str(s.get("id")) == str(sticky_id):
                s["channel_id"] = channel_id
                s["content"] = content
                s["enabled"] = bool(enabled)
                settings_db.put(guild_id, MODULE_NAME, data)
                return {
                    "id": str(s["id"]),
                    "channel_id": channel_id,
                    "content": content,
                    "message_id": str(s.get("message_id") or ""),
                    "enabled": bool(enabled),
                }
        return None

    # one sticky per channel: replace if exists
    for s in data["stickies"]:
        if str(s.get("channel_id")) == str(channel_id):
            s["content"] = content
            s["enabled"] = bool(enabled)
            s["message_id"] = ""
            settings_db.put(guild_id, MODULE_NAME, data)
            return {
                "id": str(s["id"]),
                "channel_id": channel_id,
                "content": content,
                "message_id": "",
                "enabled": bool(enabled),
            }

    if len(data["stickies"]) >= MAX_STICKIES:
        return None
    data["seq"] += 1
    sticky = {
        "id": str(data["seq"]),
        "channel_id": channel_id,
        "content": content,
        "message_id": "",
        "enabled": bool(enabled),
    }
    data["stickies"].append(sticky)
    settings_db.put(guild_id, MODULE_NAME, data)
    return {
        "id": sticky["id"],
        "channel_id": channel_id,
        "content": content,
        "message_id": "",
        "enabled": bool(enabled),
    }


def set_message_id(guild_id: int, sticky_id: str, message_id: str) -> None:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    for s in data["stickies"]:
        if str(s.get("id")) == str(sticky_id):
            s["message_id"] = str(message_id)
            settings_db.put(guild_id, MODULE_NAME, data)
            return


def delete_sticky(guild_id: int, sticky_id: str) -> bool:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    before = len(data["stickies"])
    data["stickies"] = [s for s in data["stickies"] if str(s.get("id")) != str(sticky_id)]
    if len(data["stickies"]) == before:
        return False
    settings_db.put(guild_id, MODULE_NAME, data)
    return True


def sticky_for_channel(guild_id: int, channel_id: int | str) -> dict | None:
    settings = get_settings(guild_id)
    if not settings["enabled"]:
        return None
    cid = str(channel_id)
    for s in settings["stickies"]:
        if s["enabled"] and s["channel_id"] == cid and s["content"]:
            return s
    return None
