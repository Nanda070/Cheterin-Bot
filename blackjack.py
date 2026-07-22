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
import i18n
import slash_registry
from casino import CasinoCog, check_loss_roles

logger = logging.getLogger("blackjack")


# ──────────────────────────── Embed-рендер ────────────────────────────

def _result_colour(result: bj.GameResult) -> discord.Colour:
    return {
        bj.GameResult.BLACKJACK: discord.Colour.gold(),
        bj.GameResult.WIN:       discord.Colour.green(),
        bj.GameResult.PUSH:      discord.Colour.light_grey(),
        bj.GameResult.LOSE:      discord.Colour.red(),
    }[result]


def _result_label(result: bj.GameResult, lang: str) -> str:
    keys = {
        bj.GameResult.BLACKJACK: "casino.bj.result.blackjack",
        bj.GameResult.WIN:       "casino.bj.result.win",
        bj.GameResult.PUSH:      "casino.bj.result.push",
        bj.GameResult.LOSE:      "casino.bj.result.lose",
    }
    return i18n.t(keys[result], lang)


def build_embed(
    game: bj.BlackjackGame,
    player: discord.Member | discord.User,
    econ: dict,
    lang: str,
    *,
    hide_dealer: bool = True,
    result: bj.GameResult | None = None,
    prize: int | None = None,
) -> discord.Embed:
    """Построить embed состояния партии."""

    colour = discord.Colour.blurple() if result is None else _result_colour(result)
    title = i18n.t("casino.bj.title", lang)
    if result is not None:
        title = i18n.t("casino.bj.title_result", lang, result=_result_label(result, lang))

    embed = discord.Embed(title=title, colour=colour)
    embed.set_author(name=player.display_name, icon_url=player.display_avatar.url)

    dealer_hand_str = bj.format_hand(game.dealer, hide_first=hide_dealer)
    dealer_val_str  = bj.format_value(game.dealer, hide_first=hide_dealer)
    player_hand_str = bj.format_hand(game.player)
    player_val_str  = bj.format_value(game.player)

    embed.add_field(
        name=i18n.t("casino.bj.dealer", lang, value=dealer_val_str),
        value=dealer_hand_str,
        inline=False,
    )
    embed.add_field(
        name=i18n.t("casino.bj.player", lang, value=player_val_str),
        value=player_hand_str,
        inline=False,
    )

    bet_display = economy_core.format_amount(game.bet, econ)
    if game.doubled:
        bet_display += i18n.t("casino.bj.bet_doubled", lang)
    embed.add_field(name=i18n.t("casino.bj.bet", lang), value=bet_display, inline=True)

    if prize is not None and result is not None:
        if result == bj.GameResult.LOSE:
            embed.add_field(
                name=i18n.t("casino.bj.prize", lang),
                value=i18n.t("casino.bj.prize_none", lang),
                inline=True,
            )
        else:
            embed.add_field(
                name=i18n.t("casino.bj.prize", lang),
                value=economy_core.format_amount(prize, econ),
                inline=True,
            )

    balance = economy_db.get_balance(player.id)
    embed.set_footer(text=i18n.t(
        "casino.bj.balance", lang, balance=economy_core.format_amount(balance, econ),
    ))
    return embed


# ──────────────────────────── View с кнопками ────────────────────────────

