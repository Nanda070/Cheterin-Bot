"""Ког системы уровней: XP за текст, обработка уровней и наград, /ранг.

XP за войс начисляет voice_tracker и передаёт сюда через apply_voice_session().
"""

import asyncio
import io
import logging
import time

import discord
from discord import app_commands
from discord.ext import commands

import economy_core
import economy_db
import stats_db
import xp_card
import xp_core

logger = logging.getLogger("xp")


def member_has_ignored_role(member: discord.Member, ignored_role_ids: list[str]) -> bool:
    ignored = set(ignored_role_ids)
    return any(str(role.id) in ignored for role in member.roles)


def channel_allowed(channel_id: int, scope: dict) -> bool:
    cid = str(channel_id)
    if cid in scope["ignored_channels"]:
        return False
    targets = scope["target_channels"]
    return not targets or cid in targets


# ────────────────── Лидерборд: вспомогательное ──────────────────

PER_PAGE = 10  # строк на страницу таблицы лидеров


def _fmt_voice(seconds: int) -> str:
    """Формат времени голоса Ч:ММ:СС (как в JuniperBot)."""
    s = max(0, int(seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}"


class LeaderboardView(discord.ui.View):
    """Интерактивный лидерборд: сортировка по Опыту / Голосу + пагинация."""

    def __init__(self, rows_xp: list, rows_voice: list, guild: discord.Guild | None, total: int):
        super().__init__(timeout=120)
        self.rows_xp = rows_xp
        self.rows_voice = rows_voice
        self.guild = guild
        self.total = total
        self.page = 0
        self.mode = "xp"  # "xp" | "voice"
        self._sync_buttons()

    # ── данные ──

    def _rows(self) -> list:
        return self.rows_xp if self.mode == "xp" else self.rows_voice

    def _max_pages(self) -> int:
        return max(1, (len(self._rows()) + PER_PAGE - 1) // PER_PAGE)

    def build_embed(self) -> discord.Embed:
        rows = self._rows()
        start = self.page * PER_PAGE
        page_rows = rows[start:start + PER_PAGE]

        lines: list[str] = []
        for i, row in enumerate(page_rows, start=start + 1):
            member = self.guild.get_member(row["user_id"]) if self.guild else None
            display = member.display_name if member else str(row["user_id"])
            mention = member.mention if member else str(row["user_id"])
            level, _, _ = xp_core.level_progress(row["xp"])
            voice_str = _fmt_voice(row["voice_seconds"])
            prefix = f"\u2B50 #{i}." if i <= 3 else f"#{i}."
            lines.append(
                f"**{prefix} {mention} ({display})**\n"
                f"Уровень: {level} | Опыт: {row['xp']} | \U0001f5e3\ufe0f {voice_str}"
            )

        mode_label = "опыту \U0001f3c6" if self.mode == "xp" else "голосу \U0001f5e3\ufe0f"
        embed = discord.Embed(
            title="Топ рейтинга участников",
            description="\n\n".join(lines) if lines else "Нет данных.",
            color=discord.Color.gold(),
        )
        embed.set_footer(
            text=(
                f"Отсортировано по {mode_label} \u2022 "
                f"Страница {self.page + 1} из {self._max_pages()} \u2014 "
                f"Всего участников: {self.total}"
            )
        )
        if self.guild and self.guild.icon:
            embed.set_thumbnail(url=self.guild.icon.url)
        return embed

    # ── синхронизация состояния кнопок ──

    def _sync_buttons(self) -> None:
        at_start = self.page == 0
        at_end = self.page >= self._max_pages() - 1
        self.btn_first.disabled = at_start
        self.btn_prev.disabled = at_start
        self.btn_next.disabled = at_end
        self.btn_last.disabled = at_end
        self.btn_xp.style = (
            discord.ButtonStyle.primary if self.mode == "xp" else discord.ButtonStyle.secondary
        )
        self.btn_voice.style = (
            discord.ButtonStyle.primary if self.mode == "voice" else discord.ButtonStyle.secondary
        )

    # ── кнопки сортировки (row=0) ──

    @discord.ui.button(label="\U0001f3c6 Опыт", style=discord.ButtonStyle.primary, row=0)
    async def btn_xp(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "xp"
        self.page = 0
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\U0001f5e3\ufe0f Голос", style=discord.ButtonStyle.secondary, row=0)
    async def btn_voice(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "voice"
        self.page = 0
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # ── кнопки пагинации (row=1) ──

    @discord.ui.button(label="\u00ab", style=discord.ButtonStyle.grey, row=1)
    async def btn_first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 0
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\u2039", style=discord.ButtonStyle.grey, row=1)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\u203a", style=discord.ButtonStyle.grey, row=1)
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(self._max_pages() - 1, self.page + 1)
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\u00bb", style=discord.ButtonStyle.grey, row=1)
    async def btn_last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self._max_pages() - 1
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\u2715", style=discord.ButtonStyle.red, row=1)
    async def btn_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)
        self.stop()


# ────────────────── Основной Cog ──────────────────

class XPCog(commands.Cog):
    xp_group = app_commands.Group(
        name="xp",
        description="Изменить количество опыта участника",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────── Текстовый XP ──────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        settings = xp_core.get_settings(message.guild.id)
        if not settings["enabled"] or not settings["text"]["enabled"]:
            return
        if not channel_allowed(message.channel.id, settings["text"]):
            return
        if member_has_ignored_role(message.author, settings["text"]["ignored_roles"]):
            return

        now_ts = int(time.time())
        row = stats_db.xp_get_member(message.guild.id, message.author.id)
        if row is not None and now_ts - row["last_text_xp_ts"] < xp_core.TEXT_XP_COOLDOWN:
            return

        amount = xp_core.roll_text_xp(settings["text"]["multiplier"])
        if amount <= 0:
            return
        stats_db.xp_add_text(message.guild.id, message.author.id, amount, now_ts)
        economy_core.award_for_xp(message.guild.id, message.author.id, amount, "text")
        await self.process_member(message.author, settings, fallback_channel=message.channel)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        settings = xp_core.get_settings(member.guild.id)
        if settings["enabled"] and settings["reset_on_leave"]:
            stats_db.xp_reset_member(member.guild.id, member.id)

    # ────────────────── Голосовой XP (из voice_tracker) ──────────────────

    async def apply_voice_session(self, member: discord.Member, xp_amount: int, active_seconds: int):
        if xp_amount <= 0 and active_seconds <= 0:
            return
        stats_db.xp_add_voice(member.guild.id, member.id, xp_amount, active_seconds)
        economy_core.award_for_xp(member.guild.id, member.id, xp_amount, "voice")
        settings = xp_core.get_settings(member.guild.id)
        if settings["enabled"]:
            await self.process_member(member, settings, fallback_channel=None)

    # ────────────────── Уровни и награды ──────────────────

    async def process_member(self, member: discord.Member, settings: dict, fallback_channel):
        """Пересчитывает уровень, синхронизирует роли-награды, шлёт уведомление."""
        row = stats_db.xp_get_member(member.guild.id, member.id)
        if row is None:
            return

        old_level = row["level"]
        new_level = xp_core.level_from_xp(row["xp"])
        if new_level != old_level:
            stats_db.xp_set_level(member.guild.id, member.id, new_level)

        roles_added, roles_removed = await self.sync_reward_roles(member, settings, new_level, row["voice_seconds"])

        if new_level > old_level:
            await self.announce_level_up(member, settings, new_level, roles_added, roles_removed, fallback_channel)

    async def sync_reward_roles(self, member: discord.Member, settings: dict, level: int, voice_seconds: int) -> tuple[list[str], list[str]]:
        """Приводит роли-награды участника в соответствие с его прогрессом."""
        deserved = xp_core.deserved_level_roles(settings, level) | xp_core.deserved_voice_roles(settings, voice_seconds)
        all_rewards = xp_core.all_reward_role_ids(settings)

        current_ids = {str(r.id) for r in member.roles}
        to_add = [rid for rid in deserved if rid not in current_ids]
        to_remove = [rid for rid in all_rewards if rid in current_ids and rid not in deserved]

        added_names, removed_names = [], []
        for rid in to_add:
            role = member.guild.get_role(int(rid))
            if role is None:
                continue
            try:
                await member.add_roles(role, reason="Награда за уровень/войс-активность")
                added_names.append(role.name)
            except discord.HTTPException as exc:
                logger.warning("Не удалось выдать награду %s участнику %s: %s", rid, member.id, exc)

        for rid in to_remove:
            role = member.guild.get_role(int(rid))
            if role is None:
                continue
            try:
                await member.remove_roles(role, reason="Награда снята: недостаточный уровень/время")
                removed_names.append(role.name)
            except discord.HTTPException as exc:
                logger.warning("Не удалось снять награду %s у участника %s: %s", rid, member.id, exc)

        return added_names, removed_names

    async def announce_level_up(
        self,
        member: discord.Member,
        settings: dict,
        level: int,
        roles_added: list[str],
        roles_removed: list[str],
        fallback_channel,
    ):
        announce = settings["announce"]
        if not announce["enabled"]:
            return

        channel = None
        if announce["channel_id"]:
            channel = self.bot.get_channel(int(announce["channel_id"]))
        if channel is None:
            channel = fallback_channel
        if channel is None:
            return

        text = xp_core.render_announce(announce["template"], member.mention, level, roles_added, roles_removed)
        if not text:
            return

        guild = member.guild
        guild_name = f'" {guild.name} "' if guild else ""

        embed = discord.Embed(
            description=(
                f"Поздравляю {member.mention}\U0001f929!\n"
                f"Вы достигли **{level}** уровня. "
                f"Спасибо за вашу активность на сервере {guild_name}"
            ),
            color=discord.Color.gold(),
        )
        if guild and guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        try:
            delete_after = announce["delete_after"] if announce["delete_after"] > 0 else None
            await channel.send(embed=embed, delete_after=delete_after)
        except discord.HTTPException as exc:
            logger.warning("Не удалось отправить уведомление о уровне: %s", exc)

    # ────────────────── Сброс (используется дашбордом) ──────────────────

    async def reset_member(self, member: discord.Member):
        stats_db.xp_reset_member(member.guild.id, member.id)
        settings = xp_core.get_settings(member.guild.id)
        await self.sync_reward_roles(member, settings, 0, 0)

    async def set_member_xp(self, member: discord.Member, xp: int):
        level = xp_core.level_from_xp(xp)
        stats_db.xp_set_xp(member.guild.id, member.id, xp, level)
        settings = xp_core.get_settings(member.guild.id)
        await self.sync_reward_roles(
            member, settings, level,
            (stats_db.xp_get_member(member.guild.id, member.id) or {"voice_seconds": 0})["voice_seconds"],
        )

    # ────────────────── Команда /ранг ──────────────────

    @app_commands.command(name="ранг", description="Показать карточку ранга участника")
    @app_commands.describe(участник="Чей ранг показать (по умолчанию — свой)")
    async def rank_command(self, interaction: discord.Interaction, участник: discord.Member | None = None):
        settings = xp_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message("Система уровней отключена.", ephemeral=True)

        target = участник or interaction.user
        if target.bot:
            return await interaction.response.send_message("У ботов нет ранга.", ephemeral=True)

        await interaction.response.defer()

        row = stats_db.xp_get_member(interaction.guild.id, target.id)
        xp = row["xp"] if row else 0
        voice_seconds = row["voice_seconds"] if row else 0
        level, into, step = xp_core.level_progress(xp)
        rank = stats_db.xp_rank_of(interaction.guild.id, target.id)
        total = stats_db.xp_member_count(interaction.guild.id)

        avatar_bytes = None
        try:
            avatar_bytes = await target.display_avatar.replace(size=256).read()
        except discord.HTTPException:
            pass

        frame = economy_db.get_equipped(target.id, "frame_color")
        title = economy_db.get_equipped(target.id, "title")

        png = await asyncio.to_thread(
            xp_card.render_rank_card,
            target.guild.id,
            avatar_bytes,
            target.display_name,
            level,
            into,
            step,
            rank,
            total,
            xp_core.format_voice_time(voice_seconds),
            frame_color=frame["value"] if frame else None,
            title_text=title["value"] if title else None,
        )
        file = discord.File(fp=io.BytesIO(png), filename="rank.png")
        await interaction.followup.send(file=file)

    # ────────────────── Команда /xp (add / set / clear) ──────────────────

    @xp_group.command(name="add", description="Добавить (или отнять) опыт участнику")
    @app_commands.describe(участник="Кому изменить опыт", количество="Сколько XP добавить (можно отрицательное число)")
    async def xp_add(self, interaction: discord.Interaction, участник: discord.Member, количество: int):
        settings = xp_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message("Система уровней отключена.", ephemeral=True)
        if участник.bot:
            return await interaction.response.send_message("У ботов нет опыта.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)

        row = stats_db.xp_get_member(interaction.guild.id, участник.id)
        current = row["xp"] if row else 0
        new_xp = min(xp_core.XP_ADMIN_MAX, max(xp_core.XP_ADMIN_MIN, current + количество))
        await self.set_member_xp(участник, new_xp)

        await interaction.followup.send(f"✅ Опыт {участник.mention}: {current} → **{new_xp}**.", ephemeral=True)

    @xp_group.command(name="set", description="Установить точное количество опыта участнику")
    @app_commands.describe(участник="Кому установить опыт", количество="Новое значение XP")
    async def xp_set(
        self, interaction: discord.Interaction, участник: discord.Member,
        количество: app_commands.Range[int, xp_core.XP_ADMIN_MIN, xp_core.XP_ADMIN_MAX],
    ):
        settings = xp_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message("Система уровней отключена.", ephemeral=True)
        if участник.bot:
            return await interaction.response.send_message("У ботов нет опыта.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)

        await self.set_member_xp(участник, количество)
        await interaction.followup.send(f"✅ Опыт {участник.mention} установлен: **{количество}**.", ephemeral=True)

    @xp_group.command(name="clear", description="Обнулить опыт участника")
    @app_commands.describe(участник="Кому обнулить опыт")
    async def xp_clear(self, interaction: discord.Interaction, участник: discord.Member):
        settings = xp_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message("Система уровней отключена.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)

        await self.reset_member(участник)
        await interaction.followup.send(f"✅ Опыт {участник.mention} обнулён.", ephemeral=True)

    # ────────────────── Команда /leaders ──────────────────

    @app_commands.command(name="leaders", description="Показать таблицу лидеров")
    async def leaders_command(self, interaction: discord.Interaction):
        settings = xp_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message("Система уровней отключена.", ephemeral=True)
        await interaction.response.defer()

        rows_xp = stats_db.xp_leaderboard(interaction.guild.id, limit=1000)
        rows_voice = stats_db.voice_leaderboard(interaction.guild.id, limit=1000)
        if not rows_xp and not rows_voice:
            return await interaction.followup.send("Пока никто не заработал опыт.")

        total = stats_db.xp_member_count(interaction.guild.id)
        view = LeaderboardView(rows_xp, rows_voice, interaction.guild, total)
        await interaction.followup.send(embed=view.build_embed(), view=view)


async def setup(bot: commands.Bot):
    stats_db.init()
    await bot.add_cog(XPCog(bot))
