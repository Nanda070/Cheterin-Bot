"""Quote cog: mention the bot in a reply → quote PNG of the referenced message."""

from __future__ import annotations

import asyncio
import io
import logging

import aiohttp
import discord
from discord.ext import commands

import bot.cards.quote_card as quote_card
import bot.modules.utility.quote_core as quote_core

logger = logging.getLogger("chetbot.quote")

_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")


async def _avatar_bytes(guild: discord.Guild | None, user) -> bytes | None:
    """Prefer guild member display avatar; force static PNG for reliable PIL decode."""
    subject = user
    if guild is not None:
        uid = getattr(user, "id", None)
        if uid is not None:
            member = guild.get_member(uid)
            if member is None:
                try:
                    member = await guild.fetch_member(uid)
                except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                    member = None
            if member is not None:
                subject = member
    try:
        asset = subject.display_avatar
        if hasattr(asset, "replace"):
            asset = asset.replace(size=256, format="png")
        return await asset.read()
    except Exception:
        return None


def _attachment_is_image(att: discord.Attachment) -> bool:
    ct = (att.content_type or "").lower()
    name = (att.filename or "").lower()
    if ct.startswith("image/"):
        return True
    if name.endswith(_IMAGE_EXTS):
        return True
    # Discord sets width/height for image uploads even when content_type is missing.
    return bool(getattr(att, "width", None) and getattr(att, "height", None))


async def _read_url_bytes(url: str) -> bytes | None:
    if not url:
        return None
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.read()
                return data or None
    except Exception:
        return None


async def _first_image_bytes(message: discord.Message) -> bytes | None:
    """Load the first image from attachments, then embed image/thumbnail URLs."""
    for att in message.attachments:
        if not _attachment_is_image(att):
            continue
        try:
            return await att.read()
        except Exception:
            # Fallback to CDN URL if Attachment.read fails (expired signed URL edge cases).
            url = getattr(att, "proxy_url", None) or getattr(att, "url", None)
            data = await _read_url_bytes(str(url) if url else "")
            if data:
                return data

    for emb in message.embeds:
        for slot in (emb.image, emb.thumbnail):
            if slot is None:
                continue
            url = getattr(slot, "proxy_url", None) or getattr(slot, "url", None)
            data = await _read_url_bytes(str(url) if url else "")
            if data:
                return data
    return None


async def _resolve_referenced_message(bot: commands.Bot, message: discord.Message) -> discord.Message | None:
    """Always fetch by id when possible — gateway ``resolved`` can omit attachments."""
    ref = message.reference
    if ref is None or ref.message_id is None:
        return None

    channel = message.channel
    if ref.channel_id and ref.channel_id != getattr(channel, "id", None):
        found = bot.get_channel(ref.channel_id)
        if found is None:
            try:
                found = await bot.fetch_channel(ref.channel_id)
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                found = None
        if found is not None:
            channel = found

    try:
        return await channel.fetch_message(ref.message_id)
    except (discord.NotFound, discord.HTTPException, discord.Forbidden, AttributeError):
        resolved = ref.resolved
        return resolved if isinstance(resolved, discord.Message) else None


def _format_referenced_text(guild: discord.Guild | None, message: discord.Message) -> str:
    """Resolve mentions to @names and scrub emoji/dashes for PIL fonts."""
    user_names: dict[int, str] = {}
    for u in getattr(message, "mentions", None) or []:
        uid = getattr(u, "id", None)
        if uid is None:
            continue
        name = getattr(u, "display_name", None) or getattr(u, "name", None) or str(uid)
        user_names[int(uid)] = str(name)
        if guild is not None:
            member = guild.get_member(int(uid))
            if member is not None:
                user_names[int(uid)] = member.display_name

    # Mentions present in content but missing from message.mentions (rare).
    for m in quote_core._USER_MENTION_RE.finditer(message.content or ""):
        uid = int(m.group(1))
        if uid in user_names:
            continue
        if guild is not None:
            member = guild.get_member(uid)
            if member is not None:
                user_names[uid] = member.display_name
                continue
        user_names.setdefault(uid, "user")

    role_names: dict[int, str] = {}
    for r in getattr(message, "role_mentions", None) or []:
        rid = getattr(r, "id", None)
        name = getattr(r, "name", None)
        if rid is not None and name:
            role_names[int(rid)] = str(name)

    channel_names: dict[int, str] = {}
    for ch in getattr(message, "channel_mentions", None) or []:
        cid = getattr(ch, "id", None)
        name = getattr(ch, "name", None)
        if cid is not None and name:
            channel_names[int(cid)] = str(name)

    return quote_core.format_quote_plaintext(
        message.content or "",
        user_names=user_names,
        role_names=role_names,
        channel_names=channel_names,
    ) or "…"


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

        referenced = await _resolve_referenced_message(self.bot, message)
        if not isinstance(referenced, discord.Message):
            return

        # Fetch first, then gate — need referenced.author.bot so reply-to-bot
        # (Discord auto-ping) and bot-authored targets never become quote cards.
        if not quote_core.should_quote(
            guild_id=message.guild.id,
            author_is_bot=bool(message.author.bot),
            bot_user_id=self.bot.user.id,
            mentions=list(message.mentions),
            content=message.content or "",
            has_reference=True,
            referenced_text=(referenced.content or ""),
            referenced_author_is_bot=bool(getattr(referenced.author, "bot", False)),
            settings=settings,
        ):
            return

        text = (referenced.content or "").strip()
        min_length = int(settings.get("min_length") or 0)
        if min_length > 0 and len(text) < min_length:
            return

        attachment = await _first_image_bytes(referenced)
        if not text and not attachment and not referenced.attachments:
            return

        author = referenced.author
        display = getattr(author, "display_name", None) or getattr(author, "name", "Unknown")
        avatar = await _avatar_bytes(message.guild, author)
        quote_body = _format_referenced_text(message.guild, referenced) if text else (
            ":paperclip:" if attachment or referenced.attachments else "…"
        )

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
