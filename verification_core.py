"""Ядро модуля «Верификация»: настройки панели «Я не бот» для новичков.

Без импорта discord — юнит-тестируемо напрямую (подход fun_core.py). Модуль
ПОЛНОСТЬЮ ВЫКЛЮЧЕН ПО УМОЛЧАНИЮ и ни на что не влияет, пока его явно не
включат тумблером в дашборде (раздел «Верификация») — это проверяется когом
на входе в on_member_join и в обработчике кнопки раньше любой другой логики.

Роль «Unverified» (если задана) выдаётся автоматически при входе и снимается
после клика; ограничение доступа к каналам для этой роли настраивается самим
администратором через права Discord, бот только назначает/снимает роль.
"""

import json
import os

CONFIG_FILE = "verification_config.json"

DEFAULT_WELCOME_TEXT = (
    "Нажмите кнопку ниже, чтобы подтвердить, что вы не бот, и получить доступ к серверу."
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
    tmp_path = CONFIG_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(tmp_path, CONFIG_FILE)
    _cache = data
    _cache_mtime = os.path.getmtime(CONFIG_FILE)


def get_settings() -> dict:
    """Настройки модуля с дефолтами. enabled=False по умолчанию — модуль не
    активен, пока администратор явно не включит его в дашборде.

    unverified_role_id/verified_role_id — строки, не числа: Discord ID
    (snowflake) — 18-19-значное число, превышает Number.MAX_SAFE_INTEGER во
    фронтенде, JS-числом его хранить нельзя (тихо портится при вводе)."""
    data = load_config()
    return {
        "enabled": bool(data.get("enabled", False)),
        "unverified_role_id": str(data.get("unverified_role_id", "") or ""),
        "verified_role_id": str(data.get("verified_role_id", "") or ""),
        "welcome_text": str(data.get("welcome_text", DEFAULT_WELCOME_TEXT)),
    }


def is_configured(settings: dict) -> bool:
    """Достаточно ли настроек, чтобы кнопка верификации могла отработать."""
    return bool(settings["verified_role_id"])
