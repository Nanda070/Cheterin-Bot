"""Ког «Верификация»: панель «Я не бот» для новичков.

ВЫКЛЮЧЕН ПО УМОЛЧАНИЮ и не имеет никакого эффекта, пока не включён отдельным
тумблером в дашборде (раздел «Верификация») — on_member_join и обработчик
кнопки первой же строкой проверяют verification_core.get_settings()["enabled"]
и выходят, если модуль не активен. Не связан ни с одним другим модулем.

Схема: при входе (если задана unverified_role_id) участнику выдаётся роль
«Unverified» — доступ к каналам ограничивается правами Discord, настроенными
самим администратором для этой роли (бот только назначает/снимает её). После
клика по кнопке роль «Unverified» снимается, выдаётся verified_role_id.

Панель — persistent view (custom_id), переживает перезапуск бота, как
CTD-панель в memobb.py.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

import moderation_log
import verification_core

logger = logging.getLogger("verification")

COG_NAME = "VerificationCog"


class VerificationView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Я не бот", style=discord.ButtonStyle.success, custom_id="verification:verify")
    async def verify(self, interaction: discord.Interaction, _button: discord.ui.Button):
        cog = self.bot.get_cog(COG_NAME)
        if cog is None:
            return await interaction.response.send_message("Модуль временно недоступен.", ephemeral=True)
        await cog.handle_verify(interaction)


class VerificationCog(commands.Cog, name=COG_NAME):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = verification_core.get_settings(member.guild.id)
        if not settings["enabled"] or not settings["unverified_role_id"]:
            return  # модуль выключен (или роль не настроена) — никакого эффекта

        role = member.guild.get_role(int(settings["unverified_role_id"]))
        if role is None:
            return
        try:
            await member.add_roles(role, reason="Верификация: роль до подтверждения")
        except discord.Forbidden:
            logger.warning("Верификация: нет прав выдать роль Unverified участнику %s", member.id)

    async def handle_verify(self, interaction: discord.Interaction):
        settings = verification_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message("Модуль «Верификация» отключён.", ephemeral=True)
        if not verification_core.is_configured(settings):
            return await interaction.response.send_message(
                "Верификация не настроена администратором — сообщите об этом в поддержку.", ephemeral=True
            )

        guild = interaction.guild
        member = interaction.user
        verified_role = guild.get_role(int(settings["verified_role_id"]))
        if verified_role is None:
            return await interaction.response.send_message(
                "Роль верификации не найдена на сервере — сообщите админам.", ephemeral=True
            )
        if any(r.id == verified_role.id for r in member.roles):
            return await interaction.response.send_message("Вы уже верифицированы.", ephemeral=True)

        try:
            await member.add_roles(verified_role, reason="Верификация: подтверждение по кнопке")
            if settings["unverified_role_id"]:
                unverified_role = guild.get_role(int(settings["unverified_role_id"]))
                if unverified_role is not None and any(r.id == unverified_role.id for r in member.roles):
                    await member.remove_roles(unverified_role, reason="Верификация пройдена")
        except discord.Forbidden:
            return await interaction.response.send_message(
                "Недостаточно прав у бота, чтобы выдать роль — сообщите админам.", ephemeral=True
            )

        moderation_log.append_event(
            interaction.guild_id, "verification_pass", member.id, member.name, "Верификация по кнопке пройдена",
        )
        await interaction.response.send_message("✅ Добро пожаловать! Доступ открыт.", ephemeral=True)

    @app_commands.command(name="verify_setup", description="Опубликовать панель верификации в текущем канале")
    @app_commands.default_permissions(manage_guild=True)
    async def verify_setup(self, interaction: discord.Interaction):
        settings = verification_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message("Модуль «Верификация» отключён — включите его в дашборде.", ephemeral=True)
        if not verification_core.is_configured(settings):
            return await interaction.response.send_message(
                "Сначала укажите роль верификации в дашборде (раздел «Верификация»).", ephemeral=True
            )

        await interaction.response.send_message("Панель установлена.", ephemeral=True)
        await interaction.channel.send(content=settings["welcome_text"], view=VerificationView(self.bot))


async def setup(bot: commands.Bot):
    cog = VerificationCog(bot)
    await bot.add_cog(cog)
    bot.add_view(VerificationView(bot))  # persistent «Я не бот» переживает перезапуск
