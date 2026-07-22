"""Lightweight i18n helper for bot messages (Phase 3)."""

from __future__ import annotations

import random

import language_core
from locales import en, ru

_LOCALES: dict[str, dict[str, str]] = {
    "ru": ru.MESSAGES,
    "en": en.MESSAGES,
}

DEFAULT_LANGUAGE = language_core.DEFAULT_LANGUAGE


def lang_for(guild_id: int | None) -> str:
    if guild_id is None:
        return DEFAULT_LANGUAGE
    return language_core.get_language(guild_id)


def t(key: str, lang: str = DEFAULT_LANGUAGE, **fmt) -> str:
    """Return translated string; falls back to Russian, then to the key itself."""
    messages = _LOCALES.get(lang) or _LOCALES[DEFAULT_LANGUAGE]
    text = messages.get(key) or _LOCALES[DEFAULT_LANGUAGE].get(key) or key
    if not fmt:
        return text
    try:
        return text.format(**fmt)
    except (KeyError, ValueError):
        return text


def guild_t(guild_id: int | None, key: str, **fmt) -> str:
    """Translate using the bot language configured for the guild."""
    return t(key, lang_for(guild_id), **fmt)


def module_name(module_key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    return t(f"module.{module_key}", lang)


def module_disabled(lang: str, module_key: str) -> str:
    return t("error.module_disabled_named", lang, module=module_name(module_key, lang))


def module_disabled_guild(guild_id: int | None, module_key: str) -> str:
    return module_disabled(lang_for(guild_id), module_key)


def module_disabled_dashboard_hint(lang: str, module_key: str) -> str:
    return t("error.module_disabled_dashboard_hint", lang, module=module_name(module_key, lang))


def pick_random(key_prefix: str, lang: str, count: int) -> str:
    """Pick one of ``{prefix}.1`` … ``{prefix}.{count}`` at random."""
    index = random.randint(1, count)
    return t(f"{key_prefix}.{index}", lang)
