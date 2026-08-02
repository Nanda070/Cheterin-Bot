"""Per-guild bot profile (nick / avatar / banner) settings."""

from __future__ import annotations

import base64
import re

import settings_db

MODULE_NAME = "bot_profile"

# Discord image upload limit for member profile assets (~8 MiB raw).
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_NICK_LEN = 32

_DATA_URI_RE = re.compile(
    r"^data:image/(png|jpeg|jpg|gif|webp);base64,([A-Za-z0-9+/=\s]+)$",
    re.IGNORECASE,
)


def get_settings(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "nick": str(data.get("nick") or ""),
        "has_custom_avatar": bool(data.get("has_custom_avatar", False)),
        "has_custom_banner": bool(data.get("has_custom_banner", False)),
    }


def save_settings(
    guild_id: int,
    *,
    nick: str | None = None,
    has_custom_avatar: bool | None = None,
    has_custom_banner: bool | None = None,
) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    if nick is not None:
        data["nick"] = nick
    if has_custom_avatar is not None:
        data["has_custom_avatar"] = bool(has_custom_avatar)
    if has_custom_banner is not None:
        data["has_custom_banner"] = bool(has_custom_banner)
    settings_db.put(guild_id, MODULE_NAME, data)
    return get_settings(guild_id)


def normalize_nick(value: str | None) -> str | None:
    """Return nick string, empty string to clear, or None if omitted."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("invalid_nick")
    nick = value.strip()
    if len(nick) > MAX_NICK_LEN:
        raise ValueError("nick_too_long")
    return nick


def parse_image_data_uri(value: str | None) -> tuple[str | None, bytes | None]:
    """Parse avatar/banner field.

    Returns:
      (payload_for_api, raw_bytes)
      - payload_for_api is the data URI string, or None to clear, or MISSING sentinel via not calling
      - If value is omitted conceptually, caller should not pass the field.

    Raises ValueError with error code string on bad input.
    """
    if value is None:
        return None, None
    if not isinstance(value, str):
        raise ValueError("invalid_image")
    match = _DATA_URI_RE.match(value.strip())
    if not match:
        raise ValueError("invalid_image")
    raw_b64 = re.sub(r"\s+", "", match.group(2))
    try:
        raw = base64.b64decode(raw_b64, validate=False)
    except Exception as exc:
        raise ValueError("invalid_image") from exc
    if len(raw) == 0:
        raise ValueError("invalid_image")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("image_too_large")
    # Discord API expects the data URI form in PATCH /guilds/{id}/members/@me
    mime = match.group(1).lower()
    if mime == "jpg":
        mime = "jpeg"
    payload = f"data:image/{mime};base64,{raw_b64}"
    return payload, raw
