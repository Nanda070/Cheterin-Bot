"""Ядро игры «Мафия»: конфигурация, раздача ролей, подсчёт голосов, условие победы.

Без импорта discord — юнит-тестируемо напрямую. Эмбеды и текст сообщений
собираются в mafia.py (там же, где Discord-специфика), по образцу того, как
family_tickets.py строит свои эмбеды сам, а family_core.py остаётся чистым.
"""

import json
import os
import random

CONFIG_FILE = "mafia_config.json"

PLAYERS_FLOOR = 5
PLAYERS_CEIL = 99

DEFAULT_MIN_PLAYERS = 5
DEFAULT_MAX_PLAYERS = 20
DEFAULT_NIGHT_TIMER_SEC = 60
DEFAULT_DAY_DISCUSSION_TIMER_SEC = 120
DEFAULT_DAY_VOTE_TIMER_SEC = 60

ROLE_LABELS = {
    "mafia": "Мафия",
    "citizen": "Мирный житель",
    "doctor": "Доктор",
    "sheriff": "Шериф",
}

NIGHT_ACTION_ROLES = ("mafia", "doctor", "sheriff")

_cache: dict | None = None
_cache_mtime: float | None = None


def load_config() -> dict:
    global _cache, _cache_mtime
    if not os.path.exists(CONFIG_FILE):
        _cache, _cache_mtime = None, None
        return {}

    mtime = os.path.getmtime(CONFIG_FILE)
    if _cache is not None and _cache_mtime == mtime:
        return _cache

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    _cache, _cache_mtime = data, mtime
    return data


def save_config(data: dict) -> None:
    global _cache, _cache_mtime
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    _cache = data
    _cache_mtime = os.path.getmtime(CONFIG_FILE)


def get_settings() -> dict:
    """Настройки модуля с дефолтами (выключен по умолчанию)."""
    data = load_config()
    return {
        "enabled": bool(data.get("enabled", False)),
        "default_min_players": int(data.get("default_min_players", DEFAULT_MIN_PLAYERS)),
        "default_max_players": int(data.get("default_max_players", DEFAULT_MAX_PLAYERS)),
        "default_night_timer_sec": int(data.get("default_night_timer_sec", DEFAULT_NIGHT_TIMER_SEC)),
        "default_day_discussion_timer_sec": int(
            data.get("default_day_discussion_timer_sec", DEFAULT_DAY_DISCUSSION_TIMER_SEC)
        ),
        "default_day_vote_timer_sec": int(data.get("default_day_vote_timer_sec", DEFAULT_DAY_VOTE_TIMER_SEC)),
        "log_channel_id": str(data.get("log_channel_id") or ""),
    }


def role_label(role: str) -> str:
    return ROLE_LABELS.get(role, role)


def has_moderator_access(member) -> bool:
    """Право форс-старта/отмены лобби — обычное модераторское право сервера."""
    permissions = getattr(member, "guild_permissions", None)
    if permissions is None:
        return False
    return bool(permissions.manage_guild or permissions.administrator)


# ────────────────────────── Роли ──────────────────────────

def scale_roles(player_count: int) -> dict:
    """Ровно 1 Доктор и 1 Шериф, Мафия ~25% (минимум 1), остальные — мирные."""
    mafia = max(1, round(player_count / 4))
    doctor = 1
    sheriff = 1
    citizen = max(0, player_count - mafia - doctor - sheriff)
    return {"mafia": mafia, "doctor": doctor, "sheriff": sheriff, "citizen": citizen}


def assign_roles(player_ids: list[int]) -> dict[int, str]:
    counts = scale_roles(len(player_ids))
    pool = list(player_ids)
    random.shuffle(pool)

    assignment: dict[int, str] = {}
    idx = 0
    for role in ("mafia", "doctor", "sheriff"):
        for _ in range(counts[role]):
            assignment[pool[idx]] = role
            idx += 1
    for user_id in pool[idx:]:
        assignment[user_id] = "citizen"
    return assignment


# ────────────────────────── Голосование ──────────────────────────

def _majority_target(votes: dict[int, int | None]) -> int | None:
    tally: dict[int, int] = {}
    for target in votes.values():
        if target is None:
            continue
        tally[target] = tally.get(target, 0) + 1
    if not tally:
        return None
    top = max(tally.values())
    leaders = [target for target, count in tally.items() if count == top]
    return leaders[0] if len(leaders) == 1 else None


def resolve_mafia_kill(votes: dict[int, int | None]) -> int | None:
    """Большинство голосов мафии по цели; ничья или 0 голосов — никто не убит."""
    return _majority_target(votes)


def resolve_day_vote(votes: dict[int, int | None]) -> int | None:
    """Большинство дневных голосов; ничья среди лидеров — никто не казнён."""
    return _majority_target(votes)


def check_win_condition(alive_roles: list[str]) -> str | None:
    mafia_alive = sum(1 for role in alive_roles if role == "mafia")
    town_alive = len(alive_roles) - mafia_alive
    if mafia_alive == 0:
        return "town"
    if mafia_alive >= town_alive:
        return "mafia"
    return None
