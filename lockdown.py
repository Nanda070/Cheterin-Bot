import discord
from discord.ext import commands
from discord import app_commands

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
        if not guild:
            await interaction.followup.send("Команда доступна только на сервере.", ephemeral=True)
            return

        if mode.value == "on":
            await self._activate(interaction, guild)
        elif mode.value == "off":
            await self._deactivate(interaction, guild)
        else:
            await self._status(interaction)

    async def _activate(self, interaction: discord.Interaction, guild: discord.Guild):
        modified_count, errors = await lockdown_core.activate_antispam(
            guild,
            lockdown_core.get_mention_exempt_ids(),
            lockdown_core.get_mentionable_exempt_ids(),
        )

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
        await self.bot.send_log(interaction.guild.id, embed)

        status = f"✅ Антиспам включён. Изменено ролей: **{modified_count}**."
        if errors:
            status += f"\n⚠️ Ошибки ({len(errors)}): " + ", ".join(errors[:5])
        await interaction.followup.send(status, ephemeral=True)

    async def _deactivate(self, interaction: discord.Interaction, guild: discord.Guild):
        result = await lockdown_core.deactivate_antispam(guild)
        if result is None:
            await interaction.followup.send("Нет сохранённого бэкапа — антиспам не был включён или уже выключен.", ephemeral=True)
            return
        restored_count, errors = result

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
        await self.bot.send_log(interaction.guild.id, embed)

        status = f"✅ Антиспам выключен. Восстановлено ролей: **{restored_count}**."
        if errors:
            status += f"\n⚠️ Ошибки ({len(errors)}): " + ", ".join(errors[:5])
        await interaction.followup.send(status, ephemeral=True)

    async def _status(self, interaction: discord.Interaction):
        is_active, role_count = lockdown_core.antispam_status()

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
