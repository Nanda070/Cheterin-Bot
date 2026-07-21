"""Войс-трекер: единый учёт голосовых сессий.

Кормит сразу два модуля:
- статистику войса (все сессии пишутся в stats.db);
- систему уровней (XP за активные минуты по механике Juniper — начисляется
  и записывается по окончании сессии).

Активный участник: не бот, микрофон включён, звук включён (ни self-, ни
server-mute/deaf). XP идёт, только когда активных в канале минимум двое.
"""

import logging
import time
from dataclasses import dataclass, field

import discord
from discord.ext import commands, tasks

import stats_db
import xp_core

logger = logging.getLogger("voice-tracker")

TICK_SECONDS = 60
SESSIONS_RETENTION_DAYS = 180


def is_active(state: discord.VoiceState) -> bool:
    return not (state.self_mute or state.self_deaf or state.mute or state.deaf)


@dataclass
class VoiceSession:
    channel_id: int
    channel_name: str
    joined_ts: int
    active_seconds: int = 0
    xp_accum: float = field(default=0.0)


class VoiceTracker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions: dict[int, VoiceSession] = {}
        self._started = False
        self._tick.start()
        self._prune.start()

    def cog_unload(self):
        self._tick.cancel()
        self._prune.cancel()

    # ────────────────── Жизненный цикл сессий ──────────────────

    @commands.Cog.listener()
    async def on_ready(self):
        if self._started:
            return
        self._started = True
        now = int(time.time())
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if not member.bot and member.id not in self.sessions:
                        self.sessions[member.id] = VoiceSession(channel.id, channel.name, now)
        logger.info("Восстановлено голосовых сессий: %s", len(self.sessions))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        now = int(time.time())

        moved_or_left = before.channel is not None and (after.channel is None or after.channel.id != before.channel.id)
        if moved_or_left:
            await self._close_session(member, now)

        joined = after.channel is not None and (before.channel is None or before.channel.id != after.channel.id)
        if joined:
            self.sessions[member.id] = VoiceSession(after.channel.id, after.channel.name, now)

    async def _close_session(self, member: discord.Member, now: int):
        session = self.sessions.pop(member.id, None)
        if session is None:
            return

        duration = max(0, now - session.joined_ts)
        stats_db.voice_session_add(
            member.guild.id, member.id, session.channel_id, session.channel_name,
            session.joined_ts, now, session.active_seconds,
        )

        xp_amount = int(session.xp_accum)
        if xp_amount > 0 or session.active_seconds > 0:
            xp_cog = self.bot.get_cog("XPCog")
            if xp_cog is not None:
                try:
                    await xp_cog.apply_voice_session(member, xp_amount, session.active_seconds)
                except Exception:
                    logger.exception("apply_voice_session failed for %s", member.id)

        logger.debug("Сессия %s: %sс (активных %sс, XP %s)", member.id, duration, session.active_seconds, xp_amount)

    # ────────────────── Тикер начисления ──────────────────

    @tasks.loop(seconds=TICK_SECONDS)
    async def _tick(self):
        # Всё тело под try/except: необработанное исключение навсегда остановило бы tasks.loop.
        try:
            for guild in self.bot.guilds:
                settings = xp_core.get_settings(guild.id)
                xp_enabled = settings["enabled"] and settings["voice"]["enabled"]
                voice_scope = settings["voice"]

                for channel in guild.voice_channels:
                    humans = [m for m in channel.members if not m.bot]
                    if not humans:
                        continue

                    active = [m for m in humans if m.voice and is_active(m.voice)]
                    active_count = len(active)

                    for member in active:
                        session = self.sessions.get(member.id)
                        if session is None or session.channel_id != channel.id:
                            # Подстраховка: сессия потерялась (например, рестарт шардов)
                            self.sessions[member.id] = session = VoiceSession(channel.id, channel.name, int(time.time()))

                        if active_count >= 2:
                            session.active_seconds += TICK_SECONDS

                            if xp_enabled and self._xp_channel_allowed(channel.id, voice_scope) and not self._xp_member_ignored(member, voice_scope):
                                session.xp_accum += xp_core.voice_xp_per_minute(
                                    active_count, voice_scope["max_count"], voice_scope["multiplier"],
                                    base_per_minute=voice_scope["base_per_minute"],
                                    member_multiplier=xp_core.voice_member_multiplier(voice_scope, member.id),
                                ) * (TICK_SECONDS / 60)
        except Exception:
            logger.exception("_tick: ошибка итерации — цикл продолжает работать")

    @_tick.error
    async def _tick_error(self, _error: BaseException):
        logger.exception("_tick: критическая ошибка — перезапуск цикла")
        self._tick.restart()

    @_tick.before_loop
    async def _before_tick(self):
        await self.bot.wait_until_ready()

    @staticmethod
    def _xp_channel_allowed(channel_id: int, scope: dict) -> bool:
        cid = str(channel_id)
        if cid in scope["ignored_channels"]:
            return False
        targets = scope["target_channels"]
        return not targets or cid in targets

    @staticmethod
    def _xp_member_ignored(member: discord.Member, scope: dict) -> bool:
        ignored = set(scope["ignored_roles"])
        return any(str(role.id) in ignored for role in member.roles)

    # ────────────────── Ретенция ──────────────────

    @tasks.loop(hours=24)
    async def _prune(self):
        # Всё тело под try/except: необработанное исключение навсегда остановило бы tasks.loop.
        try:
            cutoff = int(time.time()) - SESSIONS_RETENTION_DAYS * 24 * 3600
            stats_db.voice_sessions_prune(cutoff)
        except Exception:
            logger.exception("_prune: ошибка итерации — цикл продолжает работать")

    @_prune.error
    async def _prune_error(self, _error: BaseException):
        logger.exception("_prune: критическая ошибка — перезапуск цикла")
        self._prune.restart()

    @_prune.before_loop
    async def _before_prune(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    stats_db.init()
    await bot.add_cog(VoiceTracker(bot))
