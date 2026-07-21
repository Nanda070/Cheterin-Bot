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
import casino_db
import economy_core
import economy_db

logger = logging.getLogger("casino")

DISABLED_TEXT = "Модуль «Казино» отключён."
ECONOMY_DISABLED_TEXT = "Модуль «Экономика» отключён — казино недоступно."

COINFLIP_CHOICES = [
    app_commands.Choice(name="Орёл", value="орел"),
    app_commands.Choice(name="Решка", value="решка"),
]


async def check_loss_roles(interaction: discord.Interaction, settings: dict):
    user = interaction.user
    if not isinstance(user, discord.Member):
        return

    loss_roles = settings.get("loss_roles", [])
    if not loss_roles:
        return

    stats = casino_db.get_stats(user.id)
    total_losses = stats["slots_losses"] + stats["bj_losses"]

    roles_to_add = []
    for rule in loss_roles:
        try:
            role_id = int(rule.get("role_id", ""))
        except ValueError:
            continue

        # Skip if member already has this role
        if user.get_role(role_id) is not None:
            continue

        threshold = rule.get("threshold", 0)
        if threshold <= 0:
            continue

        game = rule.get("game")
        current_losses = 0
        if game == "slots":
            current_losses = stats["slots_losses"]
        elif game == "bj":
            current_losses = stats["bj_losses"]
        elif game == "total":
            current_losses = total_losses

        if current_losses >= threshold:
            role = interaction.guild.get_role(role_id) if interaction.guild else None
            if role is not None and role not in roles_to_add:
                roles_to_add.append(role)

    if roles_to_add:
        try:
            await user.add_roles(*roles_to_add, reason="Достигнут порог проигрышей в казино")
        except discord.HTTPException:
            pass


class CasinoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._cooldowns: dict[int, float] = {}  # общий кулдаун между /слоты и /монетка

    def _gate(self, interaction: discord.Interaction) -> tuple[dict, dict, str | None]:
        """Проверка тумблеров, активного блэкджека и кулдауна.

        Возвращает (casino, economy, error_text).
        Блокирует слоты/монетку если у игрока есть незавершённая BJ-партия.
        """
        settings = casino_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return settings, {}, DISABLED_TEXT
        econ = economy_core.get_settings(interaction.guild.id)
        if not econ["enabled"]:
            return settings, econ, ECONOMY_DISABLED_TEXT

        # Нельзя играть в слоты/монетку пока активна партия в блэкджек
        bj_cog = self.bot.cogs.get("BlackjackCog")
        if bj_cog is not None and bj_cog.has_active_game(interaction.user.id):
            return settings, econ, "Сначала доиграй текущую партию в блэкджек."

        now = time.monotonic()
        # Проверяем и наш кулдаун, и кулдаун блэкджека (общий пул)
        ready_at = max(
            self._cooldowns.get(interaction.user.id, 0.0),
            bj_cog.cooldown_ready_at(interaction.user.id) if bj_cog else 0.0,
        )
        if settings["cooldown_sec"] > 0 and now < ready_at:
            remaining = int(ready_at - now) + 1
            return settings, econ, f"Казино отдыхает — попробуй через {remaining} сек."
        return settings, econ, None

    def _start_cooldown(self, user_id: int, cooldown_sec: int):
        self._cooldowns[user_id] = time.monotonic() + cooldown_sec

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
            casino_db.record_slots(interaction.user.id, won=False)
            await check_loss_roles(interaction, settings)
            balance = economy_db.get_balance(interaction.user.id)
            return await interaction.response.send_message(
                f"🎰 {reels_text}\n{interaction.user.mention} — мимо. "
                f"Баланс: {economy_core.format_amount(balance, econ)}."
            )

        casino_db.record_slots(interaction.user.id, won=True)
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
            casino_db.record_slots(interaction.user.id, won=False)
            await check_loss_roles(interaction, settings)
            balance = economy_db.get_balance(interaction.user.id)
            return await interaction.response.send_message(
                f"{emoji} Выпало: **{label}**.\n{interaction.user.mention} не угадал(а). "
                f"Баланс: {economy_core.format_amount(balance, econ)}."
            )

        casino_db.record_slots(interaction.user.id, won=True)
        payout = casino_core.payout_amount(ставка, casino_core.COINFLIP_MULTIPLIER, settings["house_edge_percent"])
        balance = economy_db.add(interaction.user.id, payout, "coinflip_win")
        await interaction.response.send_message(
            f"{emoji} Выпало: **{label}**.\n{interaction.user.mention} угадал(а)! Выигрыш: "
            f"**{economy_core.format_amount(payout, econ)}** (баланс: {economy_core.format_amount(balance, econ)})."
        )


