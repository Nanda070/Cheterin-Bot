import logging
import os

import discord
from discord.ext import commands

import settings_db

import i18n

logger = logging.getLogger("news-relay")

MODULE_NAME = "news"

MAX_LOG_LENGTH = 2600


def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    """Настройки ретрансляции сервера с дефолтами."""
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "enabled": bool(data.get("enabled", True)),
        "source_guild_id": str(data.get("source_guild_id") or ""),
        "source_bot_ids": [str(v) for v in data.get("source_bot_ids", [])],
        "log_channel_id": str(data.get("log_channel_id") or ""),
        "mappings": [
            {
                "source_channel_id": str(m.get("source_channel_id") or ""),
                "target_channel_id": str(m.get("target_channel_id") or ""),
                "label": str(m.get("label") or ""),
            }
            for m in data.get("mappings", [])
        ],
    }


def get_channel_map(guild_id: int) -> dict[int, int]:
    result = {}
    for m in get_settings(guild_id)["mappings"]:
        try:
            result[int(m["source_channel_id"])] = int(m["target_channel_id"])
        except (TypeError, ValueError):
            continue
    return result


def make_embed(title: str, description: str, color: int) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description if len(description) <= MAX_LOG_LENGTH else description[:MAX_LOG_LENGTH] + "...",
        color=color
    )
    return embed


def _main_guild_id() -> int:
    """Ретрансляция — функция мейн-сервера (Фаза 2b MULTIGUILD_PLAN.md): слушает
    источники на любых серверах, публикует только в целевые каналы мейна. Настройки
    привязаны к мейн-серверу; id резолвится единообразно с main.get_main_guild_id()."""
    return int(os.getenv("GUILD_ID") or os.getenv("MAIN_GUILD_ID") or "1324239354154975252")


class NewsRelay(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_log(self, title: str, description: str, color: int):
        """Отправляет лог-сообщение в лог-канал ретрансляции и выводит его в консоль."""
        settings = get_settings(_main_guild_id())
        raw = settings["log_channel_id"]
        if raw:
            embed = make_embed(title, description, color)
            try:
                log_channel = self.bot.get_channel(int(raw))
                if not log_channel:
                    log_channel = await self.bot.fetch_channel(int(raw))
                await log_channel.send(embed=embed)
            except Exception as e:
                logger.warning("Не удалось отправить лог ретрансляции: %s", e)
        logger.info("[%s] %s", title, description)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            lang = i18n.lang_for(_main_guild_id())
            settings = get_settings(_main_guild_id())
            if not settings["enabled"]:
                return

            # Игнорируем сообщения из лог-канала, чтобы не зацикливаться
            if settings["log_channel_id"] and str(message.channel.id) == settings["log_channel_id"]:
                return

            # Фильтруем: обрабатываем только сообщения от указанных ботов
            if str(message.author.id) not in settings["source_bot_ids"]:
                return

            # Проверяем сервер
            if not message.guild or str(message.guild.id) != settings["source_guild_id"]:
                return

            # Проверяем, что канал есть в channel_map
            channel_map = get_channel_map(_main_guild_id())
            if message.channel.id not in channel_map:
                return

            target_channel_id = channel_map[message.channel.id]
            target_channel = self.bot.get_channel(target_channel_id)
            if not target_channel:
                await self.send_log(
                    "ERROR",
                    i18n.t("news.log.target_missing", lang, channel_id=target_channel_id),
                    0xED4245,
                )
                return

            await self.send_log(
                "DEBUG",
                i18n.t(
                    "news.log.debug_relay",
                    lang,
                    source=message.channel.id,
                    target=target_channel_id,
                ),
                0x5865F2,
            )

            # Собираем вложения, если они есть
            files = []
            for attachment in message.attachments:
                try:
                    file_data = await attachment.read()
                    files.append(discord.File(fp=file_data, filename=attachment.filename))
                except Exception as e:
                    await self.send_log(
                        "ERROR",
                        i18n.t(
                            "news.log.attachment_error",
                            lang,
                            filename=attachment.filename,
                            error=e,
                        ),
                        0xED4245,
                    )

            # Пересылаем текст и вложения
            try:
                if message.content or files:
                    await target_channel.send(
                        content=message.content if message.content else None,
                        files=files if files else None
                    )
            except Exception as e:
                await self.send_log(
                    "ERROR",
                    i18n.t("news.log.send_error", lang, channel_id=target_channel_id, error=e),
                    0xED4245,
                )

            # Пересылаем embeds (каждый отдельно)
            for emb in message.embeds:
                try:
                    await target_channel.send(embed=emb)
                except Exception as e:
                    await self.send_log(
                        "ERROR",
                        i18n.t("news.log.embed_error", lang, channel_id=target_channel_id, error=e),
                        0xED4245,
                    )

        except Exception:
            logger.exception("Исключение в NewsRelay.on_message")


async def setup(bot: commands.Bot):
    await bot.add_cog(NewsRelay(bot))
