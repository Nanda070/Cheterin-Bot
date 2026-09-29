"""Auto-reactions: add configured emoji reactions to new messages."""

from __future__ import annotations

import logging
import re

import discord
from discord.ext import commands

import bot.modules.community.auto_reactions_core as auto_reactions_core

logger = logging.getLogger("auto_reactions")

_CUSTOM_EMOJI_RE = re.compile(r"^<a?:(\w+):(\d+)>$")


def _resolve_emoji(guild: discord.Guild, token: str):
    token = token.strip()
    match = _CUSTOM_EMOJI_RE.match(token)
    if match:
        emoji_id = int(match.group(2))
        emoji = guild.get_emoji(emoji_id)
        return emoji if emoji is not None else token
    return token


def _emoji_targets(guild: discord.Guild, rule: dict) -> list:
    if rule.get("emoji_mode") == "all_guild":
        return auto_reactions_core.guild_emoji_tokens(guild.emojis)
    return list(rule.get("emojis") or [])


class AutoReactionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return
        if message.author == self.bot.user:
            return
        if not isinstance(message.channel, (discord.TextChannel, discord.Thread)):
            return

        settings = auto_reactions_core.get_settings(message.guild.id)
        rules = auto_reactions_core.matching_rules_for_message(
            settings,
            channel_id=message.channel.id,
            content=message.content or "",
            author_is_bot=bool(message.author.bot),
        )
        if not rules:
            return

        seen: set[str] = set()
        for rule in rules:
            for token in _emoji_targets(message.guild, rule):
                if isinstance(token, discord.Emoji):
                    key = str(token.id)
                    emoji = token
                else:
                    key = str(token).strip()
                    if not key:
                        continue
                    emoji = _resolve_emoji(message.guild, key)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    await message.add_reaction(emoji)
                except discord.HTTPException:
                    logger.debug(
                        "auto_reactions add failed guild=%s emoji=%s",
                        message.guild.id,
                        key,
                    )


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoReactionsCog(bot))
