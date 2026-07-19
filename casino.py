"""Ког «Казино»: /слоты и /монетка на серверную валюту.

Требует включённой «Экономики» (баланс/списания идут через economy_db) и
собственного тумблера в дашборде (раздел «Экономика», карточка «Казино»).
Обе команды делят один кулдаун на игрока, чтобы не спамили ставками.
"""

import logging
import time

import discord
from discord import app_commands
from discord.ext import commands

import casino_core
import economy_core
import economy_db

logger = logging.getLogger("casino")

DISABLED_TEXT = "Модуль «Казино» отключён."
ECONOMY_DISABLED_TEXT = "Модуль «Экономика» отключён — казино недоступно."

COINFLIP_CHOICES = [
    app_commands.Choice(name="Орёл", value="орел"),
    app_commands.Choice(name="Решка", value="решка"),
]


class CasinoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._cooldowns: dict[int, float] = {}  # общий кулдаун между /слоты и /монетка

    def _gate(self, interaction: discord.Interaction) -> tuple[dict, dict, str | None]:
        """Проверка тумблеров и кулдауна. Возвращает (casino, economy, error_text)."""
        settings = casino_core.get_settings()
        if not settings["enabled"]:
            return settings, {}, DISABLED_TEXT
        econ = economy_core.get_settings()
        if not econ["enabled"]:
            return settings, econ, ECONOMY_DISABLED_TEXT

        now = time.monotonic()
        ready_at = self._cooldowns.get(interaction.user.id, 0.0)
        if settings["cooldown_sec"] > 0 and now < ready_at:
            remaining = int(ready_at - now) + 1
            return settings, econ, f"Казино отдыхает — попробуй через {remaining} сек."
        return settings, econ, None

    def _start_cooldown(self, user_id: int, cooldown_sec: int):
        self._cooldowns[user_id] = time.monotonic() + cooldown_sec

    # ────────────────────────── /слоты ──────────────────────────

    @app_commands.command(name="слоты", description="Крутить слоты на ставку монет: 3 барабана, совпадения дают выигрыш")
    @app_commands.describe(ставка="Сколько монет поставить")
    async def slots_command(self, interaction: discord.Interaction, ставка: int):
        settings, econ, error = self._gate(interaction)
        if error:
            return await interaction.response.send_message(error, ephemeral=True)

        balance = economy_db.get_balance(interaction.user.id)
        bet_problem = casino_core.bet_error(ставка, balance, settings)
        if bet_problem:
            return await interaction.response.send_message(bet_problem, ephemeral=True)

        if not economy_db.try_spend(interaction.user.id, ставка, "slots_bet"):
            return await interaction.response.send_message("Недостаточно средств для ставки.", ephemeral=True)
        self._start_cooldown(interaction.user.id, settings["cooldown_sec"])

        reels = casino_core.roll_slots()
        multiplier = casino_core.slot_multiplier(reels)
        reels_text = " ".join(reels)

        if multiplier <= 0:
            balance = economy_db.get_balance(interaction.user.id)
            return await interaction.response.send_message(
                f"🎰 {reels_text}\n{interaction.user.mention} — мимо. "
                f"Баланс: {economy_core.format_amount(balance, econ)}."
            )

        payout = casino_core.payout_amount(ставка, multiplier, settings["house_edge_percent"])
        balance = economy_db.add(interaction.user.id, payout, "slots_win")
        kind = "Джекпот" if reels[0] == reels[1] == reels[2] else "Совпадение"
        await interaction.response.send_message(
            f"🎰 {reels_text}\n{interaction.user.mention} — {kind}! Выигрыш: "
            f"**{economy_core.format_amount(payout, econ)}** (баланс: {economy_core.format_amount(balance, econ)})."
        )

    # ────────────────────────── /монетка ──────────────────────────

    @app_commands.command(name="монетка", description="Подбросить монетку на ставку: угадал сторону — выигрыш")
    @app_commands.describe(ставка="Сколько монет поставить", сторона="Орёл или решка")
    @app_commands.choices(сторона=COINFLIP_CHOICES)
    async def coinflip_command(
        self, interaction: discord.Interaction, ставка: int, сторона: app_commands.Choice[str],
    ):
        settings, econ, error = self._gate(interaction)
        if error:
            return await interaction.response.send_message(error, ephemeral=True)

        balance = economy_db.get_balance(interaction.user.id)
        bet_problem = casino_core.bet_error(ставка, balance, settings)
        if bet_problem:
            return await interaction.response.send_message(bet_problem, ephemeral=True)

        if not economy_db.try_spend(interaction.user.id, ставка, "coinflip_bet"):
            return await interaction.response.send_message("Недостаточно средств для ставки.", ephemeral=True)
        self._start_cooldown(interaction.user.id, settings["cooldown_sec"])

        result = casino_core.flip_coin()
        emoji = "🦅" if result == "орел" else "🪙"
        label = "Орёл" if result == "орел" else "Решка"

        if result != сторона.value:
            balance = economy_db.get_balance(interaction.user.id)
            return await interaction.response.send_message(
                f"{emoji} Выпало: **{label}**.\n{interaction.user.mention} не угадал(а). "
                f"Баланс: {economy_core.format_amount(balance, econ)}."
            )

        payout = casino_core.payout_amount(ставка, casino_core.COINFLIP_MULTIPLIER, settings["house_edge_percent"])
        balance = economy_db.add(interaction.user.id, payout, "coinflip_win")
        await interaction.response.send_message(
            f"{emoji} Выпало: **{label}**.\n{interaction.user.mention} угадал(а)! Выигрыш: "
            f"**{economy_core.format_amount(payout, econ)}** (баланс: {economy_core.format_amount(balance, econ)})."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(CasinoCog(bot))
