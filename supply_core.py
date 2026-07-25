"""Ядро модуля «Сборы на поставку» (портировано из ChetSupply и расширено).

Сборы хранятся per-guild в settings_db (Фаза 2.2б MULTIGUILD_PLAN.md), чтобы переживать
перезапуск бота и быть изолированными между серверами. Улучшения относительно оригинала:
- персистентность и восстановление таймеров после рестарта;
- резервный список, когда основной лимит исчерпан;
- напоминание участникам за N минут до начала;
- досрочное закрытие/отмена сбора инициатором или модератором;
- история сборов и статистика участия.
"""

import re
from datetime import datetime, timedelta

import settings_db
import timezone_core

MODULE_NAME = "supply"  # должно совпадать с ключом в settings_migration.MODULE_FILE_MAP

TIME_RE = re.compile(r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")

HISTORY_LIMIT = 100


def now_local(guild_id: int) -> datetime:
    return timezone_core.now_local(guild_id)


def is_valid_time(time_str: str) -> bool:
    return bool(TIME_RE.match(time_str))


def get_target_datetime(time_str: str, guild_id: int) -> datetime:
    now = now_local(guild_id)
    target_h, target_m = map(int, time_str.split(':'))
    target_dt = now.replace(hour=target_h, minute=target_m, second=0, microsecond=0)

    if target_dt <= now:
        target_dt += timedelta(days=1)
    return target_dt


def load_data(guild_id: int) -> dict:
    return _normalized(settings_db.get(guild_id, MODULE_NAME))


def save_data(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def _normalized(data: dict) -> dict:
    data.setdefault("seq", 0)
    data.setdefault("supplies", {})
    data.setdefault("stats", {})
    return data


def create_supply(guild_id: int, initiator_id: int, opponent: str, limit: int, time_str: str) -> dict:
    data = load_data(guild_id)
    data["seq"] += 1
    supply_id = str(data["seq"])
    target_dt = get_target_datetime(time_str, guild_id)
    supply = {
        "id": supply_id,
        "guild_id": str(guild_id),
        "initiator_id": str(initiator_id),
        "opponent": opponent,
        "limit": int(limit),
        "time_str": time_str,
        "target_ts": int(target_dt.timestamp()),
        "status": "active",
        "participants": [],
        "reserve": [],
        "channel_id": "",
        "message_id": "",
        "reminder_sent": False,
        "created_at": now_local(guild_id).isoformat(),
        "closed_at": None,
    }
    data["supplies"][supply_id] = supply
    save_data(guild_id, data)
    return supply


def get_supply(guild_id: int, supply_id: str) -> dict | None:
    return load_data(guild_id)["supplies"].get(str(supply_id))


def get_supply_by_message(guild_id: int, message_id: int) -> dict | None:
    for supply in load_data(guild_id)["supplies"].values():
        if supply.get("message_id") == str(message_id):
            return supply
    return None


def update_supply(guild_id: int, supply_id: str, **fields) -> dict | None:
    data = load_data(guild_id)
    supply = data["supplies"].get(str(supply_id))
    if supply is None:
        return None
    supply.update(fields)
    save_data(guild_id, data)
    return supply


def list_active(guild_id: int) -> list[dict]:
    supplies = [s for s in load_data(guild_id)["supplies"].values() if s["status"] == "active"]
    return sorted(supplies, key=lambda s: s["target_ts"])


def list_history(guild_id: int, limit: int = 20) -> list[dict]:
    supplies = [s for s in load_data(guild_id)["supplies"].values() if s["status"] != "active"]
    supplies.sort(key=lambda s: s.get("closed_at") or "", reverse=True)
    return supplies[:limit]


def join_supply(guild_id: int, supply_id: str, user_id: int) -> str:
    """Возвращает: joined | reserve | already | closed | not_found."""
    data = load_data(guild_id)
    supply = data["supplies"].get(str(supply_id))
    if supply is None:
        return "not_found"
    if supply["status"] != "active":
        return "closed"

    uid = str(user_id)
    if uid in supply["participants"] or uid in supply["reserve"]:
        return "already"

    if len(supply["participants"]) < supply["limit"]:
        supply["participants"].append(uid)
        save_data(guild_id, data)
        return "joined"

    supply["reserve"].append(uid)
    save_data(guild_id, data)
    return "reserve"


def leave_supply(guild_id: int, supply_id: str, user_id: int) -> tuple[str, str | None]:
    """Возвращает (результат, id продвинутого из резерва или None).

    Результат: left | not_in_list | closed | not_found.
    """
    data = load_data(guild_id)
    supply = data["supplies"].get(str(supply_id))
    if supply is None:
        return "not_found", None
    if supply["status"] != "active":
        return "closed", None

    uid = str(user_id)
    promoted = None
    if uid in supply["participants"]:
        supply["participants"].remove(uid)
        if supply["reserve"] and len(supply["participants"]) < supply["limit"]:
            promoted = supply["reserve"].pop(0)
            supply["participants"].append(promoted)
    elif uid in supply["reserve"]:
        supply["reserve"].remove(uid)
    else:
        return "not_in_list", None

    save_data(guild_id, data)
    return "left", promoted


def close_supply(guild_id: int, supply_id: str, status: str = "finished") -> dict | None:
    """Закрывает сбор (finished/cancelled) и обновляет статистику участия."""
    data = load_data(guild_id)
    supply = data["supplies"].get(str(supply_id))
    if supply is None or supply["status"] != "active":
        return None

    supply["status"] = status
    supply["closed_at"] = now_local(guild_id).isoformat()

    if status == "finished":
        for uid in supply["participants"]:
            data["stats"][uid] = data["stats"].get(uid, 0) + 1

    _trim_history(data)
    save_data(guild_id, data)
    return supply


def _trim_history(data: dict) -> None:
    closed = [s for s in data["supplies"].values() if s["status"] != "active"]
    if len(closed) <= HISTORY_LIMIT:
        return
    closed.sort(key=lambda s: s.get("closed_at") or "")
    for stale in closed[:len(closed) - HISTORY_LIMIT]:
        data["supplies"].pop(stale["id"], None)


def get_stats(guild_id: int, top: int = 20) -> list[dict]:
    data = load_data(guild_id)
    ranked = sorted(data["stats"].items(), key=lambda kv: kv[1], reverse=True)
    return [{"user_id": uid, "count": count} for uid, count in ranked[:top]]
