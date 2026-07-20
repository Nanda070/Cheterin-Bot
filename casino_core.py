"""Ядро модуля «Казино»: слоты и монетка на серверную валюту.

Без импорта discord — юнит-тестируемо напрямую (подход fun_core.py/economy_core.py).
Списания/начисления выполняет economy_db — казино не хранит собственный баланс,
только настройки и правила игр.

Модель выплат: любой «честный» выигрыш (ставка × множитель) уменьшается на
house_edge_percent — единый параметр «преимущества казино», одинаково
применяемый к слотам и монетке, чтобы экономика сервера не раздувалась
бесконтрольно даже при активной игре.
"""

import json
import os
import random

CONFIG_FILE = "casino_config.json"

DEFAULT_HOUSE_EDGE_PERCENT = 5
DEFAULT_COOLDOWN_SEC = 5
DEFAULT_MIN_BET = 10
DEFAULT_MAX_BET = 5000

HOUSE_EDGE_MAX = 50
COOLDOWN_SEC_MAX = 300
BET_LIMIT_MAX = 1_000_000

# Барабан слотов: символы от частых/дешёвых к редким/дорогим.
SLOT_SYMBOLS = ("🍒", "🍋", "🔔", "⭐", "💎", "7️⃣")
SLOT_WEIGHTS = (30, 25, 20, 15, 7, 3)
SLOT_TRIPLE_MULTIPLIERS = {
    "🍒": 3, "🍋": 4, "🔔": 6, "⭐": 10, "💎": 25, "7️⃣": 50,
}
SLOT_PAIR_MULTIPLIER = 1.5
COINFLIP_MULTIPLIER = 2
COINFLIP_SIDES = ("орел", "решка")

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
    tmp_path = CONFIG_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(tmp_path, CONFIG_FILE)
    _cache = data
    _cache_mtime = os.path.getmtime(CONFIG_FILE)


def get_settings() -> dict:
    """Настройки модуля с дефолтами (выключен по умолчанию)."""
    data = load_config()
    return {
        "enabled": bool(data.get("enabled", False)),
        "house_edge_percent": int(data.get("house_edge_percent", DEFAULT_HOUSE_EDGE_PERCENT)),
        "cooldown_sec": int(data.get("cooldown_sec", DEFAULT_COOLDOWN_SEC)),
        "min_bet": int(data.get("min_bet", DEFAULT_MIN_BET)),
        "max_bet": int(data.get("max_bet", DEFAULT_MAX_BET)),
        "loss_roles": data.get("loss_roles", []),
    }


def bet_error(bet: int, balance: int, settings: dict) -> str | None:
    """None — ставка допустима, иначе текст ошибки для игрока."""
    if bet < settings["min_bet"]:
        return f"Минимальная ставка — {settings['min_bet']}."
    if settings["max_bet"] > 0 and bet > settings["max_bet"]:
        return f"Максимальная ставка — {settings['max_bet']}."
    if bet > balance:
        return f"Недостаточно средств: на балансе {balance}."
    return None


def payout_amount(bet: int, multiplier: float, house_edge_percent: int) -> int:
    """Выигрыш с учётом преимущества казино (округление вниз)."""
    if multiplier <= 0:
        return 0
    raw = bet * multiplier
    return int(raw * (100 - house_edge_percent) / 100)


# ────────────────────────── Слоты ──────────────────────────

def roll_slots() -> tuple[str, str, str]:
    """Три независимых барабана (с повторами), взвешенные по редкости символа."""
    reels = random.choices(SLOT_SYMBOLS, weights=SLOT_WEIGHTS, k=3)
    return reels[0], reels[1], reels[2]


def slot_multiplier(reels: tuple[str, str, str]) -> float:
    """0 — без выигрыша, SLOT_PAIR_MULTIPLIER — пара, множитель из таблицы — тройка."""
    a, b, c = reels
    if a == b == c:
        return SLOT_TRIPLE_MULTIPLIERS[a]
    if a == b or b == c or a == c:
        return SLOT_PAIR_MULTIPLIER
    return 0


# ────────────────────────── Монетка ──────────────────────────

def flip_coin() -> str:
    return random.choice(COINFLIP_SIDES)
