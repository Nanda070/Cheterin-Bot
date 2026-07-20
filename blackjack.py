"""Ког «Блэкджек»: интерактивная игра против дилера на серверную валюту.

Требует включённого модуля «Казино» (общий тумблер) и «Экономики».
Настройки (min_bet, max_bet, cooldown_sec, house_edge_percent) — из casino_core.

Кулдаун:
  - Блэкджек делит общий кулдаун казино со слотами и монеткой.
  - Нельзя начать слоты/монетку, пока идёт партия в блэкджек, и наоборот.
  - Кулдаун блэкджека запускается с МОМЕНТА ОКОНЧАНИЯ партии (не начала).

Блокировка параллельных кликов: asyncio.Lock на игрока.
"""

import asyncio
import logging
import time

import discord
from discord import app_commands
from discord.ext import commands

import blackjack_core as bj
import casino_core
import casino_db
import economy_core
import economy_db
from casino import CasinoCog, check_loss_roles

logger = logging.getLogger("blackjack")

DISABLED_TEXT = "Модуль «Казино» отключён."
ECONOMY_DISABLED_TEXT = "Модуль «Экономика» отключён — казино недоступно."


# ──────────────────────────── Embed-рендер ────────────────────────────

def _result_colour(result: bj.GameResult) -> discord.Colour:
    return {
        bj.GameResult.BLACKJACK: discord.Colour.gold(),
        bj.GameResult.WIN:       discord.Colour.green(),
        bj.GameResult.PUSH:      discord.Colour.light_grey(),
        bj.GameResult.LOSE:      discord.Colour.red(),
    }[result]


def _result_label(result: bj.GameResult) -> str:
    return {
        bj.GameResult.BLACKJACK: "🃏 Блэкджек!",
        bj.GameResult.WIN:       "✅ Победа!",
        bj.GameResult.PUSH:      "🤝 Ничья",
        bj.GameResult.LOSE:      "❌ Проигрыш",
    }[result]


def build_embed(
    game: bj.BlackjackGame,
    player: discord.Member | discord.User,
    econ: dict,
    *,
    hide_dealer: bool = True,
    result: bj.GameResult | None = None,
    prize: int | None = None,
) -> discord.Embed:
    """Построить embed состояния партии."""

    colour = discord.Colour.blurple() if result is None else _result_colour(result)
    title = "🎴 Блэкджек"
    if result is not None:
        title = f"🎴 Блэкджек — {_result_label(result)}"

    embed = discord.Embed(title=title, colour=colour)
    embed.set_author(name=player.display_name, icon_url=player.display_avatar.url)

    dealer_hand_str = bj.format_hand(game.dealer, hide_first=hide_dealer)
    dealer_val_str  = bj.format_value(game.dealer, hide_first=hide_dealer)
    player_hand_str = bj.format_hand(game.player)
    player_val_str  = bj.format_value(game.player)

    embed.add_field(
        name=f"Дилер — {dealer_val_str}",
        value=dealer_hand_str,
        inline=False,
    )
    embed.add_field(
        name=f"Вы — {player_val_str}",
        value=player_hand_str,
        inline=False,
    )

    bet_display = economy_core.format_amount(game.bet, econ)
    if game.doubled:
        bet_display += " (удвоено)"
    embed.add_field(name="Ставка", value=bet_display, inline=True)

    if prize is not None and result is not None:
        if result == bj.GameResult.LOSE:
            embed.add_field(name="Выигрыш", value="—", inline=True)
        else:
            embed.add_field(
                name="Выигрыш",
                value=economy_core.format_amount(prize, econ),
                inline=True,
            )

    balance = economy_db.get_balance(player.id)
    embed.set_footer(text=f"Баланс: {economy_core.format_amount(balance, econ)}")
    return embed


# ──────────────────────────── View с кнопками ────────────────────────────

