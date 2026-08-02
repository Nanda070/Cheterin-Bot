"""Starboard: mirror highly-reacted messages into a configured channel."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

import embed_style
import starboard_core
import starboard_db

logger = logging.getLogger("starboard")

CONTENT_SNIPPET = 500


class StarboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _count_stars(
        self,
        message: discord.Message,
        configured_emoji: str,
        *,
        self_star: bool,
    ) -> int:
        count = 0
        for reaction in message.reactions:
            if not starboard_core.emoji_matches(configured_emoji, reaction.emoji):
                continue
            async for user in reaction.users():
                if not starboard_core.should_include_reactor(
                    reactor_id=user.id,
                    author_id=message.author.id,
                    reactor_is_bot=bool(getattr(user, "bot", False)),
                    self_star=self_star,
                ):
                    continue
                count += 1
        return count

    def _build_embed(self, message: discord.Message, count: int, emoji: str) -> discord.Embed:
        author = message.author
        content = (message.content or "").strip()
        if len(content) > CONTENT_SNIPPET:
            content = content[: CONTENT_SNIPPET - 1] + "…"

        embed = discord.Embed(
            description=content or None,
            color=embed_style.GOLD,
            timestamp=message.created_at,
        )
        embed.set_author(
            name=getattr(author, "display_name", None) or author.name,
            icon_url=getattr(getattr(author, "display_avatar", None), "url", None),
        )
        embed.add_field(
            name="Source",
            value=f"[Jump to message]({message.jump_url})",
            inline=False,
        )
        embed.set_footer(text=f"{emoji} {count} · #{getattr(message.channel, 'name', message.channel.id)}")

        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith("image/"):
                embed.set_image(url=attachment.url)
                break
        return embed

    async def _sync_message(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id is None:
            return
        guild_id = payload.guild_id
        settings = starboard_core.get_settings(guild_id)
        if not settings["enabled"] or not settings["channel_id"]:
            return

        if not starboard_core.emoji_matches(settings["emoji"], payload.emoji):
            return

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return

        # Ignore reactions on the starboard channel itself to avoid loops.
        if str(payload.channel_id) == settings["channel_id"]:
            return

        channel = guild.get_channel(payload.channel_id) or self.bot.get_channel(payload.channel_id)
        if channel is None or not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return

        if settings["ignore_nsfw"] and getattr(channel, "nsfw", False):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.HTTPException):
            return

        if message.author.bot:
            return

        count = await self._count_stars(
            message, settings["emoji"], self_star=settings["self_star"],
        )
        threshold = settings["threshold"]
        star_channel = guild.get_channel(int(settings["channel_id"]))
        if star_channel is None or not hasattr(star_channel, "send"):
            return

        existing_id = starboard_db.get_starboard_message(guild_id, message.id)

        if count >= threshold:
            embed = self._build_embed(message, count, settings["emoji"])
            content = f"{settings['emoji']} **{count}** | <#{message.channel.id}>"
            if existing_id:
                try:
                    sb_msg = await star_channel.fetch_message(existing_id)
                    await sb_msg.edit(content=content, embed=embed)
                    return
                except (discord.NotFound, discord.HTTPException):
                    existing_id = None
            try:
                sb_msg = await star_channel.send(content=content, embed=embed)
            except discord.HTTPException:
                logger.warning("starboard send failed guild=%s", guild_id)
                return
            starboard_db.upsert(guild_id, message.id, sb_msg.id, star_channel.id)
        elif existing_id:
            try:
                sb_msg = await star_channel.fetch_message(existing_id)
                await sb_msg.delete()
            except (discord.NotFound, discord.HTTPException):
                pass
            starboard_db.delete(guild_id, message.id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == getattr(self.bot.user, "id", None):
            return
        await self._sync_message(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self._sync_message(payload)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if payload.guild_id is None:
            return
        guild_id = payload.guild_id
        settings = starboard_core.get_settings(guild_id)
        if not settings["channel_id"]:
            return

        # If original was deleted, remove starboard post.
        sb_id = starboard_db.get_starboard_message(guild_id, payload.message_id)
        if sb_id is None:
            # If the starboard message itself was deleted, drop mapping.
            original = starboard_db.find_by_starboard_message(guild_id, payload.message_id)
            if original is not None:
                starboard_db.delete(guild_id, original)
            return

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            starboard_db.delete(guild_id, payload.message_id)
            return
        star_channel = guild.get_channel(int(settings["channel_id"]))
        if star_channel is not None and hasattr(star_channel, "fetch_message"):
            try:
                sb_msg = await star_channel.fetch_message(sb_id)
                await sb_msg.delete()
            except (discord.NotFound, discord.HTTPException):
                pass
        starboard_db.delete(guild_id, payload.message_id)


async def setup(bot: commands.Bot):
    starboard_db.init()
    await bot.add_cog(StarboardCog(bot))
