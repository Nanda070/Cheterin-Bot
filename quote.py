"""Quote cog: mention the bot in a reply → quote PNG of the referenced message."""

from __future__ import annotations

import asyncio
import io
import logging

import discord
from discord.ext import commands

import quote_card
import quote_core

logger = logging.getLogger("chetbot.quote")


async def _avatar_bytes(user) -> bytes | None:
    try:
        return await user.display_avatar.replace(size=256).read()
    except Exception:
        return None


async def _first_image_attachment_bytes(message: discord.Message) -> bytes | None:
    for att in message.attachments:
        ct = (att.content_type or "").lower()
        name = (att.filename or "").lower()
        if ct.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            try:
                return await att.read()
            except Exception:
                return None
    return None


class QuoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return
        if self.bot.user is None or message.reference is None:
            return

        settings = quote_core.get_settings(message.guild.id)
        if not quote_core.should_quote(
            guild_id=message.guild.id,
            author_is_bot=bool(message.author.bot),
            bot_user_id=self.bot.user.id,
            mentions=list(message.mentions),
            content=message.content or "",
            has_reference=True,
            referenced_text=None,  # length checked after fetch
            settings={**settings, "min_length": 0},  # defer min_length until we have the target
        ):
            return

        referenced = message.reference.resolved
        if referenced is None:
            try:
                channel = message.channel
                if message.reference.channel_id and message.reference.channel_id != channel.id:
                    channel = self.bot.get_channel(message.reference.channel_id) or channel
                if message.reference.message_id:
                    referenced = await channel.fetch_message(message.reference.message_id)
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                return
        if not isinstance(referenced, discord.Message):
            return

        text = (referenced.content or "").strip()
        min_length = int(settings.get("min_length") or 0)
        if min_length > 0 and len(text) < min_length:
            return
        if not text and not referenced.attachments:
            return

        author = referenced.author
        display = getattr(author, "display_name", None) or getattr(author, "name", "Unknown")
        avatar = await _avatar_bytes(author)
        attachment = await _first_image_attachment_bytes(referenced)
        quote_body = text or "📎"

        try:
            png = await asyncio.to_thread(
                quote_card.render_quote_card,
                display_name=display,
                quote_text=quote_body,
                avatar_bytes=avatar,
                attachment_bytes=attachment,
            )
        except Exception:
            logger.exception("quote render failed guild=%s", message.guild.id)
            return

        file = discord.File(io.BytesIO(png), filename="quote.png")
        try:
            await message.reply(file=file, mention_author=False)
        except discord.HTTPException:
            logger.debug("quote reply failed guild=%s", message.guild.id)
            return

        if settings.get("delete_trigger"):
            try:
                await message.delete()
            except discord.HTTPException:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(QuoteCog(bot))
