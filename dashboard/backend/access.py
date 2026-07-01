def has_dashboard_access(member, allowed_role_ids: frozenset) -> bool:
    if member.guild_permissions.administrator:
        return True
    member_role_ids = {str(role.id) for role in member.roles}
    return not member_role_ids.isdisjoint(allowed_role_ids)
