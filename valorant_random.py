"""Guild-enabled /valorant random item commands."""

from __future__ import annotations

import random

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

import settings_db

ENDPOINTS = {
    "agent": ("/agents?isPlayableCharacter=true", "Agent", "fullPortrait"),
    "buddy": ("/buddies", "Buddy", "displayIcon"),
    "map": ("/maps", "Map", "splash"),
    "skin": ("/weapons/skins", "Skin", "displayIcon"),
    "weapon": ("/weapons", "Weapon", "displayIcon"),
}


class ValorantRandomCog(commands.Cog):
    group = app_commands.Group(name="valorant", description="Random VALORANT items", guild_only=True)

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send(self, interaction: discord.Interaction, kind: str) -> None:
        guild_id = interaction.guild_id
        if guild_id is None or not settings_db.get(guild_id, "valorant_random", {}).get("enabled", True):
            await interaction.response.send_message("This VALORANT module is disabled for this server.", ephemeral=True)
            return
        path, title, image_key = ENDPOINTS[kind]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://valorant-api.com/v1{path}", timeout=aiohttp.ClientTimeout(total=15)) as response:
                    payload = await response.json(content_type=None)
            rows = [row for row in payload.get("data", []) if isinstance(row, dict) and row.get("displayName")]
            if kind == "map":
                rows = [row for row in rows if str(row.get("displayName")).lower() != "the range"]
            if kind == "skin":
                rows = [row for row in rows if not str(row.get("displayName")).lower().startswith("standard")]
            item = random.choice(rows)
            embed = discord.Embed(title=f"Random VALORANT {title}", description=f"**{item['displayName']}**", color=discord.Colour.red())
            image = item.get(image_key) or item.get("displayIcon")
            if image:
                embed.set_image(url=image)
            await interaction.response.send_message(embed=embed)
        except Exception:
            await interaction.response.send_message("Could not load a VALORANT item. Please try again.", ephemeral=True)

    @group.command(name="agent", description="Choose a random agent")
    async def agent(self, interaction: discord.Interaction): await self._send(interaction, "agent")
    @group.command(name="buddy", description="Choose a random buddy")
    async def buddy(self, interaction: discord.Interaction): await self._send(interaction, "buddy")
    @group.command(name="map", description="Choose a random map")
    async def map(self, interaction: discord.Interaction): await self._send(interaction, "map")
    @group.command(name="skin", description="Choose a random skin")
    async def skin(self, interaction: discord.Interaction): await self._send(interaction, "skin")
    @group.command(name="weapon", description="Choose a random weapon")
    async def weapon(self, interaction: discord.Interaction): await self._send(interaction, "weapon")


async def setup(bot: commands.Bot):
    await bot.add_cog(ValorantRandomCog(bot))
