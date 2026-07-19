"""Ког «Развлечения»: русская рулетка и эмодзи-рулетка.

Модуль выключен по умолчанию, включается в дашборде (раздел «Развлечения»).
Русская рулетка — соло: один спуск курка, шанс 1/6. «Погибший» получает
Discord-таймаут на настраиваемое число минут (0 — без наказания).
"""

import asyncio
import logging
import random
import time
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

import economy_core
import economy_db
import fun_core

logger = logging.getLogger("fun")

INTRO_LINES = (
    "крутит барабан и жмёт на курок…",
    "подносит револьвер к виску и зажмуривается…",
    "раскручивает барабан, глубоко вдыхает и жмёт…",
    "шепчет «да будет удача» и спускает курок…",
    "с дрожащей рукой тянет спусковой крючок…",
    "уверенно, как в кино, жмёт на курок…",
)

SURVIVE_LINES = (
    "*щёлк* … пусто. Сегодня не твой день… в хорошем смысле. 😮‍💨",
    "*щёлк* … барабан провернулся впустую. Живём! 🎉",
    "*щёлк* … тишина. Судьба улыбнулась. 🍀",
    "*щёлк* … осечка судьбы — ты жив. 😅",
    "*щёлк* … пронесло! Сердце ушло в пятки, но всё цело. 💓",
    "*щёлк* … пустая камора. Кто-то наверху тебя любит. 😇",
    "*щёлк* … ничего. Можно выдохнуть и заказать нервный чай. 🍵",
    "*щёлк* … мимо! Барабан сегодня добрый. 🎲",
    "*щёлк* … жив. Легенды говорят, что так везёт раз в жизни. ✨",
    "*щёлк* … тишина звенит в ушах. Победа над судьбой! 🏆",
)

DEATH_LINES = (
    "💥 **БАХ!** Не повезло…",
    "💥 **ВЫСТРЕЛ!** Барабан был заряжен…",
    "💥 **БАБАХ!** Русская рулетка беспощадна…",
    "💥 **БАХ!** Эхо разносится по каналу…",
    "💥 **ВЫСТРЕЛ!** Судьба сегодня не на твоей стороне…",
    "💥 **БАМ!** Вот это поворот…",
    "💥 **БАХ!** F в чат…",
    "💥 **ВЫСТРЕЛ!** Шанс был 1 к 6 — и он выпал…",
)


