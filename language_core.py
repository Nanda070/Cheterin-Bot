"""Язык бота для сервера (Фаза 3.1 MULTIGUILD_PLAN.md).

Хранится в settings.db (guild_id, module='language') как {"code": "ru"|"en"}.
"""

import settings_db

MODULE = "language"
DEFAULT_LANGUAGE = "ru"
SUPPORTED_LANGUAGES = frozenset({"ru", "en"})


def get_language(guild_id: int) -> str:
    data = settings_db.get(guild_id, MODULE, {})
    code = data.get("code", DEFAULT_LANGUAGE)
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def set_language(guild_id: int, code: str) -> str:
    if code not in SUPPORTED_LANGUAGES:
        raise ValueError("unsupported_language")
    settings_db.put(guild_id, MODULE, {"code": code})
    return code


def get_settings(guild_id: int) -> dict:
    return {"code": get_language(guild_id)}
