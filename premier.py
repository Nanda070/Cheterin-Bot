"""Guild-scoped Premier team-application panel."""

from __future__ import annotations

import discord
from discord.ext import commands

import i18n
import valorant_features_core as core


class ApplicationModal(discord.ui.Modal, title="Premier team application"):
    team = discord.ui.TextInput(label="Team name", max_length=100)
    ranks = discord.ui.TextInput(label="Ranks / requirements", style=discord.TextStyle.paragraph, max_length=500)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=1000)
    server = discord.ui.TextInput(label="City / server", max_length=100)
    training = discord.ui.TextInput(label="Training time", max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message("Server only.", ephemeral=True)
        settings = core.get_premier_settings(interaction.guild.id)
        channel = interaction.guild.get_channel(int(settings["channel_id"])) if settings["enabled"] and settings["channel_id"].isdigit() else None
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("Premier applications are not configured for this server.", ephemeral=True)
        embed = discord.Embed(title=f"Premier · {self.team.value}", description=self.description.value, color=discord.Colour.red())
        embed.add_field(name="Created by", value=interaction.user.mention, inline=False)
        embed.add_field(name="Ranks", value=self.ranks.value, inline=False)
        embed.add_field(name="Server", value=self.server.value, inline=True)
        embed.add_field(name="Training", value=self.training.value, inline=True)
        message = await channel.send(embed=embed)
        try:
            await message.create_thread(name=f"Premier · {self.team.value}"[:100])
        except discord.HTTPException:
            pass
        await interaction.response.send_message(f"Application sent: {message.jump_url}", ephemeral=True)


class PremierView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        apply = discord.ui.Button(label="Create team application", style=discord.ButtonStyle.primary, custom_id="premier:apply")
        apply.callback = self.open_application
        self.add_item(apply)
        self.add_item(discord.ui.Button(label="Premier FAQ", style=discord.ButtonStyle.link, url=core.FAQ_URL))

    async def open_application(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ApplicationModal())


class PremierCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not getattr(self.bot, "_premier_view_registered", False):
            self.bot.add_view(PremierView())
            self.bot._premier_view_registered = True


async def setup(bot: commands.Bot):
    await bot.add_cog(PremierCog(bot))
