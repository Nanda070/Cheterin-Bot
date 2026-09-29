"""Заявки на вступление в семью: 2-этапная анкета -> приватный тред -> решение staff.

Портировано из FamQ tickets.py. Все ID (каналы/роли/эмодзи) читаются из
family_core.get_settings() вместо хардкода; модуль работает только пока
family_core.get_settings()["enabled"] истинно.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import bot.core.embed_style as embed_style
import bot.modules.games.family_core as family_core
import bot.modules.games.family_db as family_db
import bot.core.i18n as i18n
import bot.core.slash_registry as slash_registry

logger = logging.getLogger("family.tickets")


def build_mini_embed(member: discord.abc.User, ticket: dict, lang: str) -> discord.Embed:
    embed = discord.Embed(
        title=i18n.t("family.tickets.mini_title", lang),
        color=family_core.status_color(ticket["status"]),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name=i18n.t("family.tickets.field_nickname", lang), value=ticket["nickname"], inline=False)
    embed.add_field(name=i18n.t("family.tickets.field_real_name", lang), value=ticket["real_name"], inline=False)
    embed.add_field(name=i18n.t("family.tickets.field_age", lang), value=ticket["real_age"], inline=False)
    embed.add_field(name=i18n.t("family.tickets.field_status", lang), value=family_core.status_label(ticket["status"], lang), inline=False)
    avatar = getattr(member, "display_avatar", None)
    if avatar is not None:
        embed.set_thumbnail(url=avatar.url)
    embed.set_footer(text=i18n.t("family.tickets.footer_member", lang, id=member.id))
    return embed


def build_mini_embed_by_id(user_id: int, ticket: dict, lang: str) -> discord.Embed:
    """Mini-card when the applicant left and User fetch failed."""
    embed = discord.Embed(
        title=i18n.t("family.tickets.mini_title", lang),
        color=family_core.status_color(ticket["status"]),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name=i18n.t("family.tickets.field_nickname", lang), value=ticket["nickname"], inline=False)
    embed.add_field(name=i18n.t("family.tickets.field_real_name", lang), value=ticket["real_name"], inline=False)
    embed.add_field(name=i18n.t("family.tickets.field_age", lang), value=ticket["real_age"], inline=False)
    embed.add_field(name=i18n.t("family.tickets.field_status", lang), value=family_core.status_label(ticket["status"], lang), inline=False)
    embed.set_footer(text=i18n.t("family.tickets.footer_member", lang, id=user_id))
    return embed


def build_full_embed(member: discord.Member, ticket: dict, lang: str) -> discord.Embed:
    embed = discord.Embed(
        title=i18n.t("family.tickets.full_title", lang),
        description=i18n.t("family.tickets.full_description", lang),
        color=family_core.status_color(ticket["status"]),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name=i18n.t("family.tickets.field_member", lang), value=f"{member.mention}\n`{member.id}`", inline=False)
    embed.add_field(name=i18n.t("family.tickets.field_nickname", lang), value=ticket["nickname"], inline=True)
    embed.add_field(name=i18n.t("family.tickets.field_game_level", lang), value=ticket["game_level"], inline=True)
    embed.add_field(name=i18n.t("family.tickets.field_faction", lang), value=ticket["faction_pref"], inline=False)
    embed.add_field(name=i18n.t("family.tickets.field_online", lang), value=ticket["online_timezone"], inline=False)
    embed.add_field(name=i18n.t("family.tickets.field_real_name", lang), value=ticket["real_name"], inline=True)
    embed.add_field(name=i18n.t("family.tickets.field_age", lang), value=ticket["real_age"], inline=True)
    embed.add_field(name=i18n.t("family.tickets.field_about", lang), value=ticket["about_text"], inline=False)
    embed.add_field(name=i18n.t("family.tickets.field_why", lang), value=ticket["why_join"], inline=False)
    embed.add_field(
        name=i18n.t("family.tickets.field_inviter", lang),
        value=ticket["inviter_nickname"] or i18n.t("family.tickets.inviter_none", lang),
        inline=False,
    )
    embed.add_field(name=i18n.t("family.tickets.field_status", lang), value=family_core.status_label(ticket["status"], lang), inline=False)
    embed.add_field(name=i18n.t("family.tickets.field_created", lang), value=ticket["created_at"], inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    return embed


def build_ticket_status_embed(lang: str) -> discord.Embed:
    return discord.Embed(
        title=i18n.t("family.tickets.status_title", lang),
        description=i18n.t("family.tickets.status_description", lang),
        color=embed_style.GOLD,
        timestamp=datetime.now(timezone.utc),
    )


def build_ticket_result_embed(
    status: str,
    applicant: discord.abc.User,
    moderator: discord.Member,
    roles_added: list[discord.Role],
    removed_role: Optional[discord.Role],
    lang: str,
) -> discord.Embed:
    if status == "approved":
        embed = discord.Embed(
            title=i18n.t("family.tickets.approved_title", lang),
            description=i18n.t("family.tickets.approved_description", lang, mention=applicant.mention),
            color=embed_style.SUCCESS,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name=i18n.t("family.tickets.field_moderator", lang), value=moderator.mention, inline=False)
        embed.add_field(
            name=i18n.t("family.tickets.field_roles_added", lang),
            value="\n".join(f"• {r.name}" for r in roles_added) or i18n.t("family.tickets.none", lang),
            inline=False,
        )
        embed.add_field(
            name=i18n.t("family.tickets.field_role_removed", lang),
            value=removed_role.mention if removed_role else i18n.t("family.tickets.none", lang),
            inline=False,
        )
    elif status == "denied":
        embed = discord.Embed(
            title=i18n.t("family.tickets.denied_title", lang),
            description=i18n.t("family.tickets.denied_description", lang),
            color=embed_style.DANGER,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name=i18n.t("family.tickets.field_moderator", lang), value=moderator.mention, inline=True)
        embed.add_field(name=i18n.t("family.tickets.field_participant", lang), value=applicant.mention, inline=True)
        embed.add_field(
            name=i18n.t("family.tickets.field_role_removed", lang),
            value=removed_role.mention if removed_role else i18n.t("family.tickets.none", lang),
            inline=False,
        )
    else:
        embed = discord.Embed(
            title=i18n.t("family.tickets.closed_title", lang),
            description=i18n.t("family.tickets.closed_description", lang, mention=moderator.mention),
            color=embed_style.GOLD,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name=i18n.t("family.tickets.field_role_removed", lang),
            value=removed_role.mention if removed_role else i18n.t("family.tickets.none", lang),
            inline=False,
        )
    embed.set_footer(text=i18n.t("family.tickets.footer", lang))
    return embed


def member_log_value(member: discord.abc.User) -> str:
    return f"{member.mention}\n`{member.id}`"


async def send_log(bot: commands.Bot, guild_id: int, title: str, description: str, color: int, fields=None, lang: str | None = None):
    log_channel_id = family_core.get_settings(guild_id)["applications"]["log_channel_id"]
    if not log_channel_id:
        return
    channel = bot.get_channel(int(log_channel_id))
    if not isinstance(channel, discord.TextChannel):
        return

    lang = lang or i18n.lang_for(guild_id)
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    embed.set_footer(text=i18n.t("family.tickets.log_footer", lang))
    try:
        await channel.send(embed=embed)
    except discord.HTTPException:
        pass


async def send_ticket_created_log(bot, applicant, ticket, active_role, thread, message, lang: str):
    await send_log(bot, applicant.guild.id, i18n.t("family.tickets.log_created_title", lang), i18n.t("family.tickets.log_created_body", lang), embed_style.INFO_INT, [
        (i18n.t("family.tickets.log_field_member", lang), member_log_value(applicant), True),
        (i18n.t("family.tickets.log_field_nickname", lang), ticket["nickname"], True),
        (i18n.t("family.tickets.log_field_name", lang), ticket["real_name"], True),
        (i18n.t("family.tickets.log_field_age", lang), ticket["real_age"], True),
        (i18n.t("family.tickets.log_field_role", lang), active_role.mention if active_role else i18n.t("family.tickets.none", lang), True),
        (i18n.t("family.tickets.log_field_thread", lang), thread.mention, True),
        (i18n.t("family.tickets.log_field_message", lang), i18n.t("family.tickets.log_field_message_link", lang, url=message.jump_url), False),
    ], lang=lang)


async def send_ticket_result_log(
    bot,
    status,
    applicant: discord.abc.User,
    moderator: discord.Member,
    roles_added,
    removed_role,
    thread,
    lang: str,
    *,
    guild_id: int,
):
    if status == "approved":
        await send_log(bot, guild_id, i18n.t("family.tickets.log_approved_title", lang), i18n.t("family.tickets.log_approved_body", lang), embed_style.SUCCESS_INT, [
            (i18n.t("family.tickets.log_field_member", lang), member_log_value(applicant), True),
            (i18n.t("family.tickets.log_field_member", lang), member_log_value(moderator), True),
            (i18n.t("family.tickets.log_field_roles", lang), "\n".join(r.mention for r in roles_added) or i18n.t("family.tickets.none", lang), False),
            (i18n.t("family.tickets.field_role_removed", lang), removed_role.mention if removed_role else i18n.t("family.tickets.none", lang), False),
            (i18n.t("family.tickets.log_field_thread", lang), thread.mention, False),
        ], lang=lang)
    elif status == "denied":
        await send_log(bot, guild_id, i18n.t("family.tickets.log_denied_title", lang), i18n.t("family.tickets.log_denied_body", lang), embed_style.DANGER_INT, [
            (i18n.t("family.tickets.log_field_member", lang), member_log_value(applicant), True),
            (i18n.t("family.tickets.log_field_member", lang), member_log_value(moderator), True),
            (i18n.t("family.tickets.field_role_removed", lang), removed_role.mention if removed_role else i18n.t("family.tickets.none", lang), False),
            (i18n.t("family.tickets.log_field_thread", lang), thread.mention, False),
        ], lang=lang)
    else:
        await send_log(bot, guild_id, i18n.t("family.tickets.log_closed_title", lang), i18n.t("family.tickets.log_closed_body", lang), embed_style.GOLD_INT, [
            (i18n.t("family.tickets.log_field_member", lang), member_log_value(applicant), True),
            (i18n.t("family.tickets.log_field_member", lang), member_log_value(moderator), True),
            (i18n.t("family.tickets.field_role_removed", lang), removed_role.mention if removed_role else i18n.t("family.tickets.none", lang), False),
            (i18n.t("family.tickets.log_field_thread", lang), thread.mention, False),
        ], lang=lang)


async def add_custom_emoji_reaction(bot: commands.Bot, message: discord.Message, raw_emoji_id: str):
    if not raw_emoji_id:
        return
    emoji = bot.get_emoji(int(raw_emoji_id))
    if emoji:
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            pass


class ApplicationModalPart1(discord.ui.Modal):
    def __init__(self, lang: str):
        super().__init__(title=i18n.t("family.tickets.modal1.title", lang))
        self.lang = lang
        self.nickname = discord.ui.TextInput(label=i18n.t("family.tickets.modal1.nickname", lang), required=True, max_length=50)
        self.game_level = discord.ui.TextInput(label=i18n.t("family.tickets.modal1.level", lang), required=True, max_length=20)
        self.faction_pref = discord.ui.TextInput(
            label=i18n.t("family.tickets.modal1.faction", lang),
            placeholder=i18n.t("family.tickets.modal1.faction_placeholder", lang),
            required=True,
            max_length=100,
        )
        self.online_timezone = discord.ui.TextInput(
            label=i18n.t("family.tickets.modal1.online", lang), style=discord.TextStyle.paragraph, max_length=300
        )
        self.add_item(self.nickname)
        self.add_item(self.game_level)
        self.add_item(self.faction_pref)
        self.add_item(self.online_timezone)

    async def on_submit(self, interaction: discord.Interaction):
        family_db.save_pending_form(
            interaction.guild.id, interaction.user.id, str(self.nickname), str(self.game_level),
            str(self.faction_pref), str(self.online_timezone),
        )
        await interaction.response.send_message(
            i18n.t("family.tickets.modal1.done", self.lang), ephemeral=True, view=ContinueApplicationView(self.lang)
        )


class ApplicationModalPart2(discord.ui.Modal):
    def __init__(self, lang: str):
        super().__init__(title=i18n.t("family.tickets.modal2.title", lang))
        self.lang = lang
        self.real_name = discord.ui.TextInput(label=i18n.t("family.tickets.modal2.name", lang), required=True, max_length=50)
        self.real_age = discord.ui.TextInput(label=i18n.t("family.tickets.modal2.age", lang), required=True, max_length=3)
        self.about_text = discord.ui.TextInput(
            label=i18n.t("family.tickets.modal2.about", lang), required=True, style=discord.TextStyle.paragraph, max_length=700
        )
        self.why_join = discord.ui.TextInput(
            label=i18n.t("family.tickets.modal2.why", lang), required=True, style=discord.TextStyle.paragraph, max_length=700
        )
        self.inviter_nickname = discord.ui.TextInput(label=i18n.t("family.tickets.modal2.inviter", lang), required=False, max_length=50)
        self.add_item(self.real_name)
        self.add_item(self.real_age)
        self.add_item(self.about_text)
        self.add_item(self.why_join)
        self.add_item(self.inviter_nickname)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.lang
        first_part = family_db.get_pending_form(interaction.guild.id, interaction.user.id)
        if not first_part:
            await interaction.response.send_message(i18n.t("family.tickets.part1_missing", lang), ephemeral=True)
            return

        applicant, guild = interaction.user, interaction.guild
        existing = family_db.get_ticket_by_user(guild.id, applicant.id)
        if existing and existing["status"] == "open":
            family_db.delete_pending_form(guild.id, applicant.id)
            return await interaction.response.send_message(i18n.t("family.tickets.active_exists", lang), ephemeral=True)

        await interaction.response.defer(ephemeral=True, thinking=True)
        settings = family_core.get_settings(interaction.guild.id)["applications"]

        data = {
            **first_part,
            "real_name": str(self.real_name),
            "real_age": str(self.real_age),
            "about_text": str(self.about_text),
            "why_join": str(self.why_join),
            "inviter_nickname": str(self.inviter_nickname).strip() or None,
        }

        family_db.create_ticket_record(applicant.id, guild.id, data)

        active_role = guild.get_role(int(settings["ticket_active_role_id"])) if settings["ticket_active_role_id"] else None
        if active_role:
            try:
                await applicant.add_roles(active_role, reason="family ticket creation")
            except discord.HTTPException:
                pass

        app_channel_id = settings["application_channel_id"]
        app_channel = guild.get_channel(int(app_channel_id)) if app_channel_id else None
        ticket = family_db.get_ticket_by_user(guild.id, applicant.id)

        if not isinstance(app_channel, discord.TextChannel):
            family_db.delete_pending_form(guild.id, applicant.id)
            return await interaction.followup.send(
                i18n.t("family.tickets.channel_missing", lang), ephemeral=True
            )

        notify_role_id = settings["notify_role_id"]
        content = f"<@&{notify_role_id}>" if notify_role_id else None
        mini_message = await app_channel.send(content=content, embed=build_mini_embed(applicant, ticket, lang))
        await add_custom_emoji_reaction(interaction.client, mini_message, settings["yes_emoji_id"])
        await add_custom_emoji_reaction(interaction.client, mini_message, settings["no_emoji_id"])

        thread = await app_channel.create_thread(
            name=f"family-{applicant.name}".replace(" ", "-")[:80],
            type=discord.ChannelType.private_thread,
            invitable=False,
            auto_archive_duration=_clamp_archive_minutes(settings["thread_archive_minutes"]),
            reason=f"family ticket for {applicant}",
        )

        family_db.update_ticket_indexes(guild.id, applicant.id, mini_message.id, thread.id)
        try:
            await thread.add_user(applicant)
        except discord.HTTPException:
            pass

        staff_mentions = " ".join(f"<@&{rid}>" for rid in settings["staff_role_ids"])
        await thread.send(
            content=i18n.t("family.tickets.thread_wait", lang, mention=applicant.mention, staff=staff_mentions),
            embed=build_full_embed(applicant, ticket, lang),
            view=TicketControlView(lang),
        )
        await thread.send(embed=build_ticket_status_embed(lang))

        await send_ticket_created_log(interaction.client, applicant, ticket, active_role, thread, mini_message, lang)

        family_db.delete_pending_form(guild.id, applicant.id)
        await interaction.followup.send(i18n.t("family.tickets.created", lang, thread=thread.mention), ephemeral=True)


def _clamp_archive_minutes(minutes: int) -> int:
    # Discord принимает только 60/1440/4320/10080
    allowed = [60, 1440, 4320, 10080]
    return min(allowed, key=lambda a: abs(a - minutes))


class ContinueApplicationView(discord.ui.View):
    def __init__(self, lang: str):
        super().__init__(timeout=300)
        self.lang = lang

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary)
    async def continue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.label = i18n.t("family.tickets.button.continue", self.lang)
        data = family_db.get_pending_form(interaction.guild.id, interaction.user.id)
        if not data:
            return await interaction.response.send_message(i18n.t("family.tickets.form_reset", self.lang), ephemeral=True)
        await interaction.response.send_modal(ApplicationModalPart2(self.lang))


class OpenTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create ticket", style=discord.ButtonStyle.success, custom_id="family_open_ticket")
    async def open_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        lang = i18n.lang_for(interaction.guild_id)
        button.label = i18n.t("family.tickets.button.open", lang)
        if not family_core.get_settings(interaction.guild.id)["enabled"]:
            return await interaction.response.send_message(i18n.module_disabled(lang, "family"), ephemeral=True)

        existing = family_db.get_ticket_by_user(interaction.guild.id, interaction.user.id)
        if existing and existing["status"] == "open":
            return await interaction.response.send_message(i18n.t("family.tickets.active_application", lang), ephemeral=True)
        family_db.delete_pending_form(interaction.guild.id, interaction.user.id)
        await interaction.response.send_modal(ApplicationModalPart1(lang))


class TicketResolution:
    """Результат resolve_ticket — единая точка для форматирования ответа и в Discord, и в дашборде."""

    def __init__(self, ok: bool, error: str | None = None, applicant=None, roles_added=None, removed_role=None, thread=None):
        self.ok = ok
        self.error = error
        self.applicant = applicant
        self.roles_added = roles_added or []
        self.removed_role = removed_role
        self.thread = thread


async def resolve_ticket(bot: commands.Bot, guild: discord.Guild, thread: discord.Thread, status: str, moderator: discord.Member) -> TicketResolution:
    """Общая логика решения по тикету — используется и кнопками в Discord, и дашбордом.

    Approve requires the applicant still in the guild. Close/deny work if they left
    (roles are skipped; mini-card/thread/log still update).
    """
    lang = i18n.lang_for(guild.id)
    ticket = family_db.get_ticket_by_thread(guild.id, thread.id)
    if not ticket or ticket["status"] != "open":
        return TicketResolution(False, error="not_open")

    applicant: discord.Member | None = guild.get_member(ticket["user_id"])
    if applicant is None:
        try:
            applicant = await guild.fetch_member(ticket["user_id"])
        except (discord.NotFound, discord.HTTPException):
            applicant = None

    if applicant is None and status == "approved":
        return TicketResolution(False, error="member_not_found")

    display_user: discord.abc.User | None = applicant
    if display_user is None:
        try:
            display_user = await bot.fetch_user(ticket["user_id"])
        except discord.HTTPException:
            display_user = None

    settings = family_core.get_settings(guild.id)["applications"]
    roles_added: list[discord.Role] = []
    removed_role: Optional[discord.Role] = None

    if applicant is not None:
        if status == "approved":
            roles_added = [guild.get_role(int(rid)) for rid in settings["approve_role_ids"] if rid]
            roles_added = [r for r in roles_added if r is not None]
            try:
                if roles_added:
                    await applicant.add_roles(*roles_added, reason=f"Approved by {moderator}")
            except discord.HTTPException as exc:
                return TicketResolution(False, error=f"role_error: {exc}")

        active_role = guild.get_role(int(settings["ticket_active_role_id"])) if settings["ticket_active_role_id"] else None
        removed_role = active_role if active_role and active_role in applicant.roles else None
        if removed_role:
            try:
                await applicant.remove_roles(removed_role, reason="Ticket processing")
            except discord.HTTPException:
                pass

    family_db.update_ticket_status(guild.id, ticket["user_id"], status, moderator.id)

    app_channel_id = settings["application_channel_id"]
    app_channel = guild.get_channel(int(app_channel_id)) if app_channel_id else None
    if isinstance(app_channel, discord.TextChannel) and ticket["mini_message_id"]:
        try:
            msg = await app_channel.fetch_message(ticket["mini_message_id"])
            t_data = family_db.get_ticket_by_user(guild.id, ticket["user_id"])
            if display_user is not None:
                await msg.edit(embed=build_mini_embed(display_user, t_data, lang))
            else:
                await msg.edit(embed=build_mini_embed_by_id(ticket["user_id"], t_data, lang))
        except discord.HTTPException:
            pass

    if applicant is not None:
        try:
            if status == "approved":
                await thread.send(content=i18n.t("family.tickets.approved_dm", lang, mention=applicant.mention))
            elif status == "denied":
                await thread.send(content=i18n.t("family.tickets.denied_dm", lang, mention=applicant.mention))
        except discord.HTTPException:
            pass
    elif status in ("closed", "denied"):
        try:
            await thread.send(content=i18n.t("family.tickets.left_server_note", lang, id=ticket["user_id"]))
        except discord.HTTPException:
            pass

    log_user = display_user
    if log_user is None:
        # Minimal stand-in for log fields when Discord user is unreachable.
        class _IdUser:
            def __init__(self, uid: int):
                self.id = uid
                self.mention = f"<@{uid}>"

        log_user = _IdUser(ticket["user_id"])  # type: ignore[assignment]

    await send_ticket_result_log(
        bot, status, log_user, moderator, roles_added, removed_role, thread, lang, guild_id=guild.id
    )

    name_part = getattr(display_user, "name", None) or str(ticket["user_id"])
    try:
        await thread.edit(name=f"{status}-family-{name_part}"[:100], locked=True, archived=True)
    except discord.HTTPException as exc:
        logger.warning("Не удалось заархивировать тред тикета: %s", exc)

    return TicketResolution(
        True,
        applicant=log_user,
        roles_added=roles_added,
        removed_role=removed_role,
        thread=thread,
    )


class TicketControlView(discord.ui.View):
    def __init__(self, lang: str | None = None):
        super().__init__(timeout=None)
        self.lang = lang

    async def _process(self, interaction: discord.Interaction, status: str):
        lang = i18n.lang_for(interaction.guild_id)
        if not family_core.get_settings(interaction.guild.id)["enabled"]:
            return await interaction.response.send_message(i18n.module_disabled(lang, "family"), ephemeral=True)
        if not family_core.can_manage_tickets(interaction.user):
            return await interaction.response.send_message(i18n.t("family.no_access", lang), ephemeral=True)

        result = await resolve_ticket(interaction.client, interaction.guild, interaction.channel, status, interaction.user)
        if not result.ok:
            if result.error == "not_open":
                message = i18n.t("family.tickets.not_available", lang)
            elif result.error == "member_not_found":
                message = i18n.t("family.tickets.member_not_found", lang)
            else:
                message = i18n.t("family.tickets.role_error", lang, error=result.error)
            return await interaction.response.send_message(message, ephemeral=True)

        await interaction.response.send_message(
            embed=build_ticket_result_embed(status, result.applicant, interaction.user, result.roles_added, result.removed_role, lang)
        )

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, custom_id="family_approve_ticket")
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        lang = i18n.lang_for(interaction.guild_id)
        button.label = i18n.t("family.tickets.button.approve", lang)
        await self._process(interaction, "approved")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, custom_id="family_deny_ticket")
    async def deny_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        lang = i18n.lang_for(interaction.guild_id)
        button.label = i18n.t("family.tickets.button.deny", lang)
        await self._process(interaction, "denied")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.secondary, custom_id="family_close_ticket")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        lang = i18n.lang_for(interaction.guild_id)
        button.label = i18n.t("family.tickets.button.close", lang)
        await self._process(interaction, "closed")


class FamilyTicketsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Auto-close open family applications when the applicant leaves."""
        settings = family_core.get_settings(member.guild.id)
        if not settings["enabled"]:
            return
        ticket = family_db.get_ticket_by_user(member.guild.id, member.id)
        if not ticket or ticket["status"] != "open" or not ticket.get("thread_id"):
            return
        moderator = member.guild.me
        if moderator is None:
            return
        try:
            result = await self.resolve_ticket_by_user(member.guild, member.id, "closed", moderator)
            if not result.ok:
                logger.warning(
                    "auto-close family ticket failed guild=%s user=%s err=%s",
                    member.guild.id,
                    member.id,
                    result.error,
                )
        except Exception:
            logger.exception(
                "auto-close family ticket crashed guild=%s user=%s",
                member.guild.id,
                member.id,
            )

    @app_commands.command(name="семья-заявки", description="Развернуть панель создания заявки в семью")
    @app_commands.default_permissions(manage_guild=True)
    async def create_panel(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        if not family_core.get_settings(interaction.guild.id)["enabled"]:
            return await interaction.response.send_message(i18n.module_disabled(lang, "family"), ephemeral=True)
        if not family_core.has_staff_access(interaction.user):
            return await interaction.response.send_message(i18n.t("family.no_access", lang), ephemeral=True)
        await interaction.channel.send(view=OpenTicketView())
        await interaction.response.send_message(i18n.t("family.done", lang), ephemeral=True)

    async def resolve_ticket_by_user(self, guild: discord.Guild, user_id: int, status: str, moderator: discord.Member) -> TicketResolution:
        """Точка входа для дашборда: находит тред по user_id и вызывает resolve_ticket."""
        ticket = family_db.get_ticket_by_user(guild.id, user_id)
        if not ticket or ticket["status"] != "open" or not ticket["thread_id"]:
            return TicketResolution(False, error="not_open")

        thread = self.bot.get_channel(ticket["thread_id"])
        if thread is None:
            try:
                thread = await guild.fetch_channel(ticket["thread_id"])
            except discord.HTTPException:
                return TicketResolution(False, error="thread_not_found")

        return await resolve_ticket(self.bot, guild, thread, status, moderator)


async def setup(bot: commands.Bot):
    family_db.init()
    bot.add_view(OpenTicketView())
    bot.add_view(TicketControlView())
    cog = FamilyTicketsCog(bot)
    slash_registry.register_family_tickets(cog)
    await bot.add_cog(cog)
