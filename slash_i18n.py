"""Slash command localizations (Phase 3.2(3))."""

from __future__ import annotations

from discord import Locale
from discord import app_commands

import i18n

_LOCALE_BY_LANG = {
    "en": Locale.american_english,
    "ru": Locale.russian,
}


def _apply_name_localizations(
    target: app_commands.Command | app_commands.Group,
    *,
    name_key: str,
) -> None:
    en_name = i18n.t(f"{name_key}.en", "en")
    ru_name = i18n.t(f"{name_key}.ru", "ru")
    if en_name and not en_name.endswith(".en"):
        target.name = en_name
    name_locs: dict[Locale, str] = {}
    if ru_name and not ru_name.endswith(".ru") and ru_name != target.name:
        name_locs[Locale.russian] = ru_name
    if name_locs:
        target.name_localizations = name_locs


def localize_command(
    command: app_commands.Command,
    *,
    desc_key: str,
    name_key: str | None = None,
) -> app_commands.Command:
    """Attach English base name/description with ru/en localizations."""
    en_desc = i18n.t(desc_key, "en")
    command.description = en_desc
    command.description_localizations = {
        locale: i18n.t(desc_key, lang)
        for lang, locale in _LOCALE_BY_LANG.items()
    }
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
    group.description_localizations = {
        locale: i18n.t(desc_key, lang)
        for lang, locale in _LOCALE_BY_LANG.items()
    }
    if name_key:
        _apply_name_localizations(group, name_key=name_key)
    return group


def localized_choice(value: str, label_key: str) -> app_commands.Choice[str]:
    """Build a slash choice with ru default name and en/ru name localizations."""
    choice = app_commands.Choice(name=i18n.t(label_key, "ru"), value=value)
    choice.name_localizations = {
        locale: i18n.t(label_key, lang)
        for lang, locale in _LOCALE_BY_LANG.items()
    }
    return choice
