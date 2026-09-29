import asyncio
import logging

import discord
from discord.ext import commands

import bot.core.embed_style as embed_style
import bot.config as bot_config
import bot.core.i18n as i18n
import bot.core.moderation_log as moderation_log
import bot.modules.moderation.tempban_core as tempban_core

logger = logging.getLogger("chetbot.tempban")


def tempban_reason(lang: str, action: str = tempban_core.ACTION_SOFTBAN) -> str:
    return tempban_core.ban_reason_for_api(action)


class TempBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Набор user_id, для которых бан уже в процессе — защита от двойного срабатывания
        self._processing: set[int] = set()

    @commands.Cog.listener()
    async def on_ready(self):
        """
        При старте бота проверяем, нет ли пользователей в бан-листе
        с причиной softban Tempban — если есть, разбаниваем их.
        Permanent honeypot bans are left alone.
        """
        for guild in self.bot.guilds:
            lang = i18n.lang_for(guild.id)
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
        if message.author.bot or not message.guild:
            return

        tempban_channel_id = bot_config.get(message.guild.id, "TEMPBAN_CHANNEL_ID")
        if not tempban_channel_id or message.channel.id != int(tempban_channel_id):
            return

        if not isinstance(message.author, discord.Member):
            return

        if message.author.guild_permissions.administrator:
            return

        tb_settings = tempban_core.get_settings(message.guild.id)
        if not tempban_core.should_process_trap(tb_settings):
            return

        # Ignore the sticky warning message itself if somehow re-posted by a non-admin bot-less user
        warning_id = tb_settings.get("warning_message_id") or ""
        if warning_id and str(message.id) == warning_id:
            return

        user_id = message.author.id
        if user_id in self._processing:
            return

        self._processing.add(user_id)
        try:
            await self._do_tempban(message, tb_settings)
        finally:
            self._processing.discard(user_id)

    async def _do_tempban(self, message: discord.Message, tb_settings: dict):
        guild = message.guild
        member = message.author
        lang = i18n.lang_for(guild.id)
        action = tb_settings.get("action") or tempban_core.ACTION_SOFTBAN

        content_preview = message.content[:1024] if message.content else i18n.t("tempban.content_empty", lang)
        now = discord.utils.utcnow()

        invite_link = bot_config.resolve_server_invite_link(guild.id)
        dm_vars = tempban_core.dm_variables(
            member, guild, invite_link,
            action=action,
            ban_count=int(tb_settings.get("ban_count") or 0),
        )
        dm_vars["channel"] = f"<#{message.channel.id}>"

        dm_status = i18n.t("tempban.dm_success", lang)
        if tb_settings.get("dm_enabled", True):
            dm_text = (tb_settings.get("dm_message") or "").strip() or tempban_core.default_dm_message(lang)
            dm_text = tempban_core.render_template(dm_text, dm_vars)
            try:
                await member.send(dm_text)
            except Exception:
                dm_status = i18n.t("tempban.dm_failed", lang)
        else:
            dm_status = i18n.t("tempban.dm_disabled", lang)

        await asyncio.sleep(1)

        try:
            await member.ban(
                reason=tempban_reason(lang, action),
                delete_message_seconds=1200,
            )
        except discord.Forbidden:
            embed = discord.Embed(
                title=i18n.t("tempban.error.title", lang),
                description=i18n.t("tempban.error.forbidden", lang, name=member.name, id=member.id),
                color=embed_style.WARN,
            )
            await self.bot.send_log(guild.id, embed)
            return
        except discord.HTTPException as e:
            embed = discord.Embed(
                title=i18n.t("tempban.error.title", lang),
                description=i18n.t(
                    "tempban.error.http", lang,
                    name=member.name, id=member.id, status=e.status, text=e.text,
                ),
                color=embed_style.WARN,
            )
            await self.bot.send_log(guild.id, embed)
            return
        except Exception as e:
            embed = discord.Embed(
                title=i18n.t("tempban.error.title", lang),
                description=i18n.t(
                    "tempban.error.generic", lang,
                    name=member.name, id=member.id, error=e,
                ),
                color=embed_style.WARN,
            )
            await self.bot.send_log(guild.id, embed)
            return

        unban_error = None
        unban_time = None
        if action == tempban_core.ACTION_SOFTBAN:
            await asyncio.sleep(2)
            unban_time = discord.utils.utcnow()
            try:
                await guild.unban(
                    discord.Object(id=member.id),
                    reason=tempban_core.unban_reason(tb_settings, lang),
                )
            except discord.NotFound:
                pass
            except discord.Forbidden:
                unban_error = i18n.t("tempban.unban_forbidden", lang)
            except Exception as e:
                unban_error = str(e)

        new_count = tempban_core.increment_ban_count(guild.id)
        await self._refresh_warning_embed(guild, ban_count=new_count)

        moderation_log.append_event(
            guild.id,
            "tempban",
            member.id,
            member.name,
            tempban_reason(lang, action),
            extra=i18n.t(
                "tempban.log_extra", lang,
                channel=f"<#{message.channel.id}>",
                status="ok" if not unban_error else unban_error,
            ),
        )

        if tb_settings.get("log_enabled", True):
            if action == tempban_core.ACTION_SOFTBAN:
                unban_display = (
                    discord.utils.format_dt(unban_time)
                    if unban_time and not unban_error
                    else (f"❌ {unban_error}" if unban_error else "—")
                )
            else:
                unban_display = i18n.t("tempban.embed.permanent", lang)

            log_vars = {
                "name": member.name,
                "user_id": str(member.id),
                "mention": member.mention if hasattr(member, "mention") else f"<@{member.id}>",
                "ban_time": discord.utils.format_dt(now),
                "unban_time": unban_display,
                "channel": f"<#{message.channel.id}>",
                "dm_status": dm_status,
                "message_preview": content_preview,
                "unban_error": unban_error or "",
                "guild": guild.name,
                "guild_name": guild.name,
                "action": tempban_core.action_label(action, lang),
                "ban_count": str(new_count),
            }
            embed = tempban_core.build_log_embed(
                lang, log_vars, custom_message=tb_settings.get("log_message") or "",
            )
            if unban_error and not (tb_settings.get("log_message") or "").strip():
                embed.add_field(
                    name=i18n.t("tempban.embed.unban_error", lang),
                    value=i18n.t("tempban.embed.unban_error_value", lang, error=unban_error),
                    inline=False,
                )
            await self._send_tempban_log(guild, embed)

    async def _refresh_warning_embed(self, guild: discord.Guild, *, ban_count: int) -> None:
        settings = tempban_core.get_settings(guild.id)
        message_id = settings.get("warning_message_id") or ""
        channel_id = bot_config.get(guild.id, "TEMPBAN_CHANNEL_ID")
        if not message_id or not channel_id:
            return
        channel = guild.get_channel(int(channel_id))
        if channel is None:
            return
        try:
            msg = await channel.fetch_message(int(message_id))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return
        lang = i18n.lang_for(guild.id)
        action = settings.get("action") or tempban_core.ACTION_SOFTBAN
        # For display on warning, show intended action (not disabled)
        display_action = action if action != tempban_core.ACTION_DISABLED else tempban_core.ACTION_SOFTBAN
        vars_ = tempban_core.warning_variables(
            guild, channel, action=display_action, ban_count=ban_count,
        )
        embed = tempban_core.build_warning_embed(lang, settings, vars_)
        try:
            await msg.edit(embed=embed)
        except discord.HTTPException:
            logger.debug("warning embed update failed guild=%s", guild.id)

    async def _send_tempban_log(self, guild: discord.Guild, embed: discord.Embed) -> None:
        for key in ("TEMPBAN_LOG_CHANNEL_ID", "SPAM_LOG_CHANNEL_ID", "LOG_CHANNEL_ID"):
            raw = bot_config.get(guild.id, key)
            if not raw:
                continue
            ch = guild.get_channel(int(raw))
            if ch:
                await ch.send(embed=embed)
                return


