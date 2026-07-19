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

        settings = xp_core.get_settings()
        if not settings["enabled"] or not settings["text"]["enabled"]:
            return
        if not channel_allowed(message.channel.id, settings["text"]):
            return
        if member_has_ignored_role(message.author, settings["text"]["ignored_roles"]):
            return

        now_ts = int(time.time())
        row = stats_db.xp_get_member(message.author.id)
        if row is not None and now_ts - row["last_text_xp_ts"] < xp_core.TEXT_XP_COOLDOWN:
            return

        amount = xp_core.roll_text_xp(settings["text"]["multiplier"])
        if amount <= 0:
            return
        stats_db.xp_add_text(message.author.id, amount, now_ts)
        economy_core.award_for_xp(message.author.id, amount, "text")
        await self.process_member(message.author, settings, fallback_channel=message.channel)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        settings = xp_core.get_settings()
        if settings["enabled"] and settings["reset_on_leave"]:
            stats_db.xp_reset_member(member.id)

    # ────────────────── Голосовой XP (из voice_tracker) ──────────────────

    async def apply_voice_session(self, member: discord.Member, xp_amount: int, active_seconds: int):
        if xp_amount <= 0 and active_seconds <= 0:
            return
        stats_db.xp_add_voice(member.id, xp_amount, active_seconds)
        economy_core.award_for_xp(member.id, xp_amount, "voice")
        settings = xp_core.get_settings()
        if settings["enabled"]:
            await self.process_member(member, settings, fallback_channel=None)

    # ────────────────── Уровни и награды ──────────────────

    async def process_member(self, member: discord.Member, settings: dict, fallback_channel):
        """Пересчитывает уровень, синхронизирует роли-награды, шлёт уведомление."""
        row = stats_db.xp_get_member(member.id)
        if row is None:
            return

        old_level = row["level"]
        new_level = xp_core.level_from_xp(row["xp"])
        if new_level != old_level:
            stats_db.xp_set_level(member.id, new_level)

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

    async def announce_level_up(self, member: discord.Member, settings: dict, level: int, roles_added: list[str], roles_removed: list[str], fallback_channel):
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
        try:
            delete_after = announce["delete_after"] if announce["delete_after"] > 0 else None
            await channel.send(text, delete_after=delete_after)
        except discord.HTTPException as exc:
            logger.warning("Не удалось отправить уведомление о уровне: %s", exc)

    # ────────────────── Сброс (используется дашбордом) ──────────────────

    async def reset_member(self, member: discord.Member):
        stats_db.xp_reset_member(member.id)
        settings = xp_core.get_settings()
        await self.sync_reward_roles(member, settings, 0, 0)

    async def set_member_xp(self, member: discord.Member, xp: int):
        level = xp_core.level_from_xp(xp)
        stats_db.xp_set_xp(member.id, xp, level)
        settings = xp_core.get_settings()
        await self.sync_reward_roles(member, settings, level, (stats_db.xp_get_member(member.id) or {"voice_seconds": 0})["voice_seconds"])

    # ────────────────── Команда /ранг ──────────────────

    @app_commands.command(name="ранг", description="Показать карточку ранга участника")
    @app_commands.describe(участник="Чей ранг показать (по умолчанию — свой)")
    async def rank_command(self, interaction: discord.Interaction, участник: discord.Member | None = None):
        settings = xp_core.get_settings()
        if not settings["enabled"]:
            return await interaction.response.send_message("Система уровней отключена.", ephemeral=True)

        target = участник or interaction.user
        if target.bot:
            return await interaction.response.send_message("У ботов нет ранга.", ephemeral=True)

        await interaction.response.defer()

        row = stats_db.xp_get_member(target.id)
        xp = row["xp"] if row else 0
        voice_seconds = row["voice_seconds"] if row else 0
        level, into, step = xp_core.level_progress(xp)
        rank = stats_db.xp_rank_of(target.id)
        total = stats_db.xp_member_count()

        avatar_bytes = None
        try:
            avatar_bytes = await target.display_avatar.replace(size=256).read()
        except discord.HTTPException:
            pass

        frame = economy_db.get_equipped(target.id, "frame_color")
        title = economy_db.get_equipped(target.id, "title")

        png = await asyncio.to_thread(
            xp_card.render_rank_card,
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
        settings = xp_core.get_settings()
        if not settings["enabled"]:
            return await interaction.response.send_message("Система уровней отключена.", ephemeral=True)
        if участник.bot:
            return await interaction.response.send_message("У ботов нет опыта.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)

        row = stats_db.xp_get_member(участник.id)
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
        settings = xp_core.get_settings()
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
        settings = xp_core.get_settings()
        if not settings["enabled"]:
            return await interaction.response.send_message("Система уровней отключена.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)

        await self.reset_member(участник)
        await interaction.followup.send(f"✅ Опыт {участник.mention} обнулён.", ephemeral=True)

    # ────────────────── Команда /leaders ──────────────────

    @app_commands.command(name="leaders", description="Показать таблицу лидеров по опыту")
    @app_commands.describe(число="Сколько мест показать (1-25, по умолчанию 10)")
    async def leaders_command(
        self, interaction: discord.Interaction, число: app_commands.Range[int, 1, 25] = 10,
    ):
        settings = xp_core.get_settings()
        if not settings["enabled"]:
            return await interaction.response.send_message("Система уровней отключена.", ephemeral=True)
        await interaction.response.defer()

        rows = stats_db.xp_leaderboard(limit=число)
        if not rows:
            return await interaction.followup.send("Пока никто не заработал опыт.")

        guild = interaction.guild
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for i, row in enumerate(rows, start=1):
            member = guild.get_member(row["user_id"]) if guild else None
            name = member.display_name if member else str(row["user_id"])
            level, _, _ = xp_core.level_progress(row["xp"])
            prefix = medals.get(i, f"{i}.")
            lines.append(f"{prefix} **{name}** — ур. {level}, {row['xp']} XP")

        embed = discord.Embed(title="🏆 Таблица лидеров", description="\n".join(lines), color=discord.Color.gold())
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    stats_db.init()
    await bot.add_cog(XPCog(bot))
