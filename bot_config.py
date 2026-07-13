import json
import os

CONFIG_FILE = "config.json"

CONFIG_KEYS = [
    "LOG_CHANNEL_ID",
    "SPAM_EXCEPTION_CHANNELS",
    "TEMPBAN_CHANNEL_ID",
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


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get(key: str, default=None):
    return load_config().get(key, default)


def migrate_from_env_if_needed() -> None:
    if os.path.exists(CONFIG_FILE):
        return

    data = {}
    for key in CONFIG_KEYS:
        if key in LIST_KEYS:
            raw = os.getenv(key, "")
            data[key] = [v.strip() for v in raw.split(",") if v.strip()]
        else:
            data[key] = os.getenv(key, "")
    save_config(data)
