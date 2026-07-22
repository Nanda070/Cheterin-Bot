"""Ког «Розыгрыши» (giveaways): /giveaway start приз время победителей — с таймером, реролом и
автовыбором победителя. Портировано по образцу supply.py: розыгрыши хранятся
per-guild в settings_db и восстанавливаются после перезапуска бота (таймеры
пересоздаются, кнопка участия продолжает работать через persistent view).
"""

import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

import giveaway_core
import i18n
import slash_registry

logger = logging.getLogger("giveaways")


def generate_embed(giveaway: dict, lang: str) -> discord.Embed:
    is_closed = giveaway["status"] != "active"

    if giveaway["status"] == "cancelled":
        color = 0x2B2D31
        title = i18n.t("giveaways.embed.cancelled_title", lang)
        timer_text = i18n.t("giveaways.embed.cancelled_timer", lang)
    elif is_closed:
        color = 0x2B2D31
        title = i18n.t("giveaways.embed.finished_title", lang)
        timer_text = i18n.t("giveaways.embed.finished_timer", lang)
    else:
        color = 0xFEE75C
        title = i18n.t("giveaways.embed.active_title", lang)
        timer_text = f"<t:{giveaway['target_ts']}:R>"

    embed = discord.Embed(title=title, color=color)
    embed.add_field(name=i18n.t("giveaways.embed.prize", lang), value=f"**{giveaway['prize']}**", inline=True)
    embed.add_field(name=i18n.t("giveaways.embed.winners_count", lang), value=str(giveaway["winners_count"]), inline=True)
    embed.add_field(name=i18n.t("giveaways.embed.ends", lang), value=timer_text, inline=True)
    hint = i18n.t("giveaways.embed.closed_hint", lang) if is_closed else i18n.t("giveaways.embed.join_hint", lang)
    embed.add_field(
        name=i18n.t("giveaways.embed.participants_line", lang, count=len(giveaway["entrants"])),
        value=hint,
        inline=False,
    )
    if giveaway["winners"]:
        mentions = "\n".join(f"🏆 <@{uid}>" for uid in giveaway["winners"])
        embed.add_field(name=i18n.t("giveaways.embed.winners", lang), value=mentions, inline=False)
    embed.set_footer(text=i18n.t("giveaways.embed.footer", lang, id=giveaway["id"]))
    return embed


class GiveawayView(discord.ui.View):
    """Persistent view: кнопка работает и после перезапуска бота."""

    def __init__(self, cog: "GiveawayCog"):
        super().__init__(timeout=None)
        self.cog = cog

    def _get_giveaway(self, interaction: discord.Interaction) -> dict | None:
        if interaction.message is None or interaction.guild_id is None:
            return None
        return giveaway_core.get_giveaway_by_message(interaction.guild_id, interaction.message.id)

    @discord.ui.button(label="🎉", style=discord.ButtonStyle.green, custom_id="giveaway:join")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        lang = i18n.lang_for(interaction.guild_id)
        button.label = i18n.t("giveaways.button.join", lang)

        giveaway = self._get_giveaway(interaction)
        if giveaway is None:
            return await interaction.response.send_message(i18n.t("giveaways.not_found", lang), ephemeral=True)

        result = giveaway_core.join_giveaway(interaction.guild_id, giveaway["id"], interaction.user.id)
        if result == "already":
            result = giveaway_core.leave_giveaway(interaction.guild_id, giveaway["id"], interaction.user.id)
            note = i18n.t("giveaways.left", lang) if result == "left" else i18n.t("giveaways.closed", lang)
        elif result == "joined":
            note = i18n.t("giveaways.joined", lang)
        elif result == "closed":
            note = i18n.t("giveaways.closed", lang)
        else:
            note = i18n.t("giveaways.not_found", lang)

        giveaway = giveaway_core.get_giveaway(interaction.guild_id, giveaway["id"])
        if giveaway is None:
            return await interaction.response.send_message(note, ephemeral=True)

        await interaction.response.edit_message(embed=generate_embed(giveaway, lang), view=self)
        await interaction.followup.send(note, ephemeral=True)


