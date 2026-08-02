"""SQLite-хранилище настроек всех модулей, per-guild (Фаза 2.1 MULTIGUILD_PLAN.md).

Заменяет плоские JSON-конфиги (`*_config.json`) с mtime-кэшем в каждом `*_core.py`.
Один модуль настроек = одна строка (guild_id, module) с JSON-данными.

Кэш — простой словарь в памяти процесса `{(guild_id, module): data}`, без TTL и
mtime: сбрасывается точечно в `put()`. Тесты, меняющие путь к БД (`SETTINGS_DB_PATH`)
между кейсами, обязаны сами очищать `_cache` (см. паттерн в тестах `*_core.py`),
иначе значения одного теста «протекут» в другой с тем же (guild_id, module).
"""

import copy
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

_cache: dict[tuple[int, str], dict] = {}


def get_db_path() -> str:
    return os.getenv("SETTINGS_DB_PATH", "settings.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS module_settings (
                guild_id INTEGER NOT NULL,
                module TEXT NOT NULL,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (guild_id, module)
            )
        """)


def get(guild_id: int, module: str, default=None):
    """Сырые сохранённые данные модуля для сервера ({} если ещё не сохранялись).

    Дефолты по отдельным ключам — забота вызывающего `*_core.get_settings()`,
    не этого слоя (та же граница ответственности, что была у `load_config()`).
    """
    key = (guild_id, module)
    if key in _cache:
        return copy.deepcopy(_cache[key])

    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT data FROM module_settings WHERE guild_id = ? AND module = ?", (guild_id, module),
        ).fetchone()

    data = json.loads(row["data"]) if row else (default if default is not None else {})
    _cache[key] = data
    return copy.deepcopy(data)


def put(guild_id: int, module: str, data: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO module_settings (guild_id, module, data, updated_at) VALUES (?, ?, ?, ?)
               ON CONFLICT(guild_id, module) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at""",
            (guild_id, module, json.dumps(data, ensure_ascii=False), now),
        )
    _cache[(guild_id, module)] = copy.deepcopy(data)
    try:
        import slash_modules

        slash_modules.on_settings_put(guild_id, module, data)
    except Exception:
        pass


def has(guild_id: int, module: str) -> bool:
    """True, если для этого сервера уже есть сохранённые настройки модуля (для миграции)."""
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT 1 FROM module_settings WHERE guild_id = ? AND module = ?", (guild_id, module),
        ).fetchone()
    return row is not None


def iter_module(module: str):
    """Yield (guild_id, data) for every guild that has this module stored."""
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT guild_id, data FROM module_settings WHERE module = ?",
            (module,),
        ).fetchall()
    for row in rows:
        yield int(row["guild_id"]), json.loads(row["data"])


# ───────────────────────── Мета сервера (Фаза 2.4) ─────────────────────────
# Флаг активности сервера: on_guild_remove помечает неактивным (не удаляя настройки),
# on_guild_join — снова активным. Хранится отдельным зарезервированным «модулем».

_GUILD_META_MODULE = "_guild_meta"


def set_guild_active(guild_id: int, active: bool) -> None:
    meta = get(guild_id, _GUILD_META_MODULE, {})
    meta["active"] = active
    meta["active_changed_at"] = datetime.now(timezone.utc).isoformat()
    put(guild_id, _GUILD_META_MODULE, meta)


def is_guild_active(guild_id: int) -> bool:
    """Активен ли сервер. По умолчанию True (нет записи = историческая гильдия)."""
    return bool(get(guild_id, _GUILD_META_MODULE, {}).get("active", True))
