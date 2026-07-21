import discord
from discord.ext import commands
import asyncio
import logging

import bot_config
import moderation_log

logger = logging.getLogger("chetbot.tempban")

TEMPBAN_REASON = "Автоматический Tempban (Сброс сообщений за 20 мин.)"


class TempBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Набор user_id, для которых бан уже в процессе — защита от двойного срабатывания
        self._processing: set[int] = set()

    @commands.Cog.listener()
    async def on_ready(self):
        """
        При старте бота проверяем, нет ли пользователей в бан-листе
        с причиной Tempban — если есть, разбаниваем их.
        Это защищает от случая когда бот упал/перезапустился
        между member.ban() и guild.unban() во время asyncio.sleep(2).
        """
        for guild in self.bot.guilds:
            try:
                bans = [entry async for entry in guild.bans()]
            except discord.Forbidden:
                continue
            except Exception:
                continue

            for ban_entry in bans:
                # Точное сравнение причины — не ловит ручные баны
                if ban_entry.reason and ban_entry.reason == TEMPBAN_REASON:
                    try:
                        await guild.unban(
                            ban_entry.user,
                            reason="Авто-разбан после перезапуска (Tempban recovery)",
                        )
                        logger.info("Recovery unban: %s в %s", ban_entry.user, guild.name)
                    except Exception as e:
                        logger.error("Recovery unban error for %s: %s", ban_entry.user, e)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Игнорируем ботов и DM
        if message.author.bot or not message.guild:
            return

        tempban_channel_id = bot_config.get(message.guild.id, "TEMPBAN_CHANNEL_ID")
        if not tempban_channel_id or message.channel.id != int(tempban_channel_id):
            return

        # Проверяем что author — это Member (для доступа к guild_permissions)
        if not isinstance(message.author, discord.Member):
            return

        if message.author.guild_permissions.administrator:
            return

        user_id = message.author.id
        if user_id in self._processing:
            return

        self._processing.add(user_id)
        try:
            await self._do_tempban(message)
        finally:
            self._processing.discard(user_id)

    async def _do_tempban(self, message: discord.Message):
        guild = message.guild
        member = message.author

        log_channel_id = bot_config.get(guild.id, "SPAM_LOG_CHANNEL_ID")
        log_channel = None
        if log_channel_id:
            log_channel = guild.get_channel(int(log_channel_id))

        content_preview = message.content[:1024] if message.content else "Пусто/Медиа"
        now = discord.utils.utcnow()

        invite_link = bot_config.get(guild.id, "SERVER_INVITE_LINK") or "https://discord.gg/cheterin"
        dm_status = "✅ Успешно"
        try:
            await member.send(
                f'Вы были исключенны из сервера "{guild.name}" за отпись в канале в котором вы не должны были писать.\n'
                f'Ссылка на сервер: {invite_link}'
            )
        except Exception:
            dm_status = "❌ Ошибка (ЛС закрыты)"

        # Небольшая задержка, чтобы сообщение 100% успело дойти до клиента пользователя перед баном
        await asyncio.sleep(1)

        try:
            # 1200 seconds = 20 minutes — Discord удаляет сообщения за этот период при бане
            await member.ban(
                reason=TEMPBAN_REASON,
                delete_message_seconds=1200,
            )
        except discord.Forbidden:
            embed = discord.Embed(title="⚠️ Ошибка Tempban", description=f"Не удалось забанить {member.name} (`{member.id}`) — недостаточно прав бота.", color=discord.Color.orange())
            await self.bot.send_log(guild.id, embed)
            return
        except discord.HTTPException as e:
            embed = discord.Embed(title="⚠️ Ошибка Tempban", description=f"HTTP ошибка при Tempban для {member.name} (`{member.id}`): {e.status} {e.text}", color=discord.Color.orange())
            await self.bot.send_log(guild.id, embed)
            return
        except Exception as e:
            embed = discord.Embed(title="⚠️ Ошибка Tempban", description=f"Ошибка при Tempban для {member.name} (`{member.id}`): {e}", color=discord.Color.orange())
            await self.bot.send_log(guild.id, embed)
            return

        # Небольшая задержка чтобы бан успел примениться на стороне Discord
        await asyncio.sleep(2)

        unban_error = None
        unban_time = discord.utils.utcnow()
        try:
            await guild.unban(
                discord.Object(id=member.id),
                reason="Автоматический разбан после Tempban",
            )
        except discord.NotFound:
            pass  # Уже разбанен — нормально
        except discord.Forbidden:
            unban_error = "Недостаточно прав для разбана"
        except Exception as e:
            unban_error = str(e)

        embed = discord.Embed(title="🔨 Автоматический Tempban", color=discord.Color.red())
        embed.add_field(
            name="Пользователь",
            value=f"{member.name} (ID: {member.id})",
            inline=False,
        )
        embed.add_field(name="Время бана", value=discord.utils.format_dt(now), inline=True)
        embed.add_field(
            name="Время разбана",
            value=discord.utils.format_dt(unban_time) if not unban_error else f"❌ {unban_error}",
            inline=True,
        )
        embed.add_field(name="Канал", value=f"<#{message.channel.id}>", inline=False)
        embed.add_field(name="Статус ЛС", value=dm_status, inline=True)
        embed.add_field(name="Сообщение", value=content_preview, inline=False)
        if unban_error:
            embed.add_field(
                name="⚠️ Ошибка разбана",
                value=f"{unban_error}\n> Пользователь может остаться в бан-листе!",
                inline=False,
            )
        embed.set_footer(text="Пользователь кикнут (сообщения за 20 минут удалены).")
        embed.timestamp = now

        moderation_log.append_event(
            "tempban",
            member.id,
            member.name,
            TEMPBAN_REASON,
            extra=f"Канал: <#{message.channel.id}>; unban: {'ok' if not unban_error else unban_error}",
        )

        await self.bot.send_log(guild.id, embed)


async def setup(bot):
    await bot.add_cog(TempBan(bot))
