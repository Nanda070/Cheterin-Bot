"""Live-ростер семьи: список участников по настроенным ролям.

Портировано из FamQ roster.py: команда /список публикует live-сообщение,
которое дебаунс-обновляется при изменении целевых ролей участников.
"""

import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

import family_core
import family_db

logger = logging.getLogger("family.roster")


def generate_roster_text(guild: discord.Guild) -> str:
    settings = family_core.get_settings(guild.id)
    target_roles = settings["roster"]["target_roles"]
    if not target_roles:
        return "Роли ростера не настроены."

    lines = []
    for entry in target_roles:
        role = guild.get_role(int(entry["role_id"])) if entry["role_id"] else None
        if not role:
            continue
        lines.append(f"**{entry['label'] or role.name}:**")
        if role.members:
            for member in role.members:
                lines.append(f"- {member.mention}")
        else:
            lines.append("- Отсутствуют")
        lines.append("")
    return "\n".join(lines).strip() or "Данные о ролях не найдены."


class RosterCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._update_lock = asyncio.Lock()
        self._update_pending = False
        self._recovered = False

    @commands.Cog.listener()
    async def on_ready(self):
        if self._recovered:
            return
        self._recovered = True
        for guild in self.bot.guilds:
            await self.execute_roster_update(guild)

    async def execute_roster_update(self, guild: discord.Guild):
        async with self._update_lock:
            data = family_db.get_roster_data(guild.id)
            if not data:
                return

            channel = guild.get_channel(data["channel_id"])
            if not isinstance(channel, discord.TextChannel):
                return

            try:
                msg = await channel.fetch_message(data["message_id"])
                new_content = generate_roster_text(guild)
                if msg.content != new_content:
                    await msg.edit(content=new_content, allowed_mentions=discord.AllowedMentions.none())
            except discord.NotFound:
                family_db.clear_roster_data(guild.id)
            except discord.HTTPException as exc:
                logger.warning("Не удалось обновить ростер: %s", exc)

    async def schedule_roster_update(self, guild: discord.Guild):
        """Debounce: аккумулирует изменения и обновляет сообщение через 10 секунд."""
        if self._update_pending:
            return
        self._update_pending = True
        await asyncio.sleep(10)
        try:
            await self.execute_roster_update(guild)
        finally:
            self._update_pending = False

    @app_commands.command(name="список", description="Создать live-сообщение со списком участников семьи")
    async def roster_list(self, interaction: discord.Interaction):
        settings = family_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message("Модуль «Семья» отключён.", ephemeral=True)

        list_channel_id = settings["roster"]["list_channel_id"]
        if list_channel_id and str(interaction.channel_id) != list_channel_id:
            return await interaction.response.send_message("Операция запрещена в текущем канале.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        data = family_db.get_roster_data(guild.id)
        if data:
            old_channel = guild.get_channel(data["channel_id"])
            if isinstance(old_channel, discord.TextChannel):
                try:
                    old_msg = await old_channel.fetch_message(data["message_id"])
                    await old_msg.delete()
                except discord.HTTPException:
                    pass

        content = generate_roster_text(guild)
        msg = await interaction.channel.send(content=content, allowed_mentions=discord.AllowedMentions.none())
        family_db.save_roster_data(guild.id, msg.channel.id, msg.id)
        await interaction.followup.send("Live-список инициализирован.")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        settings = family_core.get_settings(after.guild.id)
        if not settings["enabled"]:
            return
        target_ids = {int(r["role_id"]) for r in settings["roster"]["target_roles"] if r["role_id"]}
        if not target_ids:
            return
        before_ids = {r.id for r in before.roles} & target_ids
        after_ids = {r.id for r in after.roles} & target_ids
        if before_ids != after_ids:
            self.bot.loop.create_task(self.schedule_roster_update(after.guild))

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        settings = family_core.get_settings(member.guild.id)
        if not settings["enabled"]:
            return
        target_ids = {int(r["role_id"]) for r in settings["roster"]["target_roles"] if r["role_id"]}
        if target_ids and {r.id for r in member.roles} & target_ids:
            self.bot.loop.create_task(self.schedule_roster_update(member.guild))


async def setup(bot: commands.Bot):
    family_db.init()
    await bot.add_cog(RosterCog(bot))
