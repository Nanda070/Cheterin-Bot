"""Одноразовая идемпотентная миграция плоских JSON-конфигов в settings_db (Фаза 2.1
MULTIGUILD_PLAN.md).

Вызывается один раз при старте бота (main.py, setup_hook) — переносит данные каждого
плоского `*_config.json` под текущий (единственный на момент миграции) guild_id и
переименовывает исходный файл в `<file>.migrated.bak`, чтобы не мигрировать повторно.

Идемпотентность: если для (guild_id, module) в settings_db уже есть строка — модуль
пропускается целиком, даже если плоский файл почему-то ещё существует.
"""

import json
import logging
import os

import settings_db

logger = logging.getLogger("settings_migration")

# module → путь к плоскому JSON-файлу. Имена модулей должны совпадать с MODULE_NAME
# соответствующего *_core.py/модуля после его перевода на settings_db.
MODULE_FILE_MAP: dict[str, str] = {
    "antiraid": "antiraid_config.json",
    "casino": "casino_config.json",
    "economy": "economy_config.json",
    "feedback_categories": "feedback_categories.json",
    "family": "family_config.json",
    "fun": "fun_config.json",
    "bunker": "bunker_config.json",
    "mafia": "mafia_config.json",
    "bot_config": "config.json",
    "news": "news_relay.json",
    "automod": "automod_config.json",
    "daily_topic": "daily_topic_config.json",
    "streams": "streams_config.json",
    "reaction_roles": "reaction_roles.json",
    "serverlog": "serverlog_config.json",
    "verification": "verification_config.json",
    "wordle": "wordle_config.json",
    "xp": "xp_config.json",
    "events": "events_data.json",
    "brackets": "brackets_data.json",
    "buttons": "buttons_config.json",
    "embed_templates": "embed_templates.json",
    "invites_stats": "invites_stats.json",
    "moderation_log": "moderation_log.json",
    "supply": "supply_data.json",
    "giveaways": "giveaways_data.json",
    "voice_panel": "voice_panel.json",
    "lockdown_backup": "antispam_backup.json",
}


def migrate_one(guild_id: int, module: str, path: str) -> bool:
    """Мигрирует один модуль. True — реально перенесён, False — нечего было переносить."""
    if settings_db.has(guild_id, module):
        return False
    if not os.path.exists(path):
        return False

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            logger.warning(
                "settings_migration: %s повреждён (невалидный JSON) — переносим как пустой объект", path,
            )
            data = {}

    settings_db.put(guild_id, module, data)
    os.replace(path, f"{path}.migrated.bak")
    logger.info("settings_migration: %s → settings_db (guild_id=%s, module=%s)", path, guild_id, module)
    return True


def migrate_all(guild_id: int) -> list[str]:
    """Мигрирует все известные модули; возвращает список реально перенесённых имён."""
    return [module for module, path in MODULE_FILE_MAP.items() if migrate_one(guild_id, module, path)]
