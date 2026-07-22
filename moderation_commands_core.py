"""Ядро команд модерации (/ban /kick /unban /clear): парсинг и форматирование срока
бана, нормализация причины, текст для Discord audit log.

Без импорта discord — юнит-тестируемо напрямую (тот же подход, что и automod_core.py).
"""

import re

import i18n

DURATION_RE = re.compile(r"^(\d+)([smhd])$")
DURATION_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
_DURATION_LABEL_KEYS = {"s": "moderation.duration.sec", "m": "moderation.duration.min", "h": "moderation.duration.hour", "d": "moderation.duration.day"}

CLEAR_MIN = 1
CLEAR_MAX = 999

# Discord ограничивает таймаут 28 днями — дальше API просто отклонит запрос.
MUTE_MAX_SECONDS = 28 * 86400

DEFAULT_REASON = i18n.t("moderation.default_reason")


def parse_duration(value: str, lang: str | None = None) -> int:
    """Секунды из строки вида 10m/2h/7d/30s. ValueError с понятным текстом при неверном формате."""
    lang = lang or i18n.DEFAULT_LANGUAGE
    match = DURATION_RE.match(value.strip().lower())
    if not match:
        raise ValueError(i18n.t("moderation.error.invalid_duration", lang))
    amount, unit = match.groups()
    return int(amount) * DURATION_UNITS[unit]


def parse_mute_duration(value: str, lang: str | None = None) -> int:
    """Как parse_duration, но с проверкой лимита Discord в 28 дней."""
    lang = lang or i18n.DEFAULT_LANGUAGE
    seconds = parse_duration(value, lang)
    if seconds <= 0:
        raise ValueError(i18n.t("moderation.error.mute_zero", lang))
    if seconds > MUTE_MAX_SECONDS:
        raise ValueError(i18n.t("moderation.error.mute_max_28d", lang))
    return seconds


def format_duration(value: str, lang: str | None = None) -> str:
    """Человекочитаемое представление уже провалидированной строки длительности (10m -> '10 мин.')."""
    lang = lang or i18n.DEFAULT_LANGUAGE
    match = DURATION_RE.match(value.strip().lower())
    amount, unit = match.groups()
    return i18n.t(_DURATION_LABEL_KEYS[unit], lang, amount=amount)


def normalize_reason(reason: str | None, lang: str | None = None) -> str:
    lang = lang or i18n.DEFAULT_LANGUAGE
    reason = (reason or "").strip()
    return reason or i18n.t("moderation.default_reason", lang)


def command_reason(reason: str, moderator_name: str, moderator_id: int, lang: str | None = None) -> str:
    """Причина, которая уходит в нативный Discord audit log — там же видно, кто и когда."""
    lang = lang or i18n.DEFAULT_LANGUAGE
    return i18n.t("moderation.command_reason", lang, reason=reason, name=moderator_name, id=moderator_id)


def is_valid_clear_count(number: int) -> bool:
    return CLEAR_MIN <= number <= CLEAR_MAX
