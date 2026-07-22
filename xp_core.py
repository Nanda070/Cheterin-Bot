"""Ядро системы уровней: конфигурация, формула уровней, награды, шаблоны.

Механика повторяет JuniperBot:
- текст: 15–25 XP за сообщение, не чаще раза в минуту, только в целевых каналах;
- войс: XP получают только «активные» (микрофон и звук включены, не бот) и только
  когда активных в канале минимум двое; опыт накопительный — при N активных каждый
  получает N-кратный опыт (N ограничен настройкой max_count);
- уровни по возрастающей кривой, потолок 999;
- два трека наград: роли за уровень и роли за суммарное время в войсе.
"""

import random

import i18n
import settings_db

MODULE_NAME = "xp"
import os
os.makedirs("card_bgs", exist_ok=True)

def get_card_bg_path(guild_id: int) -> str:
    return f"card_bgs/card_bg_{guild_id}.png"

MAX_LEVEL = 999

XP_ADMIN_MIN = 0
XP_ADMIN_MAX = 2_000_000_000  # кап ручного изменения XP (команда /xp и дашборд)

TEXT_XP_MIN = 15
TEXT_XP_MAX = 25
TEXT_XP_COOLDOWN = 60  # секунд

VOICE_XP_PER_ACTIVE_MINUTE = 6  # дефолт базового XP за минуту на одного активного (паритет с Juniper)

DEFAULT_ANNOUNCE_TEMPLATE_RU = (
    "Поздравляю {{member}}! 🎉\n"
    "Вы достигли **{{level}}** уровня. Спасибо за вашу активность на сервере!"
)
DEFAULT_ANNOUNCE_TEMPLATE_EN = (
    "Congratulations {{member}}! 🎉\n"
    "You reached **{{level}}** level. Thank you for your activity on the server!"
)
DEFAULT_ANNOUNCE_TEMPLATE = DEFAULT_ANNOUNCE_TEMPLATE_RU

def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def _default_announce_template(guild_id: int) -> str:
    return i18n.t("xp.default_announce_template", i18n.lang_for(guild_id))


def get_settings(guild_id: int) -> dict:
    """Настройки модуля сервера с дефолтами (модуль выключен по умолчанию)."""
    data = settings_db.get(guild_id, MODULE_NAME)
    text = data.get("text", {})
    voice = data.get("voice", {})
    announce = data.get("announce", {})
    stored_template = announce.get("template")
    announce_template = str(stored_template) if stored_template else _default_announce_template(guild_id)
    return {
        "enabled": bool(data.get("enabled", False)),
        "public_leaderboard": bool(data.get("public_leaderboard", True)),
        "reset_on_leave": bool(data.get("reset_on_leave", False)),
        "text": {
            "enabled": bool(text.get("enabled", True)),
            "ignored_roles": [str(v) for v in text.get("ignored_roles", [])],
            "target_channels": [str(v) for v in text.get("target_channels", [])],
            "ignored_channels": [str(v) for v in text.get("ignored_channels", [])],
            "multiplier": int(text.get("multiplier", 100)),
        },
        "voice": {
            "enabled": bool(voice.get("enabled", True)),
            "ignored_roles": [str(v) for v in voice.get("ignored_roles", [])],
            "target_channels": [str(v) for v in voice.get("target_channels", [])],
            "ignored_channels": [str(v) for v in voice.get("ignored_channels", [])],
            "multiplier": int(voice.get("multiplier", 100)),
            "max_count": int(voice.get("max_count", 5)),
            "base_per_minute": int(voice.get("base_per_minute", VOICE_XP_PER_ACTIVE_MINUTE)),
            "member_multipliers": {
                str(k): int(v) for k, v in dict(voice.get("member_multipliers", {})).items()
            },
        },
        "announce": {
            "enabled": bool(announce.get("enabled", True)),
            "channel_id": str(announce.get("channel_id") or ""),
            "template": announce_template,
            "delete_after": int(announce.get("delete_after", 0)),
        },
        "level_rewards": [
            {"level": int(r.get("level", 0)), "role_ids": [str(v) for v in r.get("role_ids", [])]}
            for r in data.get("level_rewards", [])
        ],
        "voice_rewards": [
            {"minutes": int(r.get("minutes", 0)), "role_ids": [str(v) for v in r.get("role_ids", [])]}
            for r in data.get("voice_rewards", [])
        ],
    }


