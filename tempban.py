import discord
from discord.ext import commands
import asyncio
import logging

import bot_config
import i18n
import moderation_log
import tempban_core
from message_template_core import substitute

logger = logging.getLogger("chetbot.tempban")


def tempban_reason(lang: str) -> str:
    return tempban_core.ban_reason_for_api()


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
            lang = i18n.lang_for(guild.id)
            reason = tempban_reason(lang)
            try:
                bans = [entry async for entry in guild.bans()]
            except discord.Forbidden:
                continue
            except Exception:
                continue

            for ban_entry in bans:
                if tempban_core.is_tempban_ban_reason(ban_entry.reason):
                    try:
                        await guild.unban(
                            ban_entry.user,
                            reason=i18n.t("tempban.recovery_unban_reason", lang),
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
        lang = i18n.lang_for(guild.id)

        log_channel_id = bot_config.get(guild.id, "SPAM_LOG_CHANNEL_ID")
        log_channel = None
        if log_channel_id:
            log_channel = guild.get_channel(int(log_channel_id))

        content_preview = message.content[:1024] if message.content else i18n.t("tempban.content_empty", lang)
        now = discord.utils.utcnow()

        tb_settings = tempban_core.get_settings(guild.id)
        invite_link = bot_config.resolve_server_invite_link(guild.id)
        dm_status = i18n.t("tempban.dm_success", lang)
        if tb_settings.get("dm_enabled", True):
            dm_text = (tb_settings.get("dm_message") or "").strip() or tempban_core.default_dm_message(lang)
            dm_text = substitute(dm_text, tempban_core.dm_variables(member, guild, invite_link))
            try:
                await member.send(dm_text)
            except Exception:
                dm_status = i18n.t("tempban.dm_failed", lang)
        else:
            dm_status = i18n.t("tempban.dm_disabled", lang)

        # Небольшая задержка, чтобы сообщение 100% успело дойти до клиента пользователя перед баном
        await asyncio.sleep(1)

        try:
            # 1200 seconds = 20 minutes — Discord удаляет сообщения за этот период при бане
            await member.ban(
                reason=tempban_reason(lang),
                delete_message_seconds=1200,
            )
        except discord.Forbidden:
            embed = discord.Embed(
                title=i18n.t("tempban.error.title", lang),
                description=i18n.t("tempban.error.forbidden", lang, name=member.name, id=member.id),
                color=discord.Color.orange(),
            )
            await self.bot.send_log(guild.id, embed)
            return
        except discord.HTTPException as e:
            embed = discord.Embed(
                title=i18n.t("tempban.error.title", lang),
                description=i18n.t("tempban.error.http", lang, name=member.name, id=member.id, status=e.status, text=e.text),
                color=discord.Color.orange(),
            )
            await self.bot.send_log(guild.id, embed)
            return
        except Exception as e:
            embed = discord.Embed(
                title=i18n.t("tempban.error.title", lang),
                description=i18n.t("tempban.error.generic", lang, name=member.name, id=member.id, error=e),
                color=discord.Color.orange(),
            )
            await self.bot.send_log(guild.id, embed)
            return

        # Небольшая задержка чтобы бан успел примениться на стороне Discord
        await asyncio.sleep(2)

        unban_error = None
        unban_time = discord.utils.utcnow()
        try:
            await guild.unban(
                discord.Object(id=member.id),
                reason=tempban_core.unban_reason(tb_settings, lang),
            )
        except discord.NotFound:
            pass  # Уже разбанен — нормально
        except discord.Forbidden:
            unban_error = i18n.t("tempban.unban_forbidden", lang)
        except Exception as e:
            unban_error = str(e)

        moderation_log.append_event(
            guild.id,
            "tempban",
            member.id,
            member.name,
            tempban_reason(lang),
            extra=i18n.t(
                "tempban.log_extra", lang,
                channel=f"<#{message.channel.id}>",
                status="ok" if not unban_error else unban_error,
            ),
        )

        if tb_settings.get("log_enabled", True):
            log_vars = {
                "name": member.name,
                "user_id": str(member.id),
                "ban_time": discord.utils.format_dt(now),
                "unban_time": discord.utils.format_dt(unban_time) if not unban_error else f"❌ {unban_error}",
                "channel": f"<#{message.channel.id}>",
                "dm_status": dm_status,
                "message_preview": content_preview,
                "unban_error": unban_error or "",
            }
            embed = tempban_core.build_log_embed(tb_settings, lang, log_vars)
            if unban_error:
                embed.add_field(
                    name=i18n.t("tempban.embed.unban_error", lang),
                    value=i18n.t("tempban.embed.unban_error_value", lang, error=unban_error),
                    inline=False,
                )
            await self._send_tempban_log(guild, embed)

    async def _send_tempban_log(self, guild: discord.Guild, embed: discord.Embed) -> None:
        for key in ("TEMPBAN_LOG_CHANNEL_ID", "SPAM_LOG_CHANNEL_ID", "LOG_CHANNEL_ID"):
            raw = bot_config.get(guild.id, key)
            if not raw:
                continue
            ch = guild.get_channel(int(raw))
            if ch:
                await ch.send(embed=embed)
                return


async def setup(bot):
    await bot.add_cog(TempBan(bot))