class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._roulette_cooldowns: dict[int, float] = {}
        # user_id -> сколько «щёлк» подряд без выстрела (барабан не прокручивается заново)
        self._roulette_clicks: dict[int, int] = {}
        self._auto_emoji_last: dict[int, float] = {}  # channel_id -> monotonic ts последней авто-реакции

    # ────────────────────────── Авто-Эмодзи ──────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Изредка ставит случайное серверное эмодзи на сообщения людей (как в Juniper):
        шанс в процентах + минимальный интервал на канал, реакция снимается через
        настроенное время, чтобы не висела вечно."""
        if message.author.bot or message.guild is None:
            return

        settings = fun_core.get_settings()
        if not settings["enabled"] or not settings["auto_emoji_enabled"]:
            return

        now = time.monotonic()
        interval = settings["auto_emoji_min_interval_sec"]
        if interval > 0 and now - self._auto_emoji_last.get(message.channel.id, 0.0) < interval:
            return

        if not fun_core.auto_emoji_roll(settings["auto_emoji_chance_percent"]):
            return

        emoji = fun_core.pick_emoji(list(message.guild.emojis))
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            return
        self._auto_emoji_last[message.channel.id] = now

        remove_after = settings["auto_emoji_remove_after_sec"]
        if remove_after > 0:
            self.bot.loop.create_task(self._remove_auto_emoji(message, emoji, remove_after))

    async def _remove_auto_emoji(self, message: discord.Message, emoji: str, delay_sec: int):
        try:
            await asyncio.sleep(delay_sec)
            await message.remove_reaction(emoji, self.bot.user)
        except discord.HTTPException:
            pass
        except Exception:
            logger.exception("Не удалось снять авто-эмодзи с сообщения %s", message.id)

    # ────────────────────────── Русская рулетка ──────────────────────────

    @app_commands.command(
        name="русская-рулетка",
        description="Спустить курок: барабан не прокручивается, с каждым щелчком шанс растёт. Можно ставить монеты",
    )
    @app_commands.describe(ставка="Ставка монет: выжил — удвоил, погиб — потерял (необязательно)")
    async def russian_roulette(self, interaction: discord.Interaction, ставка: int | None = None):
        settings = fun_core.get_settings()
        if not settings["enabled"]:
            return await interaction.response.send_message("Модуль «Развлечения» отключён.", ephemeral=True)

        cooldown = settings["roulette_cooldown_sec"]
        now = time.monotonic()
        ready_at = self._roulette_cooldowns.get(interaction.user.id, 0.0)
        if cooldown > 0 and now < ready_at:
            remaining = int(ready_at - now) + 1
            return await interaction.response.send_message(
                f"Барабан ещё крутится — попробуй через {remaining} сек.", ephemeral=True
            )

        # Ставка проверяется и списывается ДО установки кулдауна и спуска курка
        econ = economy_core.get_settings()
        bet = ставка or 0
        if bet > 0:
            if not econ["enabled"]:
                return await interaction.response.send_message(
                    "Модуль «Экономика» отключён — сыграй без ставки.", ephemeral=True
                )
            error = economy_core.bet_error(bet, economy_db.get_balance(interaction.user.id), econ)
            if error:
                return await interaction.response.send_message(error, ephemeral=True)
            if not economy_db.try_spend(interaction.user.id, bet, "roulette_bet"):
                return await interaction.response.send_message("Недостаточно средств для ставки.", ephemeral=True)

        self._roulette_cooldowns[interaction.user.id] = now + cooldown

        # Барабан не прокручивается заново: каждый «щёлк» приближает патрон
        clicks = self._roulette_clicks.get(interaction.user.id, 0)
        chamber_text = f"Камора **{clicks + 1}/{fun_core.ROULETTE_CHAMBERS}**."

        if not fun_core.spin_trigger(clicks):
            self._roulette_clicks[interaction.user.id] = clicks + 1
            win_text = ""
            if bet > 0:
                balance = economy_db.add(interaction.user.id, bet * 2, "roulette_win")
                win_text = (
                    f"\n💰 Ставка сыграла: **+{economy_core.format_amount(bet, econ)}** "
                    f"(баланс: {economy_core.format_amount(balance, econ)})."
                )
            return await interaction.response.send_message(
                f"🔫 {interaction.user.mention} {random.choice(INTRO_LINES)}\n"
                f"{random.choice(SURVIVE_LINES)} {chamber_text}{win_text}"
            )

        self._roulette_clicks[interaction.user.id] = 0

        timeout_minutes = settings["roulette_timeout_minutes"]
        death_line = random.choice(DEATH_LINES)
        punished = False
        if timeout_minutes > 0 and interaction.guild is not None:
            try:
                await interaction.user.timeout(
                    timedelta(minutes=timeout_minutes), reason="Проигрыш в русской рулетке"
                )
                punished = True
            except (discord.HTTPException, AttributeError):
                logger.info("Не удалось выдать таймаут за рулетку пользователю %s", interaction.user.id)

        if punished:
            suffix = f"{interaction.user.mention} выбывает и получает таймаут на **{timeout_minutes} мин**. 🪦"
        elif timeout_minutes > 0:
            suffix = f"{interaction.user.mention} должен был получить таймаут, но оказался неуязвим. Повезло. 😎"
        else:
            suffix = f"{interaction.user.mention} выбывает. Почтим память минутой молчания. 🪦"

        bet_text = ""
        if bet > 0:
            balance = economy_db.get_balance(interaction.user.id)
            bet_text = (
                f"\n💸 Ставка **{economy_core.format_amount(bet, econ)}** сгорела "
                f"(баланс: {economy_core.format_amount(balance, econ)})."
            )

        await interaction.response.send_message(
            f"🔫 {interaction.user.mention} {random.choice(INTRO_LINES)}\n"
            f"{death_line} {chamber_text}\n{suffix}{bet_text}"
        )

    # ────────────────────────── Эмодзи-рулетка ──────────────────────────

    @app_commands.command(name="эмодзи-рулетка", description="Крутануть рулетку и получить случайное эмодзи сервера")
    async def emoji_roulette(self, interaction: discord.Interaction):
        settings = fun_core.get_settings()
        if not settings["enabled"]:
            return await interaction.response.send_message("Модуль «Развлечения» отключён.", ephemeral=True)

        emojis = list(interaction.guild.emojis) if interaction.guild else []
        emoji = fun_core.pick_emoji(emojis)
        await interaction.response.send_message(f"🎰 {interaction.user.mention} крутит рулетку… выпало: {emoji}")


async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))
