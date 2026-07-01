import discord
from discord.ext import commands
from discord import app_commands
import os
import json

BACKUP_FILE = "antispam_backup.json"


def _load_backup() -> dict:
    if os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def _save_backup(data: dict):
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def _get_mention_exempt_ids() -> set[int]:
    raw = os.getenv("ANTISPAM_MENTION_EXEMPT_ROLES", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def _get_mentionable_exempt_ids() -> set[int]:
    raw = os.getenv("ANTISPAM_MENTIONABLE_EXEMPT_ROLES", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="antispam", description="Включить / выключить антиспам-режим для ролей")
    @app_commands.describe(mode="on — включить, off — выключить")
    @app_commands.choices(mode=[
        app_commands.Choice(name="on", value="on"),
        app_commands.Choice(name="off", value="off"),
        app_commands.Choice(name="status", value="status"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def antispam(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            await interaction.followup.send("Команда доступна только на сервере.", ephemeral=True)
            return

        mention_exempt = _get_mention_exempt_ids()
        mentionable_exempt = _get_mentionable_exempt_ids()

        if mode.value == "on":
            await self._activate(interaction, guild, mention_exempt, mentionable_exempt)
        elif mode.value == "off":
            await self._deactivate(interaction, guild)
        else:
            await self._status(interaction)

    async def _activate(
        self,
        interaction: discord.Interaction,
        guild: discord.Guild,
        mention_exempt: set[int],
        mentionable_exempt: set[int],
    ):
        backup = _load_backup()
        backup_roles: dict[str, dict] = {}
        modified_count = 0
        errors: list[str] = []

        for role in guild.roles:
            if role.is_default() or role.managed:
                continue

            # --- определяем, что менять ---
            is_mention_exempt = role.id in mention_exempt or role.permissions.administrator
            is_mentionable_exempt = role.id in mentionable_exempt

            need_mention_change = (not is_mention_exempt) and role.permissions.mention_everyone
            need_mentionable_change = (not is_mentionable_exempt) and role.mentionable

            if not need_mention_change and not need_mentionable_change:
                continue

            # сохраняем бэкап
            backup_roles[str(role.id)] = {
                "mention_everyone": role.permissions.mention_everyone,
                "mentionable": role.mentionable,
            }

            new_perms = role.permissions
            new_mentionable = role.mentionable

            if need_mention_change:
                new_perms = discord.Permissions(role.permissions.value)
                new_perms.update(mention_everyone=False)

            if need_mentionable_change:
                new_mentionable = False

            try:
                kwargs = {}
                if need_mention_change:
                    kwargs["permissions"] = new_perms
                if need_mentionable_change:
                    kwargs["mentionable"] = new_mentionable
                await role.edit(**kwargs, reason="Antispam ON")
                modified_count += 1
            except discord.Forbidden:
                errors.append(f"{role.name} (нет прав)")
            except Exception as exc:
                errors.append(f"{role.name} ({exc})")

        backup["roles"] = backup_roles
        backup["active"] = True
        _save_backup(backup)

        # --- лог ---
        embed = discord.Embed(
            title="🛡️ Антиспам-режим ВКЛЮЧЁН",
            color=discord.Color.red(),
            timestamp=self.bot.utcnow(),
        )
        embed.add_field(name="Кто включил", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
        embed.add_field(name="Изменено ролей", value=str(modified_count), inline=True)
        if errors:
            embed.add_field(name="Ошибки", value="\n".join(errors[:10]), inline=False)
        embed.set_footer(text="Lockdown · Antispam")
        await self.bot.send_log(embed)

        status = f"✅ Антиспам включён. Изменено ролей: **{modified_count}**."
        if errors:
            status += f"\n⚠️ Ошибки ({len(errors)}): " + ", ".join(errors[:5])
        await interaction.followup.send(status, ephemeral=True)

    async def _deactivate(self, interaction: discord.Interaction, guild: discord.Guild):
        backup = _load_backup()
        backup_roles: dict[str, dict] = backup.get("roles", {})

        if not backup_roles:
            await interaction.followup.send("Нет сохранённого бэкапа — антиспам не был включён или уже выключен.", ephemeral=True)
            return

        restored_count = 0
        errors: list[str] = []

        for role_id_str, saved in backup_roles.items():
            role = guild.get_role(int(role_id_str))
            if not role:
                continue

            try:
                kwargs = {}
                # восстановление mention_everyone
                if saved.get("mention_everyone") and not role.permissions.mention_everyone:
                    new_perms = discord.Permissions(role.permissions.value)
                    new_perms.update(mention_everyone=True)
                    kwargs["permissions"] = new_perms

                # восстановление mentionable
                if saved.get("mentionable") and not role.mentionable:
                    kwargs["mentionable"] = True

                if kwargs:
                    await role.edit(**kwargs, reason="Antispam OFF")
                    restored_count += 1
            except discord.Forbidden:
                errors.append(f"{role.name} (нет прав)")
            except Exception as exc:
                errors.append(f"{role.name} ({exc})")

        backup["roles"] = {}
        backup["active"] = False
        _save_backup(backup)

        # --- лог ---
        embed = discord.Embed(
            title="🟢 Антиспам-режим ВЫКЛЮЧЕН",
            color=discord.Color.green(),
            timestamp=self.bot.utcnow(),
        )
        embed.add_field(name="Кто выключил", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
        embed.add_field(name="Восстановлено ролей", value=str(restored_count), inline=True)
        if errors:
            embed.add_field(name="Ошибки", value="\n".join(errors[:10]), inline=False)
        embed.set_footer(text="Lockdown · Antispam")
        await self.bot.send_log(embed)

        status = f"✅ Антиспам выключен. Восстановлено ролей: **{restored_count}**."
        if errors:
            status += f"\n⚠️ Ошибки ({len(errors)}): " + ", ".join(errors[:5])
        await interaction.followup.send(status, ephemeral=True)

    async def _status(self, interaction: discord.Interaction):
        backup = _load_backup()
        is_active = backup.get("active", False)
        role_count = len(backup.get("roles", {}))

        if is_active:
            embed = discord.Embed(
                title="🛡️ Антиспам-режим: ВКЛЮЧЁН",
                description=f"Изменённых ролей в бэкапе: **{role_count}**",
                color=discord.Color.red(),
                timestamp=self.bot.utcnow(),
            )
        else:
            embed = discord.Embed(
                title="🟢 Антиспам-режим: ВЫКЛЮЧЕН",
                description="Все роли работают в обычном режиме.",
                color=discord.Color.green(),
                timestamp=self.bot.utcnow(),
            )
        embed.set_footer(text="Lockdown · Antispam Status")
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Lockdown(bot))
