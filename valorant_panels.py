"""Interactive guild-scoped VALORANT role panels."""

from __future__ import annotations

import discord
from discord.ext import commands

import valorant_features_core as core


class RolePanel(discord.ui.View):
    def __init__(self, kind: str):
        super().__init__(timeout=None)
        self.kind = kind
        catalog = core.panel_catalog()
        rows = catalog["agent_classes"].get(kind) or catalog.get(kind) or []
        if kind == "agents":
            rows = [agent for group in catalog["agent_classes"].values() for agent in group]
        rows = rows[:25]
        options = [discord.SelectOption(label=row["name"], value=row["key"]) for row in rows]
        if options:
            select = discord.ui.Select(placeholder="Choose roles", min_values=1, max_values=min(len(options), 3), options=options, custom_id=f"valorant-panel:{kind}")
            select.callback = self.choose
            self.add_item(select)

    async def choose(self, interaction: discord.Interaction):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            return
        settings = core.get_panel_settings(interaction.guild.id)
        mapping_key = {"agents": "agent_roles", "playstyles": "playstyle_roles", "notifications": "notification_roles", "servers": "server_roles"}[self.kind]
        mapping = settings[mapping_key]
        roles = [interaction.guild.get_role(int(mapping[value])) for value in self.children[0].values if mapping.get(value, "").isdigit()]
        roles = [role for role in roles if role is not None]
        if roles:
            await interaction.user.add_roles(*roles, reason="VALORANT panel selection")
        await interaction.response.send_message("Roles updated." if roles else "This panel has no mapped roles yet.", ephemeral=True)


async def publish_panel(channel: discord.TextChannel, kind: str) -> discord.Message:
    title = {"agents": "VALORANT agents", "playstyles": "Playstyle", "notifications": "Notifications", "servers": "Cities / servers"}[kind]
    return await channel.send(embed=discord.Embed(title=title, color=discord.Colour.red()), view=RolePanel(kind))


class ValorantPanelsCog(commands.Cog):
    def __init__(self, bot: commands.Bot): self.bot = bot


async def setup(bot: commands.Bot):
    await bot.add_cog(ValorantPanelsCog(bot))
