"""Timed roles: slash assign + background sweeper."""

import logging
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

import i18n
import slash_registry
import timed_roles_db

logger = logging.getLogger("timed_roles")


class TimedRolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sweeper.start()

    def cog_unload(self):
        self.sweeper.cancel()

    @app_commands.command(name="timed-role", description="Assign a role that expires after N minutes")
    @app_commands.describe(
        member="Member to give the role",
        role="Role to assign",
        minutes="Duration in minutes (1–10080)",
    )
    @app_commands.default_permissions(manage_roles=True)
    async def timed_role_command(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
        minutes: app_commands.Range[int, 1, 10080],
    ):
        lang = i18n.lang_for(interaction.guild_id)
        if role >= interaction.guild.me.top_role or role.managed:
            return await interaction.response.send_message(
                i18n.t("timed_roles.error.role_hierarchy", lang), ephemeral=True
            )
        expires = datetime.now(timezone.utc) + timedelta(minutes=int(minutes))
        try:
            await member.add_roles(role, reason="timed role")
        except discord.HTTPException:
            return await interaction.response.send_message(
                i18n.t("timed_roles.error.grant_failed", lang), ephemeral=True
            )
        timed_roles_db.add(interaction.guild.id, member.id, role.id, expires.isoformat())
        await interaction.response.send_message(
            i18n.t(
                "timed_roles.success",
                lang,
                member=member.mention,
                role=role.mention,
                minutes=minutes,
            ),
            ephemeral=True,
        )

    @tasks.loop(minutes=1)
    async def sweeper(self):
        try:
            for row in timed_roles_db.expired():
                guild = self.bot.get_guild(row["guild_id"])
                if guild is None:
                    timed_roles_db.remove(row["id"])
                    continue
                member = guild.get_member(row["user_id"])
                role = guild.get_role(row["role_id"])
                if member and role and role in member.roles:
                    try:
                        await member.remove_roles(role, reason="timed role expired")
                    except discord.HTTPException:
                        logger.warning("timed role remove failed guild=%s", guild.id)
                timed_roles_db.remove(row["id"])
        except Exception:
            logger.exception("timed_roles sweeper error")

    @sweeper.before_loop
    async def before_sweeper(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    timed_roles_db.init()
    cog = TimedRolesCog(bot)
    slash_registry.register_timed_roles(cog)
    await bot.add_cog(cog)
