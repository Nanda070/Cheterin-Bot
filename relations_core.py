"""Relations module: settings, HP levels, action helpers."""

from __future__ import annotations

import time
from typing import Any

import settings_db

MODULE_NAME = "relations"

# Level 1..11 — cumulative HP required to be at that level (index 0 = level 1).
DEFAULT_LEVEL_THRESHOLDS: list[int] = [
    0,
    50,
    120,
    220,
    350,
    520,
    750,
    1050,
    1400,
    1850,
    2400,
]

DEFAULT_ACTIONS: list[dict[str, Any]] = [
    {"id": "hug", "emoji": "🤗", "hp_gain": 10, "cooldown_sec": 60, "enabled": True},
    {"id": "kiss", "emoji": "💋", "hp_gain": 15, "cooldown_sec": 90, "enabled": True},
    {"id": "slap", "emoji": "👋", "hp_gain": 8, "cooldown_sec": 45, "enabled": True},
    {"id": "pat", "emoji": "🫶", "hp_gain": 10, "cooldown_sec": 60, "enabled": True},
    {"id": "highfive", "emoji": "🙌", "hp_gain": 8, "cooldown_sec": 45, "enabled": True},
    {"id": "cuddle", "emoji": "🥰", "hp_gain": 18, "cooldown_sec": 120, "enabled": True},
    {"id": "poke", "emoji": "👉", "hp_gain": 5, "cooldown_sec": 30, "enabled": True},
]

MAX_ACTIONS_PER_DAY = 50
MAX_ACTIONS_CONFIG = 20
HP_GAIN_MIN = 1
HP_GAIN_MAX = 500
COOLDOWN_MAX = 86400
LEVEL_COUNT = 11

