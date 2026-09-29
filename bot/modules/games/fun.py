"""Ког «Развлечения»: русская рулетка и эмодзи-рулетка.

Модуль выключен по умолчанию, включается в дашборде (раздел «Развлечения»).
Русская рулетка — соло: барабан без проворота, шанс растёт 1/6→…→1/1;
с шансом 8% барабан пустой (можно пройти 6/6). «Погибший» получает
Discord-таймаут на настраиваемое число минут (0 — без наказания).
"""

import asyncio
import logging
import time
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

import bot.modules.games.economy_core as economy_core
import bot.modules.games.economy_db as economy_db
import bot.modules.games.fun_core as fun_core
import bot.core.i18n as i18n
import bot.core.slash_registry as slash_registry

logger = logging.getLogger("fun")

INTRO_COUNT = 6
SURVIVE_COUNT = 10
DEATH_COUNT = 8


class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._roulette_cooldowns: dict[tuple[int, int], float] = {}
        self._roulette_clicks: dict[tuple[int, int], int] = {}
        self._roulette_empty: dict[tuple[int, int], bool] = {}
        self._auto_emoji_last: dict[int, float] = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        settings = fun_core.get_settings(message.guild.id)
        if not settings["enabled"] or not settings["auto_emoji_enabled"]:
            return

        now = time.monotonic()
        interval = settings["auto_emoji_min_interval_sec"]
        # Missing key = never reacted in this channel. Do not use 0.0 as a
        # sentinel: on fresh hosts time.monotonic() can be < interval and would
        # wrongly suppress the first reaction (seen on CI ubuntu runners).
        last = self._auto_emoji_last.get(message.channel.id)
        if interval > 0 and last is not None and now - last < interval:
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

    @app_commands.command(
        name="русская-рулетка",
        description="Спустить курок: шанс растёт (1/6→1/1), 8% пустой барабан. Можно ставить монеты",
    )
    @app_commands.describe(ставка="Ставка монет: выжил — удвоил, погиб — потерял (необязательно)")
    async def russian_roulette(self, interaction: discord.Interaction, ставка: int | None = None):
        lang = i18n.lang_for(interaction.guild_id)
        if interaction.guild is None or interaction.guild_id is None:
            return await interaction.response.send_message(
                i18n.t("moderation.guild_only", lang), ephemeral=True
            )

        settings = fun_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "fun"), ephemeral=True
            )

        key = (interaction.guild.id, interaction.user.id)
        cooldown = settings["roulette_cooldown_sec"]
        now = time.monotonic()
        ready_at = self._roulette_cooldowns.get(key, 0.0)
        if cooldown > 0 and now < ready_at:
            remaining = int(ready_at - now) + 1
            return await interaction.response.send_message(
                i18n.t("fun.roulette.cooldown", lang, seconds=remaining), ephemeral=True
            )

        econ = economy_core.get_settings(interaction.guild.id)
        bet = ставка or 0
        if bet > 0:
            if not econ["enabled"]:
                return await interaction.response.send_message(
                    i18n.t("error.economy_disabled_play_without_bet", lang), ephemeral=True
                )
            error = economy_core.bet_error(bet, economy_db.get_balance(interaction.guild.id, interaction.user.id), econ, lang=lang)
            if error:
                return await interaction.response.send_message(error, ephemeral=True)
            if not economy_db.try_spend(interaction.guild.id, interaction.user.id, bet, "roulette_bet"):
                return await interaction.response.send_message(
                    i18n.t("error.insufficient_funds_bet", lang), ephemeral=True
                )

        self._roulette_cooldowns[key] = now + cooldown

        clicks = self._roulette_clicks.get(key, 0)
        if clicks == 0:
            empty = fun_core.roll_empty_cylinder()
            self._roulette_empty[key] = empty
        else:
            empty = self._roulette_empty.get(key, False)

        chamber_text = i18n.t(
            "fun.roulette.chamber",
            lang,
            current=clicks + 1,
            total=fun_core.ROULETTE_CHAMBERS,
        )
        intro = i18n.pick_random("fun.roulette.intro", lang, INTRO_COUNT)

        if not fun_core.spin_trigger(clicks, empty_cylinder=empty):
            next_clicks = clicks + 1
            reload_note = ""
            if next_clicks >= fun_core.ROULETTE_CHAMBERS:
                self._roulette_clicks[key] = 0
                self._roulette_empty.pop(key, None)
                if empty:
                    reload_note = i18n.t("fun.roulette.empty_reload", lang)
            else:
                self._roulette_clicks[key] = next_clicks
            win_text = ""
            if bet > 0:
                balance = economy_db.add(interaction.guild.id, interaction.user.id, bet * 2, "roulette_win")
                win_text = i18n.t(
                    "fun.roulette.win_bet",
                    lang,
                    bet=economy_core.format_amount(bet, econ),
                    balance=economy_core.format_amount(balance, econ),
                )
            outcome = i18n.pick_random("fun.roulette.survive", lang, SURVIVE_COUNT)
            return await interaction.response.send_message(
                i18n.t(
                    "fun.roulette.play_line",
                    lang,
                    mention=interaction.user.mention,
                    intro=intro,
                    outcome=outcome,
                    chamber=chamber_text,
                    extra=win_text + reload_note,
                )
            )

        self._roulette_clicks[key] = 0
        self._roulette_empty.pop(key, None)

        timeout_minutes = settings["roulette_timeout_minutes"]
        death_line = i18n.pick_random("fun.roulette.death", lang, DEATH_COUNT)
        punished = False
        if timeout_minutes > 0 and interaction.guild is not None:
            try:
                await interaction.user.timeout(
                    timedelta(minutes=timeout_minutes),
                    reason=i18n.t("fun.roulette.timeout_reason", lang),
                )
                punished = True
            except (discord.HTTPException, AttributeError):
                logger.info("Не удалось выдать таймаут за рулетку пользователю %s", interaction.user.id)

        if punished:
            suffix = i18n.t(
                "fun.roulette.punished",
                lang,
                mention=interaction.user.mention,
                minutes=timeout_minutes,
            )
        elif timeout_minutes > 0:
            suffix = i18n.t("fun.roulette.immune", lang, mention=interaction.user.mention)
        else:
            suffix = i18n.t("fun.roulette.eliminated", lang, mention=interaction.user.mention)

        bet_text = ""
        if bet > 0:
            balance = economy_db.get_balance(interaction.guild.id, interaction.user.id)
            bet_text = i18n.t(
                "fun.roulette.lost_bet",
                lang,
                bet=economy_core.format_amount(bet, econ),
                balance=economy_core.format_amount(balance, econ),
            )

        await interaction.response.send_message(
            i18n.t(
                "fun.roulette.death_line",
                lang,
                mention=interaction.user.mention,
                intro=intro,
                death=death_line,
                chamber=chamber_text,
                suffix=suffix,
                bet_text=bet_text,
            )
        )


async def setup(bot: commands.Bot):
    cog = FunCog(bot)
    slash_registry.register_fun(cog)
    await bot.add_cog(cog)
