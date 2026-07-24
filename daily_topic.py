"""Ког «Ежедневная рубрика»: раз в день публикует тему/вопрос дня в заданный
канал, чтобы разговор не затухал в тихие дни. Выключен по умолчанию,
настраивается в дашборде (раздел «Ежедневная рубрика»): канал, набор времён
публикации (случайный выбор одного на день) и сам список тем.
"""

import logging

import discord
from discord.ext import commands, tasks

import daily_topic_core
import i18n

logger = logging.getLogger("daily_topic")


def build_topic_message(text: str, lang: str) -> str:
    return i18n.t("daily_topic.message", lang, text=text)


class DailyTopicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_topic_loop.start()

    def cog_unload(self):
        self.daily_topic_loop.cancel()

    async def post_topic_now(self, guild_id: int) -> dict | None:
        """Публикует тему дня немедленно (используется циклом и ручным триггером
        из дашборда). Возвращает опубликованную тему или None, если канал не
        настроен/не найден, тем нет или отправка не удалась."""
        settings = daily_topic_core.get_settings(guild_id)
        channel_id = settings["channel_id"]
        if not channel_id:
            return None

        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            return None

        topic = daily_topic_core.pick_next_topic(guild_id)
        if topic is None:
            return None

        lang = i18n.lang_for(guild_id)
        try:
            await channel.send(content=build_topic_message(topic["text"], lang))
        except discord.HTTPException:
            logger.warning("Не удалось опубликовать тему дня в канал %s", channel_id)
            return None

        daily_topic_core.mark_posted_today(guild_id)
        return topic

    @tasks.loop(minutes=1)
    async def daily_topic_loop(self):
        # ВСЁ тело цикла под try/except: необработанное исключение (например, гонка
        # чтения конфига с записью из дашборда) навсегда останавливает tasks.loop —
        # именно так расписание «молча умирало», при этом ручная публикация работала.
        try:
            for guild in self.bot.guilds:
                try:
                    if not daily_topic_core.get_settings(guild.id)["enabled"]:
                        continue
                    if not daily_topic_core.should_post_now(guild.id):
                        continue
                    topic = await self.post_topic_now(guild.id)
                    if topic is not None:
                        logger.info("Тема дня опубликована по расписанию: %s (guild=%s)", topic["id"], guild.id)
                    else:
                        logger.warning(
                            "Расписание сработало, но публикация не удалась (канал/темы не настроены?, guild=%s)",
                            guild.id,
                        )
                except Exception as exc:
                    logger.exception("daily_topic_loop guild=%s", guild.id)
                    cog = self.bot.get_cog("OwnerAlertsCog")
                    if cog:
                        cog.report_module_error(guild.id, "daily_topic", str(exc))
        except Exception:
            logger.exception("daily_topic_loop: ошибка итерации — цикл продолжает работать")

    @daily_topic_loop.error
    async def daily_topic_loop_error(self, _error: BaseException):
        # Страховка на случай исключения вне тела (например, в before_loop при
        # реконнекте): логируем и перезапускаем цикл вместо тихой остановки.
        logger.exception("daily_topic_loop: критическая ошибка — перезапуск цикла")
        self.daily_topic_loop.restart()

    @daily_topic_loop.before_loop
    async def before_daily_topic_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(DailyTopicCog(bot))
