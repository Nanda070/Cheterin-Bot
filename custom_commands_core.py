"""Per-guild custom commands / auto-replies (exact or contains match)."""

from __future__ import annotations

import settings_db

MODULE_NAME = "custom_commands"
MAX_COMMANDS = 50
MAX_TRIGGER_LEN = 100
MAX_REPLY_LEN = 2000


def _normalized(data: dict) -> dict:
    data.setdefault("enabled", False)
    data.setdefault("seq", 0)
    data.setdefault("commands", [])
    return data


def get_settings(guild_id: int) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    return {
        "enabled": bool(data["enabled"]),
        "commands": [
            {
                "id": str(c.get("id") or ""),
                "trigger": str(c.get("trigger") or ""),
                "match": c.get("match") if c.get("match") in ("exact", "contains") else "exact",
                "reply_text": str(c.get("reply_text") or ""),
                "embed": c.get("embed") if isinstance(c.get("embed"), dict) else None,
                "enabled": bool(c.get("enabled", True)),
            }
            for c in data["commands"]
            if isinstance(c, dict)
        ],
    }


def update_enabled(guild_id: int, enabled: bool) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    data["enabled"] = bool(enabled)
    settings_db.put(guild_id, MODULE_NAME, data)
    return get_settings(guild_id)


def add_command(
    guild_id: int,
    *,
    trigger: str,
    match: str = "exact",
    reply_text: str = "",
    embed: dict | None = None,
    enabled: bool = True,
) -> dict | None:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    if len(data["commands"]) >= MAX_COMMANDS:
        return None
    data["seq"] += 1
    cmd = {
        "id": str(data["seq"]),
        "trigger": trigger,
        "match": match if match in ("exact", "contains") else "exact",
        "reply_text": reply_text,
        "embed": embed,
        "enabled": bool(enabled),
    }
    data["commands"].append(cmd)
    settings_db.put(guild_id, MODULE_NAME, data)
    return cmd


def update_command(guild_id: int, cmd_id: str, **fields) -> dict | None:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    for cmd in data["commands"]:
        if str(cmd.get("id")) == str(cmd_id):
            if "trigger" in fields:
                cmd["trigger"] = str(fields["trigger"])
            if "match" in fields and fields["match"] in ("exact", "contains"):
                cmd["match"] = fields["match"]
            if "reply_text" in fields:
                cmd["reply_text"] = str(fields["reply_text"])
            if "embed" in fields:
                cmd["embed"] = fields["embed"] if isinstance(fields["embed"], dict) else None
            if "enabled" in fields:
                cmd["enabled"] = bool(fields["enabled"])
            settings_db.put(guild_id, MODULE_NAME, data)
            return cmd
    return None


def delete_command(guild_id: int, cmd_id: str) -> bool:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    before = len(data["commands"])
    data["commands"] = [c for c in data["commands"] if str(c.get("id")) != str(cmd_id)]
    if len(data["commands"]) == before:
        return False
    settings_db.put(guild_id, MODULE_NAME, data)
    return True


def match_message(guild_id: int, content: str) -> dict | None:
    """Return first matching enabled command for message content, or None."""
    settings = get_settings(guild_id)
    if not settings["enabled"] or not content:
        return None
    text = content.strip()
    lowered = text.lower()
    for cmd in settings["commands"]:
        if not cmd["enabled"] or not cmd["trigger"]:
            continue
        trigger = cmd["trigger"]
        if cmd["match"] == "exact":
            if lowered == trigger.lower():
                return cmd
        elif trigger.lower() in lowered:
            return cmd
    return None
