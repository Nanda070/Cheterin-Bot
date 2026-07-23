"""Invite tracker settings (welcome mention, channel)."""

from __future__ import annotations

import settings_db

MODULE_NAME = "invites"


def get_settings(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "enabled": bool(data.get("enabled", False)),
        "welcome_mention": bool(data.get("welcome_mention", False)),
        "log_channel_id": str(data.get("log_channel_id") or ""),
    }


def save_settings(guild_id: int, *, enabled: bool, welcome_mention: bool, log_channel_id: str) -> dict:
    settings_db.put(
        guild_id,
        MODULE_NAME,
        {
            "enabled": bool(enabled),
            "welcome_mention": bool(welcome_mention),
            "log_channel_id": str(log_channel_id or ""),
        },
    )
    return get_settings(guild_id)