class CasinoLeaderboardView(discord.ui.View):
    def __init__(self, bot: commands.Bot, interaction: discord.Interaction):
        super().__init__(timeout=120)
        self.bot = bot
        self.original_user = interaction.user
        self.page = 1
        self.per_page = 10
        self.mode = "total"  # "slots", "bj", "total"
        self.stat_type = "losses"  # "wins", "losses"
        
        self._update_buttons()

    def _update_buttons(self):
        self.btn_type_wins.style = discord.ButtonStyle.primary if self.stat_type == "wins" else discord.ButtonStyle.secondary
        self.btn_type_losses.style = discord.ButtonStyle.primary if self.stat_type == "losses" else discord.ButtonStyle.secondary

        self.btn_mode_slots.style = discord.ButtonStyle.primary if self.mode == "slots" else discord.ButtonStyle.secondary
        self.btn_mode_bj.style = discord.ButtonStyle.primary if self.mode == "bj" else discord.ButtonStyle.secondary
        self.btn_mode_total.style = discord.ButtonStyle.primary if self.mode == "total" else discord.ButtonStyle.secondary

    def build_embed(self, guild: discord.Guild) -> discord.Embed:
        # Full data load for simplicity and correct pagination
        all_rows = casino_db.leaderboard(self.mode, self.stat_type, limit=1000)
        total_pages = max(1, (len(all_rows) + self.per_page - 1) // self.per_page)
        self.page = min(self.page, total_pages)
        self.page = max(1, self.page)

        self.btn_first.disabled = (self.page == 1)
        self.btn_prev.disabled = (self.page == 1)
        self.btn_next.disabled = (self.page == total_pages)
        self.btn_last.disabled = (self.page == total_pages)

        embed = discord.Embed(
            title=f"Казино — Топ по {'победам' if self.stat_type == 'wins' else 'проигрышам'} "
                  f"({self._mode_name()})",
            colour=discord.Colour.red() if self.stat_type == "losses" else discord.Colour.green(),
        )
        if guild and guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        offset = (self.page - 1) * self.per_page
        page_rows = all_rows[offset:offset + self.per_page]

        lines = []
        for i, row in enumerate(page_rows):
            rank = offset + i + 1
            member = guild.get_member(row["user_id"])
            display = member.display_name if member else str(row["user_id"])
            mention = member.mention if member else display
            
            icon = "⭐" if rank == 1 else "🌟" if rank == 2 else "✨" if rank == 3 else "▫️"
            
            if self.mode == "total":
                if self.stat_type == "wins":
                    total_val = row["slots_wins"] + row["bj_wins"]
                    lines.append(f"{icon} **#{rank}.** {mention} — Всего: {total_val} 🏆 (🎰 {row['slots_wins']} | 🎴 {row['bj_wins']})")
                else:
                    total_val = row["slots_losses"] + row["bj_losses"]
                    lines.append(f"{icon} **#{rank}.** {mention} — Всего: {total_val} ❌ (🎰 {row['slots_losses']} | 🎴 {row['bj_losses']})")
            elif self.mode == "slots":
                val = row["slots_wins"] if self.stat_type == "wins" else row["slots_losses"]
                emoji = "🏆" if self.stat_type == "wins" else "❌"
                lines.append(f"{icon} **#{rank}.** {mention} — 🎰 {val} {emoji}")
            elif self.mode == "bj":
                val = row["bj_wins"] if self.stat_type == "wins" else row["bj_losses"]
                emoji = "🏆" if self.stat_type == "wins" else "❌"
                lines.append(f"{icon} **#{rank}.** {mention} — 🎴 {val} {emoji}")

        if not lines:
            embed.description = "Таблица пуста."
        else:
            embed.description = "\n".join(lines)

        embed.set_footer(text=f"Страница {self.page} из {total_pages}")
        return embed

    def _mode_name(self) -> str:
        if self.mode == "slots": return "Слоты/Монетка"
        if self.mode == "bj": return "Блэкджек"
        return "Общий"

    async def _update(self, interaction: discord.Interaction):
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(interaction.guild), view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.original_user:
            await interaction.response.send_message("Это не ваше меню.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🏆 Победы", row=0, custom_id="type_wins")
    async def btn_type_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stat_type = "wins"
        self.page = 1
        await self._update(interaction)

    @discord.ui.button(label="❌ Проигрыши", row=0, custom_id="type_losses")
    async def btn_type_losses(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stat_type = "losses"
        self.page = 1
        await self._update(interaction)

    @discord.ui.button(label="🎰 Слоты/Монетка", row=1, custom_id="mode_slots")
    async def btn_mode_slots(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "slots"
        self.page = 1
        await self._update(interaction)

    @discord.ui.button(label="🎴 Блэкджек", row=1, custom_id="mode_bj")
    async def btn_mode_bj(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "bj"
        self.page = 1
        await self._update(interaction)

    @discord.ui.button(label="📊 Общий", row=1, custom_id="mode_total")
    async def btn_mode_total(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "total"
        self.page = 1
        await self._update(interaction)

    @discord.ui.button(label="«", row=2, custom_id="page_first")
    async def btn_first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 1
        await self._update(interaction)

    @discord.ui.button(label="‹", row=2, custom_id="page_prev")
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        await self._update(interaction)

    @discord.ui.button(label="›", row=2, custom_id="page_next")
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await self._update(interaction)

    @discord.ui.button(label="»", row=2, custom_id="page_last")
    async def btn_last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 9999
        await self._update(interaction)

    @discord.ui.button(label="✕", row=2, style=discord.ButtonStyle.danger, custom_id="close")
    async def btn_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        self.stop()

@app_commands.command(name="казино-топ", description="Таблица лидеров казино по победам и проигрышам")
async def casino_top_command(interaction: discord.Interaction):
    settings = casino_core.get_settings(interaction.guild.id)
    if not settings["enabled"]:
        return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)
    econ = economy_core.get_settings(interaction.guild.id)
    if not econ["enabled"]:
        return await interaction.response.send_message(ECONOMY_DISABLED_TEXT, ephemeral=True)

    view = CasinoLeaderboardView(interaction.client, interaction)
    embed = view.build_embed(interaction.guild)
    await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    cog = CasinoCog(bot)
    bot.tree.add_command(casino_top_command)
    await bot.add_cog(cog)
