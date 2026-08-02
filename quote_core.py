"""Quote-from-reply: settings + trigger gate helpers."""

from __future__ import annotations

import settings_db

MODULE_NAME = "quote"

DEFAULTS = {
    "enabled": True,
    "delete_trigger": False,
    "min_length": 0,
}


def _load_raw(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return data if isinstance(data, dict) else {}


def get_settings(guild_id: int) -> dict:
    raw = _load_raw(guild_id)
    min_length = raw.get("min_length", DEFAULTS["min_length"])
    try:
        min_length = int(min_length)
    except (TypeError, ValueError):
        min_length = DEFAULTS["min_length"]
    min_length = max(0, min(2000, min_length))
    return {
        "enabled": bool(raw.get("enabled", DEFAULTS["enabled"])),
        "delete_trigger": bool(raw.get("delete_trigger", DEFAULTS["delete_trigger"])),
        "min_length": min_length,
    }


def save_settings(guild_id: int, data: dict) -> dict:
    payload = {
        "enabled": bool(data.get("enabled", DEFAULTS["enabled"])),
        "delete_trigger": bool(data.get("delete_trigger", DEFAULTS["delete_trigger"])),
        "min_length": data.get("min_length", DEFAULTS["min_length"]),
    }
    try:
        payload["min_length"] = max(0, min(2000, int(payload["min_length"])))
    except (TypeError, ValueError):
        payload["min_length"] = DEFAULTS["min_length"]
    settings_db.put(guild_id, MODULE_NAME, payload)
    return get_settings(guild_id)


def bot_is_mentioned(*, bot_user_id: int | None, mentions: list, content: str) -> bool:
    """True if the bot is in mentions or content contains <@id> / <@!id>."""
    if bot_user_id is None:
        return False
    for user in mentions or []:
        uid = getattr(user, "id", None)
        if uid == bot_user_id:
            return True
    content = content or ""
    return f"<@{bot_user_id}>" in content or f"<@!{bot_user_id}>" in content


def should_quote(
    *,
    guild_id: int | None,
    author_is_bot: bool,
    bot_user_id: int | None,
    mentions: list,
    content: str,
    has_reference: bool,
    referenced_text: str | None = None,
    settings: dict | None = None,
) -> bool:
    """Pure gate for mention+reply quote trigger (unit-testable)."""
    if guild_id is None or author_is_bot:
        return False
    if not has_reference:
        return False
    cfg = settings if settings is not None else get_settings(guild_id)
    if not cfg.get("enabled", True):
        return False
    if not bot_is_mentioned(bot_user_id=bot_user_id, mentions=mentions, content=content):
        return False
    min_length = int(cfg.get("min_length") or 0)
    if min_length > 0:
        text = (referenced_text or "").strip()
        if len(text) < min_length:
            return False
    return True