# Romance / marriage defaults
DEFAULT_MIN_LEVEL_TO_MARRY = 3
DEFAULT_PROPOSAL_TIMEOUT_SEC = 300
DEFAULT_MARRIED_HP_BONUS_PERCENT = 25
DEFAULT_DATE_HP_GAIN = 35
DEFAULT_DATE_COOLDOWN_SEC = 86400
PROPOSAL_TIMEOUT_MIN = 60
PROPOSAL_TIMEOUT_MAX = 3600
MIN_LEVEL_TO_MARRY_MAX = LEVEL_COUNT
MARRIED_BONUS_MAX = 200
DATE_HP_MAX = 500


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def _clamp_int(value: Any, default: int, lo: int, hi: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = default
    return max(lo, min(hi, n))


def _normalize_role_id(raw: Any) -> str:
    rid = str(raw or "").strip()
    return rid if rid.isdigit() else ""


def _normalize_actions(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        return [dict(a) for a in DEFAULT_ACTIONS]
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw[:MAX_ACTIONS_CONFIG]:
        if not isinstance(item, dict):
            continue
        aid = str(item.get("id") or "").strip().lower()
        if not aid or aid in seen or len(aid) > 32:
            continue
        seen.add(aid)
        try:
            hp = int(item.get("hp_gain", 10))
        except (TypeError, ValueError):
            hp = 10
        try:
            cd = int(item.get("cooldown_sec", 60))
        except (TypeError, ValueError):
            cd = 60
        emoji = str(item.get("emoji") or "❤️").strip()[:32] or "❤️"
        out.append(
            {
                "id": aid,
                "emoji": emoji,
                "hp_gain": max(HP_GAIN_MIN, min(HP_GAIN_MAX, hp)),
                "cooldown_sec": max(0, min(COOLDOWN_MAX, cd)),
                "enabled": bool(item.get("enabled", True)),
            }
        )
    return out or [dict(a) for a in DEFAULT_ACTIONS]


def _normalize_thresholds(raw: Any) -> list[int]:
    if not isinstance(raw, list) or len(raw) < LEVEL_COUNT:
        return list(DEFAULT_LEVEL_THRESHOLDS)
    out: list[int] = []
    prev = -1
    for i in range(LEVEL_COUNT):
        try:
            v = int(raw[i])
        except (TypeError, ValueError):
            return list(DEFAULT_LEVEL_THRESHOLDS)
        if v < 0 or v <= prev:
            return list(DEFAULT_LEVEL_THRESHOLDS)
        out.append(v)
        prev = v
    return out


def _normalize_reward_roles(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in raw.items():
        try:
            lvl = int(k)
        except (TypeError, ValueError):
            continue
        if not 1 <= lvl <= LEVEL_COUNT:
            continue
        rid = str(v or "").strip()
        if rid and rid.isdigit():
            out[str(lvl)] = rid
    return out


def get_settings(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    try:
        max_day = int(data.get("max_actions_per_day", MAX_ACTIONS_PER_DAY))
    except (TypeError, ValueError):
        max_day = MAX_ACTIONS_PER_DAY
    return {
        "enabled": bool(data.get("enabled", False)),
        "announce_channel_id": str(data.get("announce_channel_id") or ""),
        "max_actions_per_day": max(1, min(500, max_day)),
        "actions": _normalize_actions(data.get("actions")),
        "level_thresholds": _normalize_thresholds(data.get("level_thresholds")),
        "reward_roles": _normalize_reward_roles(data.get("reward_roles")),
        # Romance
        "marriage_enabled": _as_bool(data.get("marriage_enabled"), True),
        "min_level_to_marry": _clamp_int(
            data.get("min_level_to_marry"), DEFAULT_MIN_LEVEL_TO_MARRY, 1, MIN_LEVEL_TO_MARRY_MAX
        ),
        "married_role_id": _normalize_role_id(data.get("married_role_id")),
        "allow_polygamy": _as_bool(data.get("allow_polygamy"), False),
        "proposal_timeout_sec": _clamp_int(
            data.get("proposal_timeout_sec"),
            DEFAULT_PROPOSAL_TIMEOUT_SEC,
            PROPOSAL_TIMEOUT_MIN,
            PROPOSAL_TIMEOUT_MAX,
        ),
        "married_hp_bonus_percent": _clamp_int(
            data.get("married_hp_bonus_percent"),
            DEFAULT_MARRIED_HP_BONUS_PERCENT,
            0,
            MARRIED_BONUS_MAX,
        ),
        "divorce_requires_accept": _as_bool(data.get("divorce_requires_accept"), True),
        "date_hp_gain": _clamp_int(
            data.get("date_hp_gain"), DEFAULT_DATE_HP_GAIN, HP_GAIN_MIN, DATE_HP_MAX
        ),
        "date_cooldown_sec": _clamp_int(
            data.get("date_cooldown_sec"), DEFAULT_DATE_COOLDOWN_SEC, 0, COOLDOWN_MAX
        ),
    }


def save_config(guild_id: int, data: dict) -> dict:
    settings_db.put(
        guild_id,
        MODULE_NAME,
        {
            "enabled": bool(data.get("enabled", False)),
            "announce_channel_id": str(data.get("announce_channel_id") or ""),
            "max_actions_per_day": int(data.get("max_actions_per_day", MAX_ACTIONS_PER_DAY)),
            "actions": _normalize_actions(data.get("actions")),
            "level_thresholds": _normalize_thresholds(data.get("level_thresholds")),
            "reward_roles": _normalize_reward_roles(data.get("reward_roles")),
            "marriage_enabled": _as_bool(data.get("marriage_enabled"), True),
            "min_level_to_marry": _clamp_int(
                data.get("min_level_to_marry"), DEFAULT_MIN_LEVEL_TO_MARRY, 1, MIN_LEVEL_TO_MARRY_MAX
            ),
            "married_role_id": _normalize_role_id(data.get("married_role_id")),
            "allow_polygamy": _as_bool(data.get("allow_polygamy"), False),
            "proposal_timeout_sec": _clamp_int(
                data.get("proposal_timeout_sec"),
                DEFAULT_PROPOSAL_TIMEOUT_SEC,
                PROPOSAL_TIMEOUT_MIN,
                PROPOSAL_TIMEOUT_MAX,
            ),
            "married_hp_bonus_percent": _clamp_int(
                data.get("married_hp_bonus_percent"),
                DEFAULT_MARRIED_HP_BONUS_PERCENT,
                0,
                MARRIED_BONUS_MAX,
            ),
            "divorce_requires_accept": _as_bool(data.get("divorce_requires_accept"), True),
            "date_hp_gain": _clamp_int(
                data.get("date_hp_gain"), DEFAULT_DATE_HP_GAIN, HP_GAIN_MIN, DATE_HP_MAX
            ),
            "date_cooldown_sec": _clamp_int(
                data.get("date_cooldown_sec"), DEFAULT_DATE_COOLDOWN_SEC, 0, COOLDOWN_MAX
            ),
        },
    )
    return get_settings(guild_id)


def pair_ids(user_a: int, user_b: int) -> tuple[int, int]:
    return (user_a, user_b) if user_a < user_b else (user_b, user_a)


def find_action(settings: dict, action_id: str) -> dict[str, Any] | None:
    aid = (action_id or "").strip().lower()
    for a in settings.get("actions") or []:
        if a.get("id") == aid:
            return a
    return None


def level_for_hp(hp: int, thresholds: list[int] | None = None) -> int:
    th = thresholds if thresholds and len(thresholds) >= LEVEL_COUNT else DEFAULT_LEVEL_THRESHOLDS
    level = 1
    for i, need in enumerate(th):
        if hp >= need:
            level = i + 1
        else:
            break
    return min(LEVEL_COUNT, max(1, level))


def progress_to_next(hp: int, thresholds: list[int] | None = None) -> tuple[int, int, int | None]:
    """Return (level, hp_into_level, hp_needed_for_next or None if max)."""
    th = thresholds if thresholds and len(thresholds) >= LEVEL_COUNT else DEFAULT_LEVEL_THRESHOLDS
    level = level_for_hp(hp, th)
    cur_need = th[level - 1]
    if level >= LEVEL_COUNT:
        return level, max(0, hp - cur_need), None
    next_need = th[level]
    return level, max(0, hp - cur_need), max(1, next_need - cur_need)


def deserved_reward_role_ids(settings: dict, level: int) -> set[int]:
    """Roles for all thresholds <= current level."""
    roles = settings.get("reward_roles") or {}
    out: set[int] = set()
    for lvl_s, rid in roles.items():
        try:
            lvl = int(lvl_s)
            role_id = int(rid)
        except (TypeError, ValueError):
            continue
        if 1 <= lvl <= level:
            out.add(role_id)
    return out


def all_reward_role_ids(settings: dict) -> set[int]:
    roles = settings.get("reward_roles") or {}
    out: set[int] = set()
    for rid in roles.values():
        try:
            out.add(int(rid))
        except (TypeError, ValueError):
            continue
    return out


def validate_channel_id(channel_id: str) -> str | None:
    if not isinstance(channel_id, str):
        return "invalid_channel"
    if not channel_id:
        return None
    if not channel_id.isdigit():
        return "invalid_channel"
    return None


def validate_role_id(role_id: str) -> str | None:
    if not isinstance(role_id, str):
        return "invalid_role"
    if not role_id:
        return None
    if not role_id.isdigit():
        return "invalid_role"
    return None


def ship_score(user_a: int, user_b: int) -> int:
    """Stable 0–100 compatibility score for a pair."""
    a, b = pair_ids(user_a, user_b)
    return (a ^ (b * 2654435761)) % 101


def ship_label_key(score: int) -> str:
    if score >= 90:
        return "relations.ship.tier.soulmates"
    if score >= 75:
        return "relations.ship.tier.hot"
    if score >= 50:
        return "relations.ship.tier.spark"
    if score >= 25:
        return "relations.ship.tier.friendzone"
    return "relations.ship.tier.awkward"


def apply_married_bonus(base_hp: int, bonus_percent: int) -> int:
    base = max(0, int(base_hp))
    pct = max(0, min(MARRIED_BONUS_MAX, int(bonus_percent)))
    return base + (base * pct) // 100


def days_together(married_at: float, *, now: float | None = None) -> int:
    ts = time.time() if now is None else now
    return max(0, int((ts - float(married_at)) // 86400))
