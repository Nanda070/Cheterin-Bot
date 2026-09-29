"""Quote-from-reply: settings + trigger gate helpers."""

from __future__ import annotations

import re

import bot.core.settings_db as settings_db

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


_USER_MENTION_RE = re.compile(r"<@!?(\d+)>")
_ROLE_MENTION_RE = re.compile(r"<@&(\d+)>")
_CHANNEL_MENTION_RE = re.compile(r"<#(\d+)>")
_CUSTOM_EMOJI_RE = re.compile(r"<a?:([A-Za-z0-9_]+):\d+>")
# Common Unicode emoji / symbol blocks that PIL default fonts render as tofu.
_UNICODE_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # Misc Symbols and Pictographs + Supplemental
    "\U0001FA00-\U0001FAFF"  # Extended-A
    "\U00002600-\U000026FF"  # Misc symbols
    "\U00002700-\U000027BF"  # Dingbats
    "\U0000FE0F"  # variation selector
    "\U0000200D"  # ZWJ
    "]+",
    flags=re.UNICODE,
)
_DASH_TRANSLATE = str.maketrans(
    {
        "\u2014": "-",  # em dash —
        "\u2013": "-",  # en dash –
        "\u2212": "-",  # minus −
        "\u2012": "-",  # figure dash
        "\u2015": "-",  # horizontal bar
    }
)


def format_quote_plaintext(
    text: str,
    *,
    user_names: dict[int, str] | None = None,
    role_names: dict[int, str] | None = None,
    channel_names: dict[int, str] | None = None,
) -> str:
    """Turn Discord markup into PNG-safe plain text (mentions, emoji, dashes)."""
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    users = user_names or {}
    roles = role_names or {}
    channels = channel_names or {}

    def _user(m: re.Match[str]) -> str:
        uid = int(m.group(1))
        name = users.get(uid)
        return f"@{name}" if name else "@user"

    def _role(m: re.Match[str]) -> str:
        rid = int(m.group(1))
        name = roles.get(rid)
        return f"@{name}" if name else "@role"

    def _channel(m: re.Match[str]) -> str:
        cid = int(m.group(1))
        name = channels.get(cid)
        return f"#{name}" if name else "#channel"

    out = _USER_MENTION_RE.sub(_user, raw)
    out = _ROLE_MENTION_RE.sub(_role, out)
    out = _CHANNEL_MENTION_RE.sub(_channel, out)
    out = _CUSTOM_EMOJI_RE.sub(r":\1:", out)
    out = _UNICODE_EMOJI_RE.sub("", out)
    out = out.translate(_DASH_TRANSLATE)
    # Collapse leftover spaces from removed emoji, keep newlines.
    out = re.sub(r"[^\S\n]{2,}", " ", out)
    out = re.sub(r" *\n *", "\n", out)
    return out.strip()


def should_quote(
    *,
    guild_id: int | None,
    author_is_bot: bool,
    bot_user_id: int | None,
    mentions: list,
    content: str,
    has_reference: bool,
    referenced_text: str | None = None,
    referenced_author_is_bot: bool = False,
    settings: dict | None = None,
) -> bool:
    """Pure gate for mention+reply quote trigger (unit-testable).

    Quotes only when a human replies to a *user* message while mentioning the bot.
    Blocks:
    - bot authors (author_is_bot)
    - non-replies (no reference)
    - replies to bot messages (referenced_author_is_bot) — Discord auto-pings the
      bot on reply, so mention alone must not create a quote of the bot itself
      or of a reply-to-bot trigger.
    """
    if guild_id is None or author_is_bot:
        return False
    if not has_reference:
        return False
    # Reply-to-bot (or quoting any bot-authored message): never quote.
    if referenced_author_is_bot:
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
