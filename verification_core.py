"""Ядро модуля «Верификация»: настройки панели «Я не бот» для новичков.

Без импорта discord — юнит-тестируемо напрямую (подход fun_core.py). Модуль
ПОЛНОСТЬЮ ВЫКЛЮЧЕН ПО УМОЛЧАНИЮ и ни на что не влияет, пока его явно не
включат тумблером в дашборде (раздел «Верификация») — это проверяется когом
на входе в on_member_join и в обработчике кнопки раньше любой другой логики.

Роль «Unverified» (если задана) выдаётся автоматически при входе и снимается
после клика; ограничение доступа к каналам для этой роли настраивается самим
администратором через права Discord, бот только назначает/снимает роль.
"""

import settings_db

MODULE_NAME = "verification"

DEFAULT_WELCOME_TEXT = (
    "Нажмите кнопку ниже, чтобы подтвердить, что вы не бот, и получить доступ к серверу."
)


def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    """Настройки модуля сервера с дефолтами. enabled=False по умолчанию — модуль не
    активен, пока администратор явно не включит его в дашборде.

    unverified_role_id/verified_role_id — строки, не числа: Discord ID
    (snowflake) — 18-19-значное число, превышает Number.MAX_SAFE_INTEGER во
    фронтенде, JS-числом его хранить нельзя (тихо портится при вводе)."""
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "enabled": bool(data.get("enabled", False)),
        "unverified_role_id": str(data.get("unverified_role_id", "") or ""),
        "verified_role_id": str(data.get("verified_role_id", "") or ""),
        "welcome_text": str(data.get("welcome_text", DEFAULT_WELCOME_TEXT)),
    }


def is_configured(settings: dict) -> bool:
    """Достаточно ли настроек, чтобы кнопка верификации могла отработать."""
    return bool(settings["verified_role_id"])
