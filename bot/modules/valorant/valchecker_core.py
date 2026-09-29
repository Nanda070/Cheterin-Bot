"""ValChecker module settings in settings_db (dashboard source of truth)."""

from __future__ import annotations

import bot.core.settings_db as settings_db
import bot.modules.valorant.valchecker_db as valchecker_db

MODULE_NAME = "valchecker"

DEFAULT_POLL_INTERVAL_SEC = 90
POLL_INTERVAL_MIN = 30
POLL_INTERVAL_MAX = 3600


def _clamp_poll(value) -> int:
    try:
        poll = int(value)
    except (TypeError, ValueError):
        poll = DEFAULT_POLL_INTERVAL_SEC
    return max(POLL_INTERVAL_MIN, min(POLL_INTERVAL_MAX, poll))


def get_settings(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    poll = _clamp_poll(data.get("poll_interval_sec", DEFAULT_POLL_INTERVAL_SEC))
    return {
        "enabled": bool(data.get("enabled", False)),
        "match_channel_id": str(data.get("match_channel_id") or ""),
        "alert_channel_id": str(data.get("alert_channel_id") or ""),
        "poll_interval_sec": poll,
    }


def save_settings(guild_id: int, data: dict) -> dict:
    poll = _clamp_poll(data.get("poll_interval_sec", DEFAULT_POLL_INTERVAL_SEC))
    match_channel_id = str(data.get("match_channel_id") or "")
    alert_channel_id = str(data.get("alert_channel_id") or "")
    payload = {
        "enabled": bool(data.get("enabled", False)),
        "match_channel_id": match_channel_id,
        "alert_channel_id": alert_channel_id,
        "poll_interval_sec": poll,
    }
    settings_db.put(guild_id, MODULE_NAME, payload)
    # Mirror channels into valchecker_db for poller/status (settings_db is SoT).
    valchecker_db.set_guild_settings(
        guild_id,
        {
            "match_channel_id": match_channel_id or None,
            "alert_channel_id": alert_channel_id or None,
        },
    )
    return get_settings(guild_id)


def resolve_match_channel_id(guild_id: int) -> str:
    """Prefer settings_db; fall back to valchecker_db.guild_settings."""
    settings = get_settings(guild_id)
    if settings["match_channel_id"]:
        return settings["match_channel_id"]
    gs = valchecker_db.get_guild_settings(guild_id)
    return str(gs.get("match_channel_id") or "")


def resolve_alert_channel_id(guild_id: int) -> str:
    settings = get_settings(guild_id)
    if settings["alert_channel_id"]:
        return settings["alert_channel_id"]
    if settings["match_channel_id"]:
        return settings["match_channel_id"]
    gs = valchecker_db.get_guild_settings(guild_id)
    return str(gs.get("alert_channel_id") or gs.get("match_channel_id") or "")


def validate_channel_id(channel_id: str, *, required: bool) -> str | None:
    if not isinstance(channel_id, str):
        return "invalid_channel"
    if not channel_id:
        return "channel_required" if required else None
    if not channel_id.isdigit():
        return "invalid_channel"
    return None


def validate_poll_interval(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, float):
        if not value.is_integer():
            return None
        value = int(value)
    if not isinstance(value, int):
        return None
    if value < POLL_INTERVAL_MIN or value > POLL_INTERVAL_MAX:
        return None
    return value


def any_enabled_match_guild(guild_ids: list[int]) -> bool:
    """True if at least one guild has the module on and a match channel set."""
    for gid in guild_ids:
        s = get_settings(gid)
        if s["enabled"] and s["match_channel_id"]:
            return True
    return False
