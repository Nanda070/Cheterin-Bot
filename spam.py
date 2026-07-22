import discord
from discord.ext import commands, tasks
import asyncio
from datetime import timedelta
import logging

import bot_config
import i18n
import moderation_log
import spam_core

logger = logging.getLogger("chetbot.spam")


class Spam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # {user_id: [ {"signature": str, "has_attachments": bool, "time": datetime, "channel_id": int}, ... ]}
        self.cache: dict[int, list] = {}
        # Набор user_id, для которых уже запущено наказание (защита от двойного срабатывания)
        self._processing: set[int] = set()

        self._cleanup_cache.start()

    def cog_unload(self):
        self._cleanup_cache.cancel()

    # ---------- periodic cache cleanup ----------

    @tasks.loop(minutes=5)
    async def _cleanup_cache(self):
        """Удаляет устаревшие записи из кэша спам-детектора."""
        # Всё тело под try/except: необработанное исключение навсегда остановило бы tasks.loop.
        try:
            now = discord.utils.utcnow()
            expired_users = []
            for user_id, entries in self.cache.items():
                entries[:] = [e for e in entries if (now - e["time"]).total_seconds() <= 120]
                if not entries:
                    expired_users.append(user_id)
            for uid in expired_users:
                del self.cache[uid]
        except Exception:
            logger.exception("_cleanup_cache: ошибка итерации — цикл продолжает работать")

    @_cleanup_cache.error
    async def _cleanup_cache_error(self, _error: BaseException):
        logger.exception("_cleanup_cache: критическая ошибка — перезапуск цикла")
        self._cleanup_cache.restart()

    @_cleanup_cache.before_loop
    async def _before_cleanup(self):
        await self.bot.wait_until_ready()

    # ---------- persistent spam buttons via on_interaction ----------

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Обработка кнопок спам-инцидентов — работает и после перезапуска бота."""
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")

        if custom_id.startswith("spam_ban_"):
            await self._handle_spam_ban(interaction, custom_id)
        elif custom_id.startswith("spam_leave_"):
            await self._handle_spam_leave(interaction, custom_id)

    def _make_disabled_spam_view(self, incident_id: str, lang: str) -> discord.ui.View:
        """Создаёт вью с отключёнными кнопками для обновления сообщения."""
        view = discord.ui.View(timeout=None)
        ban_btn = discord.ui.Button(
            label=i18n.t("spam.btn.ban", lang),
            style=discord.ButtonStyle.danger,
            custom_id=f"spam_ban_{incident_id}",
            disabled=True,
        )
        leave_btn = discord.ui.Button(
            label=i18n.t("spam.btn.leave", lang),
            style=discord.ButtonStyle.secondary,
            custom_id=f"spam_leave_{incident_id}",
            disabled=True,
        )
        view.add_item(ban_btn)
        view.add_item(leave_btn)
        return view

    async def _handle_spam_ban(self, interaction: discord.Interaction, custom_id: str):
        lang = i18n.lang_for(interaction.guild_id)
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message(
                i18n.t("spam.no_permission", lang), ephemeral=True
            )

        # custom_id = "spam_ban_{user_id}_{timestamp}"
        incident_id = custom_id.removeprefix("spam_ban_")
        parts = incident_id.split("_")
        if not parts:
            return
        try:
            target_id = int(parts[0])
        except ValueError:
            return

        guild = interaction.guild
        try:
            await guild.ban(
                discord.Object(id=target_id),
                reason=i18n.t(
                    "spam.ban_reason", lang,
                    id=interaction.user.id, name=interaction.user.name,
                ),
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                i18n.t("spam.ban_forbidden", lang), ephemeral=True
            )
        except discord.NotFound:
            return await interaction.response.send_message(
                i18n.t("spam.ban_not_found", lang), ephemeral=True
            )
        except Exception as e:
            return await interaction.response.send_message(
                i18n.t("spam.ban_error", lang, error=e), ephemeral=True
            )

        # Бан прошёл успешно — блокируем кнопки
        view = self._make_disabled_spam_view(incident_id, lang)
        await interaction.response.edit_message(
            content=i18n.t("spam.ban_success", lang, mention=interaction.user.mention),
            view=view,
        )

    async def _handle_spam_leave(self, interaction: discord.Interaction, custom_id: str):
        lang = i18n.lang_for(interaction.guild_id)
        if (
            not interaction.user.guild_permissions.ban_members
            and not interaction.user.guild_permissions.moderate_members
        ):
            return await interaction.response.send_message(
                i18n.t("spam.no_permission", lang), ephemeral=True
            )

        incident_id = custom_id.removeprefix("spam_leave_")
        view = self._make_disabled_spam_view(incident_id, lang)
        await interaction.response.edit_message(
            content=i18n.t("spam.leave_success", lang, mention=interaction.user.mention),
            view=view,
        )

    # ---------- message listener ----------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Не реагируем на канал Tempban
        tempban_channel_id = bot_config.get(message.guild.id, "TEMPBAN_CHANNEL_ID")
        if tempban_channel_id and message.channel.id == int(tempban_channel_id):
            return

        # Не реагируем на администраторов
        if not isinstance(message.author, discord.Member):
            return
        if message.author.guild_permissions.administrator:
            return

        # Проверяем наличие массового тега
        has_mass_tag = message.mention_everyone or len(message.role_mentions) > 0
        if not has_mass_tag:
            return

        # Игнорируем каналы-исключения
        exception_channels = [int(c) for c in bot_config.get(message.guild.id, "SPAM_EXCEPTION_CHANNELS", [])]
        if message.channel.id in exception_channels:
            return

        user_id = message.author.id

        # Если уже обрабатываем этого пользователя — пропускаем
        if user_id in self._processing:
            return

        now = discord.utils.utcnow()
        has_attachments = len(message.attachments) > 0
        signature = message.content.strip()

        spam_settings = spam_core.get_settings(message.guild.id)
        limit = spam_core.message_limit(spam_settings, has_attachments)
        time_window = spam_settings["time_window_sec"]

        if user_id not in self.cache:
            self.cache[user_id] = []

        self.cache[user_id].append(
            {
                "signature": signature,
                "has_attachments": has_attachments,
                "time": now,
                "channel_id": message.channel.id,
            }
        )

        # Удаляем записи старше time_window
        self.cache[user_id] = [
            e
            for e in self.cache[user_id]
            if (now - e["time"]).total_seconds() <= time_window
        ]

        # Если кэш пуст после фильтрации — удаляем запись пользователя из памяти
        if not self.cache[user_id]:
            del self.cache[user_id]
            return

        # Совпадения по сигнатуре и наличию вложений
        matches = [
            e
            for e in self.cache[user_id]
            if e["signature"] == signature and e["has_attachments"] == has_attachments
        ]

        if len(matches) >= limit:
            self.cache.pop(user_id, None)
            self._processing.add(user_id)
            try:
                await self._punish(message, matches, limit)
            finally:
                self._processing.discard(user_id)

    async def _punish(self, message: discord.Message, matches: list, limit: int):
        member = message.author
        guild = message.guild
        lang = i18n.lang_for(guild.id)
        spam_settings = spam_core.get_settings(guild.id)
        log_channel_id = bot_config.get(guild.id, "SPAM_LOG_CHANNEL_ID")
        role_ping_id = bot_config.get(guild.id, "SPAM_LOG_ROLE_ID")
        signature = matches[0]["signature"]
        log_reason = i18n.t(
            "spam.log_reason",
            lang,
            limit=limit,
            time_window=spam_settings["time_window_sec"],
        )

        # Таймаут на 24 часа
        try:
            until = discord.utils.utcnow() + timedelta(days=1)
            await member.timeout(until, reason=i18n.t("spam.timeout_reason", lang))
        except discord.Forbidden:
            logger.warning("Нет прав для таймаута %s", member.id)
        except Exception as e:
            logger.error("Ошибка таймаута %s: %s", member.id, e)

        # Purge сообщений за последние 20 минут в фоне (текстовые каналы + треды)
        asyncio.create_task(self.purge_recent_messages(guild, member))

        channels_spammed_for_log = list(set(f"<#{e['channel_id']}>" for e in matches))
        moderation_log.append_event(
            guild.id,
            "spam_punish",
            member.id,
            member.name,
            log_reason,
            extra=", ".join(channels_spammed_for_log),
        )

        # Лог
        if not log_channel_id:
            return
        log_channel = guild.get_channel(int(log_channel_id))
        if not log_channel:
            return

        embed = discord.Embed(
            title=i18n.t("spam.embed.title", lang),
            color=discord.Color.orange(),
        )
        embed.add_field(
            name=i18n.t("spam.embed.user", lang),
            value=f"{member.name} ({member.mention})",
            inline=False,
        )
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(
            name=i18n.t("spam.embed.violation", lang),
            value=log_reason,
            inline=False,
        )
        channels_spammed = list(set(f"<#{e['channel_id']}>" for e in matches))
        embed.add_field(
            name=i18n.t("spam.embed.channels", lang),
            value=", ".join(channels_spammed),
            inline=False,
        )
        embed.add_field(
            name=i18n.t("spam.embed.message", lang),
            value=signature[:1024] if signature else i18n.t("spam.embed.message_media_only", lang),
            inline=False,
        )
        embed.add_field(
            name=i18n.t("spam.embed.punishment", lang),
            value=i18n.t("spam.embed.punishment_value", lang),
            inline=False,
        )
        embed.timestamp = discord.utils.utcnow()

        ping_text = f"<@&{role_ping_id}>" if role_ping_id else ""

        # Уникальный incident_id — user_id + timestamp
        incident_id = f"{member.id}_{int(discord.utils.utcnow().timestamp())}"

        # Кнопки для лога (обрабатываются через on_interaction)
        view = discord.ui.View(timeout=None)
        ban_btn = discord.ui.Button(
            label=i18n.t("spam.btn.ban", lang),
            style=discord.ButtonStyle.danger,
            custom_id=f"spam_ban_{incident_id}",
        )
        leave_btn = discord.ui.Button(
            label=i18n.t("spam.btn.leave", lang),
            style=discord.ButtonStyle.secondary,
            custom_id=f"spam_leave_{incident_id}",
        )
        view.add_item(ban_btn)
        view.add_item(leave_btn)

        await log_channel.send(content=ping_text, embed=embed, view=view)

    async def purge_recent_messages(self, guild: discord.Guild, member: discord.Member):
        """Удаляет сообщения участника за последние 20 минут во всех каналах и тредах."""
        limit_time = discord.utils.utcnow() - timedelta(minutes=20)

        def check(m: discord.Message) -> bool:
            return m.author.id == member.id

        # Собираем все каналы: текстовые + активные треды
        channels_to_purge: list = list(guild.text_channels)
        try:
            threads = await guild.active_threads()
            channels_to_purge.extend(threads)
        except Exception as e:
            logger.warning("Ошибка получения активных тредов при purge: %s", e)

        for channel in channels_to_purge:
            try:
                await channel.purge(limit=200, check=check, bulk=True, after=limit_time)
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass
            except Exception as e:
                logger.warning("Purge error in %s: %s", channel.id, e)
            await asyncio.sleep(0.5)


async def setup(bot):
    await bot.add_cog(Spam(bot))
