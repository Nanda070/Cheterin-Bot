"""Birthday calendar settings: channel + optional ping role."""

from __future__ import annotations

import bot.core.settings_db as settings_db

MODULE_NAME = "birthdays"


def get_settings(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "enabled": bool(data.get("enabled", False)),
        "channel_id": str(data.get("channel_id") or ""),
        "ping_role_id": str(data.get("ping_role_id") or ""),
        "last_announced_date": str(data.get("last_announced_date") or ""),
    }


def save_settings(
    guild_id: int,
    *,
    enabled: bool,
    channel_id: str,
    ping_role_id: str = "",
) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    data.update(
        {
            "enabled": bool(enabled),
            "channel_id": str(channel_id or ""),
            "ping_role_id": str(ping_role_id or ""),
            "last_announced_date": str(data.get("last_announced_date") or ""),
        }
    )
    settings_db.put(guild_id, MODULE_NAME, data)
    return get_settings(guild_id)


def mark_announced(guild_id: int, date_iso: str) -> None:
    data = settings_db.get(guild_id, MODULE_NAME)
    data["last_announced_date"] = date_iso
    settings_db.put(guild_id, MODULE_NAME, data)
