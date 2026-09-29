"""Guild-scoped settings and catalog for the VALORANT dashboard modules."""

from __future__ import annotations

import bot.core.settings_db as settings_db

PREMIER_MODULE = "premier"
PANELS_MODULE = "valorant_panels"

FAQ_URL = "https://playvalorant.com/ru-ru/news/game-updates/premier-global-open-beta-faq/"

AGENT_CLASSES = {
    "duelist": [("jett", "Jett"), ("phoenix", "Phoenix"), ("raze", "Raze"), ("reyna", "Reyna"), ("yoru", "Yoru")],
    "initiator": [("sova", "Sova"), ("breach", "Breach"), ("skye", "Skye"), ("kayo", "KAY/O"), ("fade", "Fade")],
    "controller": [("brimstone", "Brimstone"), ("omen", "Omen"), ("viper", "Viper"), ("astra", "Astra"), ("harbor", "Harbor")],
    "sentinel": [("sage", "Sage"), ("cypher", "Cypher"), ("killjoy", "Killjoy"), ("chamber", "Chamber"), ("deadlock", "Deadlock")],
}
SERVERS = [("frankfurt", "Frankfurt"), ("paris", "Paris"), ("london", "London"), ("stockholm", "Stockholm"), ("warsaw", "Warsaw")]
NOTIFICATIONS = [("news", "News"), ("tournaments", "Tournaments"), ("premier", "Premier")]


def _id(value: object) -> str:
    raw = str(value or "")
    return raw if not raw or raw.isdigit() else ""


def get_premier_settings(guild_id: int) -> dict:
    raw = settings_db.get(guild_id, PREMIER_MODULE)
    return {"enabled": bool(raw.get("enabled", False)), "channel_id": _id(raw.get("channel_id"))}


def save_premier_settings(guild_id: int, data: dict) -> dict:
    result = {"enabled": bool(data.get("enabled", False)), "channel_id": _id(data.get("channel_id"))}
    settings_db.put(guild_id, PREMIER_MODULE, result)
    return result


def get_panel_settings(guild_id: int) -> dict:
    raw = settings_db.get(guild_id, PANELS_MODULE)
    maps = ("agent_roles", "playstyle_roles", "notification_roles", "server_roles", "notification_channels")
    result = {"enabled": bool(raw.get("enabled", False)), "button_role_id": _id(raw.get("button_role_id")), "button_label": str(raw.get("button_label") or "Get role")[:80]}
    for key in maps:
        values = raw.get(key) if isinstance(raw.get(key), dict) else {}
        result[key] = {str(k): _id(v) for k, v in values.items() if _id(v)}
    return result


def save_panel_settings(guild_id: int, data: dict) -> dict:
    current = get_panel_settings(guild_id)
    current["enabled"] = bool(data.get("enabled", current["enabled"]))
    current["button_role_id"] = _id(data.get("button_role_id", current["button_role_id"]))
    current["button_label"] = str(data.get("button_label", current["button_label"]) or "Get role")[:80]
    for key in ("agent_roles", "playstyle_roles", "notification_roles", "server_roles", "notification_channels"):
        if isinstance(data.get(key), dict):
            current[key] = {str(k): _id(v) for k, v in data[key].items() if _id(v)}
    settings_db.put(guild_id, PANELS_MODULE, current)
    return get_panel_settings(guild_id)


def panel_catalog() -> dict:
    return {
        "agent_classes": {key: [{"key": agent, "name": name} for agent, name in rows] for key, rows in AGENT_CLASSES.items()},
        "playstyles": [{"key": key, "name": key.title()} for key in AGENT_CLASSES],
        "notifications": [{"key": key, "name": name} for key, name in NOTIFICATIONS],
        "servers": [{"key": key, "name": name} for key, name in SERVERS],
    }
