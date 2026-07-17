"""Ког «Ежедневная рубрика»: раз в день публикует тему/вопрос дня в заданный
канал, чтобы разговор не затухал в тихие дни. Выключен по умолчанию,
настраивается в дашборде (раздел «Ежедневная рубрика»): канал, набор времён
публикации (случайный выбор одного на день) и сам список тем.
"""

import logging

import discord
from discord.ext import commands, tasks

import daily_topic_core

logger = logging.getLogger("daily_topic")


def build_topic_embed(text: str) -> discord.Embed:
    return discord.Embed(
        title="💬 Тема дня",
        description=text,
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow(),
    )


class DailyTopicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_topic_loop.start()

    def cog_unload(self):
        self.daily_topic_loop.cancel()

    async def post_topic_now(self) -> dict | None:
        """Публикует тему дня немедленно (используется циклом и ручным триггером
        из дашборда). Возвращает опубликованную тему или None, если канал не
        настроен/не найден, тем нет или отправка не удалась."""
        settings = daily_topic_core.get_settings()
        channel_id = settings["channel_id"]
        if not channel_id:
            return None

        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            return None

        topic = daily_topic_core.pick_next_topic()
        if topic is None:
            return None

        try:
            await channel.send(embed=build_topic_embed(topic["text"]))
        except discord.HTTPException:
            logger.warning("Не удалось опубликовать тему дня в канал %s", channel_id)
            return None

        daily_topic_core.mark_posted_today()
        return topic

    @tasks.loop(minutes=1)
    async def daily_topic_loop(self):
        if not daily_topic_core.get_settings()["enabled"]:
            return
        if not daily_topic_core.should_post_now():
            return
        try:
            await self.post_topic_now()
        except Exception:
            logger.exception("daily_topic_loop: не удалось опубликовать тему дня")

    @daily_topic_loop.before_loop
    async def before_daily_topic_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(DailyTopicCog(bot))
