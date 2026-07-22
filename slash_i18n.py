"""Slash command localizations (Phase 3.2(3)).

discord.py only sends name/description localizations when a CommandTree Translator
is installed — setting ``command.name_localizations`` alone is ignored by ``sync()``.
"""

from __future__ import annotations

from discord import Locale
from discord import app_commands
from discord.app_commands import (
    TranslationContextLocation,
    TranslationContextTypes,
    Translator,
    locale_str,
)

import i18n

_LANG_BY_LOCALE: dict[Locale, str] = {
    Locale.american_english: "en",
    Locale.british_english: "en",
    Locale.russian: "ru",
}


def _locale_lang(locale: Locale) -> str | None:
    return _LANG_BY_LOCALE.get(locale)


class SlashI18nTranslator(Translator):
    """Resolves locale_str extras written by localize_command / localized_choice."""

    async def translate(
        self,
        string: locale_str,
        locale: Locale,
        context: TranslationContextTypes,
    ) -> str | None:
        lang = _locale_lang(locale)
        if lang is None:
            return None

        key = string.extras.get("i18n_key")
        kind = string.extras.get("kind")
        if not key:
            return None

        location = context.location

        if kind == "name" or location in (
            TranslationContextLocation.command_name,
            TranslationContextLocation.group_name,
        ):
            suffix = "ru" if lang == "ru" else "en"
            translated = i18n.t(f"{key}.{suffix}", lang)
            if not translated or translated.endswith(f".{suffix}"):
                return None
            # Same as default English base → omit (Discord uses the base name).
            if translated == string.message:
                return None
            return translated

        if kind == "desc" or location in (
            TranslationContextLocation.command_description,
            TranslationContextLocation.group_description,
        ):
            translated = i18n.t(key, lang)
            if not translated or translated == key or translated.endswith(".desc"):
                return None
            if translated == string.message and lang == "en":
                return None
            return translated

        if kind == "choice" or location == TranslationContextLocation.choice_name:
            translated = i18n.t(key, lang)
            if not translated or translated == key:
                return None
            if translated == string.message and lang == "en":
                return None
            return translated

        return None


def _apply_name_localizations(
    target: app_commands.Command | app_commands.Group,
    *,
    name_key: str,
) -> None:
    en_name = i18n.t(f"{name_key}.en", "en")
    if en_name and not en_name.endswith(".en"):
        target.name = en_name
    # locale_str is what sync()+Translator actually sends to Discord.
    target._locale_name = locale_str(target.name, i18n_key=name_key, kind="name")


def localize_command(
    command: app_commands.Command,
    *,
    desc_key: str,
    name_key: str | None = None,
) -> app_commands.Command:
    """Attach English base name/description; Russian (and EN) via Translator at sync."""
    en_desc = i18n.t(desc_key, "en")
    command.description = en_desc
    command._locale_description = locale_str(en_desc, i18n_key=desc_key, kind="desc")
    if name_key:
        _apply_name_localizations(command, name_key=name_key)
    return command


def localize_group(
    group: app_commands.Group,
    *,
    desc_key: str,
    name_key: str | None = None,
) -> app_commands.Group:
    en_desc = i18n.t(desc_key, "en")
    group.description = en_desc
    group._locale_description = locale_str(en_desc, i18n_key=desc_key, kind="desc")
    if name_key:
        _apply_name_localizations(group, name_key=name_key)
    return group


def localized_choice(value: str, label_key: str) -> app_commands.Choice[str]:
    """Build a slash choice with English base name and Translator-backed localizations."""
    en_label = i18n.t(label_key, "en")
    ru_label = i18n.t(label_key, "ru")
    choice = app_commands.Choice(
        name=locale_str(en_label, i18n_key=label_key, kind="choice"),
        value=value,
    )
    # Also set dict for non-translator paths (Choice.to_dict includes it).
    choice.name_localizations = {
        Locale.american_english: en_label,
        Locale.british_english: en_label,
        Locale.russian: ru_label,
    }
    return choice
