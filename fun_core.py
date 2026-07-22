"""Ядро модуля «Развлечения»: настройки рулеток.

Без импорта discord — юнит-тестируемо напрямую (тот же подход, что и bunker_core.py).
Настройки хранятся per-guild в settings_db (Фаза 2.1 MULTIGUILD_PLAN.md).
"""

import random

import settings_db

MODULE_NAME = "fun"  # должно совпадать с ключом в settings_migration.MODULE_FILE_MAP

ROULETTE_CHAMBERS = 6  # барабан револьвера: 6 камор, обычно 1 патрон
EMPTY_CYLINDER_CHANCE = 0.08  # 8% — барабан вообще без патрона (можно пройти 6/6)
DEFAULT_ROULETTE_TIMEOUT_MINUTES = 1
DEFAULT_ROULETTE_COOLDOWN_SEC = 30
TIMEOUT_MINUTES_MAX = 1440  # 24 часа — развлекательный кап, далеко до лимита Discord (28 дней)
COOLDOWN_SEC_MAX = 3600

DEFAULT_AUTO_EMOJI_CHANCE_PERCENT = 4
DEFAULT_AUTO_EMOJI_MIN_INTERVAL_SEC = 300
DEFAULT_AUTO_EMOJI_REMOVE_AFTER_SEC = 120
AUTO_EMOJI_MIN_INTERVAL_MAX = 86400
AUTO_EMOJI_REMOVE_AFTER_MAX = 3600

# Запасной пул, если на сервере нет кастомных эмодзи.
FALLBACK_EMOJIS = (
    "🎲", "🎰", "🎯", "🃏", "🎁", "🍀", "🔥", "⭐", "💎", "🍒",
    "🍋", "🔔", "💰", "🚀", "🐸", "🦄", "👑", "⚡", "🌈", "🎉",
)

def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    """Настройки модуля сервера с дефолтами (выключен по умолчанию)."""
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "enabled": bool(data.get("enabled", False)),
        "roulette_timeout_minutes": int(data.get("roulette_timeout_minutes", DEFAULT_ROULETTE_TIMEOUT_MINUTES)),
        "roulette_cooldown_sec": int(data.get("roulette_cooldown_sec", DEFAULT_ROULETTE_COOLDOWN_SEC)),
        "auto_emoji_enabled": bool(data.get("auto_emoji_enabled", False)),
        "auto_emoji_chance_percent": int(data.get("auto_emoji_chance_percent", DEFAULT_AUTO_EMOJI_CHANCE_PERCENT)),
        "auto_emoji_min_interval_sec": int(data.get("auto_emoji_min_interval_sec", DEFAULT_AUTO_EMOJI_MIN_INTERVAL_SEC)),
        "auto_emoji_remove_after_sec": int(data.get("auto_emoji_remove_after_sec", DEFAULT_AUTO_EMOJI_REMOVE_AFTER_SEC)),
    }


def auto_emoji_roll(chance_percent: int) -> bool:
    """Ставить ли авто-эмодзи на это сообщение (шанс в процентах)."""
    if chance_percent <= 0:
        return False
    return random.random() * 100 < chance_percent


def roll_empty_cylinder() -> bool:
    """При зарядке нового барабана: True — патронов нет вообще (8%)."""
    return random.random() < EMPTY_CYLINDER_CHANCE


def spin_trigger(consecutive_clicks: int = 0, empty_cylinder: bool = False) -> bool:
    """Один спуск курка: True — выстрел.

    Барабан НЕ прокручивается заново после осечки: с каждым «щёлк» камор
    остаётся меньше, шанс растёт 1/6 → 1/5 → … → 1/1. На шестом нажатии
    при обычной зарядке выстрел гарантирован.

    empty_cylinder=True (8% при зарядке): патрона нет — все 6 камор пустые,
    после 6/6 барабан перезаряжается заново.
    """
    if empty_cylinder:
        return False
    chambers_left = max(1, ROULETTE_CHAMBERS - consecutive_clicks)
    return random.randrange(chambers_left) == 0


def pick_emoji(guild_emojis: list) -> str:
    """Случайное эмодзи сервера; если кастомных нет — из запасного пула."""
    pool = list(guild_emojis) or list(FALLBACK_EMOJIS)
    return str(random.choice(pool))
