"""Ког «Развлечения»: русская рулетка и эмодзи-рулетка.

Модуль выключен по умолчанию, включается в дашборде (раздел «Развлечения»).
Русская рулетка — соло: один спуск курка, шанс 1/6. «Погибший» получает
Discord-таймаут на настраиваемое число минут (0 — без наказания).
"""

import logging
import random
import time
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

import fun_core

logger = logging.getLogger("fun")

SURVIVE_LINES = (
    "*щёлк* … пусто. Сегодня не твой день… в хорошем смысле. 😮‍💨",
    "*щёлк* … барабан провернулся впустую. Живём! 🎉",
    "*щёлк* … тишина. Судьба улыбнулась. 🍀",
    "*щёлк* … осечка судьбы — ты жив. 😅",
)

DEATH_LINES = (
    "💥 **БАХ!** Не повезло…",
    "💥 **ВЫСТРЕЛ!** Барабан был заряжен…",
    "💥 **БАБАХ!** Русская рулетка беспощадна…",
)


class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._roulette_cooldowns: dict[int, float] = {}

    # ────────────────────────── Русская рулетка ──────────────────────────

    @app_commands.command(name="русская-рулетка", description="Спустить курок: 1 шанс из 6. Проигравший получает таймаут")
    async def russian_roulette(self, interaction: discord.Interaction):
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
        self._roulette_cooldowns[interaction.user.id] = now + cooldown

        if not fun_core.spin_trigger():
            return await interaction.response.send_message(
                f"🔫 {interaction.user.mention} крутит барабан и жмёт на курок…\n{random.choice(SURVIVE_LINES)}"
            )

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

        await interaction.response.send_message(
            f"🔫 {interaction.user.mention} крутит барабан и жмёт на курок…\n{death_line}\n{suffix}"
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
