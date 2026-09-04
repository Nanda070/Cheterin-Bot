"""Guild-enabled /valorant random item commands."""

from __future__ import annotations

import random

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

import i18n
import settings_db
import slash_registry

ENDPOINTS = {
    "agent": ("/agents?isPlayableCharacter=true", "agent", "fullPortrait"),
    "buddy": ("/buddies", "buddy", "displayIcon"),
    "map": ("/maps", "map", "splash"),
    "skin": ("/weapons/skins", "skin", "displayIcon"),
    "weapon": ("/weapons", "weapon", "displayIcon"),
}


class ValorantRandomCog(commands.Cog):
    group = app_commands.Group(name="valorant", description="Random VALORANT items", guild_only=True)

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send(self, interaction: discord.Interaction, kind: str) -> None:
        guild_id = interaction.guild_id
        lang = i18n.lang_for(guild_id)
        if guild_id is None or not settings_db.get(guild_id, "valorant_random", {}).get("enabled", True):
            await interaction.response.send_message(
                i18n.t("valorant.random.disabled", lang), ephemeral=True
            )
            return
        path, title_key, image_key = ENDPOINTS[kind]
        title = i18n.t(f"valorant.random.kind.{title_key}", lang)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://valorant-api.com/v1{path}",
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    payload = await response.json(content_type=None)
            rows = [row for row in payload.get("data", []) if isinstance(row, dict) and row.get("displayName")]
            if kind == "map":
                rows = [row for row in rows if str(row.get("displayName")).lower() != "the range"]
            if kind == "skin":
                rows = [row for row in rows if not str(row.get("displayName")).lower().startswith("standard")]
            item = random.choice(rows)
            embed = discord.Embed(
                title=i18n.t("valorant.random.embed_title", lang, title=title),
                description=f"**{item['displayName']}**",
                color=discord.Colour.red(),
            )
            image = item.get(image_key) or item.get("displayIcon")
            if image:
                embed.set_image(url=image)
            await interaction.response.send_message(embed=embed)
        except Exception:
            await interaction.response.send_message(
                i18n.t("valorant.random.error", lang), ephemeral=True
            )

    @group.command(name="agent", description="Choose a random agent")
    async def agent(self, interaction: discord.Interaction):
        await self._send(interaction, "agent")

    @group.command(name="buddy", description="Choose a random buddy")
    async def buddy(self, interaction: discord.Interaction):
        await self._send(interaction, "buddy")

    @group.command(name="map", description="Choose a random map")
    async def map(self, interaction: discord.Interaction):
        await self._send(interaction, "map")

    @group.command(name="skin", description="Choose a random skin")
    async def skin(self, interaction: discord.Interaction):
        await self._send(interaction, "skin")

    @group.command(name="weapon", description="Choose a random weapon")
    async def weapon(self, interaction: discord.Interaction):
        await self._send(interaction, "weapon")


async def setup(bot: commands.Bot):
    cog = ValorantRandomCog(bot)
    slash_registry.register_valorant_random(cog)
    await bot.add_cog(cog)
