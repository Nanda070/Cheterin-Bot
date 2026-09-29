"""Per-guild timezone for schedules (daily posts, Wordle day, weekly reports, birthdays).

Default: Europe/Moscow (historical MSK behaviour). Stored in settings.db module `timezone`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import bot.core.settings_db as settings_db

MODULE = "timezone"
DEFAULT_TIMEZONE = "Europe/Moscow"

# Curated list for the dashboard select (IANA names).
SUPPORTED_TIMEZONES: tuple[str, ...] = (
    "Europe/Moscow",
    "Europe/Samara",
    "Europe/Kaliningrad",
    "Asia/Yekaterinburg",
    "Asia/Novosibirsk",
    "Asia/Vladivostok",
    "UTC",
    "Europe/London",
    "Europe/Berlin",
    "Europe/Paris",
    "Europe/Warsaw",
    "Europe/Kyiv",
    "Asia/Dubai",
    "Asia/Tashkent",
    "Asia/Almaty",
    "Asia/Bangkok",
    "Asia/Shanghai",
    "Asia/Tokyo",
    "America/New_York",
    "America/Chicago",
    "America/Los_Angeles",
)


def get_timezone(guild_id: int) -> str:
    data = settings_db.get(guild_id, MODULE, {})
    code = str(data.get("code") or DEFAULT_TIMEZONE)
    if code not in SUPPORTED_TIMEZONES:
        return DEFAULT_TIMEZONE
    return code


def set_timezone(guild_id: int, code: str) -> str:
    if code not in SUPPORTED_TIMEZONES:
        raise ValueError("unsupported_timezone")
    settings_db.put(guild_id, MODULE, {"code": code})
    return code


def get_settings(guild_id: int) -> dict:
    return {"code": get_timezone(guild_id), "supported": list(SUPPORTED_TIMEZONES)}


def get_tz(guild_id: int) -> ZoneInfo:
    code = get_timezone(guild_id)
    try:
        return ZoneInfo(code)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def now_local(guild_id: int) -> datetime:
    return datetime.now(timezone.utc).astimezone(get_tz(guild_id))


def today_local(guild_id: int) -> str:
    return now_local(guild_id).strftime("%Y-%m-%d")
