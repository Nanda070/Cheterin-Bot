"""Ког «Автомодерация»: 9 настраиваемых фильтров сообщений, эскалация по
количеству активных предупреждений и команды /warn для ручной выдачи/снятия.
Модуль выключен по умолчанию — включается тумблером в дашборде (раздел
«Автомодерация»), каждый фильтр настраивается отдельно.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

import bot.core.embed_style as embed_style
import bot.modules.moderation.automod_core as automod_core
import bot.config as bot_config
import bot.core.i18n as i18n
import bot.core.moderation_embed_core as moderation_embed_core
import bot.core.moderation_log as moderation_log
import bot.core.slash_registry as slash_registry
import bot.modules.moderation.warns_core as warns_core
import bot.modules.moderation.warns_db as warns_db

logger = logging.getLogger("automod")

REPEATED_TEXT_WINDOW_SECONDS = 60


def _consecutive_run_length(entries: list[dict], signature: str) -> int:
    count = 0
    for entry in reversed(entries):
        if entry["signature"] == signature:
            count += 1
        else:
            break
    return count


class AutoMod(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._repeat_cache: dict[tuple[int, int], list[dict]] = {}
        self._cleanup_repeat_cache.start()

    def cog_unload(self):
        self._cleanup_repeat_cache.cancel()

    @tasks.loop(minutes=5)
    async def _cleanup_repeat_cache(self):
        try:
            now = discord.utils.utcnow()
            stale_keys = []
            for key, entries in self._repeat_cache.items():
                entries[:] = [e for e in entries if (now - e["time"]).total_seconds() <= REPEATED_TEXT_WINDOW_SECONDS]
                if not entries:
                    stale_keys.append(key)
            for key in stale_keys:
                del self._repeat_cache[key]
        except Exception:
            logger.exception("_cleanup_repeat_cache: ошибка итерации — цикл продолжает работать")

    @_cleanup_repeat_cache.error
    async def _cleanup_repeat_cache_error(self, _error: BaseException):
        logger.exception("_cleanup_repeat_cache: критическая ошибка — перезапуск цикла")
        self._cleanup_repeat_cache.restart()

    @_cleanup_repeat_cache.before_loop
    async def _before_cleanup(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if not isinstance(message.author, discord.Member):
            return
        if message.author.guild_permissions.administrator:
            return

        settings = automod_core.get_settings(message.guild.id)
        if not settings["enabled"]:
            return

        content = message.content or ""

        for key in automod_core.FILTER_KEYS:
            cfg = settings["filters"][key]
            if not cfg["enabled"]:
                continue
            if self._is_violation(key, message, content, cfg):
                await self._handle_violation(message, key, cfg)
                return

    def _is_violation(self, key: str, message: discord.Message, content: str, cfg: dict) -> bool:
        if key == "links":
            return automod_core.detect_links(content, cfg["whitelist_domains"])
        if key == "invites":
            return automod_core.detect_invites(content, cfg["allow_own_server"], bot_config.get(message.guild.id, "SERVER_INVITE_LINK") or "")
        if key == "scam_links":
            return automod_core.detect_scam_links(content, cfg["blocklist_keywords"])
        if key == "bad_words":
            return automod_core.detect_bad_words(content, cfg["words"])
        if key == "repeated_text":
            return self._check_repeated_text(message, content, cfg)
        if key == "caps_lock":
            return automod_core.detect_caps_lock(content, cfg["max_percent"], cfg["min_length"])
        if key == "emoji_spam":
            return automod_core.detect_emoji_spam(content, cfg["max_count"])
        if key == "mentions":
            mention_count = len(message.mentions) + len(message.role_mentions) + (1 if message.mention_everyone else 0)
            return automod_core.detect_mentions(mention_count, cfg["max_count"])
        if key == "zalgo":
            return automod_core.detect_zalgo(content, cfg["max_count"])
        return False

    def _check_repeated_text(self, message: discord.Message, content: str, cfg: dict) -> bool:
        if not content:
            return False
        cache_key = (message.guild.id, message.author.id)
        now = discord.utils.utcnow()
        entries = self._repeat_cache.setdefault(cache_key, [])
        entries[:] = [e for e in entries if (now - e["time"]).total_seconds() <= REPEATED_TEXT_WINDOW_SECONDS]

        if cfg["consecutive_only"]:
            run_length = _consecutive_run_length(entries, content)
            recent_signatures = [content] * run_length
        else:
            recent_signatures = [e["signature"] for e in entries]

        triggered = automod_core.detect_repeated_text(recent_signatures, content, cfg["max_repeats"])

        if triggered and cfg["reset_on_trigger"]:
            entries.clear()
        else:
            entries.append({"signature": content, "time": now})

        return triggered

    async def _handle_violation(self, message: discord.Message, key: str, cfg: dict):
        member = message.author
        guild = message.guild
        lang = i18n.lang_for(guild.id)
        reason = i18n.t("automod.reason", lang, filter=automod_core.FILTER_LABELS[key])

        if cfg["delete_message"]:
            try:
                await message.delete()
            except discord.HTTPException:
                pass

        duration = min(cfg["duration_minutes"], automod_core.MAX_DURATION_MINUTES) if cfg["duration_minutes"] > 0 else 0
        await self._apply_punishment(guild, member, cfg["punishment"], duration, reason, source=key, lang=lang)

        if cfg["notify_member"]:
            await self._notify(message, cfg, reason)

        extra = i18n.t("automod.punishment_extra", lang, punishment=cfg["punishment"])
        moderation_log.append_event(
            guild.id,
            f"automod_{key}",
            member.id,
            member.name,
            reason,
            extra=extra,
        )
        await self._send_mod_log(
            guild.id,
            title=i18n.t("automod.embed.title", lang, filter=automod_core.FILTER_LABELS[key]),
            member=member,
            reason=reason,
            extra=extra,
            lang=lang,
        )

    async def _send_mod_log(
        self,
        guild_id: int,
        *,
        title: str,
        member: discord.abc.User,
        reason: str,
        extra: str = "",
        lang: str,
        actor: discord.abc.User | None = None,
    ):
        embed = moderation_embed_core.build_user_action_embed(
            lang,
            title=title,
            actor=actor if actor is not None else self.bot.user,
            target_name=member.name,
            target_id=member.id,
            target_mention=getattr(member, "mention", None),
            reason=reason,
            extra=extra,
            color=embed_style.WARN,
            footer_key="moderation.embed.footer",
        )
        await self.bot.send_log(guild_id, embed)

    async def _apply_punishment(
        self,
        guild: discord.Guild,
        member: discord.Member,
        punishment: str,
        duration_minutes: int,
        reason: str,
        source: str,
        lang: str | None = None,
    ):
        lang = lang or i18n.lang_for(guild.id)
        if punishment == "warn":
            warns_core.add_warn(guild.id, member.id, reason, None, source=source, duration_minutes=duration_minutes)
            await self.apply_escalation_if_needed(guild, member, lang=lang)
        elif punishment == "mute":
            until = discord.utils.utcnow() + timedelta(minutes=duration_minutes or 1440)
            try:
                await member.timeout(until, reason=reason)
            except discord.Forbidden:
                logger.warning("Нет прав для таймаута %s", member.id)
        elif punishment == "kick":
            try:
                await member.kick(reason=reason)
            except discord.Forbidden:
                logger.warning("Нет прав для кика %s", member.id)
        elif punishment == "ban":
            try:
                await member.ban(reason=reason, delete_message_seconds=0)
            except discord.Forbidden:
                logger.warning("Нет прав для бана %s", member.id)
            else:
                if duration_minutes > 0:
                    asyncio.create_task(self._scheduled_unban(guild, member.id, duration_minutes, lang))

    async def apply_escalation_if_needed(self, guild: discord.Guild, member: discord.Member, lang: str | None = None):
        lang = lang or i18n.lang_for(guild.id)
        count = warns_core.get_active_warn_count(guild.id, member.id)
        rule = automod_core.find_escalation_rule(guild.id, count)
        if rule is None:
            return
        reason = i18n.t("automod.escalation_reason", lang, count=count)
        duration = min(rule["duration_minutes"], automod_core.MAX_DURATION_MINUTES) if rule["duration_minutes"] > 0 else 0
        await self._apply_punishment(guild, member, rule["action"], duration, reason, source="escalation", lang=lang)
        extra = i18n.t("automod.escalation_extra", lang, action=rule["action"])
        moderation_log.append_event(
            guild.id,
            "warn_escalation",
            member.id,
            member.name,
            reason,
            extra=extra,
        )
        await self._send_mod_log(
            guild.id,
            title=i18n.t("automod.embed.escalation_title", lang),
            member=member,
            reason=reason,
            extra=extra,
            lang=lang,
        )

    async def _scheduled_unban(self, guild: discord.Guild, user_id: int, duration_minutes: int, lang: str):
        try:
            await asyncio.sleep(duration_minutes * 60)
            await guild.unban(discord.Object(id=user_id), reason=i18n.t("automod.unban_reason", lang))
        except discord.HTTPException:
            pass
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ошибка авто-разбана после эскалации/наказания для %s", user_id)

    async def _notify(self, message: discord.Message, cfg: dict, reason: str):
        text = automod_core.render_notify_template(cfg["notify_template"], message.author.mention, reason)
        channel = message.channel
        if cfg["notify_channel_id"] and message.guild is not None:
            target = message.guild.get_channel(int(cfg["notify_channel_id"]))
            if target is not None:
                channel = target
        try:
            await channel.send(text, allowed_mentions=discord.AllowedMentions(users=True))
        except discord.HTTPException:
            pass

    @app_commands.command(name="warn", description="Управление предупреждениями участников")
    @app_commands.describe(
        action="Действие: add / list / remove",
        member="Участник (для add и list)",
        reason="Причина (для add)",
        warn_id="ID предупреждения (для remove, из /warn list)",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="add", value="add"),
            app_commands.Choice(name="list", value="list"),
            app_commands.Choice(name="remove", value="remove"),
        ]
    )
    @app_commands.default_permissions(manage_guild=True)
    async def warn_command(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        member: discord.Member | None = None,
        reason: str | None = None,
        warn_id: int | None = None,
    ):
        lang = i18n.lang_for(interaction.guild_id)
        if not interaction.guild:
            return await interaction.response.send_message(i18n.t("automod.guild_only", lang), ephemeral=True)

        act = action.value
        if act == "add":
            if member is None or not (reason or "").strip():
                return await interaction.response.send_message(
                    i18n.t("automod.warn.error.add_args", lang), ephemeral=True,
                )
            await interaction.response.defer(ephemeral=True)
            settings = automod_core.get_settings(interaction.guild.id)
            reason_text = reason.strip()
            warns_core.add_warn(
                interaction.guild.id,
                member.id,
                reason_text,
                interaction.user.id,
                source="manual",
                duration_minutes=settings["manual_warn_duration_minutes"],
            )
            await self.apply_escalation_if_needed(interaction.guild, member, lang=lang)
            moderation_log.append_event(
                interaction.guild.id,
                "warn_manual",
                member.id,
                member.name,
                reason_text,
                moderator_id=interaction.user.id,
                moderator_display=interaction.user.name,
            )
            await self._send_mod_log(
                interaction.guild.id,
                title=i18n.t("automod.embed.warn_title", lang),
                member=member,
                reason=reason_text,
                lang=lang,
                actor=interaction.user,
            )
            active = warns_core.get_active_warn_count(interaction.guild.id, member.id)
            await interaction.followup.send(
                i18n.t("automod.warn.add_success", lang, mention=member.mention, count=active),
                ephemeral=True,
            )
            return

        if act == "list":
            if member is None:
                return await interaction.response.send_message(
                    i18n.t("automod.warn.error.list_args", lang), ephemeral=True,
                )
            await interaction.response.defer(ephemeral=True)
            warns = warns_core.get_warns(interaction.guild.id, member.id)
            if not warns:
                return await interaction.followup.send(
                    i18n.t("automod.warn.no_warns", lang, mention=member.mention), ephemeral=True,
                )
            now = datetime.now(timezone.utc).isoformat()
            lines = []
            for w in warns[:20]:
                active = not w["removed"] and (not w["expires_at"] or w["expires_at"] > now)
                if active:
                    status = i18n.t("automod.warn.status_active", lang)
                elif w["removed"]:
                    status = i18n.t("automod.warn.status_removed", lang)
                else:
                    status = i18n.t("automod.warn.status_expired", lang)
                lines.append(i18n.t("automod.warn.list_entry", lang, id=w["id"], status=status, reason=w["reason"]))
            embed = discord.Embed(
                title=i18n.t("automod.warn.list_title", lang, name=member.display_name),
                description="\n".join(lines),
                color=embed_style.WARN,
            )
            embed.set_footer(text=i18n.t(
                "automod.warn.list_footer", lang,
                count=warns_core.get_active_warn_count(interaction.guild.id, member.id),
            ))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if warn_id is None:
            return await interaction.response.send_message(
                i18n.t("automod.warn.error.remove_args", lang), ephemeral=True,
            )
        await interaction.response.defer(ephemeral=True)
        ok = warns_core.remove_warn(warn_id, interaction.user.id, guild_id=interaction.guild.id)
        if not ok:
            return await interaction.followup.send(i18n.t("automod.warn.remove_not_found", lang), ephemeral=True)
        await interaction.followup.send(i18n.t("automod.warn.remove_success", lang, id=warn_id), ephemeral=True)


async def setup(bot: commands.Bot):
    warns_db.db_init()
    cog = AutoMod(bot)
    slash_registry.register_automod(cog)
    await bot.add_cog(cog)