async def publish_warning_panel(bot, guild: discord.Guild) -> discord.Message:
    """Post or edit the honeypot warning embed in the trap channel."""
    channel_id = bot_config.get(guild.id, "TEMPBAN_CHANNEL_ID")
    if not channel_id:
        raise ValueError("trap_channel_not_set")
    channel = guild.get_channel(int(channel_id))
    if channel is None:
        raise ValueError("channel_not_found")

    settings = tempban_core.get_settings(guild.id)
    lang = i18n.lang_for(guild.id)
    action = settings.get("action") or tempban_core.ACTION_SOFTBAN
    display_action = action if action != tempban_core.ACTION_DISABLED else tempban_core.ACTION_SOFTBAN
    vars_ = tempban_core.warning_variables(
        guild, channel,
        action=display_action,
        ban_count=int(settings.get("ban_count") or 0),
    )
    embed = tempban_core.build_warning_embed(lang, settings, vars_)

    message_id = settings.get("warning_message_id") or ""
    if message_id:
        try:
            msg = await channel.fetch_message(int(message_id))
            await msg.edit(embed=embed)
            return msg
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    msg = await channel.send(embed=embed)
    tempban_core.set_warning_message_id(guild.id, msg.id)
    return msg


async def setup(bot):
    await bot.add_cog(TempBan(bot))