# ────────────────────────── Формула уровней ──────────────────────────

def xp_for_level_step(level: int) -> int:
    """Сколько XP нужно, чтобы перейти с уровня `level` на `level + 1`."""
    return 5 * level * level + 50 * level + 100


def total_xp_for_level(level: int) -> int:
    """Суммарный XP, необходимый для достижения уровня `level`."""
    level = max(0, min(level, MAX_LEVEL))
    total = 0
    for l in range(level):
        total += xp_for_level_step(l)
    return total


def level_from_xp(xp: int) -> int:
    level = 0
    remaining = max(0, xp)
    while level < MAX_LEVEL:
        step = xp_for_level_step(level)
        if remaining < step:
            break
        remaining -= step
        level += 1
    return level


def level_progress(xp: int) -> tuple[int, int, int]:
    """(уровень, XP внутри уровня, XP до следующего уровня)."""
    level = level_from_xp(xp)
    into = xp - total_xp_for_level(level)
    step = xp_for_level_step(level) if level < MAX_LEVEL else 0
    return level, into, step


def roll_text_xp(multiplier: int) -> int:
    base = random.randint(TEXT_XP_MIN, TEXT_XP_MAX)
    return max(0, round(base * multiplier / 100))


def voice_xp_per_minute(
    active_count: int,
    max_count: int,
    multiplier: int,
    base_per_minute: int = VOICE_XP_PER_ACTIVE_MINUTE,
    member_multiplier: int = 100,
) -> int:
    """XP за минуту голосовой активности при active_count активных участниках.

    Формула Juniper: база × число активных (кап max_count) × общий множитель ×
    индивидуальный множитель участника. Минимум два активных участника.
    """
    if active_count < 2:
        return 0
    effective = min(active_count, max_count) if max_count > 0 else active_count
    return max(0, round(base_per_minute * effective * multiplier / 100 * member_multiplier / 100))


def voice_member_multiplier(scope: dict, user_id: int) -> int:
    """Индивидуальный множитель участника (в процентах, 100 = без изменения)."""
    return int(scope.get("member_multipliers", {}).get(str(user_id), 100))


# ────────────────────────── Награды ──────────────────────────

def deserved_level_roles(settings: dict, level: int) -> set[str]:
    result: set[str] = set()
    for reward in settings["level_rewards"]:
        if reward["level"] <= level:
            result.update(reward["role_ids"])
    return result


def deserved_voice_roles(settings: dict, voice_seconds: int) -> set[str]:
    minutes = voice_seconds // 60
    result: set[str] = set()
    for reward in settings["voice_rewards"]:
        if reward["minutes"] <= minutes:
            result.update(reward["role_ids"])
    return result


def all_reward_role_ids(settings: dict) -> set[str]:
    result: set[str] = set()
    for reward in settings["level_rewards"]:
        result.update(reward["role_ids"])
    for reward in settings["voice_rewards"]:
        result.update(reward["role_ids"])
    return result


# ────────────────────────── Шаблон уведомления ──────────────────────────

def render_announce(template: str, member_mention: str, level: int, roles_added: list[str], roles_removed: list[str]) -> str:
    text = template
    replacements = {
        "{{member}}": member_mention,
        "{{level}}": str(level),
        "{{member.rank.level}}": str(level),  # совместимость с шаблонами Juniper
        "{{roles_added}}": ", ".join(roles_added) if roles_added else "",
        "{{roles_removed}}": ", ".join(roles_removed) if roles_removed else "",
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text.strip()


def format_voice_time(seconds: int, lang: str = "ru") -> str:
    """Человекочитаемое время войса: «2 нед. 1 д. 3 ч.» / «2 wk 1 d 3 h»."""
    minutes = seconds // 60
    weeks, rem = divmod(minutes, 7 * 24 * 60)
    days, rem = divmod(rem, 24 * 60)
    hours, mins = divmod(rem, 60)
    parts = []
    if weeks:
        parts.append(i18n.t("xp.voice_time.week", lang, n=weeks))
    if days:
        parts.append(i18n.t("xp.voice_time.day", lang, n=days))
    if hours:
        parts.append(i18n.t("xp.voice_time.hour", lang, n=hours))
    if mins or not parts:
        parts.append(i18n.t("xp.voice_time.min", lang, n=mins))
    return " ".join(parts)
