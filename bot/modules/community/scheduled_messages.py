"""Scheduled messages cog: posts due one-shot / daily messages."""

import logging

import discord
from discord.ext import commands, tasks

import bot.modules.community.scheduled_messages_core as scheduled_messages_core

logger = logging.getLogger("scheduled_messages")


class ScheduledMessagesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.scheduler_loop.start()

    def cog_unload(self):
        self.scheduler_loop.cancel()

    @tasks.loop(minutes=1)
    async def scheduler_loop(self):
        try:
            for guild in self.bot.guilds:
                try:
                    due = scheduled_messages_core.due_messages(guild.id)
                    for msg in due:
                        channel = self.bot.get_channel(int(msg["channel_id"]))
                        if channel is None:
                            continue
                        try:
                            await channel.send(content=msg["content"][:2000])
                            scheduled_messages_core.mark_posted(
                                guild.id, msg["id"], once=(msg["schedule_type"] == "once")
                            )
                        except discord.HTTPException as exc:
                            logger.warning("scheduled message post failed guild=%s id=%s", guild.id, msg["id"])
                            cog = self.bot.get_cog("OwnerAlertsCog")
                            if cog:
                                cog.report_module_error(guild.id, "scheduled_messages", str(exc))
                except Exception as exc:
                    logger.exception("scheduler_loop guild=%s", guild.id)
                    cog = self.bot.get_cog("OwnerAlertsCog")
                    if cog:
                        cog.report_module_error(guild.id, "scheduled_messages", str(exc))
        except Exception:
            logger.exception("scheduler_loop error")

    @scheduler_loop.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(ScheduledMessagesCog(bot))
