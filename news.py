import json
import logging
import os

import discord
from discord.ext import commands

logger = logging.getLogger("news-relay")

CONFIG_FILE = "news_relay.json"

MAX_LOG_LENGTH = 2600


# Кэш конфига: on_message вызывается на каждое сообщение сервера,
# поэтому файл перечитывается только когда изменился на диске.
_cache: dict | None = None
_cache_mtime: float | None = None


def load_config() -> dict:
    global _cache, _cache_mtime
    if not os.path.exists(CONFIG_FILE):
        _cache, _cache_mtime = None, None
        return {}

    mtime = os.path.getmtime(CONFIG_FILE)
    if _cache is not None and _cache_mtime == mtime:
        return _cache

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    _cache, _cache_mtime = data, mtime
    return data


def save_config(data: dict) -> None:
    global _cache, _cache_mtime
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    _cache = data
    _cache_mtime = os.path.getmtime(CONFIG_FILE)


def get_settings() -> dict:
    """Настройки ретрансляции с дефолтами."""
    data = load_config()
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


def get_channel_map() -> dict[int, int]:
    result = {}
    for m in get_settings()["mappings"]:
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


class NewsRelay(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_log(self, title: str, description: str, color: int):
        """Отправляет лог-сообщение в лог-канал ретрансляции и выводит его в консоль."""
        settings = get_settings()
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
            settings = get_settings()
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
            channel_map = get_channel_map()
            if message.channel.id not in channel_map:
                return

            target_channel_id = channel_map[message.channel.id]
            target_channel = self.bot.get_channel(target_channel_id)
            if not target_channel:
                await self.send_log("ERROR", f"Не найден целевой канал с ID {target_channel_id}.", 0xED4245)
                return

            await self.send_log("DEBUG", f"Пересылаем сообщение из {message.channel.id} в {target_channel_id}", 0x5865F2)

            # Собираем вложения, если они есть
            files = []
            for attachment in message.attachments:
                try:
                    file_data = await attachment.read()
                    files.append(discord.File(fp=file_data, filename=attachment.filename))
                except Exception as e:
                    await self.send_log("ERROR", f"Ошибка при обработке вложения {attachment.filename}: {e}", 0xED4245)

            # Пересылаем текст и вложения
            try:
                if message.content or files:
                    await target_channel.send(
                        content=message.content if message.content else None,
                        files=files if files else None
                    )
            except Exception as e:
                await self.send_log("ERROR", f"Ошибка при отправке в канал {target_channel_id}: {e}", 0xED4245)

            # Пересылаем embeds (каждый отдельно)
            for emb in message.embeds:
                try:
                    await target_channel.send(embed=emb)
                except Exception as e:
                    await self.send_log("ERROR", f"Ошибка при отправке embed в канал {target_channel_id}: {e}", 0xED4245)

        except Exception:
            logger.exception("Исключение в NewsRelay.on_message")


async def setup(bot: commands.Bot):
    await bot.add_cog(NewsRelay(bot))
