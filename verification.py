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

import i18n
import slash_registry
import moderation_log
import verification_core

logger = logging.getLogger("verification")

COG_NAME = "VerificationCog"
LEGACY_VERIFY_CUSTOM_ID = "verification:verify"


def verify_custom_id(guild_id: int | None) -> str:
    if guild_id is None:
        return LEGACY_VERIFY_CUSTOM_ID
    return f"verification:verify:{guild_id}"


class VerificationView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild_id: int | None = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        lang = i18n.lang_for(guild_id)
        button = discord.ui.Button(
            label=i18n.t("verification.button", lang),
            style=discord.ButtonStyle.success,
            custom_id=verify_custom_id(guild_id),
        )
        button.callback = self.verify
        self.add_item(button)

    async def verify(self, interaction: discord.Interaction):
        cog = self.bot.get_cog(COG_NAME)
        if cog is None:
            lang = i18n.lang_for(interaction.guild_id)
            return await interaction.response.send_message(
                i18n.t("error.module_unavailable", lang), ephemeral=True
            )
        await cog.handle_verify(interaction)


class VerificationCog(commands.Cog, name=COG_NAME):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if getattr(self.bot, "_verification_views_loaded", False):
            return
        self.bot.add_view(VerificationView(self.bot, None))
        for guild in self.bot.guilds:
            settings = verification_core.get_settings(guild.id)
            if settings["enabled"] and verification_core.is_configured(settings):
                self.bot.add_view(VerificationView(self.bot, guild.id))
        self.bot._verification_views_loaded = True

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = verification_core.get_settings(member.guild.id)
        if not settings["enabled"] or not settings["unverified_role_id"]:
            return

        lang = i18n.lang_for(member.guild.id)
        role = member.guild.get_role(int(settings["unverified_role_id"]))
        if role is None:
            return
        try:
            await member.add_roles(role, reason=i18n.t("verification.role_reason_unverified", lang))
        except discord.Forbidden:
            logger.warning("Верификация: нет прав выдать роль Unverified участнику %s", member.id)

    async def handle_verify(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        settings = verification_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "verification"), ephemeral=True
            )
        if not verification_core.is_configured(settings):
            return await interaction.response.send_message(
                i18n.t("verification.not_configured", lang), ephemeral=True
            )

        guild = interaction.guild
        member = interaction.user
        verified_role = guild.get_role(int(settings["verified_role_id"]))
        if verified_role is None:
            return await interaction.response.send_message(
                i18n.t("verification.role_not_found", lang), ephemeral=True
            )
        if any(r.id == verified_role.id for r in member.roles):
            return await interaction.response.send_message(
                i18n.t("verification.already_verified", lang), ephemeral=True
            )

        try:
            await member.add_roles(
                verified_role, reason=i18n.t("verification.role_reason_verified", lang)
            )
            if settings["unverified_role_id"]:
                unverified_role = guild.get_role(int(settings["unverified_role_id"]))
                if unverified_role is not None and any(r.id == unverified_role.id for r in member.roles):
                    await member.remove_roles(
                        unverified_role, reason=i18n.t("verification.role_reason_remove_unverified", lang)
                    )
        except discord.Forbidden:
            return await interaction.response.send_message(
                i18n.t("verification.bot_forbidden", lang), ephemeral=True
            )

        moderation_log.append_event(
            interaction.guild_id,
            "verification_pass",
            member.id,
            member.name,
            i18n.t("verification.log_reason", lang),
        )
        await interaction.response.send_message(i18n.t("verification.success", lang), ephemeral=True)

    @app_commands.command(name="verify_setup", description="Опубликовать панель верификации в текущем канале")
    @app_commands.default_permissions(manage_guild=True)
    async def verify_setup(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        settings = verification_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled_dashboard_hint(lang, "verification"), ephemeral=True
            )
        if not verification_core.is_configured(settings):
            return await interaction.response.send_message(
                i18n.t("verification.setup_configure_first", lang), ephemeral=True
            )

        await interaction.response.send_message(i18n.t("verification.panel_installed", lang), ephemeral=True)
        await interaction.channel.send(
            content=settings["welcome_text"],
            view=VerificationView(self.bot, interaction.guild.id),
        )


async def setup(bot: commands.Bot):
    cog = VerificationCog(bot)
    slash_registry.register_verification(cog)
    await bot.add_cog(cog)
