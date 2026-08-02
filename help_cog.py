"""Member-facing /help command with paginated embed pages."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import embed_style
import i18n
import slash_registry

PAGE_COUNT = 7


class HelpView(discord.ui.View):
    def __init__(self, lang: str, page: int = 0):
        super().__init__(timeout=180)
        self.lang = lang
        self.page = max(0, min(page, PAGE_COUNT - 1))
        self._sync_buttons()

    def build_embed(self) -> discord.Embed:
        n = self.page + 1
        footer_detail = i18n.t("help.footer", self.lang, page=n, total=PAGE_COUNT)
        return embed_style.make_embed(
            title=i18n.t(f"help.page{n}.title", self.lang),
            description=i18n.t(f"help.page{n}.body", self.lang),
            color=embed_style.INFO,
            footer=f"{embed_style.module_footer('Cheterin', 'Help')} · {footer_detail}",
        )

    def _sync_buttons(self) -> None:
        at_start = self.page == 0
        at_end = self.page >= PAGE_COUNT - 1
        self.btn_prev.disabled = at_start
        self.btn_next.disabled = at_end
        self.btn_prev.label = i18n.t("help.btn.prev", self.lang)
        self.btn_next.label = i18n.t("help.btn.next", self.lang)
        self.btn_close.label = i18n.t("help.btn.close", self.lang)

    @discord.ui.button(style=discord.ButtonStyle.secondary, row=0)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(style=discord.ButtonStyle.secondary, row=0)
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(PAGE_COUNT - 1, self.page + 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(style=discord.ButtonStyle.danger, row=0)
    async def btn_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)
        self.stop()


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Member commands and features")
    async def help_command(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        view = HelpView(lang)
        await interaction.response.send_message(embed=view.build_embed(), view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    cog = HelpCog(bot)
    slash_registry.register_help(cog)
    await bot.add_cog(cog)
