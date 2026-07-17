"""Ког «Гивевеи»: /giveaway start приз время победителей — с таймером, реролом и
автовыбором победителя. Портировано по образцу supply.py: розыгрыши хранятся в
giveaways_data.json и восстанавливаются после перезапуска бота (таймеры
пересоздаются, кнопка участия продолжает работать через persistent view).
"""

import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

import giveaway_core

logger = logging.getLogger("giveaways")


def generate_embed(giveaway: dict) -> discord.Embed:
    is_closed = giveaway["status"] != "active"

    if giveaway["status"] == "cancelled":
        color, title, timer_text = 0x2B2D31, "🚫 Розыгрыш отменён", "Отменено"
    elif is_closed:
        color, title, timer_text = 0x2B2D31, "🎉 Розыгрыш завершён", "Завершено"
    else:
        color, title, timer_text = 0xFEE75C, "🎉 Розыгрыш приза", f"<t:{giveaway['target_ts']}:R>"

    embed = discord.Embed(title=title, color=color)
    embed.add_field(name="Приз", value=f"**{giveaway['prize']}**", inline=True)
    embed.add_field(name="Победителей", value=str(giveaway["winners_count"]), inline=True)
    embed.add_field(name="Окончание", value=timer_text, inline=True)
    embed.add_field(
        name=f"Участников: {len(giveaway['entrants'])}",
        value="Нажми «Участвовать», чтобы принять участие." if not is_closed else "Розыгрыш закрыт.",
        inline=False,
    )
    if giveaway["winners"]:
        mentions = "\n".join(f"🏆 <@{uid}>" for uid in giveaway["winners"])
        embed.add_field(name="Победители", value=mentions, inline=False)
    embed.set_footer(text=f"ID розыгрыша: {giveaway['id']}")
    return embed


