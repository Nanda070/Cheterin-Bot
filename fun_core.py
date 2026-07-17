"""Ядро модуля «Развлечения»: настройки рулеток.

Без импорта discord — юнит-тестируемо напрямую (тот же подход, что и bunker_core.py).
"""

import json
import os
import random

CONFIG_FILE = "fun_config.json"

ROULETTE_CHAMBERS = 6  # барабан револьвера: 6 камор, 1 патрон
DEFAULT_ROULETTE_TIMEOUT_MINUTES = 1
DEFAULT_ROULETTE_COOLDOWN_SEC = 30
TIMEOUT_MINUTES_MAX = 1440  # 24 часа — развлекательный кап, далеко до лимита Discord (28 дней)
COOLDOWN_SEC_MAX = 3600

# Запасной пул, если на сервере нет кастомных эмодзи.
FALLBACK_EMOJIS = (
    "🎲", "🎰", "🎯", "🃏", "🎁", "🍀", "🔥", "⭐", "💎", "🍒",
    "🍋", "🔔", "💰", "🚀", "🐸", "🦄", "👑", "⚡", "🌈", "🎉",
)

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
        "roulette_timeout_minutes": int(data.get("roulette_timeout_minutes", DEFAULT_ROULETTE_TIMEOUT_MINUTES)),
        "roulette_cooldown_sec": int(data.get("roulette_cooldown_sec", DEFAULT_ROULETTE_COOLDOWN_SEC)),
    }


def spin_trigger() -> bool:
    """Один спуск курка: True — выстрел (1 шанс из ROULETTE_CHAMBERS)."""
    return random.randrange(ROULETTE_CHAMBERS) == 0


def pick_emoji(guild_emojis: list) -> str:
    """Случайное эмодзи сервера; если кастомных нет — из запасного пула."""
    pool = list(guild_emojis) or list(FALLBACK_EMOJIS)
    return str(random.choice(pool))
