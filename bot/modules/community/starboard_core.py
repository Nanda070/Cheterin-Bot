"""Starboard settings and pure helpers (threshold / emoji / channel checks)."""

from __future__ import annotations

import re

import bot.core.settings_db as settings_db

MODULE_NAME = "starboard"

DEFAULT_EMOJI = "⭐"
DEFAULT_THRESHOLD = 3
THRESHOLD_MIN = 1
THRESHOLD_MAX = 100
MAX_EMOJI_LEN = 64

_CUSTOM_EMOJI_RE = re.compile(r"^<a?:(\w+):(\d+)>$")


def get_settings(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "enabled": bool(data.get("enabled", False)),
        "channel_id": str(data.get("channel_id") or ""),
        "emoji": str(data.get("emoji") or DEFAULT_EMOJI),
        "threshold": int(data.get("threshold", DEFAULT_THRESHOLD)),
        "self_star": bool(data.get("self_star", False)),
        "ignore_nsfw": bool(data.get("ignore_nsfw", False)),
    }


def save_config(guild_id: int, data: dict) -> dict:
    settings_db.put(guild_id, MODULE_NAME, {
        "enabled": bool(data.get("enabled", False)),
        "channel_id": str(data.get("channel_id") or ""),
        "emoji": str(data.get("emoji") or DEFAULT_EMOJI),
        "threshold": int(data.get("threshold", DEFAULT_THRESHOLD)),
        "self_star": bool(data.get("self_star", False)),
        "ignore_nsfw": bool(data.get("ignore_nsfw", False)),
    })
    return get_settings(guild_id)


def validate_channel_id(channel_id: str, *, required: bool) -> str | None:
    """Return error code, or None if valid."""
    if not isinstance(channel_id, str):
        return "invalid_channel"
    if not channel_id:
        return "channel_required" if required else None
    if not channel_id.isdigit():
        return "invalid_channel"
    return None


def validate_threshold(value) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool):
        return None
    if not THRESHOLD_MIN <= value <= THRESHOLD_MAX:
        return None
    return value


def validate_emoji(value: str) -> str | None:
    if not isinstance(value, str):
        return None
    emoji = value.strip()
    if not emoji or len(emoji) > MAX_EMOJI_LEN:
        return None
    return emoji


def emoji_matches(configured: str, payload_emoji) -> bool:
    """Compare configured emoji string with a discord PartialEmoji / str.

    Unicode: compare str(emoji) / .name carefully.
    Custom: accept <:name:id>, <a:name:id>, or bare id match.
    """
    configured = (configured or "").strip()
    if not configured:
        return False

    emoji_str = str(payload_emoji)
    if emoji_str == configured:
        return True

    custom = _CUSTOM_EMOJI_RE.match(configured)
    emoji_id = getattr(payload_emoji, "id", None)
    emoji_name = getattr(payload_emoji, "name", None)

    if custom:
        conf_name, conf_id = custom.group(1), custom.group(2)
        if emoji_id is not None and str(emoji_id) == conf_id:
            return True
        # Sometimes str(PartialEmoji) is name:id without brackets
        if emoji_str == f"{conf_name}:{conf_id}":
            return True
        return False

    # Unicode / name-only
    if emoji_id is None and emoji_name is not None:
        return emoji_name == configured
    return emoji_str == configured


def count_meets_threshold(count: int, threshold: int) -> bool:
    return count >= threshold


def should_include_reactor(
    *,
    reactor_id: int,
    author_id: int,
    reactor_is_bot: bool,
    self_star: bool,
) -> bool:
    if reactor_is_bot:
        return False
    if not self_star and reactor_id == author_id:
        return False
    return True
