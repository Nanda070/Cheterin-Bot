"""Ядро модуля «Гивевеи».

Розыгрыши хранятся per-guild в settings_db (Фаза 2.2б MULTIGUILD_PLAN.md), чтобы
переживать перезапуск бота и быть изолированными между серверами — тот же паттерн,
что и у supply_core.py.
"""

import random
import re
from datetime import datetime, timezone

import settings_db

MODULE_NAME = "giveaways"  # должно совпадать с ключом в settings_migration.MODULE_FILE_MAP

DURATION_RE = re.compile(r"^(\d+)([smhd])$")
DURATION_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}

HISTORY_LIMIT = 100


def parse_duration(value: str) -> int:
    match = DURATION_RE.match(value.strip().lower())
    if not match:
        raise ValueError("Используйте формат: число + единица (s/m/h/d), например 10m, 2h, 1d.")
    amount, unit = match.groups()
    return int(amount) * DURATION_UNITS[unit]


def load_data(guild_id: int) -> dict:
    return _normalized(settings_db.get(guild_id, MODULE_NAME))


def save_data(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def _normalized(data: dict) -> dict:
    data.setdefault("seq", 0)
    data.setdefault("giveaways", {})
    return data


def create_giveaway(guild_id: int, initiator_id: int, prize: str, duration_str: str, winners_count: int) -> dict:
    data = load_data(guild_id)
    data["seq"] += 1
    giveaway_id = str(data["seq"])
    now_ts = int(datetime.now(timezone.utc).timestamp())
    giveaway = {
        "id": giveaway_id,
        "guild_id": str(guild_id),
        "initiator_id": str(initiator_id),
        "prize": prize,
        "winners_count": int(winners_count),
        "duration_str": duration_str,
        "target_ts": now_ts + parse_duration(duration_str),
        "status": "active",
        "entrants": [],
        "winners": [],
        "past_winners": [],
        "channel_id": "",
        "message_id": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "closed_at": None,
    }
    data["giveaways"][giveaway_id] = giveaway
    save_data(guild_id, data)
    return giveaway


def get_giveaway(guild_id: int, giveaway_id: str) -> dict | None:
    return load_data(guild_id)["giveaways"].get(str(giveaway_id))


def get_giveaway_by_message(guild_id: int, message_id: int) -> dict | None:
    for giveaway in load_data(guild_id)["giveaways"].values():
        if giveaway.get("message_id") == str(message_id):
            return giveaway
    return None


def update_giveaway(guild_id: int, giveaway_id: str, **fields) -> dict | None:
    data = load_data(guild_id)
    giveaway = data["giveaways"].get(str(giveaway_id))
    if giveaway is None:
        return None
    giveaway.update(fields)
    save_data(guild_id, data)
    return giveaway


def list_active(guild_id: int) -> list[dict]:
    giveaways = [g for g in load_data(guild_id)["giveaways"].values() if g["status"] == "active"]
    return sorted(giveaways, key=lambda g: g["target_ts"])


def list_history(guild_id: int, limit: int = 20) -> list[dict]:
    giveaways = [g for g in load_data(guild_id)["giveaways"].values() if g["status"] != "active"]
    giveaways.sort(key=lambda g: g.get("closed_at") or "", reverse=True)
    return giveaways[:limit]


def join_giveaway(guild_id: int, giveaway_id: str, user_id: int) -> str:
    """Возвращает: joined | already | closed | not_found."""
    data = load_data(guild_id)
    giveaway = data["giveaways"].get(str(giveaway_id))
    if giveaway is None:
        return "not_found"
    if giveaway["status"] != "active":
        return "closed"

    uid = str(user_id)
    if uid in giveaway["entrants"]:
        return "already"

    giveaway["entrants"].append(uid)
    save_data(guild_id, data)
    return "joined"


def leave_giveaway(guild_id: int, giveaway_id: str, user_id: int) -> str:
    """Возвращает: left | not_in_list | closed | not_found."""
    data = load_data(guild_id)
    giveaway = data["giveaways"].get(str(giveaway_id))
    if giveaway is None:
        return "not_found"
    if giveaway["status"] != "active":
        return "closed"

    uid = str(user_id)
    if uid not in giveaway["entrants"]:
        return "not_in_list"

    giveaway["entrants"].remove(uid)
    save_data(guild_id, data)
    return "left"


def _draw_winners(giveaway: dict, exclude_past: bool = True) -> list[str]:
    pool = list(giveaway["entrants"])
    if exclude_past:
        past = set(giveaway.get("past_winners", []))
        pool = [uid for uid in pool if uid not in past]
    count = min(giveaway["winners_count"], len(pool))
    if count <= 0:
        return []
    return random.sample(pool, count)


def draw_winners(guild_id: int, giveaway_id: str, exclude_past: bool = True) -> list[str]:
    giveaway = get_giveaway(guild_id, giveaway_id)
    if giveaway is None:
        return []
    return _draw_winners(giveaway, exclude_past=exclude_past)


def close_giveaway(guild_id: int, giveaway_id: str, status: str = "finished") -> dict | None:
    """Закрывает гивевей (finished/cancelled); при finished сразу выбирает победителей."""
    data = load_data(guild_id)
    giveaway = data["giveaways"].get(str(giveaway_id))
    if giveaway is None or giveaway["status"] != "active":
        return None

    winners = _draw_winners(giveaway) if status == "finished" else []
    giveaway["status"] = status
    giveaway["winners"] = winners
    giveaway["past_winners"] = sorted(set(giveaway.get("past_winners", [])) | set(winners))
    giveaway["closed_at"] = datetime.now(timezone.utc).isoformat()

    _trim_history(data)
    save_data(guild_id, data)
    return giveaway


def reroll_giveaway(guild_id: int, giveaway_id: str) -> list[str] | None:
    """Перевыбирает победителей, исключая тех, кто уже выигрывал в этом гивевее ранее."""
    data = load_data(guild_id)
    giveaway = data["giveaways"].get(str(giveaway_id))
    if giveaway is None or giveaway["status"] != "finished":
        return None

    winners = _draw_winners(giveaway, exclude_past=True)
    giveaway["winners"] = winners
    giveaway["past_winners"] = sorted(set(giveaway.get("past_winners", [])) | set(winners))
    save_data(guild_id, data)
    return winners


def _trim_history(data: dict) -> None:
    closed = [g for g in data["giveaways"].values() if g["status"] != "active"]
    if len(closed) <= HISTORY_LIMIT:
        return
    closed.sort(key=lambda g: g.get("closed_at") or "")
    for stale in closed[:len(closed) - HISTORY_LIMIT]:
        data["giveaways"].pop(stale["id"], None)
