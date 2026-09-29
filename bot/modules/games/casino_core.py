"""Ядро модуля «Казино»: слоты, монетка и блэкджек на серверную валюту.

Без импорта discord — юнит-тестируемо напрямую (подход fun_core.py/economy_core.py).
Списания/начисления выполняет economy_db — казино не хранит собственный баланс,
только настройки и правила игр.

Модель выплат: любой «честный» выигрыш (ставка × множитель) уменьшается на
house_edge_percent — единый параметр «преимущества казино», одинаково
применяемый к слотам и монетке, чтобы экономика сервера не раздувалась
бесконтрольно даже при активной игре.
"""

import random

import bot.core.i18n as i18n
import bot.core.settings_db as settings_db

MODULE_NAME = "casino"

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

def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    """Настройки модуля сервера с дефолтами (выключен по умолчанию)."""
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "enabled": bool(data.get("enabled", False)),
        "house_edge_percent": int(data.get("house_edge_percent", DEFAULT_HOUSE_EDGE_PERCENT)),
        "cooldown_sec": int(data.get("cooldown_sec", DEFAULT_COOLDOWN_SEC)),
        "min_bet": int(data.get("min_bet", DEFAULT_MIN_BET)),
        "max_bet": int(data.get("max_bet", DEFAULT_MAX_BET)),
        "loss_roles": data.get("loss_roles", []),
    }


def bet_error(
    bet: int,
    balance: int,
    settings: dict,
    *,
    lang: str | None = None,
    balance_display: str | None = None,
) -> str | None:
    """None — ставка допустима, иначе текст ошибки для игрока."""
    lang = lang or i18n.DEFAULT_LANGUAGE
    if bet < settings["min_bet"]:
        return i18n.t("casino.bet_min", lang, min=settings["min_bet"])
    if settings["max_bet"] > 0 and bet > settings["max_bet"]:
        return i18n.t("casino.bet_max", lang, max=settings["max_bet"])
    if bet > balance:
        return i18n.t(
            "casino.bet_insufficient",
            lang,
            balance=balance_display if balance_display is not None else balance,
        )
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
