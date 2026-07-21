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

import automod_core
import bot_config
import moderation_log
import warns_core
import warns_db

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
    warn_group = app_commands.Group(
        name="warn",
        description="Управление предупреждениями участников",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # {user_id: [{"signature": str, "time": datetime}, ...]} — для фильтра "Повторяемый текст"
        self._repeat_cache: dict[int, list[dict]] = {}
        self._cleanup_repeat_cache.start()

    def cog_unload(self):
        self._cleanup_repeat_cache.cancel()

    @tasks.loop(minutes=5)
    async def _cleanup_repeat_cache(self):
        # Всё тело под try/except: необработанное исключение навсегда остановило бы tasks.loop.
        try:
            now = discord.utils.utcnow()
            stale_users = []
            for user_id, entries in self._repeat_cache.items():
                entries[:] = [e for e in entries if (now - e["time"]).total_seconds() <= REPEATED_TEXT_WINDOW_SECONDS]
                if not entries:
                    stale_users.append(user_id)
            for user_id in stale_users:
                del self._repeat_cache[user_id]
        except Exception:
            logger.exception("_cleanup_repeat_cache: ошибка итерации — цикл продолжает работать")

    @_cleanup_repeat_cache.error
    async def _cleanup_repeat_cache_error(self, _error: BaseException):
        logger.exception("_cleanup_repeat_cache: критическая ошибка — перезапуск цикла")
        self._cleanup_repeat_cache.restart()

    @_cleanup_repeat_cache.before_loop
    async def _before_cleanup(self):
        await self.bot.wait_until_ready()

    # ────────────────── Обнаружение нарушений ──────────────────

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
        user_id = message.author.id
        now = discord.utils.utcnow()
        entries = self._repeat_cache.setdefault(user_id, [])
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

    # ────────────────── Применение наказания ──────────────────

    async def _handle_violation(self, message: discord.Message, key: str, cfg: dict):
        member = message.author
        guild = message.guild
        reason = f"Автомодерация: {automod_core.FILTER_LABELS[key]}"

        if cfg["delete_message"]:
            try:
                await message.delete()
            except discord.HTTPException:
                pass

        duration = min(cfg["duration_minutes"], automod_core.MAX_DURATION_MINUTES) if cfg["duration_minutes"] > 0 else 0
        await self._apply_punishment(guild, member, cfg["punishment"], duration, reason, source=key)

        if cfg["notify_member"]:
            await self._notify(message, cfg, reason)

        moderation_log.append_event(
            f"automod_{key}",
            member.id,
            member.name,
            reason,
            extra=f"Наказание: {cfg['punishment']}",
        )

    async def _apply_punishment(
        self,
        guild: discord.Guild,
        member: discord.Member,
        punishment: str,
        duration_minutes: int,
        reason: str,
        source: str,
    ):
        if punishment == "warn":
            warns_core.add_warn(guild.id, member.id, reason, None, source=source, duration_minutes=duration_minutes)
            await self.apply_escalation_if_needed(guild, member)
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
                    asyncio.create_task(self._scheduled_unban(guild, member.id, duration_minutes))
        # punishment == "none" — без дополнительного действия

    async def apply_escalation_if_needed(self, guild: discord.Guild, member: discord.Member):
        count = warns_core.get_active_warn_count(guild.id, member.id)
        rule = automod_core.find_escalation_rule(guild.id, count)
        if rule is None:
            return
        reason = f"Автоматическая эскалация: {count} активных предупреждений"
        duration = min(rule["duration_minutes"], automod_core.MAX_DURATION_MINUTES) if rule["duration_minutes"] > 0 else 0
        await self._apply_punishment(guild, member, rule["action"], duration, reason, source="escalation")
        moderation_log.append_event(
            "warn_escalation",
            member.id,
            member.name,
            reason,
            extra=f"Действие: {rule['action']}",
        )

    async def _scheduled_unban(self, guild: discord.Guild, user_id: int, duration_minutes: int):
        try:
            await asyncio.sleep(duration_minutes * 60)
            await guild.unban(discord.Object(id=user_id), reason="Автомодерация: истёк срок временного наказания")
        except discord.HTTPException:
            pass
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ошибка авто-разбана после эскалации/наказания для %s", user_id)

    async def _notify(self, message: discord.Message, cfg: dict, reason: str):
        text = automod_core.render_notify_template(cfg["notify_template"], message.author.mention, reason)
        channel = message.channel
        if cfg["notify_channel_id"]:
            target = self.bot.get_channel(int(cfg["notify_channel_id"]))
            if target is not None:
                channel = target
        try:
            await channel.send(text, allowed_mentions=discord.AllowedMentions(users=True))
        except discord.HTTPException:
            pass

    # ────────────────── Команды /warn ──────────────────

    @warn_group.command(name="add", description="Выдать предупреждение участнику")
    @app_commands.describe(участник="Кому выдать предупреждение", причина="За что выдано предупреждение")
    async def warn_add(self, interaction: discord.Interaction, участник: discord.Member, причина: str):
        if not interaction.guild:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)

        settings = automod_core.get_settings(interaction.guild.id)
        warns_core.add_warn(
            interaction.guild.id,
            участник.id,
            причина,
            interaction.user.id,
            source="manual",
            duration_minutes=settings["manual_warn_duration_minutes"],
        )
        await self.apply_escalation_if_needed(interaction.guild, участник)
        moderation_log.append_event(
            "warn_manual",
            участник.id,
            участник.name,
            причина,
            moderator_id=interaction.user.id,
            moderator_display=interaction.user.name,
        )

        active = warns_core.get_active_warn_count(interaction.guild.id, участник.id)
        await interaction.followup.send(
            f"⚠️ {участник.mention} получил предупреждение. Активных предупреждений: **{active}**.", ephemeral=True
        )

    @warn_group.command(name="list", description="Показать предупреждения участника")
    @app_commands.describe(участник="Чьи предупреждения показать")
    async def warn_list(self, interaction: discord.Interaction, участник: discord.Member):
        if not interaction.guild:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)

        warns = warns_core.get_warns(interaction.guild.id, участник.id)
        if not warns:
            return await interaction.followup.send(f"У {участник.mention} нет предупреждений.", ephemeral=True)

        now = datetime.now(timezone.utc).isoformat()
        lines = []
        for w in warns[:20]:
            active = not w["removed"] and (not w["expires_at"] or w["expires_at"] > now)
            status = "🟢 активно" if active else ("❌ снято" if w["removed"] else "⏱️ истекло")
            lines.append(f"`#{w['id']}` {status} — {w['reason']}")

        embed = discord.Embed(
            title=f"Предупреждения: {участник.display_name}",
            description="\n".join(lines),
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"Активных: {warns_core.get_active_warn_count(interaction.guild.id, участник.id)}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @warn_group.command(name="remove", description="Снять предупреждение по ID")
    @app_commands.describe(warn_id="ID предупреждения (из /warn list)")
    async def warn_remove(self, interaction: discord.Interaction, warn_id: int):
        await interaction.response.defer(ephemeral=True)
        ok = warns_core.remove_warn(warn_id, interaction.user.id)
        if not ok:
            return await interaction.followup.send("Предупреждение не найдено или уже снято.", ephemeral=True)
        await interaction.followup.send(f"✅ Предупреждение `#{warn_id}` снято.", ephemeral=True)


async def setup(bot: commands.Bot):
    warns_db.db_init()
    await bot.add_cog(AutoMod(bot))
