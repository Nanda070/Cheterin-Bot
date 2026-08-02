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

import embed_style
import casino_core
import casino_db
import economy_core
import economy_db
import i18n
import slash_i18n
import slash_registry

logger = logging.getLogger("casino")

COINFLIP_CHOICES = [
    slash_i18n.localized_choice("орел", "casino.coinflip.heads"),
    slash_i18n.localized_choice("решка", "casino.coinflip.tails"),
]


def _coinflip_label(side: str, lang: str) -> str:
    if side == "орел":
        return i18n.t("casino.coinflip.heads", lang)
    return i18n.t("casino.coinflip.tails", lang)


async def check_loss_roles(interaction: discord.Interaction, settings: dict):
    user = interaction.user
    if not isinstance(user, discord.Member):
        return

    lang = i18n.lang_for(interaction.guild_id)
    loss_roles = settings.get("loss_roles", [])
    if not loss_roles:
        return

    stats = casino_db.get_stats(interaction.guild.id, user.id)
    total_losses = stats["slots_losses"] + stats["bj_losses"]

    roles_to_add = []
    for rule in loss_roles:
        try:
            role_id = int(rule.get("role_id", ""))
        except ValueError:
            continue

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
            await user.add_roles(
                *roles_to_add,
                reason=i18n.t("casino.loss_role_reason", lang),
            )
        except discord.HTTPException:
            pass


class CasinoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._cooldowns: dict[tuple[int, int], float] = {}

    def cooldown_ready_at(self, guild_id: int, user_id: int) -> float:
        return self._cooldowns.get((guild_id, user_id), 0.0)

    def _gate(
        self, interaction: discord.Interaction,
    ) -> tuple[dict, dict, str | None, str]:
        lang = i18n.lang_for(interaction.guild_id)
        settings = casino_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return settings, {}, i18n.module_disabled(lang, "casino"), lang
        econ = economy_core.get_settings(interaction.guild.id)
        if not econ["enabled"]:
            return settings, econ, i18n.t("error.economy_disabled_casino", lang), lang

        bj_cog = self.bot.cogs.get("BlackjackCog")
        if (
            bj_cog is not None
            and interaction.guild_id is not None
            and bj_cog.has_active_game(interaction.guild_id, interaction.user.id)
        ):
            return settings, econ, i18n.t("casino.bj_active_first", lang), lang

        guild_id = interaction.guild.id
        user_id = interaction.user.id
        now = time.monotonic()
        ready_at = max(
            self.cooldown_ready_at(guild_id, user_id),
            bj_cog.cooldown_ready_at(guild_id, user_id) if bj_cog else 0.0,
        )
        if settings["cooldown_sec"] > 0 and now < ready_at:
            remaining = int(ready_at - now) + 1
            return settings, econ, i18n.t("casino.cooldown", lang, seconds=remaining), lang
        return settings, econ, None, lang

    def _start_cooldown(self, guild_id: int, user_id: int, cooldown_sec: int):
        self._cooldowns[(guild_id, user_id)] = time.monotonic() + cooldown_sec

    @app_commands.command(name="слоты", description="Крутить слоты на ставку монет: 3 барабана, совпадения дают выигрыш")
    @app_commands.describe(ставка="Сколько монет поставить")
    async def slots_command(self, interaction: discord.Interaction, ставка: int):
        settings, econ, error, lang = self._gate(interaction)
        if error:
            return await interaction.response.send_message(error, ephemeral=True)

        balance = economy_db.get_balance(interaction.guild.id, interaction.user.id)
        balance_display = economy_core.format_amount(balance, econ)
        bet_problem = casino_core.bet_error(
            ставка, balance, settings, lang=lang, balance_display=balance_display,
        )
        if bet_problem:
            return await interaction.response.send_message(bet_problem, ephemeral=True)

        if not economy_db.try_spend(interaction.guild.id, interaction.user.id, ставка, "slots_bet"):
            return await interaction.response.send_message(
                i18n.t("error.insufficient_funds_bet", lang), ephemeral=True,
            )
        self._start_cooldown(interaction.guild.id, interaction.user.id, settings["cooldown_sec"])

        reels = casino_core.roll_slots()
        multiplier = casino_core.slot_multiplier(reels)
        reels_text = " ".join(reels)

        if multiplier <= 0:
            casino_db.record_slots(interaction.guild.id, interaction.user.id, won=False)
            await check_loss_roles(interaction, settings)
            balance = economy_db.get_balance(interaction.guild.id, interaction.user.id)
            return await interaction.response.send_message(
                i18n.t(
                    "casino.slots.miss",
                    lang,
                    reels=reels_text,
                    mention=interaction.user.mention,
                    balance=economy_core.format_amount(balance, econ),
                )
            )

        casino_db.record_slots(interaction.guild.id, interaction.user.id, won=True)
        payout = casino_core.payout_amount(ставка, multiplier, settings["house_edge_percent"])
        balance = economy_db.add(interaction.guild.id, interaction.user.id, payout, "slots_win")
        kind_key = (
            "casino.slots.kind.jackpot" if reels[0] == reels[1] == reels[2]
            else "casino.slots.kind.match"
        )
        await interaction.response.send_message(
            i18n.t(
                "casino.slots.win",
                lang,
                reels=reels_text,
                mention=interaction.user.mention,
                kind=i18n.t(kind_key, lang),
                payout=economy_core.format_amount(payout, econ),
                balance=economy_core.format_amount(balance, econ),
            )
        )

    @app_commands.command(name="монетка", description="Подбросить монетку на ставку: угадал сторону — выигрыш")
    @app_commands.describe(ставка="Сколько монет поставить", сторона="Орёл или решка")
    @app_commands.choices(сторона=COINFLIP_CHOICES)
    async def coinflip_command(
        self, interaction: discord.Interaction, ставка: int, сторона: app_commands.Choice[str],
    ):
        settings, econ, error, lang = self._gate(interaction)
        if error:
            return await interaction.response.send_message(error, ephemeral=True)

        balance = economy_db.get_balance(interaction.guild.id, interaction.user.id)
        balance_display = economy_core.format_amount(balance, econ)
        bet_problem = casino_core.bet_error(
            ставка, balance, settings, lang=lang, balance_display=balance_display,
        )
        if bet_problem:
            return await interaction.response.send_message(bet_problem, ephemeral=True)

        if not economy_db.try_spend(interaction.guild.id, interaction.user.id, ставка, "coinflip_bet"):
            return await interaction.response.send_message(
                i18n.t("error.insufficient_funds_bet", lang), ephemeral=True,
            )
        self._start_cooldown(interaction.guild.id, interaction.user.id, settings["cooldown_sec"])

        result = casino_core.flip_coin()
        emoji = "🦅" if result == "орел" else "🪙"
        label = _coinflip_label(result, lang)

        if result != сторона.value:
            casino_db.record_slots(interaction.guild.id, interaction.user.id, won=False)
            await check_loss_roles(interaction, settings)
            balance = economy_db.get_balance(interaction.guild.id, interaction.user.id)
            return await interaction.response.send_message(
                i18n.t(
                    "casino.coinflip.loss",
                    lang,
                    emoji=emoji,
                    label=label,
                    mention=interaction.user.mention,
                    balance=economy_core.format_amount(balance, econ),
                )
            )

        casino_db.record_slots(interaction.guild.id, interaction.user.id, won=True)
        payout = casino_core.payout_amount(ставка, casino_core.COINFLIP_MULTIPLIER, settings["house_edge_percent"])
        balance = economy_db.add(interaction.guild.id, interaction.user.id, payout, "coinflip_win")
        await interaction.response.send_message(
            i18n.t(
                "casino.coinflip.win",
                lang,
                emoji=emoji,
                label=label,
                mention=interaction.user.mention,
                payout=economy_core.format_amount(payout, econ),
                balance=economy_core.format_amount(balance, econ),
            )
        )


