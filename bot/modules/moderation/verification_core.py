"""Ядро модуля «Верификация»: настройки панели «Я не бот» / согласия с правилами.

Без импорта discord — юнит-тестируемо напрямую (подход fun_core.py). Модуль
ПОЛНОСТЬЮ ВЫКЛЮЧЕН ПО УМОЛЧАНИЮ и ни на что не влияет, пока его явно не
включат тумблером в дашборде (раздел «Верификация») — это проверяется когом
на входе в on_member_join и в обработчике кнопки раньше любой другой логики.

Роль «Unverified» (если задана) выдаётся автоматически при входе и снимается
после клика; ограничение доступа к каналам для этой роли настраивается самим
администратором через права Discord, бот только назначает/снимает роль.

Опционально: режим согласия с правилами (другая подпись кнопки) и повторное
подтверждение каждые N дней (роль снимается, участник снова жмёт кнопку).
"""

from datetime import datetime, timedelta, timezone

import bot.core.settings_db as settings_db

import bot.core.i18n as i18n

MODULE_NAME = "verification"

# Legacy RU default kept for migration detection only.
DEFAULT_WELCOME_TEXT = (
    "Нажмите кнопку ниже, чтобы подтвердить, что вы не бот, и получить доступ к серверу."
)

DEFAULT_REVERIFY_DAYS = 30
MIN_REVERIFY_DAYS = 1
MAX_REVERIFY_DAYS = 365


def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def clamp_reverify_days(value) -> int:
    try:
        days = int(value)
    except (TypeError, ValueError):
        return DEFAULT_REVERIFY_DAYS
    return max(MIN_REVERIFY_DAYS, min(MAX_REVERIFY_DAYS, days))


def resolve_welcome_text(
    guild_id: int,
    stored: str | None = None,
    *,
    rules_consent_enabled: bool = False,
) -> str:
    raw = (stored if stored is not None else "").strip()
    if not raw or raw == DEFAULT_WELCOME_TEXT:
        key = (
            "verification.panel_rules"
            if rules_consent_enabled
            else "verification.panel_welcome"
        )
        return i18n.guild_t(guild_id, key)
    return raw


def get_settings(guild_id: int) -> dict:
    """Настройки модуля сервера с дефолтами. enabled=False по умолчанию — модуль не
    активен, пока администратор явно не включит его в дашборде.

    unverified_role_id/verified_role_id — строки, не числа: Discord ID
    (snowflake) — 18-19-значное число, превышает Number.MAX_SAFE_INTEGER во
    фронтенде, JS-числом его хранить нельзя (тихо портится при вводе)."""
    data = settings_db.get(guild_id, MODULE_NAME)
    rules_consent_enabled = bool(data.get("rules_consent_enabled", False))
    stored_welcome = str(data.get("welcome_text", "") or "")
    return {
        "enabled": bool(data.get("enabled", False)),
        "unverified_role_id": str(data.get("unverified_role_id", "") or ""),
        "verified_role_id": str(data.get("verified_role_id", "") or ""),
        "welcome_text": resolve_welcome_text(
            guild_id, stored_welcome, rules_consent_enabled=rules_consent_enabled
        ),
        "rules_consent_enabled": rules_consent_enabled,
        "reverify_enabled": bool(data.get("reverify_enabled", False)),
        "reverify_days": clamp_reverify_days(data.get("reverify_days", DEFAULT_REVERIFY_DAYS)),
    }


def is_configured(settings: dict) -> bool:
    """Достаточно ли настроек, чтобы кнопка верификации могла отработать."""
    return bool(settings["verified_role_id"])


def parse_verified_at(value: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_consent_expired(
    verified_at: str | datetime,
    settings: dict,
    now: datetime | None = None,
) -> bool:
    """True, если включено повторное подтверждение и срок N дней истёк."""
    if not settings.get("reverify_enabled"):
        return False
    if isinstance(verified_at, str):
        verified_at = parse_verified_at(verified_at)
    if verified_at is None:
        return True
    now = now or datetime.now(timezone.utc)
    days = clamp_reverify_days(settings.get("reverify_days", DEFAULT_REVERIFY_DAYS))
    return now >= verified_at + timedelta(days=days)


def has_valid_consent(
    consent: dict | None,
    settings: dict,
    now: datetime | None = None,
) -> bool:
    """Есть ли неистёкшее согласие (без учёта Discord-ролей)."""
    if not consent:
        return False
    return not is_consent_expired(consent["verified_at"], settings, now=now)
