"""Ког «Антирейд»: автоматический Lockdown при всплеске входов новых участников.

ВЫКЛЮЧЕН ПО УМОЛЧАНИЮ и не имеет никакого эффекта, пока не включён отдельным
тумблером в дашборде (раздел «Антирейд») — on_member_join первой же строкой
проверяет antiraid_core.get_settings()["enabled"] и выходит, если модуль не
активен. Не связан ни с одним другим модулем: включение остальных функций
бота не активирует и не меняет поведение антирейда.

При срабатывании включает уже существующий lockdown_core.activate_antispam()
(тот же механизм, что у ручной /antispam и панели «Lockdown» в дашборде) и,
опционально, slowmode во всех текстовых каналах — с кулдауном, чтобы не
триггериться повторно, пока рейд ещё не закончился.
"""

import logging

import discord
from discord.ext import commands

import antiraid_core
import lockdown_core
import moderation_log

logger = logging.getLogger("antiraid")


class AntiRaidCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._trackers: dict[int, antiraid_core.JoinTracker] = {}
        self._last_trigger: dict[int, float] = {}  # guild_id -> monotonic-ish ts (unix) последнего срабатывания

    def _tracker_for(self, guild_id: int, window_sec: int) -> antiraid_core.JoinTracker:
        tracker = self._trackers.get(guild_id)
        if tracker is None or tracker.window_sec != window_sec:
            tracker = antiraid_core.JoinTracker(window_sec)
            self._trackers[guild_id] = tracker
        return tracker

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = antiraid_core.get_settings()
        if not settings["enabled"]:
            return  # модуль выключен — никакого эффекта, точка входа для всей фичи

        # member.joined_at — момент самого входа (из payload шлюза Discord), а не
        # время обработки события ботом; окно и кулдаун считаются от него, чтобы
        # логика была детерминированной и не зависела от задержек обработки.
        joined_at = member.joined_at or antiraid_core.utcnow()
        if not antiraid_core.is_suspicious_account(member.created_at, joined_at, settings["min_account_age_hours"]):
            return

        guild_id = member.guild.id
        cooldown_sec = settings["cooldown_minutes"] * 60
        last = self._last_trigger.get(guild_id, 0.0)
        if cooldown_sec > 0 and joined_at.timestamp() - last < cooldown_sec:
            return  # рейд уже обрабатывается — не спамим повторными срабатываниями

        tracker = self._tracker_for(guild_id, settings["join_window_sec"])
        count = tracker.register(joined_at)
        if count < settings["join_threshold"]:
            return

        self._last_trigger[guild_id] = joined_at.timestamp()
        tracker.reset()
        await self._trigger_raid_response(member, settings, count)

    async def _trigger_raid_response(self, member: discord.Member, settings: dict, join_count: int):
        guild = member.guild
        logger.warning("Антирейд сработал на сервере %s: %s входов за %sс", guild.id, join_count, settings["join_window_sec"])

        lockdown_result = None
        if settings["action_lockdown"]:
            try:
                modified_count, _errors = await lockdown_core.activate_antispam(
                    guild,
                    lockdown_core.get_mention_exempt_ids(),
                    lockdown_core.get_mentionable_exempt_ids(),
                )
                lockdown_result = modified_count
            except Exception:
                logger.exception("Антирейд: не удалось активировать lockdown на сервере %s", guild.id)

        slowmode_applied = 0
        if settings["action_slowmode_sec"] > 0:
            for channel in guild.text_channels:
                try:
                    await channel.edit(slowmode_delay=settings["action_slowmode_sec"], reason="Автоантирейд")
                    slowmode_applied += 1
                except discord.HTTPException:
                    continue

        extra_parts = [f"Входов за {settings['join_window_sec']}с: {join_count}"]
        if lockdown_result is not None:
            extra_parts.append(f"Lockdown: изменено ролей {lockdown_result}")
        if slowmode_applied:
            extra_parts.append(f"Slowmode: {slowmode_applied} канал(ов) на {settings['action_slowmode_sec']}с")

        moderation_log.append_event(
            "antiraid_trigger", member.id, member.name,
            "Автоматическое срабатывание антирейда", extra=" · ".join(extra_parts),
        )

        embed = discord.Embed(
            title="🚨 Антирейд сработал",
            description="\n".join(extra_parts),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Последний вход", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.set_footer(text="Антирейд · Автоматически")
        await self.bot.send_log(embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiRaidCog(bot))
