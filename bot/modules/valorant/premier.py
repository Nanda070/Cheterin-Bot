"""Guild-scoped Premier team-application panel."""

from __future__ import annotations

import discord
from discord.ext import commands

import bot.core.i18n as i18n
import bot.modules.valorant.valorant_features_core as core


class ApplicationModal(discord.ui.Modal):
    def __init__(self, lang: str):
        super().__init__(title=i18n.t("premier.modal.title", lang)[:45])
        self.lang = lang
        self.team = discord.ui.TextInput(label=i18n.t("premier.modal.team", lang), max_length=100)
        self.ranks = discord.ui.TextInput(
            label=i18n.t("premier.modal.ranks", lang),
            style=discord.TextStyle.paragraph,
            max_length=500,
        )
        self.description = discord.ui.TextInput(
            label=i18n.t("premier.modal.description", lang),
            style=discord.TextStyle.paragraph,
            max_length=1000,
        )
        self.server = discord.ui.TextInput(label=i18n.t("premier.modal.server", lang), max_length=100)
        self.training = discord.ui.TextInput(label=i18n.t("premier.modal.training", lang), max_length=100)
        self.add_item(self.team)
        self.add_item(self.ranks)
        self.add_item(self.description)
        self.add_item(self.server)
        self.add_item(self.training)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.lang
        if interaction.guild is None:
            return await interaction.response.send_message(
                i18n.t("premier.error.guild_only", lang), ephemeral=True
            )
        settings = core.get_premier_settings(interaction.guild.id)
        channel = (
            interaction.guild.get_channel(int(settings["channel_id"]))
            if settings["enabled"] and settings["channel_id"].isdigit()
            else None
        )
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                i18n.t("premier.error.not_configured", lang), ephemeral=True
            )
        embed = discord.Embed(
            title=f"Premier · {self.team.value}",
            description=self.description.value,
            color=discord.Colour.red(),
        )
        embed.add_field(
            name=i18n.t("premier.embed.created_by", lang),
            value=interaction.user.mention,
            inline=False,
        )
        embed.add_field(name=i18n.t("premier.embed.ranks", lang), value=self.ranks.value, inline=False)
        embed.add_field(name=i18n.t("premier.embed.server", lang), value=self.server.value, inline=True)
        embed.add_field(
            name=i18n.t("premier.embed.training", lang), value=self.training.value, inline=True
        )
        message = await channel.send(embed=embed)
        try:
            await message.create_thread(name=f"Premier · {self.team.value}"[:100])
        except discord.HTTPException:
            pass
        await interaction.response.send_message(
            i18n.t("premier.sent", lang, url=message.jump_url), ephemeral=True
        )


class PremierView(discord.ui.View):
    def __init__(self, lang: str = "en"):
        super().__init__(timeout=None)
        apply = discord.ui.Button(
            label=i18n.t("premier.button.apply", lang)[:80],
            style=discord.ButtonStyle.primary,
            custom_id="premier:apply",
        )
        apply.callback = self.open_application
        self.add_item(apply)
        self.add_item(
            discord.ui.Button(
                label=i18n.t("premier.button.faq", lang)[:80],
                style=discord.ButtonStyle.link,
                url=core.FAQ_URL,
            )
        )

    async def open_application(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        await interaction.response.send_modal(ApplicationModal(lang))


class PremierCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not getattr(self.bot, "_premier_view_registered", False):
            # Persistent view labels use English base; interaction modal uses guild language.
            self.bot.add_view(PremierView("en"))
            self.bot._premier_view_registered = True


async def setup(bot: commands.Bot):
    await bot.add_cog(PremierCog(bot))
