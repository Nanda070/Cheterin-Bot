"""Ког слэш-команд модерации: /ban /kick /mute /unmute /unban /clear.

Каждое действие пишет в общий журнал модерации (виден на странице «Lockdown и
модерация» дашборда) и, если настроен LOG_CHANNEL_ID, шлёт embed «Кто/Кого/Причина»
— тот же формат, что и у ручных действий из дашборда (dashboard/backend/routes/moderation.py).

Временный бан (/ban с параметром time) переживает перезапуск бота: срок хранится в
ban_db.py, на старте все ещё не истёкшие сроки планируются заново (recover-паттерн
mafia.py/bunker.py).
"""

import asyncio
import logging
import time
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

import ban_db
import moderation_commands_core
import moderation_log

logger = logging.getLogger("moderation-commands")


class ModerationCommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._unban_timers: dict[int, asyncio.Task] = {}
        self._recovered = False

    def cog_unload(self):
        for task in self._unban_timers.values():
            task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if self._recovered:
            return
        self._recovered = True
        rows = ban_db.list_all()
        for row in rows:
            self._schedule_unban(row["id"], row["guild_id"], row["user_id"], row["unban_at_ts"])
        if rows:
            logger.info("Восстановлено запланированных разбанов: %s", len(rows))

    # ────────────────────────── Таймер временного бана ──────────────────────────

    def _schedule_unban(self, row_id: int, guild_id: int, user_id: int, unban_at_ts: int):
        old = self._unban_timers.pop(row_id, None)
        if old:
            old.cancel()
        self._unban_timers[row_id] = self.bot.loop.create_task(
            self._run_unban_timer(row_id, guild_id, user_id, unban_at_ts)
        )

    async def _run_unban_timer(self, row_id: int, guild_id: int, user_id: int, unban_at_ts: int):
        try:
            remaining = unban_at_ts - int(time.time())
            if remaining > 0:
                await asyncio.sleep(remaining)

            guild = self.bot.get_guild(guild_id)
            if guild is not None:
                try:
                    await guild.unban(discord.Object(id=user_id), reason="Истёк срок временного бана (/ban)")
                except discord.HTTPException:
                    pass
            ban_db.remove(row_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ошибка авто-разбана user=%s guild=%s", user_id, guild_id)
        finally:
            self._unban_timers.pop(row_id, None)

    def _cancel_scheduled_unban(self, guild_id: int, user_id: int):
        row = ban_db.get_by_user(guild_id, user_id)
        if row is None:
            return
        task = self._unban_timers.pop(row["id"], None)
        if task:
            task.cancel()
        ban_db.remove(row["id"])

    # ────────────────────────── Журнал действий ──────────────────────────

    async def _log_action(
        self, title: str, target_id: int, target_name: str, moderator: discord.abc.User,
        reason: str, extra: str = "", event_type: str = "",
    ):
        embed = discord.Embed(title=title, color=discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.add_field(name="Кто", value=f"{moderator.name} (`{moderator.id}`)", inline=False)
        embed.add_field(name="Кого", value=f"{target_name} (`{target_id}`)", inline=False)
        embed.add_field(name="Причина", value=reason, inline=False)
        if extra:
            embed.add_field(name="Дополнительно", value=extra, inline=False)
        embed.set_footer(text="Модерация · Команда")
        await self.bot.send_log(embed)
        if event_type:
            moderation_log.append_event(
                event_type, target_id, target_name, reason,
                moderator_id=moderator.id, moderator_display=moderator.name, extra=extra,
            )

    # ────────────────────────── /ban ──────────────────────────

    @app_commands.command(name="ban", description="Забанить пользователя на сервере")
    @app_commands.describe(
        user="Пользователь для бана — выбрать из списка или вставить ID",
        reason="Причина бана (необязательно)",
        time_str="Срок бана: число + единица s/m/h/d, например 7d (не указано — бан навсегда)",
    )
    @app_commands.rename(time_str="time")
    @app_commands.default_permissions(ban_members=True)
    async def ban_command(
        self, interaction: discord.Interaction, user: discord.User,
        reason: str | None = None, time_str: str | None = None,
    ):
        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)

        duration_seconds = None
        if time_str:
            try:
                duration_seconds = moderation_commands_core.parse_duration(time_str)
            except ValueError as exc:
                return await interaction.response.send_message(str(exc), ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        reason_text = moderation_commands_core.normalize_reason(reason)
        full_reason = moderation_commands_core.command_reason(reason_text, interaction.user.name, interaction.user.id)

        try:
            await interaction.guild.ban(user, reason=full_reason)
        except discord.Forbidden:
            return await interaction.followup.send("Недостаточно прав, чтобы забанить этого пользователя.", ephemeral=True)
        except discord.HTTPException as exc:
            return await interaction.followup.send(f"Не удалось забанить: {exc}", ephemeral=True)

        duration_display = "навсегда"
        if duration_seconds:
            unban_at_ts = int(time.time()) + duration_seconds
            row_id = ban_db.add(interaction.guild.id, user.id, unban_at_ts)
            self._schedule_unban(row_id, interaction.guild.id, user.id, unban_at_ts)
            duration_display = moderation_commands_core.format_duration(time_str)

        await self._log_action(
            "🔨 Бан (команда)", user.id, user.name, interaction.user, reason_text,
            extra=f"Срок: {duration_display}", event_type="command_ban",
        )
        await interaction.followup.send(
            f"✅ {user.mention} забанен. Срок: **{duration_display}**. Причина: {reason_text}", ephemeral=True
        )

    # ────────────────────────── /kick ──────────────────────────

    @app_commands.command(name="kick", description="Кикнуть участника с сервера")
    @app_commands.describe(user="Участник для кика", reason="Причина кика (необязательно)")
    @app_commands.default_permissions(kick_members=True)
    async def kick_command(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        reason_text = moderation_commands_core.normalize_reason(reason)
        full_reason = moderation_commands_core.command_reason(reason_text, interaction.user.name, interaction.user.id)

        try:
            await user.kick(reason=full_reason)
        except discord.Forbidden:
            return await interaction.followup.send("Недостаточно прав, чтобы кикнуть этого участника.", ephemeral=True)
        except discord.HTTPException as exc:
            return await interaction.followup.send(f"Не удалось кикнуть: {exc}", ephemeral=True)

        await self._log_action(
            "👢 Кик (команда)", user.id, user.name, interaction.user, reason_text, event_type="command_kick"
        )
        await interaction.followup.send(f"✅ {user.mention} кикнут. Причина: {reason_text}", ephemeral=True)

    # ────────────────────────── /mute ──────────────────────────

    @app_commands.command(name="mute", description="Выдать участнику таймаут (максимум 28 дней)")
    @app_commands.describe(
        user="Участник для таймаута",
        time_str="Срок: число + единица s/m/h/d, например 2h (обязательно, максимум 28 дней)",
        reason="Причина таймаута (необязательно)",
    )
    @app_commands.rename(time_str="time")
    @app_commands.default_permissions(moderate_members=True)
    async def mute_command(
        self, interaction: discord.Interaction, user: discord.Member, time_str: str, reason: str | None = None,
    ):
        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)

        try:
            duration_seconds = moderation_commands_core.parse_mute_duration(time_str)
        except ValueError as exc:
            return await interaction.response.send_message(str(exc), ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        reason_text = moderation_commands_core.normalize_reason(reason)
        full_reason = moderation_commands_core.command_reason(reason_text, interaction.user.name, interaction.user.id)

        try:
            await user.timeout(discord.utils.utcnow() + timedelta(seconds=duration_seconds), reason=full_reason)
        except discord.Forbidden:
            return await interaction.followup.send("Недостаточно прав, чтобы выдать таймаут этому участнику.", ephemeral=True)
        except discord.HTTPException as exc:
            return await interaction.followup.send(f"Не удалось выдать таймаут: {exc}", ephemeral=True)

        duration_display = moderation_commands_core.format_duration(time_str)
        await self._log_action(
            "🔇 Таймаут (команда)", user.id, user.name, interaction.user, reason_text,
            extra=f"Срок: {duration_display}", event_type="command_mute",
        )
        await interaction.followup.send(
            f"✅ {user.mention} получил(а) таймаут на **{duration_display}**. Причина: {reason_text}", ephemeral=True
        )

    # ────────────────────────── /unmute ──────────────────────────

    @app_commands.command(name="unmute", description="Досрочно снять таймаут с участника")
    @app_commands.describe(user="Участник, с которого снять таймаут", reason="Причина снятия (необязательно)")
    @app_commands.default_permissions(moderate_members=True)
    async def unmute_command(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)
        if not user.is_timed_out():
            return await interaction.response.send_message(f"{user.mention} сейчас не под таймаутом.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        reason_text = moderation_commands_core.normalize_reason(reason)
        full_reason = moderation_commands_core.command_reason(reason_text, interaction.user.name, interaction.user.id)

        try:
            await user.timeout(None, reason=full_reason)
        except discord.Forbidden:
            return await interaction.followup.send("Недостаточно прав, чтобы снять таймаут с этого участника.", ephemeral=True)
        except discord.HTTPException as exc:
            return await interaction.followup.send(f"Не удалось снять таймаут: {exc}", ephemeral=True)

        await self._log_action(
            "🔊 Снятие таймаута (команда)", user.id, user.name, interaction.user, reason_text, event_type="command_unmute"
        )
        await interaction.followup.send(f"✅ Таймаут с {user.mention} снят. Причина: {reason_text}", ephemeral=True)

    # ────────────────────────── /unban ──────────────────────────

    @app_commands.command(name="unban", description="Разбанить пользователя по ID")
    @app_commands.describe(userid="ID пользователя для разбана", reason="Причина разбана (необязательно)")
    @app_commands.default_permissions(ban_members=True)
    async def unban_command(self, interaction: discord.Interaction, userid: str, reason: str | None = None):
        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)
        if not userid.isdigit():
            return await interaction.response.send_message("ID пользователя должен быть числом.", ephemeral=True)
        user_id = int(userid)

        await interaction.response.defer(ephemeral=True)
        try:
            ban_entry = await interaction.guild.fetch_ban(discord.Object(id=user_id))
        except discord.NotFound:
            return await interaction.followup.send("Этот пользователь не забанен.", ephemeral=True)
        except discord.HTTPException as exc:
            return await interaction.followup.send(f"Не удалось получить информацию о бане: {exc}", ephemeral=True)

        target = ban_entry.user
        reason_text = moderation_commands_core.normalize_reason(reason)
        full_reason = moderation_commands_core.command_reason(reason_text, interaction.user.name, interaction.user.id)
        try:
            await interaction.guild.unban(target, reason=full_reason)
        except discord.HTTPException as exc:
            return await interaction.followup.send(f"Не удалось разбанить: {exc}", ephemeral=True)

        self._cancel_scheduled_unban(interaction.guild.id, user_id)

        await self._log_action(
            "🔓 Разбан (команда)", target.id, target.name, interaction.user, reason_text, event_type="command_unban"
        )
        await interaction.followup.send(f"✅ {target} (`{target.id}`) разбанен. Причина: {reason_text}", ephemeral=True)

    # ────────────────────────── /clear ──────────────────────────

    @app_commands.command(name="clear", description="Удалить сообщения в текущем канале")
    @app_commands.describe(number="Сколько сообщений удалить (1-999)")
    @app_commands.default_permissions(manage_messages=True)
    async def clear_command(
        self, interaction: discord.Interaction,
        number: app_commands.Range[int, moderation_commands_core.CLEAR_MIN, moderation_commands_core.CLEAR_MAX],
    ):
        if interaction.guild is None:
            return await interaction.response.send_message("Команда доступна только на сервере.", ephemeral=True)
        channel = interaction.channel
        if not hasattr(channel, "purge"):
            return await interaction.response.send_message("В этом типе канала очистка недоступна.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            deleted = await channel.purge(limit=number)
        except discord.Forbidden:
            return await interaction.followup.send("Недостаточно прав для удаления сообщений в этом канале.", ephemeral=True)
        except discord.HTTPException as exc:
            return await interaction.followup.send(f"Не удалось удалить сообщения: {exc}", ephemeral=True)

        await self._log_action(
            "🧹 Очистка чата (команда)", interaction.user.id, interaction.user.name, interaction.user,
            f"Удалено сообщений: {len(deleted)}", extra=f"Канал: {channel.mention}", event_type="command_clear",
        )
        await interaction.followup.send(f"✅ Удалено сообщений: **{len(deleted)}**.", ephemeral=True)


async def setup(bot: commands.Bot):
    ban_db.init()
    await bot.add_cog(ModerationCommandsCog(bot))
