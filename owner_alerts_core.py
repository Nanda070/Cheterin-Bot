"""Owner alerts: notify guild owner on critical events."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
from time import time

import settings_db

MODULE_NAME = "owner_alerts"


def get_settings(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "enabled": bool(data.get("enabled", False)),
        "notify_dm": bool(data.get("notify_dm", True)),
        "channel_id": str(data.get("channel_id") or ""),
        "mass_ban_threshold": int(data.get("mass_ban_threshold", 5)),
        "mass_ban_window_sec": int(data.get("mass_ban_window_sec", 60)),
        "module_error_threshold": int(data.get("module_error_threshold", 5)),
        "alert_missing_perms": bool(data.get("alert_missing_perms", True)),
        "alert_mass_ban": bool(data.get("alert_mass_ban", True)),
        "alert_module_errors": bool(data.get("alert_module_errors", True)),
    }


def save_settings(guild_id: int, payload: dict) -> dict:
    current = get_settings(guild_id)
    current.update(
        {
            "enabled": bool(payload.get("enabled", current["enabled"])),
            "notify_dm": bool(payload.get("notify_dm", current["notify_dm"])),
            "channel_id": str(payload.get("channel_id") or ""),
            "mass_ban_threshold": max(2, min(50, int(payload.get("mass_ban_threshold", current["mass_ban_threshold"])))),
            "mass_ban_window_sec": max(10, min(600, int(payload.get("mass_ban_window_sec", current["mass_ban_window_sec"])))),
            "module_error_threshold": max(2, min(100, int(payload.get("module_error_threshold", current["module_error_threshold"])))),
            "alert_missing_perms": bool(payload.get("alert_missing_perms", current["alert_missing_perms"])),
            "alert_mass_ban": bool(payload.get("alert_mass_ban", current["alert_mass_ban"])),
            "alert_module_errors": bool(payload.get("alert_module_errors", current["alert_module_errors"])),
        }
    )
    settings_db.put(guild_id, MODULE_NAME, current)
    return get_settings(guild_id)


# In-memory trackers (process lifetime)
_ban_events: dict[int, deque] = defaultdict(deque)
_module_errors: dict[int, deque] = defaultdict(deque)


def register_ban(guild_id: int, settings: dict | None = None) -> bool:
    """Record a ban; return True if threshold crossed."""
    settings = settings or get_settings(guild_id)
    if not settings["enabled"] or not settings["alert_mass_ban"]:
        return False
    now = time()
    window = settings["mass_ban_window_sec"]
    q = _ban_events[guild_id]
    q.append(now)
    while q and now - q[0] > window:
        q.popleft()
    return len(q) >= settings["mass_ban_threshold"]


def register_module_error(guild_id: int, settings: dict | None = None) -> bool:
    settings = settings or get_settings(guild_id)
    if not settings["enabled"] or not settings["alert_module_errors"]:
        return False
    now = time()
    q = _module_errors[guild_id]
    q.append(now)
    while q and now - q[0] > 300:
        q.popleft()
    return len(q) >= settings["module_error_threshold"]


def critical_perms_missing(guild_perms) -> list[str]:
    """guild_perms: discord.Permissions-like with attributes."""
    needed = (
        ("send_messages", "Send Messages"),
        ("embed_links", "Embed Links"),
        ("manage_messages", "Manage Messages"),
        ("manage_roles", "Manage Roles"),
        ("kick_members", "Kick Members"),
        ("ban_members", "Ban Members"),
        ("moderate_members", "Timeout Members"),
        ("view_audit_log", "View Audit Log"),
    )
    missing = []
    for attr, label in needed:
        if not getattr(guild_perms, attr, False):
            missing.append(label)
    return missing


def format_alert(kind: str, detail: str, lang: str = "en") -> str:
    prefix = {
        "missing_perms": "⚠️ Critical permissions missing",
        "mass_ban": "🚨 Mass ban spike",
        "module_error": "❗ Module errors threshold",
    }.get(kind, "⚠️ Owner alert")
    if lang == "ru":
        prefix = {
            "missing_perms": "⚠️ Нет критических прав",
            "mass_ban": "🚨 Всплеск массовых банов",
            "module_error": "❗ Порог ошибок модуля",
        }.get(kind, "⚠️ Алерт владельцу")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"**{prefix}**\n{detail}\n_{ts}_"
