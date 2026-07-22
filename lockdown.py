import discord
from discord.ext import commands
from discord import app_commands

import i18n
import slash_registry
import lockdown_core


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
        lang = i18n.lang_for(interaction.guild_id)
        if not guild:
            await interaction.followup.send(i18n.t("lockdown.guild_only", lang), ephemeral=True)
            return

        if mode.value == "on":
            await self._activate(interaction, guild, lang)
        elif mode.value == "off":
            await self._deactivate(interaction, guild, lang)
        else:
            await self._status(interaction, lang)

    async def _activate(self, interaction: discord.Interaction, guild: discord.Guild, lang: str):
        modified_count, errors = await lockdown_core.activate_antispam(
            guild,
            lockdown_core.get_mention_exempt_ids(),
            lockdown_core.get_mentionable_exempt_ids(),
            lang,
        )

        embed = discord.Embed(
            title=i18n.t("lockdown.activate.title", lang),
            color=discord.Color.red(),
            timestamp=self.bot.utcnow(),
        )
        embed.add_field(
            name=i18n.t("lockdown.activate.who", lang),
            value=f"{interaction.user.mention} (`{interaction.user.id}`)",
            inline=False,
        )
        embed.add_field(name=i18n.t("lockdown.activate.roles_modified", lang), value=str(modified_count), inline=True)
        if errors:
            embed.add_field(name=i18n.t("lockdown.activate.errors", lang), value="\n".join(errors[:10]), inline=False)
        embed.set_footer(text=i18n.t("lockdown.activate.footer", lang))
        await self.bot.send_log(interaction.guild.id, embed)

        status = i18n.t("lockdown.activate.success", lang, count=modified_count)
        if errors:
            status += i18n.t("lockdown.activate.errors_suffix", lang, count=len(errors), errors=", ".join(errors[:5]))
        await interaction.followup.send(status, ephemeral=True)

    async def _deactivate(self, interaction: discord.Interaction, guild: discord.Guild, lang: str):
        result = await lockdown_core.deactivate_antispam(guild, lang)
        if result is None:
            await interaction.followup.send(i18n.t("lockdown.deactivate.no_backup", lang), ephemeral=True)
            return
        restored_count, errors = result

        embed = discord.Embed(
            title=i18n.t("lockdown.deactivate.title", lang),
            color=discord.Color.green(),
            timestamp=self.bot.utcnow(),
        )
        embed.add_field(
            name=i18n.t("lockdown.deactivate.who", lang),
            value=f"{interaction.user.mention} (`{interaction.user.id}`)",
            inline=False,
        )
        embed.add_field(name=i18n.t("lockdown.deactivate.roles_restored", lang), value=str(restored_count), inline=True)
        if errors:
            embed.add_field(name=i18n.t("lockdown.activate.errors", lang), value="\n".join(errors[:10]), inline=False)
        embed.set_footer(text=i18n.t("lockdown.activate.footer", lang))
        await self.bot.send_log(interaction.guild.id, embed)

        status = i18n.t("lockdown.deactivate.success", lang, count=restored_count)
        if errors:
            status += i18n.t("lockdown.activate.errors_suffix", lang, count=len(errors), errors=", ".join(errors[:5]))
        await interaction.followup.send(status, ephemeral=True)

    async def _status(self, interaction: discord.Interaction, lang: str):
        is_active, role_count = lockdown_core.antispam_status(interaction.guild.id)

        if is_active:
            embed = discord.Embed(
                title=i18n.t("lockdown.status.active_title", lang),
                description=i18n.t("lockdown.status.active_desc", lang, count=role_count),
                color=discord.Color.red(),
                timestamp=self.bot.utcnow(),
            )
        else:
            embed = discord.Embed(
                title=i18n.t("lockdown.status.inactive_title", lang),
                description=i18n.t("lockdown.status.inactive_desc", lang),
                color=discord.Color.green(),
                timestamp=self.bot.utcnow(),
            )
        embed.set_footer(text=i18n.t("lockdown.status.footer", lang))
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    cog = Lockdown(bot)
    slash_registry.register_lockdown(cog)
    await bot.add_cog(cog)
