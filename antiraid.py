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
import i18n
import lockdown_core
import moderation_log

logger = logging.getLogger("antiraid")


class AntiRaidCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._trackers: dict[int, antiraid_core.JoinTracker] = {}
        self._last_trigger: dict[int, float] = {}

    def _tracker_for(self, guild_id: int, window_sec: int) -> antiraid_core.JoinTracker:
        tracker = self._trackers.get(guild_id)
        if tracker is None or tracker.window_sec != window_sec:
            tracker = antiraid_core.JoinTracker(window_sec)
            self._trackers[guild_id] = tracker
        return tracker

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = antiraid_core.get_settings(member.guild.id)
        if not settings["enabled"]:
            return

        joined_at = member.joined_at or antiraid_core.utcnow()
        if not antiraid_core.is_suspicious_account(member.created_at, joined_at, settings["min_account_age_hours"]):
            return

        guild_id = member.guild.id
        cooldown_sec = settings["cooldown_minutes"] * 60
        last = self._last_trigger.get(guild_id, 0.0)
        if cooldown_sec > 0 and joined_at.timestamp() - last < cooldown_sec:
            return

        tracker = self._tracker_for(guild_id, settings["join_window_sec"])
        count = tracker.register(joined_at)
        if count < settings["join_threshold"]:
            return

        self._last_trigger[guild_id] = joined_at.timestamp()
        tracker.reset()
        await self._trigger_raid_response(member, settings, count)

    async def _trigger_raid_response(self, member: discord.Member, settings: dict, join_count: int):
        guild = member.guild
        lang = i18n.lang_for(guild.id)
        logger.warning("Антирейд сработал на сервере %s: %s входов за %sс", guild.id, join_count, settings["join_window_sec"])

        lockdown_result = None
        if settings["action_lockdown"]:
            try:
                modified_count, _errors = await lockdown_core.activate_antispam(
                    guild,
                    lockdown_core.get_mention_exempt_ids(),
                    lockdown_core.get_mentionable_exempt_ids(),
                    lang,
                )
                lockdown_result = modified_count
            except Exception:
                logger.exception("Антирейд: не удалось активировать lockdown на сервере %s", guild.id)

        slowmode_applied = 0
        if settings["action_slowmode_sec"] > 0:
            for channel in guild.text_channels:
                try:
                    await channel.edit(
                        slowmode_delay=settings["action_slowmode_sec"],
                        reason=i18n.t("antiraid.slowmode_reason", lang),
                    )
                    slowmode_applied += 1
                except discord.HTTPException:
                    continue

        extra_parts = [
            i18n.t("antiraid.extra.joins", lang, window=settings["join_window_sec"], count=join_count),
        ]
        if lockdown_result is not None:
            extra_parts.append(i18n.t("antiraid.extra.lockdown", lang, count=lockdown_result))
        if slowmode_applied:
            extra_parts.append(i18n.t(
                "antiraid.extra.slowmode", lang,
                channels=slowmode_applied, seconds=settings["action_slowmode_sec"],
            ))

        moderation_log.append_event(
            guild.id, "antiraid_trigger", member.id, member.name,
            self.bot.user.id, self.bot.user.name,
            i18n.t("antiraid.log_reason", lang), extra=" · ".join(extra_parts),
        )

        embed = discord.Embed(
            title=i18n.t("antiraid.embed.title", lang),
            description="\n".join(extra_parts),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name=i18n.t("antiraid.embed.last_join", lang),
            value=f"{member.mention} (`{member.id}`)",
            inline=False,
        )
        embed.set_footer(text=i18n.t("antiraid.embed.footer", lang))
        await self.bot.send_log(guild.id, embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiRaidCog(bot))