class CasinoLeaderboardView(discord.ui.View):
    def __init__(self, bot: commands.Bot, interaction: discord.Interaction, lang: str):
        super().__init__(timeout=120)
        self.bot = bot
        self.original_user = interaction.user
        self.lang = lang
        self.page = 1
        self.per_page = 10
        self.mode = "total"
        self.stat_type = "losses"

        self._update_buttons()

    def _update_buttons(self):
        self.btn_type_wins.label = i18n.t("casino.top.btn.wins", self.lang)
        self.btn_type_losses.label = i18n.t("casino.top.btn.losses", self.lang)
        self.btn_mode_slots.label = i18n.t("casino.top.btn.mode_slots", self.lang)
        self.btn_mode_bj.label = i18n.t("casino.top.btn.mode_bj", self.lang)
        self.btn_mode_total.label = i18n.t("casino.top.btn.mode_total", self.lang)

        self.btn_type_wins.style = discord.ButtonStyle.primary if self.stat_type == "wins" else discord.ButtonStyle.secondary
        self.btn_type_losses.style = discord.ButtonStyle.primary if self.stat_type == "losses" else discord.ButtonStyle.secondary

        self.btn_mode_slots.style = discord.ButtonStyle.primary if self.mode == "slots" else discord.ButtonStyle.secondary
        self.btn_mode_bj.style = discord.ButtonStyle.primary if self.mode == "bj" else discord.ButtonStyle.secondary
        self.btn_mode_total.style = discord.ButtonStyle.primary if self.mode == "total" else discord.ButtonStyle.secondary

    def build_embed(self, guild: discord.Guild) -> discord.Embed:
        all_rows = casino_db.leaderboard(guild.id, self.mode, self.stat_type, limit=1000)
        total_pages = max(1, (len(all_rows) + self.per_page - 1) // self.per_page)
        self.page = min(self.page, total_pages)
        self.page = max(1, self.page)

        self.btn_first.disabled = (self.page == 1)
        self.btn_prev.disabled = (self.page == 1)
        self.btn_next.disabled = (self.page == total_pages)
        self.btn_last.disabled = (self.page == total_pages)

        stat_key = (
            "casino.top.stat.wins" if self.stat_type == "wins"
            else "casino.top.stat.losses"
        )
        embed = discord.Embed(
            title=i18n.t(
                "casino.top.title",
                self.lang,
                stat=i18n.t(stat_key, self.lang),
                mode=self._mode_name(),
            ),
            color=embed_style.DANGER if self.stat_type == "losses" else embed_style.SUCCESS,
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
                    lines.append(i18n.t(
                        "casino.top.line.total.wins",
                        self.lang,
                        icon=icon, rank=rank, mention=mention,
                        total=total_val, slots=row["slots_wins"], bj=row["bj_wins"],
                    ))
                else:
                    total_val = row["slots_losses"] + row["bj_losses"]
                    lines.append(i18n.t(
                        "casino.top.line.total.losses",
                        self.lang,
                        icon=icon, rank=rank, mention=mention,
                        total=total_val, slots=row["slots_losses"], bj=row["bj_losses"],
                    ))
            elif self.mode == "slots":
                val = row["slots_wins"] if self.stat_type == "wins" else row["slots_losses"]
                emoji = "🏆" if self.stat_type == "wins" else "❌"
                lines.append(i18n.t(
                    "casino.top.line.slots",
                    self.lang,
                    icon=icon, rank=rank, mention=mention, val=val, emoji=emoji,
                ))
            elif self.mode == "bj":
                val = row["bj_wins"] if self.stat_type == "wins" else row["bj_losses"]
                emoji = "🏆" if self.stat_type == "wins" else "❌"
                lines.append(i18n.t(
                    "casino.top.line.bj",
                    self.lang,
                    icon=icon, rank=rank, mention=mention, val=val, emoji=emoji,
                ))

        if not lines:
            embed.description = i18n.t("casino.top.empty", self.lang)
        else:
            embed.description = "\n".join(lines)

        embed.set_footer(text=i18n.t("casino.top.footer", self.lang, page=self.page, total=total_pages))
        return embed

    def _mode_name(self) -> str:
        if self.mode == "slots":
            return i18n.t("casino.top.mode.slots", self.lang)
        if self.mode == "bj":
            return i18n.t("casino.top.mode.bj", self.lang)
        return i18n.t("casino.top.mode.total", self.lang)

    async def _update(self, interaction: discord.Interaction):
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(interaction.guild), view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.original_user:
            await interaction.response.send_message(
                i18n.t("casino.top.not_your_menu", self.lang), ephemeral=True,
            )
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

    view = CasinoLeaderboardView(interaction.client, interaction, lang)
    embed = view.build_embed(interaction.guild)
    await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    cog = CasinoCog(bot)
    slash_registry.register_casino(cog, casino_top_command)
    bot.tree.add_command(casino_top_command)
    await bot.add_cog(cog)
