"""Ядро модуля «Сборы на поставку» (портировано из ChetSupply и расширено).

Хранит сборы в supply_data.json, чтобы они переживали перезапуск бота.
Улучшения относительно оригинала:
- персистентность и восстановление таймеров после рестарта;
- резервный список, когда основной лимит исчерпан;
- напоминание участникам за N минут до начала;
- досрочное закрытие/отмена сбора инициатором или модератором;
- история сборов и статистика участия.
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone

DATA_FILE = "supply_data.json"

MSK = timezone(timedelta(hours=3))

TIME_RE = re.compile(r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")

HISTORY_LIMIT = 100


def now_msk() -> datetime:
    return datetime.now(MSK)


def is_valid_time(time_str: str) -> bool:
    return bool(TIME_RE.match(time_str))


def get_target_datetime(time_str: str) -> datetime:
    now = now_msk()
    target_h, target_m = map(int, time_str.split(':'))
    target_dt = now.replace(hour=target_h, minute=target_m, second=0, microsecond=0)

    if target_dt <= now:
        target_dt += timedelta(days=1)
    return target_dt


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_data(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def _normalized(data: dict) -> dict:
    data.setdefault("seq", 0)
    data.setdefault("supplies", {})
    data.setdefault("stats", {})
    return data


def create_supply(initiator_id: int, opponent: str, limit: int, time_str: str) -> dict:
    data = _normalized(load_data())
    data["seq"] += 1
    supply_id = str(data["seq"])
    target_dt = get_target_datetime(time_str)
    supply = {
        "id": supply_id,
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
        "created_at": now_msk().isoformat(),
        "closed_at": None,
    }
    data["supplies"][supply_id] = supply
    save_data(data)
    return supply


def get_supply(supply_id: str) -> dict | None:
    return _normalized(load_data())["supplies"].get(str(supply_id))


def get_supply_by_message(message_id: int) -> dict | None:
    for supply in _normalized(load_data())["supplies"].values():
        if supply.get("message_id") == str(message_id):
            return supply
    return None


def update_supply(supply_id: str, **fields) -> dict | None:
    data = _normalized(load_data())
    supply = data["supplies"].get(str(supply_id))
    if supply is None:
        return None
    supply.update(fields)
    save_data(data)
    return supply


def list_active() -> list[dict]:
    supplies = [s for s in _normalized(load_data())["supplies"].values() if s["status"] == "active"]
    return sorted(supplies, key=lambda s: s["target_ts"])


def list_history(limit: int = 20) -> list[dict]:
    supplies = [s for s in _normalized(load_data())["supplies"].values() if s["status"] != "active"]
    supplies.sort(key=lambda s: s.get("closed_at") or "", reverse=True)
    return supplies[:limit]


def join_supply(supply_id: str, user_id: int) -> str:
    """Возвращает: joined | reserve | already | closed | not_found."""
    data = _normalized(load_data())
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
        save_data(data)
        return "joined"

    supply["reserve"].append(uid)
    save_data(data)
    return "reserve"


def leave_supply(supply_id: str, user_id: int) -> tuple[str, str | None]:
    """Возвращает (результат, id продвинутого из резерва или None).

    Результат: left | not_in_list | closed | not_found.
    """
    data = _normalized(load_data())
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

    save_data(data)
    return "left", promoted


def close_supply(supply_id: str, status: str = "finished") -> dict | None:
    """Закрывает сбор (finished/cancelled) и обновляет статистику участия."""
    data = _normalized(load_data())
    supply = data["supplies"].get(str(supply_id))
    if supply is None or supply["status"] != "active":
        return None

    supply["status"] = status
    supply["closed_at"] = now_msk().isoformat()

    if status == "finished":
        for uid in supply["participants"]:
            data["stats"][uid] = data["stats"].get(uid, 0) + 1

    _trim_history(data)
    save_data(data)
    return supply


def _trim_history(data: dict) -> None:
    closed = [s for s in data["supplies"].values() if s["status"] != "active"]
    if len(closed) <= HISTORY_LIMIT:
        return
    closed.sort(key=lambda s: s.get("closed_at") or "")
    for stale in closed[:len(closed) - HISTORY_LIMIT]:
        data["supplies"].pop(stale["id"], None)


def get_stats(top: int = 20) -> list[dict]:
    data = _normalized(load_data())
    ranked = sorted(data["stats"].items(), key=lambda kv: kv[1], reverse=True)
    return [{"user_id": uid, "count": count} for uid, count in ranked[:top]]