class BlackjackView(discord.ui.View):
    """Кнопки игры: Ещё карту / Стоп / Удвоить."""

    def __init__(
        self,
        cog: "BlackjackCog",
        player: discord.Member | discord.User,
        lang: str | None = None,
    ):
        super().__init__(timeout=300)
        self.cog = cog
        self.player = player
        self.lang = lang or i18n.DEFAULT_LANGUAGE
        self._lock = asyncio.Lock()
        self.message: discord.Message | None = None
        self._set_button_labels()

    def _set_button_labels(self) -> None:
        for child in self.children:
            if not isinstance(child, discord.ui.Button):
                continue
            if child.custom_id == "bj_hit":
                child.label = i18n.t("casino.bj.btn.hit", self.lang)
            elif child.custom_id == "bj_stand":
                child.label = i18n.t("casino.bj.btn.stand", self.lang)
            elif child.custom_id == "bj_double":
                child.label = i18n.t("casino.bj.btn.double", self.lang)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                i18n.t("error.not_your_turn", self.lang), ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        self.cog._games.pop(self.player.id, None)
        self._finish_view()
        if self.message is not None:
            try:
                embed = self.message.embeds[0] if self.message.embeds else discord.Embed()
                embed.colour = discord.Colour.dark_grey()
                embed.set_footer(text=i18n.t("casino.bj.timeout", self.lang))
                await self.message.edit(embed=embed, view=self)
            except discord.NotFound:
                pass

    def _finish_view(self) -> None:
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
        if prize > 0:
            economy_db.add(self.player.id, prize, f"blackjack_{result.name.lower()}")

        db_result = "win"
        if result == bj.GameResult.LOSE:
            db_result = "lose"
        elif result == bj.GameResult.PUSH:
            db_result = "push"

        casino_db.record_bj(self.player.id, db_result)
        await check_loss_roles(interaction, settings)

        self.cog._cooldowns[self.player.id] = time.monotonic() + settings["cooldown_sec"]
        self.cog._games.pop(self.player.id, None)

        self._finish_view()
        embed = build_embed(
            game, self.player, econ, self.lang,
            hide_dealer=False, result=result, prize=prize,
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Ещё карту", emoji="🃏", style=discord.ButtonStyle.primary, custom_id="bj_hit")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self._lock:
            game = self.cog._games.get(self.player.id)
            if game is None or game.finished:
                await interaction.response.defer()
                return

            settings = casino_core.get_settings(interaction.guild.id)
            econ = economy_core.get_settings(interaction.guild.id)

            bj.hit(game)

            if bj.is_bust(game.player):
                game.finished = True
                result = bj.resolve(game)
                bj.dealer_play(game)
                await self._end_game(interaction, game, econ, settings, prize=0, result=result)
            else:
                self._update_double_button()
                embed = build_embed(game, self.player, econ, self.lang, hide_dealer=True)
                await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Стоп", emoji="✋", style=discord.ButtonStyle.secondary, custom_id="bj_stand")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self._lock:
            game = self.cog._games.get(self.player.id)
            if game is None or game.finished:
                await interaction.response.defer()
                return

            settings = casino_core.get_settings(interaction.guild.id)
            econ = economy_core.get_settings(interaction.guild.id)

            game.finished = True
            bj.dealer_play(game)
            result = bj.resolve(game)
            prize = bj.payout(game.bet, result, settings["house_edge_percent"])
            await self._end_game(interaction, game, econ, settings, prize=prize, result=result)

    @discord.ui.button(label="Удвоить", emoji="⬆️", style=discord.ButtonStyle.danger, custom_id="bj_double")
    async def double_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self._lock:
            game = self.cog._games.get(self.player.id)
            if game is None or game.finished or not bj.can_double(game.player):
                await interaction.response.defer()
                return

            settings = casino_core.get_settings(interaction.guild.id)
            econ = economy_core.get_settings(interaction.guild.id)

            if not economy_db.try_spend(self.player.id, game.bet, "blackjack_double"):
                await interaction.response.send_message(
                    i18n.t("casino.bj.double_insufficient", self.lang), ephemeral=True,
                )
                return

            game.bet *= 2
            game.doubled = True
            game.finished = True

            bj.hit(game)
            bj.dealer_play(game)
            result = bj.resolve(game)
            prize = bj.payout(game.bet, result, settings["house_edge_percent"])
            await self._end_game(interaction, game, econ, settings, prize=prize, result=result)

    def _update_double_button(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "bj_double":
                child.disabled = True


# ──────────────────────────── Ког ────────────────────────────

class BlackjackCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._games: dict[int, bj.BlackjackGame] = {}
        self._cooldowns: dict[int, float] = {}

    def has_active_game(self, user_id: int) -> bool:
        return user_id in self._games

    def cooldown_ready_at(self, user_id: int) -> float:
        return self._cooldowns.get(user_id, 0.0)

    @app_commands.command(
        name="блэкджек",
        description="Сыграть в блэкджек против дилера на ставку монет",
    )
    @app_commands.describe(ставка="Сколько монет поставить")
    async def blackjack_command(self, interaction: discord.Interaction, ставка: int):

        lang = i18n.lang_for(interaction.guild_id)
        settings = casino_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "casino"), ephemeral=True,
            )

        econ = economy_core.get_settings(interaction.guild.id)
        if not econ["enabled"]:
            return await interaction.response.send_message(
                i18n.t("error.economy_disabled_casino", lang), ephemeral=True,
            )

        user_id = interaction.user.id

        if self.has_active_game(user_id):
            return await interaction.response.send_message(
                i18n.t("casino.bj.already_active", lang), ephemeral=True,
            )

        now = time.monotonic()
        ready_at = self._cooldowns.get(user_id, 0.0)
        if settings["cooldown_sec"] > 0 and now < ready_at:
            remaining = int(ready_at - now) + 1
            return await interaction.response.send_message(
                i18n.t("casino.cooldown", lang, seconds=remaining), ephemeral=True,
            )

        casino_cog: "CasinoCog | None" = self.bot.cogs.get("CasinoCog")
        if casino_cog is not None:
            casino_ready_at = casino_cog._cooldowns.get(user_id, 0.0)
            if settings["cooldown_sec"] > 0 and now < casino_ready_at:
                remaining = int(casino_ready_at - now) + 1
                return await interaction.response.send_message(
                    i18n.t("casino.cooldown", lang, seconds=remaining), ephemeral=True,
                )

        balance = economy_db.get_balance(user_id)
        balance_display = economy_core.format_amount(balance, econ)
        bet_problem = casino_core.bet_error(
            ставка, balance, settings, lang=lang, balance_display=balance_display,
        )
        if bet_problem:
            return await interaction.response.send_message(bet_problem, ephemeral=True)

        if not economy_db.try_spend(user_id, ставка, "blackjack_bet"):
            return await interaction.response.send_message(
                i18n.t("error.insufficient_funds_bet", lang), ephemeral=True,
            )

        game = bj.new_game(ставка)
        self._games[user_id] = game

        if bj.is_blackjack(game.player) or bj.is_blackjack(game.dealer):
            game.finished = True
            bj.dealer_play(game)
            result = bj.resolve(game)
            prize = bj.payout(game.bet, result, settings["house_edge_percent"])
            if prize > 0:
                economy_db.add(user_id, prize, f"blackjack_{result.value}")
            db_result = "win"
            if result == bj.GameResult.LOSE:
                db_result = "lose"
            elif result == bj.GameResult.PUSH:
                db_result = "push"
            casino_db.record_bj(user_id, db_result)
            await check_loss_roles(interaction, settings)
            self._cooldowns[user_id] = time.monotonic() + settings["cooldown_sec"]
            self._games.pop(user_id, None)

            embed = build_embed(
                game, interaction.user, econ, lang,
                hide_dealer=False, result=result, prize=prize,
            )
            return await interaction.response.send_message(embed=embed)

        view = BlackjackView(cog=self, player=interaction.user, lang=lang)
        embed = build_embed(game, interaction.user, econ, lang, hide_dealer=True)
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot):
    cog = BlackjackCog(bot)
    slash_registry.register_blackjack(cog)
    await bot.add_cog(cog)
