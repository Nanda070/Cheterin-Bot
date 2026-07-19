"""Ядро команд модерации (/ban /kick /unban /clear): парсинг и форматирование срока
бана, нормализация причины, текст для Discord audit log.

Без импорта discord — юнит-тестируемо напрямую (тот же подход, что и automod_core.py).
"""

import re

DURATION_RE = re.compile(r"^(\d+)([smhd])$")
DURATION_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
DURATION_LABELS = {"s": "сек.", "m": "мин.", "h": "ч.", "d": "дн."}

CLEAR_MIN = 1
CLEAR_MAX = 999

# Discord ограничивает таймаут 28 днями — дальше API просто отклонит запрос.
MUTE_MAX_SECONDS = 28 * 86400

DEFAULT_REASON = "Причина не указана"


def parse_duration(value: str) -> int:
    """Секунды из строки вида 10m/2h/7d/30s. ValueError с понятным текстом при неверном формате."""
    match = DURATION_RE.match(value.strip().lower())
    if not match:
        raise ValueError("Неверный формат срока. Используйте число + единицу (s/m/h/d), например 10m, 2h, 7d.")
    amount, unit = match.groups()
    return int(amount) * DURATION_UNITS[unit]


def parse_mute_duration(value: str) -> int:
    """Как parse_duration, но с проверкой лимита Discord в 28 дней."""
    seconds = parse_duration(value)
    if seconds <= 0:
        raise ValueError("Срок таймаута должен быть больше нуля.")
    if seconds > MUTE_MAX_SECONDS:
        raise ValueError("Discord не позволяет выдать таймаут дольше 28 дней.")
    return seconds


def format_duration(value: str) -> str:
    """Человекочитаемое представление уже провалидированной строки длительности (10m -> '10 мин.')."""
    match = DURATION_RE.match(value.strip().lower())
    amount, unit = match.groups()
    return f"{amount} {DURATION_LABELS[unit]}"


def normalize_reason(reason: str | None) -> str:
    reason = (reason or "").strip()
    return reason or DEFAULT_REASON


def command_reason(reason: str, moderator_name: str, moderator_id: int) -> str:
    """Причина, которая уходит в нативный Discord audit log — там же видно, кто и когда."""
    return f"{reason} — команда: {moderator_name} ({moderator_id})"


def is_valid_clear_count(number: int) -> bool:
    return CLEAR_MIN <= number <= CLEAR_MAX
