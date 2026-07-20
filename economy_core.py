"""Ядро модуля «Экономика»: настройки валюты, курс от XP, магазин ролей.

Без импорта discord — юнит-тестируемо напрямую (подход fun_core.py).
Монеты начисляются как процент от заработанного XP (текст и войс отдельно),
поэтому экономика автоматически уважает все правила XP-модуля: кулдауны,
игнорируемые каналы/роли, множители.
"""

import json
import os
import re
from datetime import date, datetime, timedelta, timezone

import economy_db

COLOR_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
SHOP_ITEM_TYPES = ("role", "frame_color", "title")
TITLE_TEXT_MAX = 30

CONFIG_FILE = "economy_config.json"

DEFAULT_CURRENCY_NAME = "монеты"
DEFAULT_CURRENCY_EMOJI = "🪙"
DEFAULT_TEXT_RATE_PERCENT = 50   # монет за XP: 50% => 10 XP -> 5 монет
DEFAULT_VOICE_RATE_PERCENT = 50
DEFAULT_TRANSFER_FEE_PERCENT = 0
DEFAULT_ROULETTE_MAX_BET = 1000
DEFAULT_DAILY_BONUS_ENABLED = True
DEFAULT_DAILY_BASE_AMOUNT = 50
DEFAULT_DAILY_GROWTH_PER_DAY = 25
DEFAULT_DAILY_MAX_STREAK_DAYS = 7

RATE_PERCENT_MAX = 1000
TRANSFER_FEE_MAX = 50
ROULETTE_BET_MAX_LIMIT = 1_000_000
SHOP_PRICE_MAX = 10_000_000
SHOP_ITEMS_MAX = 25  # лимит кнопок в одном сообщении Discord
BALANCE_ADMIN_MAX = 2_000_000_000
DAILY_AMOUNT_MAX = 1_000_000
DAILY_STREAK_DAYS_MAX = 365

_MSK = timezone(timedelta(hours=3))

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


def _normalize_shop_item(item: dict) -> dict:
    item_type = item.get("type", "role")
    if item_type not in SHOP_ITEM_TYPES:
        item_type = "role"
    # role_id — строка: Discord ID (snowflake) — 18-19-значное число, превышает
    # Number.MAX_SAFE_INTEGER во фронтенде; JSON/JS-числом его хранить нельзя,
    # иначе значение тихо портится при вводе (см. wordle_core.channel_id).
    return {
        "id": str(item.get("id", "")),
        "type": item_type,
        "role_id": str(item.get("role_id", "") or ""),
        "color_hex": str(item.get("color_hex", "")),
        "title_text": str(item.get("title_text", "")),
        "price": int(item.get("price", 0)),
        "name": str(item.get("name", "")),
    }


def get_settings() -> dict:
    """Настройки модуля с дефолтами (выключен по умолчанию)."""
    data = load_config()
    return {
        "enabled": bool(data.get("enabled", False)),
        "currency_name": str(data.get("currency_name", DEFAULT_CURRENCY_NAME)),
        "currency_emoji": str(data.get("currency_emoji", DEFAULT_CURRENCY_EMOJI)),
        "text_rate_percent": int(data.get("text_rate_percent", DEFAULT_TEXT_RATE_PERCENT)),
        "voice_rate_percent": int(data.get("voice_rate_percent", DEFAULT_VOICE_RATE_PERCENT)),
        "transfer_enabled": bool(data.get("transfer_enabled", True)),
        "transfer_fee_percent": int(data.get("transfer_fee_percent", DEFAULT_TRANSFER_FEE_PERCENT)),
        "roulette_bets_enabled": bool(data.get("roulette_bets_enabled", True)),
        "roulette_max_bet": int(data.get("roulette_max_bet", DEFAULT_ROULETTE_MAX_BET)),
        "daily_bonus_enabled": bool(data.get("daily_bonus_enabled", DEFAULT_DAILY_BONUS_ENABLED)),
        "daily_base_amount": int(data.get("daily_base_amount", DEFAULT_DAILY_BASE_AMOUNT)),
        "daily_growth_per_day": int(data.get("daily_growth_per_day", DEFAULT_DAILY_GROWTH_PER_DAY)),
        "daily_max_streak_days": int(data.get("daily_max_streak_days", DEFAULT_DAILY_MAX_STREAK_DAYS)),
        "shop_items": [_normalize_shop_item(i) for i in data.get("shop_items", []) if isinstance(i, dict)],
    }


