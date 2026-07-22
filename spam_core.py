"""Anti-spam detection thresholds (per-guild, dashboard-configurable)."""

import settings_db

MODULE_NAME = "spam"

DEFAULT_LIMIT_WITH_ATTACHMENTS = 3
DEFAULT_LIMIT_WITHOUT_ATTACHMENTS = 5
DEFAULT_TIME_WINDOW_SEC = 60

LIMIT_MIN = 1
LIMIT_MAX = 50
TIME_WINDOW_MIN = 10
TIME_WINDOW_MAX = 600


def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "limit_with_attachments": int(
            data.get("limit_with_attachments", DEFAULT_LIMIT_WITH_ATTACHMENTS)
        ),
        "limit_without_attachments": int(
            data.get("limit_without_attachments", DEFAULT_LIMIT_WITHOUT_ATTACHMENTS)
        ),
        "time_window_sec": int(data.get("time_window_sec", DEFAULT_TIME_WINDOW_SEC)),
    }


def message_limit(settings: dict, has_attachments: bool) -> int:
    if has_attachments:
        return int(settings.get("limit_with_attachments", DEFAULT_LIMIT_WITH_ATTACHMENTS))
    return int(settings.get("limit_without_attachments", DEFAULT_LIMIT_WITHOUT_ATTACHMENTS))
