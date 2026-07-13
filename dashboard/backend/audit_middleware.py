"""Аудит действий дашборда: каждое мутирующее действие модератора пишется в stats.db."""

import logging
import time

from aiohttp import web

import stats_db

logger = logging.getLogger("dashboard.audit")

# Порядок важен: первое совпадение по (метод, префикс) даёт подпись
ACTION_LABELS: list[tuple[str, str, str]] = [
    ("PUT", "/api/config", "Изменение конфигурации"),
    ("POST", "/api/lockdown/activate", "Включение антиспам-режима"),
    ("POST", "/api/lockdown/deactivate", "Выключение антиспам-режима"),
    ("POST", "/api/members/", "Действие над участником (бан/кик/роль)"),
    ("DELETE", "/api/members/", "Снятие роли с участника"),
    ("POST", "/api/mass-assign", "Массовая выдача ролей"),
    ("PUT", "/api/welcome-settings", "Настройки приветствий"),
    ("PUT", "/api/auto-roles", "Настройки авто-ролей"),
    ("POST", "/api/reaction-roles", "Создание роли по реакции"),
    ("PUT", "/api/reaction-roles", "Изменение роли по реакции"),
    ("DELETE", "/api/reaction-roles", "Удаление роли по реакции"),
    ("POST", "/api/embed-builder", "Отправка/изменение эмбеда"),
    ("POST", "/api/feedback", "Действие с обратной связью"),
    ("PUT", "/api/feedback", "Изменение категории обратной связи"),
    ("DELETE", "/api/feedback", "Удаление категории обратной связи"),
    ("POST", "/api/events", "Действие с событием"),
    ("DELETE", "/api/events", "Удаление события"),
    ("POST", "/api/brackets", "Действие с турнирной сеткой"),
    ("DELETE", "/api/brackets", "Удаление турнирной сетки"),
    ("POST", "/api/supply", "Действие с поставкой"),
    ("DELETE", "/api/voice/rooms", "Удаление приватной комнаты"),
    ("POST", "/api/voice/panel", "Публикация панели комнат"),
    ("PUT", "/api/news", "Настройки ретрансляции"),
    ("PUT", "/api/serverlog", "Настройки логирования"),
    ("PUT", "/api/xp/members", "Изменение XP участника"),
    ("POST", "/api/xp/members", "Сброс XP участника"),
    ("POST", "/api/xp/reset-all", "Полный сброс рейтинга"),
    ("POST", "/api/xp/card-bg", "Загрузка фона карточки ранга"),
    ("DELETE", "/api/xp/card-bg", "Удаление фона карточки ранга"),
    ("PUT", "/api/xp", "Настройки системы уровней"),
    ("POST", "/api/streams", "Действие с подпиской на стримы"),
    ("PATCH", "/api/streams", "Изменение подписки на стримы"),
    ("DELETE", "/api/streams", "Удаление подписки на стримы"),
]

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def describe_action(method: str, path: str) -> str:
    for label_method, prefix, label in ACTION_LABELS:
        if method == label_method and path.startswith(prefix):
            return label
    return f"{method} {path}"


@web.middleware
async def audit_middleware(request: web.Request, handler):
    response = await handler(request)
    try:
        if (
            request.method in MUTATING_METHODS
            and request.path.startswith("/api/")
            and not request.path.startswith("/api/auth")
        ):
            moderator = request.get("moderator")
            status = getattr(response, "status", 0)
            if moderator is not None and 200 <= status < 300:
                stats_db.audit_add(
                    ts=int(time.time()),
                    moderator_id=moderator.id,
                    moderator_name=getattr(moderator, "display_name", str(moderator.id)),
                    method=request.method,
                    path=request.path,
                    action=describe_action(request.method, request.path),
                    status=status,
                    details=str(request.get("audit_details", "")),
                )
    except Exception:
        logger.exception("Не удалось записать аудит для %s %s", request.method, request.path)
    return response
