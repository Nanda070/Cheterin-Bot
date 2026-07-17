"""Ядро модуля «Гивевеи».

Хранит розыгрыши в giveaways_data.json, чтобы они переживали перезапуск бота —
тот же паттерн персистентности и восстановления таймеров, что и у supply_core.py.
"""

import json
import os
import random
import re
from datetime import datetime, timezone

DATA_FILE = "giveaways_data.json"

DURATION_RE = re.compile(r"^(\d+)([smhd])$")
DURATION_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}

HISTORY_LIMIT = 100


def parse_duration(value: str) -> int:
    match = DURATION_RE.match(value.strip().lower())
    if not match:
        raise ValueError("Используйте формат: число + единица (s/m/h/d), например 10m, 2h, 1d.")
    amount, unit = match.groups()
    return int(amount) * DURATION_UNITS[unit]


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
    data.setdefault("giveaways", {})
    return data


def create_giveaway(initiator_id: int, prize: str, duration_str: str, winners_count: int) -> dict:
    data = _normalized(load_data())
    data["seq"] += 1
    giveaway_id = str(data["seq"])
    now_ts = int(datetime.now(timezone.utc).timestamp())
    giveaway = {
        "id": giveaway_id,
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
    save_data(data)
    return giveaway


def get_giveaway(giveaway_id: str) -> dict | None:
    return _normalized(load_data())["giveaways"].get(str(giveaway_id))


def get_giveaway_by_message(message_id: int) -> dict | None:
    for giveaway in _normalized(load_data())["giveaways"].values():
        if giveaway.get("message_id") == str(message_id):
            return giveaway
    return None


def update_giveaway(giveaway_id: str, **fields) -> dict | None:
    data = _normalized(load_data())
    giveaway = data["giveaways"].get(str(giveaway_id))
    if giveaway is None:
        return None
    giveaway.update(fields)
    save_data(data)
    return giveaway


def list_active() -> list[dict]:
    giveaways = [g for g in _normalized(load_data())["giveaways"].values() if g["status"] == "active"]
    return sorted(giveaways, key=lambda g: g["target_ts"])


def list_history(limit: int = 20) -> list[dict]:
    giveaways = [g for g in _normalized(load_data())["giveaways"].values() if g["status"] != "active"]
    giveaways.sort(key=lambda g: g.get("closed_at") or "", reverse=True)
    return giveaways[:limit]


def join_giveaway(giveaway_id: str, user_id: int) -> str:
    """Возвращает: joined | already | closed | not_found."""
    data = _normalized(load_data())
    giveaway = data["giveaways"].get(str(giveaway_id))
    if giveaway is None:
        return "not_found"
    if giveaway["status"] != "active":
        return "closed"

    uid = str(user_id)
    if uid in giveaway["entrants"]:
        return "already"

    giveaway["entrants"].append(uid)
    save_data(data)
    return "joined"


def leave_giveaway(giveaway_id: str, user_id: int) -> str:
    """Возвращает: left | not_in_list | closed | not_found."""
    data = _normalized(load_data())
    giveaway = data["giveaways"].get(str(giveaway_id))
    if giveaway is None:
        return "not_found"
    if giveaway["status"] != "active":
        return "closed"

    uid = str(user_id)
    if uid not in giveaway["entrants"]:
        return "not_in_list"

    giveaway["entrants"].remove(uid)
    save_data(data)
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


def draw_winners(giveaway_id: str, exclude_past: bool = True) -> list[str]:
    giveaway = get_giveaway(giveaway_id)
    if giveaway is None:
        return []
    return _draw_winners(giveaway, exclude_past=exclude_past)


def close_giveaway(giveaway_id: str, status: str = "finished") -> dict | None:
    """Закрывает гивевей (finished/cancelled); при finished сразу выбирает победителей."""
    data = _normalized(load_data())
    giveaway = data["giveaways"].get(str(giveaway_id))
    if giveaway is None or giveaway["status"] != "active":
        return None

    winners = _draw_winners(giveaway) if status == "finished" else []
    giveaway["status"] = status
    giveaway["winners"] = winners
    giveaway["past_winners"] = sorted(set(giveaway.get("past_winners", [])) | set(winners))
    giveaway["closed_at"] = datetime.now(timezone.utc).isoformat()

    _trim_history(data)
    save_data(data)
    return giveaway


def reroll_giveaway(giveaway_id: str) -> list[str] | None:
    """Перевыбирает победителей, исключая тех, кто уже выигрывал в этом гивевее ранее."""
    data = _normalized(load_data())
    giveaway = data["giveaways"].get(str(giveaway_id))
    if giveaway is None or giveaway["status"] != "finished":
        return None

    winners = _draw_winners(giveaway, exclude_past=True)
    giveaway["winners"] = winners
    giveaway["past_winners"] = sorted(set(giveaway.get("past_winners", [])) | set(winners))
    save_data(data)
    return winners


def _trim_history(data: dict) -> None:
    closed = [g for g in data["giveaways"].values() if g["status"] != "active"]
    if len(closed) <= HISTORY_LIMIT:
        return
    closed.sort(key=lambda g: g.get("closed_at") or "")
    for stale in closed[:len(closed) - HISTORY_LIMIT]:
        data["giveaways"].pop(stale["id"], None)