class GiveawayCog(commands.Cog):
    giveaway_group = app_commands.Group(
        name="giveaway",
        description="Розыгрыши призов",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._timers: dict[str, asyncio.Task] = {}
        self._recovered = False
        self.view = GiveawayView(self)

    async def cog_load(self):
        self.bot.add_view(self.view)

    def cog_unload(self):
        for task in self._timers.values():
            task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if self._recovered:
            return
        self._recovered = True
        await self.recover_giveaways()

    async def recover_giveaways(self):
        for guild in self.bot.guilds:
            for giveaway in giveaway_core.list_active(guild.id):
                self.schedule_giveaway(giveaway)

    def schedule_giveaway(self, giveaway: dict):
        guild_id = int(giveaway["guild_id"])
        key = (guild_id, giveaway["id"])
        old = self._timers.pop(key, None)
        if old:
            old.cancel()
        self._timers[key] = self.bot.loop.create_task(self._run_giveaway_timer(guild_id, giveaway["id"]))

    async def _run_giveaway_timer(self, guild_id: int, giveaway_id: str):
        try:
            giveaway = giveaway_core.get_giveaway(guild_id, giveaway_id)
            if giveaway is None or giveaway["status"] != "active":
                return
            now_ts = int(datetime.now(timezone.utc).timestamp())
            if giveaway["target_ts"] > now_ts:
                await asyncio.sleep(giveaway["target_ts"] - now_ts)
            await self.finalize_giveaway(guild_id, giveaway_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Giveaway timer failed: %s", giveaway_id)

    async def finalize_giveaway(self, guild_id: int, giveaway_id: str, status: str = "finished") -> bool:
        lang = i18n.lang_for(guild_id)
        giveaway = giveaway_core.close_giveaway(guild_id, giveaway_id, status=status)
        if giveaway is None:
            return False

        task = self._timers.pop((guild_id, giveaway_id), None)
        if task and task is not asyncio.current_task():
            task.cancel()

        channel = self.bot.get_channel(int(giveaway["channel_id"] or 0))
        message = None
        if channel is not None and giveaway["message_id"]:
            try:
                message = await channel.fetch_message(int(giveaway["message_id"]))
            except discord.HTTPException:
                message = None

        try:
            if message is not None:
                await message.edit(embed=generate_embed(giveaway, lang), view=None)

            if status == "finished" and channel is not None:
                if giveaway["winners"]:
                    mentions = " ".join(f"<@{uid}>" for uid in giveaway["winners"])
                    await channel.send(
                        content=i18n.t("giveaways.winners_announce", lang, mentions=mentions, prize=giveaway["prize"])
                    )
                else:
                    await channel.send(
                        content=i18n.t("giveaways.no_entrants", lang, prize=giveaway["prize"])
                    )
        except discord.HTTPException:
            logger.warning("Не удалось объявить итоги розыгрыша %s", giveaway_id)
        return True

    async def publish_giveaway(self, guild_id: int, channel, initiator_id: int, prize: str, duration_str: str, winners_count: int) -> dict:
        """Создаёт розыгрыш и публикует сообщение с кнопкой. Используется командой и дашбордом."""
        lang = i18n.lang_for(guild_id)
        giveaway = giveaway_core.create_giveaway(guild_id, initiator_id, prize, duration_str, winners_count)
        message = await channel.send(embed=generate_embed(giveaway, lang), view=self.view)
        giveaway = giveaway_core.update_giveaway(
            guild_id, giveaway["id"], channel_id=str(message.channel.id), message_id=str(message.id)
        )
        self.schedule_giveaway(giveaway)
        return giveaway

    @giveaway_group.command(name="start", description="Начать розыгрыш приза")
    @app_commands.describe(
        приз="Что разыгрывается",
        время="Длительность розыгрыша (например, 10m, 2h, 1d)",
        победителей="Сколько победителей выбрать",
    )
    async def giveaway_start(
        self,
        interaction: discord.Interaction,
        приз: str,
        время: str,
        победителей: app_commands.Range[int, 1, 20] = 1,
    ):
        lang = i18n.lang_for(interaction.guild_id)
        try:
            giveaway_core.parse_duration(время, lang)
        except ValueError as exc:
            return await interaction.response.send_message(f"❌ {exc}", ephemeral=True)

        await interaction.response.defer()
        giveaway = await self.publish_giveaway(interaction.guild_id, interaction.channel, interaction.user.id, приз, время, победителей)
        await interaction.followup.send(i18n.t("giveaways.started", lang, id=giveaway["id"]), ephemeral=True)

    async def reroll_and_announce(self, guild_id: int, giveaway_id: str) -> list[str] | None:
        """Перевыбирает победителей и объявляет в канале розыгрыша. Используется командой и дашбордом."""
        lang = i18n.lang_for(guild_id)
        winners = giveaway_core.reroll_giveaway(guild_id, giveaway_id)
        if winners is None:
            return None

        giveaway = giveaway_core.get_giveaway(guild_id, giveaway_id)
        channel = self.bot.get_channel(int(giveaway["channel_id"] or 0)) if giveaway else None
        if channel is not None:
            if winners:
                mentions = " ".join(f"<@{uid}>" for uid in winners)
                try:
                    await channel.send(content=i18n.t("giveaways.reroll_announce", lang, mentions=mentions))
                except discord.HTTPException:
                    pass
            if giveaway and giveaway["message_id"]:
                try:
                    message = await channel.fetch_message(int(giveaway["message_id"]))
                    await message.edit(embed=generate_embed(giveaway, lang))
                except discord.HTTPException:
                    pass
        return winners

    @giveaway_group.command(name="reroll", description="Перевыбрать победителя(ей) завершённого розыгрыша")
    @app_commands.describe(giveaway_id="ID розыгрыша (указан в футере эмбеда)")
    async def giveaway_reroll(self, interaction: discord.Interaction, giveaway_id: str):
        lang = i18n.lang_for(interaction.guild_id)
        await interaction.response.defer(ephemeral=True)
        winners = await self.reroll_and_announce(interaction.guild_id, giveaway_id)
        if winners is None:
            return await interaction.followup.send(i18n.t("giveaways.reroll.not_found", lang), ephemeral=True)
        if not winners:
            return await interaction.followup.send(i18n.t("giveaways.reroll.no_entrants", lang), ephemeral=True)
        await interaction.followup.send(i18n.t("giveaways.reroll.done", lang), ephemeral=True)

    @giveaway_group.command(name="end", description="Досрочно завершить розыгрыш")
    @app_commands.describe(giveaway_id="ID розыгрыша (указан в футере эмбеда)")
    async def giveaway_end(self, interaction: discord.Interaction, giveaway_id: str):
        lang = i18n.lang_for(interaction.guild_id)
        await interaction.response.defer(ephemeral=True)
        ok = await self.finalize_giveaway(interaction.guild_id, giveaway_id)
        if not ok:
            return await interaction.followup.send(i18n.t("giveaways.end.not_found", lang), ephemeral=True)
        await interaction.followup.send(i18n.t("giveaways.end.done", lang), ephemeral=True)


async def setup(bot: commands.Bot):
    cog = GiveawayCog(bot)
    slash_registry.register_giveaways(cog)
    await bot.add_cog(cog)
