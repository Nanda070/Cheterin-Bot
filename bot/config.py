import os

import bot.core.settings_db as settings_db

MODULE_NAME = "bot_config"

CONFIG_KEYS = [
    "LOG_CHANNEL_ID",
    "SPAM_EXCEPTION_CHANNELS",
    "TEMPBAN_CHANNEL_ID",
    "TEMPBAN_LOG_CHANNEL_ID",
    "SPAM_LOG_CHANNEL_ID",
    "SPAM_LOG_ROLE_ID",
    "WELCOME_CHANNEL_ID",
    "INVITE_LOG_CHANNEL_ID",
    "ANNOUNCEMENTS_CHANNEL_ID",
    "RULES_CHANNEL_ID",
    "ROLES_CHANNEL_ID",
    "SEARCH_PLAYERS_CHANNEL_ID",
    "CTD_ROLE_ID",
    "CTD_CHANNEL_ID",
    "BUTTON_CREATE_ALLOWED_ROLES",
    "BUTTON_WEBHOOK_URL",
    "BUTTON_WEBHOOK_USERNAME",
    "BUTTON_WEBHOOK_AVATAR_URL",
    "SERVER_INVITE_LINK",
    "VOICE_LOBBY_CHANNEL_ID",
    "VOICE_PANEL_CHANNEL_ID",
    "VOICE_LOG_CHANNEL_ID",
    "VOICE_PANEL_THUMB_URL",
    "SUPPLY_ROLE_ID",
    "SUPPLY_VOICE_CHANNEL_ID",
    "SUPPLY_LOG_CHANNEL_ID",
    "SUPPLY_REMINDER_MINUTES",
]

LIST_KEYS = {"SPAM_EXCEPTION_CHANNELS", "BUTTON_CREATE_ALLOWED_ROLES"}


def load_config(guild_id: int) -> dict:
    return settings_db.get(guild_id, MODULE_NAME)


def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get(guild_id: int, key: str, default=None):
    return load_config(guild_id).get(key, default)


def resolve_server_invite_link(guild_id: int) -> str:
    """Invite link for tempban DM and other modules (no hardcoded fallback)."""
    return str(get(guild_id, "SERVER_INVITE_LINK") or "").strip()


def migrate_from_env_if_needed(guild_id: int) -> None:
    if settings_db.has(guild_id, MODULE_NAME):
        return

    data = {}
    for key in CONFIG_KEYS:
        if key in LIST_KEYS:
            raw = os.getenv(key, "")
            data[key] = [v.strip() for v in raw.split(",") if v.strip()]
        else:
            data[key] = os.getenv(key, "")
    save_config(guild_id, data)
