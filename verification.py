"""Ког «Верификация»: панель «Я не бот» / согласия с правилами для новичков.

ВЫКЛЮЧЕН ПО УМОЛЧАНИЮ и не имеет никакого эффекта, пока не включён отдельным
тумблером в дашборде (раздел «Верификация») — on_member_join и обработчик
кнопки первой же строкой проверяют verification_core.get_settings()["enabled"]
и выходят, если модуль не активен. Не связан ни с одним другим модулем.

Схема: при входе (если задана unverified_role_id) участнику выдаётся роль
«Unverified» — доступ к каналам ограничивается правами Discord, настроенными
самим администратором для этой роли (бот только назначает/снимает её). После
клика по кнопке роль «Unverified» снимается, выдаётся verified_role_id.

Опционально: режим «согласие с правилами» (подпись кнопки) и повторное
подтверждение каждые N дней — sweeper снимает verified-роль (и снова выдаёт
unverified, если настроена), участник должен нажать кнопку снова.

Панель — persistent view (custom_id), переживает перезапуск бота, как
CTD-панель в memobb.py.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks

import embed_style
import i18n
import moderation_embed_core
import moderation_log
import slash_registry
import verification_core
import verification_db

logger = logging.getLogger("verification")

COG_NAME = "VerificationCog"
LEGACY_VERIFY_CUSTOM_ID = "verification:verify"


def verify_custom_id(guild_id: int | None) -> str:
    if guild_id is None:
        return LEGACY_VERIFY_CUSTOM_ID
    return f"verification:verify:{guild_id}"


def _button_label(guild_id: int | None) -> str:
    lang = i18n.lang_for(guild_id)
    if guild_id is not None:
        settings = verification_core.get_settings(guild_id)
        if settings["rules_consent_enabled"]:
            return i18n.t("verification.rules_button", lang)
    return i18n.t("verification.button", lang)


class VerificationView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild_id: int | None = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        button = discord.ui.Button(
            label=_button_label(guild_id),
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


async def publish_verification_panel(bot: commands.Bot, channel: discord.TextChannel) -> discord.Message:
    """Publish the verification panel to `channel`. Shared by /verify_setup and the dashboard."""
    settings = verification_core.get_settings(channel.guild.id)
    return await channel.send(
        content=settings["welcome_text"],
        view=VerificationView(bot, channel.guild.id),
    )


class VerificationCog(commands.Cog, name=COG_NAME):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reverify_sweeper.start()

    def cog_unload(self):
        self.reverify_sweeper.cancel()

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

    def _already_verified(self, member: discord.Member, verified_role: discord.Role, settings: dict) -> bool:
        if not any(r.id == verified_role.id for r in member.roles):
            return False
        if not settings["reverify_enabled"]:
            return True
        consent = verification_db.get_consent(member.guild.id, member.id)
        return verification_core.has_valid_consent(consent, settings)

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
        if self._already_verified(member, verified_role, settings):
            return await interaction.response.send_message(
                i18n.t("verification.already_verified", lang), ephemeral=True
            )

        try:
            if not any(r.id == verified_role.id for r in member.roles):
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

        verification_db.record_consent(interaction.guild_id, member.id)
        reason = i18n.t("verification.log_reason", lang)
        moderation_log.append_event(
            interaction.guild_id,
            "verification_pass",
            member.id,
            member.name,
            reason,
        )
        embed = moderation_embed_core.build_user_action_embed(
            lang,
            title=i18n.t("verification.embed.pass_title", lang),
            actor=self.bot.user,
            target_name=member.name,
            target_id=member.id,
            target_mention=member.mention,
            reason=reason,
            color=embed_style.SUCCESS,
            footer_key="moderation.embed.footer",
        )
        await self.bot.send_log(interaction.guild_id, embed)
        success_key = (
            "verification.rules_success"
            if settings["rules_consent_enabled"]
            else "verification.success"
        )
        await interaction.response.send_message(i18n.t(success_key, lang), ephemeral=True)

    async def _expire_member(self, guild: discord.Guild, member: discord.Member, settings: dict) -> None:
        lang = i18n.lang_for(guild.id)
        verified_role = guild.get_role(int(settings["verified_role_id"])) if settings["verified_role_id"] else None
        try:
            if verified_role is not None and any(r.id == verified_role.id for r in member.roles):
                await member.remove_roles(
                    verified_role, reason=i18n.t("verification.role_reason_reverify", lang)
                )
            if settings["unverified_role_id"]:
                unverified_role = guild.get_role(int(settings["unverified_role_id"]))
                if unverified_role is not None and not any(r.id == unverified_role.id for r in member.roles):
                    await member.add_roles(
                        unverified_role, reason=i18n.t("verification.role_reason_reverify", lang)
                    )
        except discord.Forbidden:
            logger.warning(
                "Верификация: нет прав снять/выдать роли при повторной проверке guild=%s user=%s",
                guild.id,
                member.id,
            )
            return
        except discord.HTTPException:
            logger.warning(
                "Верификация: HTTP ошибка при повторной проверке guild=%s user=%s",
                guild.id,
                member.id,
            )
            return

        verification_db.clear_consent(guild.id, member.id)
        reason = i18n.t("verification.log_reverify", lang)
        moderation_log.append_event(
            guild.id,
            "verification_expired",
            member.id,
            member.name,
            reason,
        )
        embed = moderation_embed_core.build_user_action_embed(
            lang,
            title=i18n.t("verification.embed.expire_title", lang),
            actor=self.bot.user,
            target_name=member.name,
            target_id=member.id,
            target_mention=member.mention,
            reason=reason,
            color=embed_style.WARN,
            footer_key="moderation.embed.footer",
        )
        await self.bot.send_log(guild.id, embed)

    @tasks.loop(hours=1)
    async def reverify_sweeper(self):
        # Всё тело под try/except: необработанное исключение навсегда остановило бы tasks.loop.
        try:
            for guild in self.bot.guilds:
                try:
                    settings = verification_core.get_settings(guild.id)
                    if (
                        not settings["enabled"]
                        or not settings["reverify_enabled"]
                        or not verification_core.is_configured(settings)
                    ):
                        continue
                    for row in verification_db.list_consents(guild.id):
                        if not verification_core.is_consent_expired(row["verified_at"], settings):
                            continue
                        member = guild.get_member(row["user_id"])
                        if member is None:
                            verification_db.clear_consent(guild.id, row["user_id"])
                            continue
                        await self._expire_member(guild, member, settings)
                except Exception as exc:
                    logger.exception("verification reverify sweeper guild=%s", guild.id)
                    cog = self.bot.get_cog("OwnerAlertsCog")
                    if cog:
                        cog.report_module_error(int(guild.id), "verification", str(exc))
        except Exception:
            logger.exception("verification reverify sweeper error")

    @reverify_sweeper.before_loop
    async def before_reverify_sweeper(self):
        await self.bot.wait_until_ready()

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
        await publish_verification_panel(self.bot, interaction.channel)


async def setup(bot: commands.Bot):
    verification_db.init()
    cog = VerificationCog(bot)
    slash_registry.register_verification(cog)
    await bot.add_cog(cog)