class BlackjackView(discord.ui.View):
    """Кнопки игры: Ещё карту / Стоп / Удвоить."""

    def __init__(self, cog: "BlackjackCog", player: discord.Member | discord.User):
        super().__init__(timeout=300)  # 5 минут
        self.cog = cog
        self.player = player
        self._lock = asyncio.Lock()
        self.message: discord.Message | None = None  # заполняется после отправки

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "Это не твоя партия.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        """По истечении таймаута — ставка уже списана, партия молча завершается."""
        self.cog._games.pop(self.player.id, None)
        # Кулдаун НЕ запускаем при таймауте (игрок уже «наказан» потерей ставки)
        # Серый embed + отключённые кнопки, чтобы не было «Interaction Failed»
        self._finish_view()
        if self.message is not None:
            try:
                embed = self.message.embeds[0] if self.message.embeds else discord.Embed()
                embed.colour = discord.Colour.dark_grey()
                embed.set_footer(text="⏰ Время вышло — ставка потеряна.")
                await self.message.edit(embed=embed, view=self)
            except discord.NotFound:
                pass

    def _finish_view(self) -> None:
        """Отключить все кнопки после завершения партии."""
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

    async def _end_game(
        self,
        interaction: discord.Interaction,
        game: bj.BlackjackGame,
        econ: dict,
        settings: dict,
        *,
        prize: int,
        result: bj.GameResult,
    ) -> None:
        """Финализировать партию: начислить, обновить кулдаун, обновить embed."""
        if prize > 0:
            economy_db.add(self.player.id, prize, f"blackjack_{result.name.lower()}")

        db_result = "win"
        if result == bj.GameResult.LOSE:
            db_result = "lose"
        elif result == bj.GameResult.PUSH:
            db_result = "push"
        
        casino_db.record_bj(self.player.id, db_result)
        await check_loss_roles(interaction, settings)

        # Кулдаун стартует с момента окончания партии
        self.cog._cooldowns[self.player.id] = time.monotonic() + settings["cooldown_sec"]
        self.cog._games.pop(self.player.id, None)

        self._finish_view()
        embed = build_embed(
            game, self.player, econ,
            hide_dealer=False, result=result, prize=prize,
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    # ──────────────────────────── Кнопки ────────────────────────────

    @discord.ui.button(label="Ещё карту", emoji="🃏", style=discord.ButtonStyle.primary)
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self._lock:
            game = self.cog._games.get(self.player.id)
            if game is None or game.finished:
                await interaction.response.defer()
                return

            settings = casino_core.get_settings()
            econ = economy_core.get_settings()

            bj.hit(game)

            if bj.is_bust(game.player):
                game.finished = True
                result = bj.resolve(game)   # всегда LOSE при bust
                bj.dealer_play(game)        # открываем карты дилера для красоты
                await self._end_game(interaction, game, econ, settings, prize=0, result=result)
            else:
                # Игра продолжается: убираем кнопку «Удвоить» (2 карты уже нет)
                self._update_double_button()
                embed = build_embed(game, self.player, econ, hide_dealer=True)
                await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Стоп", emoji="✋", style=discord.ButtonStyle.secondary)
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self._lock:
            game = self.cog._games.get(self.player.id)
            if game is None or game.finished:
                await interaction.response.defer()
                return

            settings = casino_core.get_settings()
            econ = economy_core.get_settings()

            game.finished = True
            bj.dealer_play(game)
            result = bj.resolve(game)
            prize = bj.payout(game.bet, result, settings["house_edge_percent"])
            await self._end_game(interaction, game, econ, settings, prize=prize, result=result)

    @discord.ui.button(label="Удвоить", emoji="⬆️", style=discord.ButtonStyle.danger)
    async def double_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self._lock:
            game = self.cog._games.get(self.player.id)
            if game is None or game.finished or not bj.can_double(game.player):
                await interaction.response.defer()
                return

            settings = casino_core.get_settings()
            econ = economy_core.get_settings()

            # Списать ещё раз ту же ставку
            if not economy_db.try_spend(self.player.id, game.bet, "blackjack_double"):
                await interaction.response.send_message(
                    "Недостаточно средств для удвоения.", ephemeral=True
                )
                return

            game.bet *= 2
            game.doubled = True
            game.finished = True

            bj.hit(game)       # одна карта
            bj.dealer_play(game)
            result = bj.resolve(game)
            prize = bj.payout(game.bet, result, settings["house_edge_percent"])
            await self._end_game(interaction, game, econ, settings, prize=prize, result=result)

    def _update_double_button(self) -> None:
        """Отключить «Удвоить» если уже взяли карту."""
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "Удвоить":
                child.disabled = True


# ──────────────────────────── Ког ────────────────────────────

class BlackjackCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._games: dict[int, bj.BlackjackGame] = {}  # user_id → партия
        self._cooldowns: dict[int, float] = {}          # user_id → monotonic ready_at

    # ─── Публичный API для CasinoCog ───

    def has_active_game(self, user_id: int) -> bool:
        """True — у игрока есть незавершённая партия в блэкджек."""
        return user_id in self._games

    def cooldown_ready_at(self, user_id: int) -> float:
        """monotonic-время, когда кулдаун блэкджека снимается (0 если нет)."""
        return self._cooldowns.get(user_id, 0.0)

    # ─── Команда ───

    @app_commands.command(
        name="блэкджек",
        description="Сыграть в блэкджек против дилера на ставку монет",
    )
    @app_commands.describe(ставка="Сколько монет поставить")
    async def blackjack_command(self, interaction: discord.Interaction, ставка: int):

        settings = casino_core.get_settings()
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)

        econ = economy_core.get_settings()
        if not econ["enabled"]:
            return await interaction.response.send_message(ECONOMY_DISABLED_TEXT, ephemeral=True)

        user_id = interaction.user.id

        # Проверить: нет активной партии у игрока
        if self.has_active_game(user_id):
            return await interaction.response.send_message(
                "У тебя уже идёт партия в блэкджек — сначала доиграй её.", ephemeral=True
            )

        # Проверить кулдаун казино (общий — слоты / монетка / блэкджек)
        now = time.monotonic()
        ready_at = self._cooldowns.get(user_id, 0.0)
        if settings["cooldown_sec"] > 0 and now < ready_at:
            remaining = int(ready_at - now) + 1
            return await interaction.response.send_message(
                f"Казино отдыхает — попробуй через {remaining} сек.", ephemeral=True
            )

        # Также проверить кулдаун из CasinoCog (слоты/монетка поставили кулдаун)
        casino_cog: "CasinoCog | None" = self.bot.cogs.get("CasinoCog")
        if casino_cog is not None:
            casino_ready_at = casino_cog._cooldowns.get(user_id, 0.0)
            if settings["cooldown_sec"] > 0 and now < casino_ready_at:
                remaining = int(casino_ready_at - now) + 1
                return await interaction.response.send_message(
                    f"Казино отдыхает — попробуй через {remaining} сек.", ephemeral=True
                )
            # Проверить: нет активной BJ-партии через CasinoCog (если вдруг несколько экземпляров)
            # Дополнительная проверка не нужна — _games уже проверен выше

        # Валидация ставки
        balance = economy_db.get_balance(user_id)
        bet_problem = casino_core.bet_error(ставка, balance, settings)
        if bet_problem:
            return await interaction.response.send_message(bet_problem, ephemeral=True)

        # Списать ставку
        if not economy_db.try_spend(user_id, ставка, "blackjack_bet"):
            return await interaction.response.send_message(
                "Недостаточно средств для ставки.", ephemeral=True
            )

        # Создать партию
        game = bj.new_game(ставка)
        self._games[user_id] = game

        # Проверить натуральный блэкджек сразу (у игрока или дилера)
        if bj.is_blackjack(game.player) or bj.is_blackjack(game.dealer):
            game.finished = True
            bj.dealer_play(game)
            result = bj.resolve(game)
            prize = bj.payout(game.bet, result, settings["house_edge_percent"])
            if prize > 0:
                economy_db.add(user_id, prize, f"blackjack_{result.value}")
            # Кулдаун стартует с окончания партии
            self._cooldowns[user_id] = time.monotonic() + settings["cooldown_sec"]
            self._games.pop(user_id, None)

            embed = build_embed(
                game, interaction.user, econ,
                hide_dealer=False, result=result, prize=prize,
            )
            return await interaction.response.send_message(embed=embed)

        # Обычная игра — отправить embed + View
        view = BlackjackView(cog=self, player=interaction.user)
        embed = build_embed(game, interaction.user, econ, hide_dealer=True)
        await interaction.response.send_message(embed=embed, view=view)
        # Сохранить ссылку на сообщение — нужна для on_timeout (отключение кнопок)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot):
    await bot.add_cog(BlackjackCog(bot))