def format_amount(amount: int, settings: dict | None = None) -> str:
    settings = settings or get_settings()
    return f"{amount} {settings['currency_emoji']}"


def coins_from_xp(xp_amount: int, rate_percent: int) -> int:
    """Монеты за заработанный XP (округление вниз, не меньше 0)."""
    if xp_amount <= 0 or rate_percent <= 0:
        return 0
    return xp_amount * rate_percent // 100


def award_for_xp(user_id: int, xp_amount: int, kind: str) -> int:
    """Хук из xp.py: начислить монеты за только что выданный XP.

    kind — "text" или "voice". Возвращает начисленную сумму (0, если модуль
    выключен или по курсу вышло 0).
    """
    settings = get_settings()
    if not settings["enabled"]:
        return 0
    rate = settings["text_rate_percent"] if kind == "text" else settings["voice_rate_percent"]
    coins = coins_from_xp(xp_amount, rate)
    if coins > 0:
        economy_db.add(user_id, coins, f"{kind}_xp")
    return coins


def transfer_fee(amount: int, fee_percent: int) -> int:
    """Комиссия перевода (округление вверх, чтобы 1% от 50 не был нулём)."""
    if fee_percent <= 0:
        return 0
    return -(-amount * fee_percent // 100)


def bet_error(bet: int, balance: int, settings: dict) -> str | None:
    """None — ставка допустима, иначе текст ошибки для игрока."""
    if not settings["roulette_bets_enabled"]:
        return "Ставки в рулетке отключены."
    if bet < 1:
        return "Ставка должна быть не меньше 1."
    max_bet = settings["roulette_max_bet"]
    if max_bet > 0 and bet > max_bet:
        return f"Максимальная ставка — {format_amount(max_bet, settings)}."
    if bet > balance:
        return f"Недостаточно средств: на балансе {format_amount(balance, settings)}."
    return None


def find_shop_item(settings: dict, item_id: str) -> dict | None:
    return next((i for i in settings["shop_items"] if i["id"] == item_id), None)


# ────────────────────────── Ежедневный бонус (/daily) ──────────────────────────

def today_msk_date() -> str:
    """Календарная дата по МСК (ISO), тот же принцип смены дня, что у Вордла."""
    return datetime.now(_MSK).date().isoformat()


def daily_bonus_amount(streak: int, settings: dict) -> int:
    """Линейный рост от base до base + growth*(max_days-1), дальше — плато."""
    effective_day = min(max(streak, 1), settings["daily_max_streak_days"])
    return settings["daily_base_amount"] + settings["daily_growth_per_day"] * (effective_day - 1)


def claim_daily_bonus(user_id: int, today: str | None = None) -> dict:
    """Забрать бонус за сегодня. Стрик продолжается, если предыдущий клейм был
    вчера; пропуск дня (или первый визит) начинает стрик заново с 1.

    today — только для тестов; в бою всегда берётся реальная дата по МСК.
    """
    today = today or today_msk_date()
    settings = get_settings()
    state = economy_db.get_daily_bonus(user_id)

    if state["last_claim_date"] == today:
        return {
            "claimed": False, "already_claimed": True,
            "streak": state["streak"], "amount": 0, "balance": economy_db.get_balance(user_id),
        }

    yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
    streak = state["streak"] + 1 if state["last_claim_date"] == yesterday else 1
    amount = daily_bonus_amount(streak, settings)
    balance = economy_db.add(user_id, amount, "daily_bonus")
    economy_db.set_daily_bonus(user_id, streak, today)

    return {"claimed": True, "already_claimed": False, "streak": streak, "amount": amount, "balance": balance}
