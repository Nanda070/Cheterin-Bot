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

import family_core
import family_db

logger = logging.getLogger("family.tickets")


def build_mini_embed(member: discord.Member, ticket: dict) -> discord.Embed:
    embed = discord.Embed(
        title="Новая заявка в Семью",
        color=family_core.status_color(ticket["status"]),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Ваш никнейм", value=ticket["nickname"], inline=False)
    embed.add_field(name="Ваше имя", value=ticket["real_name"], inline=False)
    embed.add_field(name="Ваш возраст", value=ticket["real_age"], inline=False)
    embed.add_field(name="Статус заявки", value=family_core.status_label(ticket["status"]), inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"ID участника: {member.id}")
    return embed


def build_full_embed(member: discord.Member, ticket: dict) -> discord.Embed:
    embed = discord.Embed(
        title="Заявка участника",
        description="Заявка отправлена на рассмотрение.",
        color=family_core.status_color(ticket["status"]),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Участник:", value=f"{member.mention}\n`{member.id}`", inline=False)
    embed.add_field(name="Ваш никнейм:", value=ticket["nickname"], inline=True)
    embed.add_field(name="Игровой уровень:", value=ticket["game_level"], inline=True)
    embed.add_field(name="Предпочтения по фракциям:", value=ticket["faction_pref"], inline=False)
    embed.add_field(name="Суточный онлайн и Часовой Пояс:", value=ticket["online_timezone"], inline=False)
    embed.add_field(name="Ваше имя:", value=ticket["real_name"], inline=True)
    embed.add_field(name="Ваш возраст:", value=ticket["real_age"], inline=True)
    embed.add_field(name="Расскажите немного о себе:", value=ticket["about_text"], inline=False)
    embed.add_field(name="Почему Вы хотите вступить в семью?", value=ticket["why_join"], inline=False)
    embed.add_field(name="Никнейм пригласившего:", value=ticket["inviter_nickname"] or "Не указан", inline=False)
    embed.add_field(name="Статус заявки:", value=family_core.status_label(ticket["status"]), inline=False)
    embed.add_field(name="Создано:", value=ticket["created_at"], inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    return embed


def build_ticket_status_embed() -> discord.Embed:
    return discord.Embed(
        title="Статус тикета",
        description="Тикет открыт. Администрация может принять участника или отклонить заявку.",
        color=0xFEE75C,
        timestamp=datetime.now(timezone.utc),
    )


def build_ticket_result_embed(
    status: str,
    applicant: discord.Member,
    moderator: discord.Member,
    roles_added: list[discord.Role],
    removed_role: Optional[discord.Role],
) -> discord.Embed:
    if status == "approved":
        embed = discord.Embed(
            title="Заявка принята",
            description=f"{applicant.mention} был принят в семью.",
            color=0x57F287,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Модератор", value=moderator.mention, inline=False)
        embed.add_field(name="Выданы роли", value="\n".join(f"• {r.name}" for r in roles_added) or "Нет", inline=False)
        embed.add_field(name="Снята роль", value=removed_role.mention if removed_role else "Нет", inline=False)
    elif status == "denied":
        embed = discord.Embed(
            title="Заявка отклонена",
            description="Администрация отказала по этой заявке.",
            color=0xED4245,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Модератор", value=moderator.mention, inline=True)
        embed.add_field(name="Участник", value=applicant.mention, inline=True)
        embed.add_field(name="Снята роль", value=removed_role.mention if removed_role else "Нет", inline=False)
    else:
        embed = discord.Embed(
            title="Тикет закрыт",
            description=f"Тикет был закрыт модератором {moderator.mention}.",
            color=0xFEE75C,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Снята роль", value=removed_role.mention if removed_role else "Нет", inline=False)
    embed.set_footer(text="Семья · модерация")
    return embed


def member_log_value(member: discord.Member) -> str:
    return f"{member.mention}\n`{member.id}`"


async def send_log(bot: commands.Bot, guild_id: int, title: str, description: str, color: int, fields=None):
    log_channel_id = family_core.get_settings(guild_id)["applications"]["log_channel_id"]
    if not log_channel_id:
        return
    channel = bot.get_channel(int(log_channel_id))
    if not isinstance(channel, discord.TextChannel):
        return

    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    embed.set_footer(text="Семья · логи")
    try:
        await channel.send(embed=embed)
    except discord.HTTPException:
        pass


async def send_ticket_created_log(bot, applicant, ticket, active_role, thread, message):
    await send_log(bot, applicant.guild.id, "Создан новый тикет", "Новая заявка успешно создана.", 0x5865F2, [
        ("Участник", member_log_value(applicant), True),
        ("Никнейм", ticket["nickname"], True),
        ("Имя", ticket["real_name"], True),
        ("Возраст", ticket["real_age"], True),
        ("Выдана роль", active_role.mention if active_role else "Нет", True),
        ("Тред", thread.mention, True),
        ("Сообщение", f"[Перейти]({message.jump_url})", False),
    ])


async def send_ticket_result_log(bot, status, applicant, moderator, roles_added, removed_role, thread):
    guild_id = applicant.guild.id
    if status == "approved":
        await send_log(bot, guild_id, "Заявка одобрена", "Администрация приняла участника.", 0x57F287, [
            ("Участник", member_log_value(applicant), True),
            ("Модератор", member_log_value(moderator), True),
            ("Роли", "\n".join(r.mention for r in roles_added) or "Нет", False),
            ("Снята роль", removed_role.mention if removed_role else "Нет", False),
            ("Тред", thread.mention, False),
        ])
    elif status == "denied":
        await send_log(bot, guild_id, "Заявка отклонена", "Администрация отклонила заявку.", 0xED4245, [
            ("Участник", member_log_value(applicant), True),
            ("Модератор", member_log_value(moderator), True),
            ("Снята роль", removed_role.mention if removed_role else "Нет", False),
            ("Тред", thread.mention, False),
        ])
    else:
        await send_log(bot, guild_id, "Тикет закрыт", "Заявка была закрыта без принятия.", 0xFEE75C, [
            ("Участник", member_log_value(applicant), True),
            ("Модератор", member_log_value(moderator), True),
            ("Снята роль", removed_role.mention if removed_role else "Нет", False),
            ("Тред", thread.mention, False),
        ])


async def add_custom_emoji_reaction(bot: commands.Bot, message: discord.Message, raw_emoji_id: str):
    if not raw_emoji_id:
        return
    emoji = bot.get_emoji(int(raw_emoji_id))
    if emoji:
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            pass


class ApplicationModalPart1(discord.ui.Modal, title="Заявка в семью • 1/2"):
    nickname = discord.ui.TextInput(label="Ваш никнейм", required=True, max_length=50)
    game_level = discord.ui.TextInput(label="Игровой уровень", required=True, max_length=20)
    faction_pref = discord.ui.TextInput(
        label="Предпочтения по фракциям", placeholder="Гос / Крайм / оба", required=True, max_length=100
    )
    online_timezone = discord.ui.TextInput(
        label="Суточный онлайн и Часовой Пояс", style=discord.TextStyle.paragraph, max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):
        family_db.save_pending_form(
            interaction.guild.id, interaction.user.id, str(self.nickname), str(self.game_level),
            str(self.faction_pref), str(self.online_timezone),
        )
        await interaction.response.send_message(
            "Первая часть заполнена. Открой вторую.", ephemeral=True, view=ContinueApplicationView()
        )


class ApplicationModalPart2(discord.ui.Modal, title="Заявка в семью • 2/2"):
    real_name = discord.ui.TextInput(label="Ваше имя", required=True, max_length=50)
    real_age = discord.ui.TextInput(label="Ваш возраст", required=True, max_length=3)
    about_text = discord.ui.TextInput(
        label="Расскажите немного о себе", required=True, style=discord.TextStyle.paragraph, max_length=700
    )
    why_join = discord.ui.TextInput(
        label="Почему Вы хотите вступить в семью?", required=True, style=discord.TextStyle.paragraph, max_length=700
    )
    inviter_nickname = discord.ui.TextInput(label="Никнейм пригласившего", required=False, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        first_part = family_db.get_pending_form(interaction.guild.id, interaction.user.id)
        if not first_part:
            await interaction.response.send_message("Первая часть не найдена.", ephemeral=True)
            return

        applicant, guild = interaction.user, interaction.guild
        existing = family_db.get_ticket_by_user(guild.id, applicant.id)
        if existing and existing["status"] == "open":
            family_db.delete_pending_form(guild.id, applicant.id)
            return await interaction.response.send_message("Уже есть активная заявка.", ephemeral=True)

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
                "Канал заявок не настроен — обратитесь к администрации.", ephemeral=True
            )

        notify_role_id = settings["notify_role_id"]
        content = f"<@&{notify_role_id}>" if notify_role_id else None
        mini_message = await app_channel.send(content=content, embed=build_mini_embed(applicant, ticket))
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
            content=f"{applicant.mention} Ожидайте ответа.\n{staff_mentions}",
            embed=build_full_embed(applicant, ticket),
            view=TicketControlView(),
        )
        await thread.send(embed=build_ticket_status_embed())

        await send_ticket_created_log(interaction.client, applicant, ticket, active_role, thread, mini_message)

        family_db.delete_pending_form(guild.id, applicant.id)
        await interaction.followup.send(f"Твой приватный тикет: {thread.mention}", ephemeral=True)


def _clamp_archive_minutes(minutes: int) -> int:
    # Discord принимает только 60/1440/4320/10080
    allowed = [60, 1440, 4320, 10080]
    return min(allowed, key=lambda a: abs(a - minutes))


class ContinueApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Продолжить", style=discord.ButtonStyle.primary)
    async def continue_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        data = family_db.get_pending_form(interaction.guild.id, interaction.user.id)
        if not data:
            return await interaction.response.send_message("Анкета сброшена.", ephemeral=True)
        await interaction.response.send_modal(ApplicationModalPart2())


class OpenTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Создать тикет", style=discord.ButtonStyle.success, custom_id="family_open_ticket")
    async def open_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if not family_core.get_settings(interaction.guild.id)["enabled"]:
            return await interaction.response.send_message("Модуль «Семья» отключён.", ephemeral=True)

        existing = family_db.get_ticket_by_user(interaction.guild.id, interaction.user.id)
        if existing and existing["status"] == "open":
            return await interaction.response.send_message("Активная заявка уже есть.", ephemeral=True)
        family_db.delete_pending_form(interaction.guild.id, interaction.user.id)
        await interaction.response.send_modal(ApplicationModalPart1())


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
    """Общая логика решения по тикету — используется и кнопками в Discord, и дашбордом."""
    ticket = family_db.get_ticket_by_thread(guild.id, thread.id)
    if not ticket or ticket["status"] != "open":
        return TicketResolution(False, error="not_open")

    applicant = guild.get_member(ticket["user_id"])
    if applicant is None:
        try:
            applicant = await guild.fetch_member(ticket["user_id"])
        except discord.NotFound:
            applicant = None
    if applicant is None:
        return TicketResolution(False, error="member_not_found")

    settings = family_core.get_settings(guild.id)["applications"]
    roles_added: list[discord.Role] = []
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
            await msg.edit(embed=build_mini_embed(applicant, t_data))
        except discord.HTTPException:
            pass

    try:
        if status == "approved":
            await thread.send(content=f"{applicant.mention}, твоя заявка одобрена. Добро пожаловать.")
        elif status == "denied":
            await thread.send(content=f"{applicant.mention}, твоя заявка была отклонена.")
    except discord.HTTPException:
        pass

    await send_ticket_result_log(bot, status, applicant, moderator, roles_added, removed_role, thread)

    try:
        await thread.edit(name=f"{status}-family-{applicant.name}"[:100], locked=True, archived=True)
    except discord.HTTPException as exc:
        logger.warning("Не удалось заархивировать тред тикета: %s", exc)

    return TicketResolution(True, applicant=applicant, roles_added=roles_added, removed_role=removed_role, thread=thread)


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _process(self, interaction: discord.Interaction, status: str):
        if not family_core.get_settings(interaction.guild.id)["enabled"]:
            return await interaction.response.send_message("Модуль «Семья» отключён.", ephemeral=True)
        if not family_core.can_manage_tickets(interaction.user):
            return await interaction.response.send_message("Нет доступа.", ephemeral=True)

        result = await resolve_ticket(interaction.client, interaction.guild, interaction.channel, status, interaction.user)
        if not result.ok:
            message = "Тикет недоступен." if result.error == "not_open" else \
                "Пользователь не найден." if result.error == "member_not_found" else \
                f"Ошибка ролей: {result.error}"
            return await interaction.response.send_message(message, ephemeral=True)

        await interaction.response.send_message(
            embed=build_ticket_result_embed(status, result.applicant, interaction.user, result.roles_added, result.removed_role)
        )

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, custom_id="family_approve_ticket")
    async def approve_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._process(interaction, "approved")

    @discord.ui.button(label="Отказать", style=discord.ButtonStyle.danger, custom_id="family_deny_ticket")
    async def deny_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._process(interaction, "denied")

    @discord.ui.button(label="Закрыть", style=discord.ButtonStyle.secondary, custom_id="family_close_ticket")
    async def close_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._process(interaction, "closed")


class FamilyTicketsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="семья-заявки", description="Развернуть панель создания заявки в семью")
    async def create_panel(self, interaction: discord.Interaction):
        if not family_core.get_settings(interaction.guild.id)["enabled"]:
            return await interaction.response.send_message("Модуль «Семья» отключён.", ephemeral=True)
        if not family_core.has_staff_access(interaction.user):
            return await interaction.response.send_message("Нет доступа.", ephemeral=True)
        await interaction.channel.send(view=OpenTicketView())
        await interaction.response.send_message("Выполнено.", ephemeral=True)

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
    await bot.add_cog(FamilyTicketsCog(bot))
