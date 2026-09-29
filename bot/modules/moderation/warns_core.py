"""Ядро системы предупреждений (варнов). Хранение — warns_db.py (SQLite),
чтобы поддерживать быстрый подсчёт активных варнов и историю по участнику.

Варн может быть выдан вручную модератором (/warn, дашборд) или автоматически
модулем автомодерации (source = ключ сработавшего фильтра). Срок действия
варна (expires_at) настраивается отдельно для каждого источника — см.
automod_core.py.
"""

from datetime import datetime, timedelta, timezone

import bot.modules.moderation.warns_db as warns_db


def _serialize(row) -> dict:
    return {
        "id": row["id"],
        "guild_id": str(row["guild_id"]),
        "user_id": str(row["user_id"]),
        "reason": row["reason"],
        "moderator_id": str(row["moderator_id"]) if row["moderator_id"] is not None else None,
        "source": row["source"],
        "created_at": row["created_at"],
        "expires_at": row["expires_at"],
        "removed": bool(row["removed"]),
        "removed_by": str(row["removed_by"]) if row["removed_by"] is not None else None,
        "removed_at": row["removed_at"],
    }


def compute_expiry(duration_minutes: int) -> str | None:
    if duration_minutes <= 0:
        return None
    return (datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)).isoformat()


def add_warn(
    guild_id: int,
    user_id: int,
    reason: str,
    moderator_id: int | None,
    source: str = "manual",
    duration_minutes: int = 0,
) -> dict:
    row = warns_db.add_warn(guild_id, user_id, reason, moderator_id, source, compute_expiry(duration_minutes))
    return _serialize(row)


def remove_warn(warn_id: int, removed_by: int | None, *, guild_id: int | None = None) -> bool:
    if guild_id is not None:
        warn = get_warn(warn_id)
        if warn is None or int(warn["guild_id"]) != int(guild_id):
            return False
    return warns_db.remove_warn(warn_id, removed_by)


def get_warn(warn_id: int) -> dict | None:
    row = warns_db.get_warn(warn_id)
    return _serialize(row) if row else None


def get_warns(guild_id: int, user_id: int) -> list[dict]:
    return [_serialize(r) for r in warns_db.get_warns(guild_id, user_id)]


def get_active_warn_count(guild_id: int, user_id: int) -> int:
    return warns_db.get_active_warn_count(guild_id, user_id)
