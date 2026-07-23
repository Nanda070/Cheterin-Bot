"""Sticky messages: repost sticky content when new messages arrive."""

import asyncio
import logging

import discord
from discord.ext import commands

import sticky_core

logger = logging.getLogger("sticky")


class StickyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._locks: dict[int, asyncio.Lock] = {}
        self._reposting: set[int] = set()  # channel ids currently being updated

    def _lock_for(self, channel_id: int) -> asyncio.Lock:
        lock = self._locks.get(channel_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[channel_id] = lock
        return lock

    async def refresh_sticky(self, channel: discord.TextChannel, sticky: dict) -> bool:
        """Repost sticky. Returns False if send failed (old message left intact)."""
        async with self._lock_for(channel.id):
            self._reposting.add(channel.id)
            try:
                try:
                    msg = await channel.send(content=sticky["content"][:2000])
                except discord.HTTPException:
                    logger.warning("sticky refresh failed channel=%s", channel.id)
                    return False

                sticky_core.set_message_id(channel.guild.id, sticky["id"], str(msg.id))

                old_id = sticky.get("message_id") or ""
                if old_id.isdigit() and old_id != str(msg.id):
                    try:
                        old = await channel.fetch_message(int(old_id))
                        await old.delete()
                    except (discord.NotFound, discord.HTTPException):
                        pass
                return True
            finally:
                self._reposting.discard(channel.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or not isinstance(message.channel, discord.TextChannel):
            return
        if message.channel.id in self._reposting:
            return
        if message.author == self.bot.user:
            return
        sticky = sticky_core.sticky_for_channel(message.guild.id, message.channel.id)
        if sticky is None:
            return
        # Ignore if this message is the sticky itself
        if sticky.get("message_id") and str(message.id) == sticky["message_id"]:
            return
        await self.refresh_sticky(message.channel, sticky)


async def setup(bot: commands.Bot):
    await bot.add_cog(StickyCog(bot))
