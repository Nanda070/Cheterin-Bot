import settings_db

import discord

BACKUP_FILE = "antispam_backup.json"


def load_backup(guild_id: int) -> dict:
    return settings_db.get(guild_id, "lockdown_backup", {})


def save_backup(guild_id: int, data: dict):
    settings_db.put(guild_id, "lockdown_backup", data)


def get_mention_exempt_ids() -> set[int]:
    import os

    raw = os.getenv("ANTISPAM_MENTION_EXEMPT_ROLES", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def get_mentionable_exempt_ids() -> set[int]:
    import os

    raw = os.getenv("ANTISPAM_MENTIONABLE_EXEMPT_ROLES", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def antispam_status(guild_id: int) -> tuple[bool, int]:
    backup = load_backup(guild_id)
    return bool(backup.get("active", False)), len(backup.get("roles", {}))


async def activate_antispam(
    guild,
    mention_exempt: set[int],
    mentionable_exempt: set[int],
    lang: str = "ru",
) -> tuple[int, list[str]]:
    import i18n

    backup = load_backup(guild.id)
    backup_roles: dict[str, dict] = {}
    modified_count = 0
    errors: list[str] = []

    for role in guild.roles:
        if role.is_default() or role.managed:
            continue

        is_mention_exempt = role.id in mention_exempt or role.permissions.administrator
        is_mentionable_exempt = role.id in mentionable_exempt

        need_mention_change = (not is_mention_exempt) and role.permissions.mention_everyone
        need_mentionable_change = (not is_mentionable_exempt) and role.mentionable

        if not need_mention_change and not need_mentionable_change:
            continue

        backup_roles[str(role.id)] = {
            "mention_everyone": role.permissions.mention_everyone,
            "mentionable": role.mentionable,
        }

        try:
            kwargs = {}
            if need_mention_change:
                new_perms = discord.Permissions(getattr(role.permissions, "value", 0))
                new_perms.update(mention_everyone=False)
                kwargs["permissions"] = new_perms
            if need_mentionable_change:
                kwargs["mentionable"] = False
            await role.edit(**kwargs, reason="Antispam ON")
            modified_count += 1
        except discord.Forbidden:
            errors.append(i18n.t("lockdown.error.forbidden", lang, role=role.name))
        except Exception as exc:
            errors.append(i18n.t("lockdown.error.generic", lang, role=role.name, error=exc))

    backup["roles"] = backup_roles
    backup["active"] = True
    save_backup(guild.id, backup)
    return modified_count, errors


async def deactivate_antispam(guild, lang: str = "ru") -> tuple[int, list[str]] | None:
    import i18n

    backup = load_backup(guild.id)
    backup_roles: dict[str, dict] = backup.get("roles", {})
    if not backup_roles:
        return None

    restored_count = 0
    errors: list[str] = []

    for role_id_str, saved in backup_roles.items():
        role = guild.get_role(int(role_id_str))
        if not role:
            continue
        try:
            kwargs = {}
            if saved.get("mention_everyone") and not role.permissions.mention_everyone:
                new_perms = discord.Permissions(getattr(role.permissions, "value", 0))
                new_perms.update(mention_everyone=True)
                kwargs["permissions"] = new_perms
            if saved.get("mentionable") and not role.mentionable:
                kwargs["mentionable"] = True
            if kwargs:
                await role.edit(**kwargs, reason="Antispam OFF")
                restored_count += 1
        except discord.Forbidden:
            errors.append(i18n.t("lockdown.error.forbidden", lang, role=role.name))
        except Exception as exc:
            errors.append(i18n.t("lockdown.error.generic", lang, role=role.name, error=exc))

    backup["roles"] = {}
    backup["active"] = False
    save_backup(guild.id, backup)
    return restored_count, errors
