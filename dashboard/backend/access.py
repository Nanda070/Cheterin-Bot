def has_dashboard_access(member, allowed_role_ids: frozenset) -> bool:
    if member.guild_permissions.administrator:
        return True
    member_role_ids = {str(role.id) for role in member.roles}
    return not member_role_ids.isdisjoint(allowed_role_ids)


# Список серверов бота (супер-админ) — намеренно хардкод, не настройка через .env/дашборд.
SUPER_ADMIN_ROLE_IDS = frozenset({"1505359848433516734"})


def has_super_admin_access(member) -> bool:
    return has_dashboard_access(member, SUPER_ADMIN_ROLE_IDS)
