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
        "weekly_digest_enabled": bool(data.get("weekly_digest_enabled", False)),
        "weekly_digest_channel_id": str(data.get("weekly_digest_channel_id") or ""),
        "last_weekly_digest_date": str(data.get("last_weekly_digest_date") or ""),
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
            "weekly_digest_enabled": bool(payload.get("weekly_digest_enabled", current["weekly_digest_enabled"])),
            "weekly_digest_channel_id": str(payload.get("weekly_digest_channel_id") or ""),
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


# ────────────────────────── Setup health: module checks ──────────────────────────

# Modules with a simple top-level "channel_id" setting — checked for dead/missing
# channels when enabled. Lazily imported to dodge any accidental import cycles.
_CHANNEL_CHECK_MODULES: tuple[tuple[str, str], ...] = (
    ("starboard", "starboard_core"),
    ("birthdays", "birthdays_core"),
    ("daily_topic", "daily_topic_core"),
    ("wordle", "wordle_core"),
)


def check_module_health(guild) -> list[dict]:
    """Scan enabled modules for dead channels / missing critical roles.

    `guild`: discord.Guild-like object exposing `.id`, `get_channel()`, `get_role()`.
    Returns a list of {"module": str, "kind": "missing_channel" | "missing_role", "detail": str}.
    Never raises — a broken module's settings should never break the health check.
    """
    import importlib

    issues: list[dict] = []
    guild_id = guild.id

    for module_key, module_name in _CHANNEL_CHECK_MODULES:
        try:
            core = importlib.import_module(module_name)
            settings = core.get_settings(guild_id)
        except Exception:
            continue
        if not settings.get("enabled"):
            continue
        channel_id = settings.get("channel_id")
        if not channel_id:
            continue
        try:
            channel = guild.get_channel(int(channel_id))
        except (TypeError, ValueError):
            channel = None
        if channel is None:
            issues.append({"module": module_key, "kind": "missing_channel", "detail": str(channel_id)})

    try:
        import xp_core

        xp_settings = xp_core.get_settings(guild_id)
        announce = xp_settings.get("announce", {})
        channel_id = announce.get("channel_id")
        if announce.get("enabled") and channel_id and guild.get_channel(int(channel_id)) is None:
            issues.append({"module": "levels", "kind": "missing_channel", "detail": str(channel_id)})
    except Exception:
        pass

    try:
        import verification_core

        v_settings = verification_core.get_settings(guild_id)
        if v_settings.get("enabled"):
            role_id = v_settings.get("verified_role_id")
            if not role_id:
                issues.append({"module": "verification", "kind": "missing_role", "detail": "verified_role_id"})
            elif guild.get_role(int(role_id)) is None:
                issues.append({"module": "verification", "kind": "missing_role", "detail": str(role_id)})
    except Exception:
        pass

    try:
        import valchecker_core

        vc = valchecker_core.get_settings(guild_id)
        if vc.get("enabled"):
            for field in ("match_channel_id", "alert_channel_id"):
                channel_id = vc.get(field) or ""
                if not channel_id:
                    # Match channel is required for auto-posts; alert may fall back to match.
                    if field == "match_channel_id":
                        issues.append({
                            "module": "valchecker",
                            "kind": "missing_channel",
                            "detail": field,
                        })
                    continue
                try:
                    channel = guild.get_channel(int(channel_id))
                except (TypeError, ValueError):
                    channel = None
                if channel is None:
                    issues.append({
                        "module": "valchecker",
                        "kind": "missing_channel",
                        "detail": str(channel_id),
                    })
    except Exception:
        pass

    return issues


# ────────────────────────── Weekly settings digest ──────────────────────────

def weekly_digest_channel_id(settings: dict) -> str:
    """Digest channel: explicit override, else the shared owner-alerts channel."""
    return settings.get("weekly_digest_channel_id") or settings.get("channel_id") or ""


def mark_weekly_digest_posted(guild_id: int, week_key: str) -> None:
    data = settings_db.get(guild_id, MODULE_NAME)
    data["last_weekly_digest_date"] = week_key
    settings_db.put(guild_id, MODULE_NAME, data)


def should_post_weekly_digest(guild_id: int) -> bool:
    """True on Monday in guild TZ if enabled, a channel resolves, and not yet posted this ISO week."""
    import timezone_core

    settings = get_settings(guild_id)
    if not settings["enabled"] or not settings["weekly_digest_enabled"]:
        return False
    if not weekly_digest_channel_id(settings):
        return False
    now = timezone_core.now_local(guild_id)
    if now.weekday() != 0:  # Monday
        return False
    week_key = now.strftime("%G-W%V")
    return settings["last_weekly_digest_date"] != week_key


def prettify_action(action: str) -> str:
    """Human-readable label for an i18n audit action key, without needing a translation table."""
    key = action.removeprefix("audit.action.") if action else ""
    label = key.replace("_", " ").replace(".", " ").strip()
    return label.capitalize() if label else "Unknown"


def summarize_audit_actions(rows: list[dict], limit: int = 15) -> list[dict]:
    """Group audit rows by action, counted desc. Pure/testable — `rows` are plain dicts with an "action" key."""
    counts: dict[str, int] = {}
    for row in rows:
        action = row.get("action") or "unknown"
        counts[action] = counts.get(action, 0) + 1
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return [{"action": action, "label": prettify_action(action), "count": count} for action, count in ranked[:limit]]


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
