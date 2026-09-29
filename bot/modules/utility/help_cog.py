"""Member-facing /help — category select + leaders-style pagination."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import bot.core.embed_style as embed_style
import bot.core.i18n as i18n
import bot.core.slash_registry as slash_registry

# Order matches select options and locale keys help.page.<id>.*
HELP_CATEGORIES: tuple[str, ...] = (
    "overview",
    "levels",
    "economy",
    "casino",
    "fun",
    "community",
    "relations",
    "valchecker",
    "events",
)


class HelpCategorySelect(discord.ui.Select):
    def __init__(self, view: "HelpView"):
        self.help_view = view
        options = [
            discord.SelectOption(
                label=i18n.t(f"help.cat.{cat}.label", view.lang),
                value=cat,
                description=i18n.t(f"help.cat.{cat}.desc", view.lang)[:100],
                emoji=i18n.t(f"help.cat.{cat}.emoji", view.lang) or None,
                default=(cat == view.category),
            )
            for cat in HELP_CATEGORIES
        ]
        super().__init__(
            placeholder=i18n.t("help.select_placeholder", view.lang),
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        self.help_view.category = self.values[0]
        self.help_view._rebuild_select()
        self.help_view._sync_buttons()
        await interaction.response.edit_message(
            embed=self.help_view.build_embed(),
            view=self.help_view,
        )


class HelpView(discord.ui.View):
    """Interactive help: category dropdown (row 0) + « ‹ › » ✕ (row 1), like /leaders."""

    def __init__(self, lang: str, category: str = "overview"):
        super().__init__(timeout=180)
        self.lang = lang
        self.category = category if category in HELP_CATEGORIES else "overview"
        self._select: HelpCategorySelect | None = None
        self._rebuild_select()
        self._sync_buttons()

    def _page_index(self) -> int:
        return HELP_CATEGORIES.index(self.category)

    def _max_pages(self) -> int:
        return len(HELP_CATEGORIES)

    def _rebuild_select(self) -> None:
        if self._select is not None:
            self.remove_item(self._select)
        self._select = HelpCategorySelect(self)
        self.add_item(self._select)

    def build_embed(self) -> discord.Embed:
        lang = self.lang
        cat = self.category
        embed = embed_style.make_embed(
            title=i18n.t(f"help.page.{cat}.title", lang),
            description=i18n.t(f"help.page.{cat}.body", lang),
            color=embed_style.INFO,
            footer=i18n.t(
                "help.footer",
                lang,
                category=i18n.t(f"help.cat.{cat}.label", lang),
                page=self._page_index() + 1,
                max_pages=self._max_pages(),
            ),
        )
        # Optional extra fields (field1..field6) — skip missing keys.
        for i in range(1, 7):
            name_key = f"help.page.{cat}.field{i}.name"
            value_key = f"help.page.{cat}.field{i}.value"
            name = i18n.t(name_key, lang)
            value = i18n.t(value_key, lang)
            if name == name_key or value == value_key:
                continue
            embed.add_field(name=name, value=value, inline=False)
        return embed

    def _sync_buttons(self) -> None:
        at_start = self._page_index() == 0
        at_end = self._page_index() >= self._max_pages() - 1
        self.btn_first.disabled = at_start
        self.btn_prev.disabled = at_start
        self.btn_next.disabled = at_end
        self.btn_last.disabled = at_end

    def _go(self, index: int) -> None:
        self.category = HELP_CATEGORIES[max(0, min(index, self._max_pages() - 1))]
        self._rebuild_select()
        self._sync_buttons()

    @discord.ui.button(label="\u00ab", style=discord.ButtonStyle.grey, row=1)
    async def btn_first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._go(0)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\u2039", style=discord.ButtonStyle.grey, row=1)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._go(self._page_index() - 1)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\u203a", style=discord.ButtonStyle.grey, row=1)
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._go(self._page_index() + 1)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\u00bb", style=discord.ButtonStyle.grey, row=1)
    async def btn_last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._go(self._max_pages() - 1)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\u2715", style=discord.ButtonStyle.red, row=1)
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
