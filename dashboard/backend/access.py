"""Контроль доступа к дашборду (модель MEE6, Фаза 2.3).

Доступ к серверу = право **Manage Server / Administrator** на этом сервере.
Роль-списки из .env (`DASHBOARD_ACCESS_ROLE_IDS`) выведены из обихода — доступ
считается по факту прав участника на конкретной гильдии. Супер-админ проверяется
всегда против МЕЙН-сервера.
"""

import os

# Биты прав Discord (permissions в /users/@me/guilds приходит строкой-битмаской).
PERMISSION_MANAGE_GUILD = 0x20
PERMISSION_ADMINISTRATOR = 0x8

# Мейн-сервер: CTD/новости/супер-админ завязаны на него. Переопределяемо env-переменной.
MAIN_GUILD_ID = int(os.getenv("MAIN_GUILD_ID", "1324239354154975252"))

# Список серверов бота (супер-админ) — намеренно хардкод, не настройка через .env/дашборд.
SUPER_ADMIN_ROLE_IDS = frozenset({"1505359848433516734"})


def has_dashboard_access(member, allowed_role_ids: frozenset) -> bool:
    """DEPRECATED (Фаза 1, роль-модель). Оставлено до перевода auth/middleware на
    has_manage_server — будет удалено в рамках Фазы 2.3."""
    if member.guild_permissions.administrator:
        return True
    member_role_ids = {str(role.id) for role in member.roles}
    return not member_role_ids.isdisjoint(allowed_role_ids)


def has_manage_server(member) -> bool:
    """Доступ к настройкам сервера: Manage Server или Administrator на этой гильдии."""
    perms = member.guild_permissions
    return bool(perms.administrator or getattr(perms, "manage_guild", False))


def has_super_admin_access(member) -> bool:
    """Супер-админ: администратор или носитель супер-роли на МЕЙН-сервере
    (сам факт «на мейне» проверяется вызывающим — резолвом участника мейн-гильдии)."""
    if member.guild_permissions.administrator:
        return True
    member_role_ids = {str(role.id) for role in member.roles}
    return not member_role_ids.isdisjoint(SUPER_ADMIN_ROLE_IDS)


def can_manage_guild_permissions(permissions: int) -> bool:
    """Право управлять сервером по битмаске из OAuth-списка `/users/@me/guilds`."""
    return bool(permissions & (PERMISSION_MANAGE_GUILD | PERMISSION_ADMINISTRATOR))


def manageable_guilds(guilds: list[dict], bot) -> list[dict]:
    """Отфильтровать OAuth-список серверов пользователя до управляемых им и
    аннотировать флагом `has_bot` (бот присутствует на сервере).

    Это лишь предварительный фильтр для UI — окончательная авторизация на запись
    делается серверной проверкой прав участника (см. select-guild / middleware).
    """
    result = []
    for guild in guilds:
        try:
            perms = int(guild.get("permissions", 0))
        except (TypeError, ValueError):
            perms = 0
        if guild.get("owner") or can_manage_guild_permissions(perms):
            gid = int(guild["id"])
            result.append({
                "id": str(gid),
                "name": guild.get("name", ""),
                "icon": guild.get("icon"),
                "has_bot": bot.get_guild(gid) is not None,
            })
    return result