class GiveawayView(discord.ui.View):
    """Persistent view: кнопка работает и после перезапуска бота."""

    def __init__(self, cog: "GiveawayCog"):
        super().__init__(timeout=None)
        self.cog = cog

    def _get_giveaway(self, interaction: discord.Interaction) -> dict | None:
        if interaction.message is None:
            return None
        return giveaway_core.get_giveaway_by_message(interaction.message.id)

    @discord.ui.button(label="🎉 Участвовать", style=discord.ButtonStyle.green, custom_id="giveaway:join")
    async def join_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        giveaway = self._get_giveaway(interaction)
        if giveaway is None:
            return await interaction.response.send_message("Розыгрыш не найден.", ephemeral=True)

        result = giveaway_core.join_giveaway(giveaway["id"], interaction.user.id)
        if result == "already":
            result = giveaway_core.leave_giveaway(giveaway["id"], interaction.user.id)
            note = "Ты вышел из розыгрыша." if result == "left" else "Розыгрыш уже закрыт."
        elif result == "joined":
            note = "Ты участвуешь в розыгрыше!"
        elif result == "closed":
            note = "Розыгрыш уже закрыт."
        else:
            note = "Розыгрыш не найден."

        giveaway = giveaway_core.get_giveaway(giveaway["id"])
        if giveaway is None:
            return await interaction.response.send_message(note, ephemeral=True)

        await interaction.response.edit_message(embed=generate_embed(giveaway), view=self)
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
        for giveaway in giveaway_core.list_active():
            self.schedule_giveaway(giveaway)

    def schedule_giveaway(self, giveaway: dict):
        old = self._timers.pop(giveaway["id"], None)
        if old:
            old.cancel()
        self._timers[giveaway["id"]] = self.bot.loop.create_task(self._run_giveaway_timer(giveaway["id"]))

    async def _run_giveaway_timer(self, giveaway_id: str):
        try:
            giveaway = giveaway_core.get_giveaway(giveaway_id)
            if giveaway is None or giveaway["status"] != "active":
                return
            now_ts = int(datetime.now(timezone.utc).timestamp())
            if giveaway["target_ts"] > now_ts:
                await asyncio.sleep(giveaway["target_ts"] - now_ts)
            await self.finalize_giveaway(giveaway_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Giveaway timer failed: %s", giveaway_id)

    async def finalize_giveaway(self, giveaway_id: str, status: str = "finished") -> bool:
        giveaway = giveaway_core.close_giveaway(giveaway_id, status=status)
        if giveaway is None:
            return False

        task = self._timers.pop(giveaway_id, None)
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
                await message.edit(embed=generate_embed(giveaway), view=None)

            if status == "finished" and channel is not None:
                if giveaway["winners"]:
                    mentions = " ".join(f"<@{uid}>" for uid in giveaway["winners"])
                    await channel.send(content=f"🎉 Поздравляем {mentions} — вы выиграли **{giveaway['prize']}**!")
                else:
                    await channel.send(content=f"🎉 Розыгрыш **{giveaway['prize']}** завершён — никто не участвовал.")
        except discord.HTTPException:
            logger.warning("Не удалось объявить итоги розыгрыша %s", giveaway_id)
        return True

    async def publish_giveaway(self, channel, initiator_id: int, prize: str, duration_str: str, winners_count: int) -> dict:
        """Создаёт розыгрыш и публикует сообщение с кнопкой. Используется командой и дашбордом."""
        giveaway = giveaway_core.create_giveaway(initiator_id, prize, duration_str, winners_count)
        message = await channel.send(embed=generate_embed(giveaway), view=self.view)
        giveaway = giveaway_core.update_giveaway(
            giveaway["id"], channel_id=str(message.channel.id), message_id=str(message.id)
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
        try:
            giveaway_core.parse_duration(время)
        except ValueError as exc:
            return await interaction.response.send_message(f"❌ {exc}", ephemeral=True)

        await interaction.response.defer()
        giveaway = await self.publish_giveaway(interaction.channel, interaction.user.id, приз, время, победителей)
        await interaction.followup.send(f"Розыгрыш №{giveaway['id']} запущен.", ephemeral=True)

    async def reroll_and_announce(self, giveaway_id: str) -> list[str] | None:
        """Перевыбирает победителей и объявляет в канале розыгрыша. Используется командой и дашбордом."""
        winners = giveaway_core.reroll_giveaway(giveaway_id)
        if winners is None:
            return None

        giveaway = giveaway_core.get_giveaway(giveaway_id)
        channel = self.bot.get_channel(int(giveaway["channel_id"] or 0)) if giveaway else None
        if channel is not None:
            if winners:
                mentions = " ".join(f"<@{uid}>" for uid in winners)
                try:
                    await channel.send(content=f"🎉 Новый победитель после реролла: {mentions}")
                except discord.HTTPException:
                    pass
            if giveaway and giveaway["message_id"]:
                try:
                    message = await channel.fetch_message(int(giveaway["message_id"]))
                    await message.edit(embed=generate_embed(giveaway))
                except discord.HTTPException:
                    pass
        return winners

    @giveaway_group.command(name="reroll", description="Перевыбрать победителя(ей) завершённого розыгрыша")
    @app_commands.describe(giveaway_id="ID розыгрыша (указан в футере эмбеда)")
    async def giveaway_reroll(self, interaction: discord.Interaction, giveaway_id: str):
        await interaction.response.defer(ephemeral=True)
        winners = await self.reroll_and_announce(giveaway_id)
        if winners is None:
            return await interaction.followup.send("Розыгрыш не найден или ещё не завершён.", ephemeral=True)
        if not winners:
            return await interaction.followup.send("Нет доступных участников для реролла.", ephemeral=True)
        await interaction.followup.send("Готово — победитель объявлен в канале.", ephemeral=True)

    @giveaway_group.command(name="end", description="Досрочно завершить розыгрыш")
    @app_commands.describe(giveaway_id="ID розыгрыша (указан в футере эмбеда)")
    async def giveaway_end(self, interaction: discord.Interaction, giveaway_id: str):
        await interaction.response.defer(ephemeral=True)
        ok = await self.finalize_giveaway(giveaway_id)
        if not ok:
            return await interaction.followup.send("Розыгрыш не найден или уже завершён.", ephemeral=True)
        await interaction.followup.send("Розыгрыш завершён.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayCog(bot))
