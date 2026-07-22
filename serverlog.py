"""Тотальное логирование событий сервера.

Каждый тип события включается отдельно и может писать в свой канал.
Настраивается из дашборда (раздел «Логирование»), хранение — settings_db (module «serverlog»).

Стиль эмбедов (единый на все каналы логов): цветная полоса слева по категории
события, предложение с упоминанием участника в description (Discord не рендерит
пинги в title/author, поэтому именно description), крупный аватар справа
(thumbnail) и футер «ID участника: <id>» — Discord сам склеивает его с временем
события через точку.
"""

import asyncio
import logging
import random

import discord
from discord import app_commands
from discord.ext import commands

import i18n
import settings_db

logger = logging.getLogger("serverlog")

MODULE_NAME = "serverlog"

# Тип события -> подпись для дашборда. Порядок = порядок в панели.
EVENT_TYPES: dict[str, str] = {
    "message_edit": "Редактирование сообщений",
    "message_delete": "Удаление сообщений",
    "member_join": "Вход участника на сервер",
    "member_leave": "Выход участника с сервера",
    "member_ban": "Бан участника",
    "member_unban": "Разбан участника",
    "member_timeout": "Тайм-аут участника (выдан/снят)",
    "nickname_change": "Смена никнейма",
    "roles_change": "Изменение ролей участника",
    "voice_join": "Вход в голосовой канал",
    "voice_leave": "Выход из голосового канала",
    "voice_move": "Переключение между голосовыми (сам участник)",
    "voice_move_admin": "Перемещение между голосовыми администратором",
    "voice_disconnect_admin": "Отключение из голосового администратором",
    "voice_state": "Мут/деф от администратора",
    "role_create": "Создание роли",
    "role_delete": "Удаление роли",
    "role_update": "Изменение роли",
    "channel_create": "Создание канала",
    "channel_delete": "Удаление канала",
    "channel_update": "Изменение канала",
    "channel_permissions_update": "Изменение прав канала",
    "thread_create": "Создание треда",
    "thread_delete": "Удаление треда",
    "thread_update": "Изменение треда",
    "emoji_update": "Изменение эмодзи",
    "invite_create": "Создание приглашения",
    "invite_delete": "Удаление приглашения",
    "guild_update": "Изменение настроек сервера",
    "moderation_command": "Использование модераторской команды",
}

MAX_CONTENT = 1000
AUDIT_LOOKUP_WINDOW_SECONDS = 5


def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    """Полные настройки сервера с дефолтами по каждому типу события."""
    data = settings_db.get(guild_id, MODULE_NAME)
    events = data.get("events", {})
    result = {}
    for event_type in EVENT_TYPES:
        entry = events.get(event_type, {})
        result[event_type] = {
            "enabled": bool(entry.get("enabled", False)),
            "channel_id": str(entry.get("channel_id") or ""),
        }
    return {"events": result}


def event_channel_id(guild_id: int, event_type: str) -> int:
    """ID канала для типа события, 0 если тип выключен или канал не задан."""
    entry = get_settings(guild_id)["events"].get(event_type)
    if not entry or not entry["enabled"]:
        return 0
    try:
        return int(entry["channel_id"])
    except (TypeError, ValueError):
        return 0


def _clip(text: str | None, lang: str | None = None) -> str:
    lang = lang or i18n.DEFAULT_LANGUAGE
    if not text:
        return i18n.t("serverlog.empty", lang)
    return text if len(text) <= MAX_CONTENT else text[:MAX_CONTENT] + "…"


def _plural_unit(lang: str, n: int, prefix: str) -> str:
    """Pick localized time unit with correct plural form."""
    n_abs = abs(int(n))
    if lang == "ru":
        if 11 <= n_abs % 100 <= 14:
            form = "many"
        else:
            last = n_abs % 10
            if last == 1:
                form = "one"
            elif 2 <= last <= 4:
                form = "few"
            else:
                form = "many"
    else:
        form = "one" if n == 1 else "other"
    return i18n.t(f"{prefix}.{form}", lang)


def format_stay_duration(seconds: float, lang: str | None = None) -> str:
    """Одна крупная единица времени: «31 секунда», «5 минут», «2 часа», «3 дня»."""
    lang = lang or i18n.DEFAULT_LANGUAGE
    total = max(0, int(seconds))
    if total < 60:
        return f"{total} {_plural_unit(lang, total, 'serverlog.unit.second')}"
    minutes = total // 60
    if minutes < 60:
        return f"{minutes} {_plural_unit(lang, minutes, 'serverlog.unit.minute')}"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} {_plural_unit(lang, hours, 'serverlog.unit.hour')}"
    days = hours // 24
    return f"{days} {_plural_unit(lang, days, 'serverlog.unit.day')}"


async def _recent_audit_entry(
    guild: discord.Guild,
    action: discord.AuditLogAction,
    target_id: int | None = None,
    channel: discord.abc.GuildChannel | None = None,
) -> discord.AuditLogEntry | None:
    """Эвристика: ищет только что созданную запись аудита по действию/цели."""
    try:
        async for entry in guild.audit_logs(action=action, limit=5):
            age = (discord.utils.utcnow() - entry.created_at).total_seconds()
            if age > AUDIT_LOOKUP_WINDOW_SECONDS:
                break
            if target_id is not None and getattr(entry.target, "id", None) != target_id:
                continue
            entry_channel = getattr(entry.extra, "channel", None)
            if channel is not None and entry_channel is not None and entry_channel.id != channel.id:
                continue
            return entry
    except (discord.Forbidden, discord.HTTPException):
        pass
    return None


def _is_moderation_command(command: app_commands.Command) -> bool:
    perms = command.default_permissions
    if perms is None:
        root = command.root_parent
        if root is not None:
            perms = root.default_permissions
    if perms is None:
        return False
    return perms.administrator or perms.manage_guild


class ServerLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def emit(self, guild_id: int, event_type: str, embed: discord.Embed):
        channel_id = event_channel_id(guild_id, event_type)
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            return
        await asyncio.sleep(random.uniform(0.5, 2.5))
        try:
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException as exc:
            logger.warning("Не удалось отправить лог %s: %s", event_type, exc)

    def _embed(
        self, description: str, color: discord.Color, lang: str,
        subject: discord.abc.User | None = None,
    ) -> discord.Embed:
        embed = discord.Embed(description=description, color=color, timestamp=discord.utils.utcnow())
        if subject is not None:
            embed.set_thumbnail(url=subject.display_avatar.url)
            footer = i18n.t("serverlog.footer.member_id", lang)
            embed.set_footer(text=f"{footer}: {subject.id}")
        return embed

    def _add_actor_fields(self, embed: discord.Embed, entry: discord.AuditLogEntry | None, lang: str) -> None:
        if entry is None:
            return
        if entry.user is not None:
            embed.add_field(
                name=i18n.t("serverlog.field.actor", lang),
                value=f"{entry.user.mention} ({entry.user})",
                inline=False,
            )
        if entry.reason:
            embed.add_field(name=i18n.t("serverlog.field.reason", lang), value=_clip(entry.reason, lang), inline=False)

    # ────────────────── Сообщения ──────────────────

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.guild is None:
            return
        if before.content == after.content:
            return
        lang = i18n.lang_for(before.guild.id)
        embed = self._embed(
            i18n.t("serverlog.event.message_edit", lang, author=before.author.mention, channel=before.channel.mention),
            discord.Color.orange(), lang, before.author,
        )
        embed.add_field(name=i18n.t("serverlog.field.before", lang), value=_clip(before.content, lang), inline=False)
        embed.add_field(name=i18n.t("serverlog.field.after", lang), value=_clip(after.content, lang), inline=False)
        embed.add_field(
            name=i18n.t("serverlog.field.link", lang),
            value=f"[{i18n.t('serverlog.field.link_go', lang)}]({after.jump_url})",
            inline=False,
        )
        await self.emit(before.guild.id, "message_edit", embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        lang = i18n.lang_for(message.guild.id)
        embed = self._embed(
            i18n.t("serverlog.event.message_delete", lang, author=message.author.mention, channel=message.channel.mention),
            discord.Color.red(), lang, message.author,
        )
        embed.add_field(name=i18n.t("serverlog.field.content", lang), value=_clip(message.content, lang), inline=False)
        if message.attachments:
            names = ", ".join(a.filename for a in message.attachments[:5])
            embed.add_field(name=i18n.t("serverlog.field.attachments", lang), value=_clip(names, lang), inline=False)
        await self.emit(message.guild.id, "message_delete", embed)

    # ────────────────── Участники ──────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        lang = i18n.lang_for(member.guild.id)
        embed = self._embed(
            i18n.t(
                "serverlog.event.member_join", lang,
                member=member.mention, display_name=member.display_name,
            ),
            discord.Color.green(), lang, member,
        )
        ts = int(member.created_at.timestamp())
        embed.add_field(name=i18n.t("serverlog.field.registration_date", lang), value=f"<t:{ts}:D> (<t:{ts}:R>)", inline=False)
        embed.add_field(name=i18n.t("serverlog.field.member_count", lang), value=str(member.guild.member_count), inline=True)
        await self.emit(member.guild.id, "member_join", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        lang = i18n.lang_for(member.guild.id)
        embed = self._embed(
            i18n.t(
                "serverlog.event.member_leave", lang,
                member=member.mention, display_name=member.display_name,
            ),
            discord.Color.gold(), lang, member,
        )
        roles = [r.mention for r in member.roles if not r.is_default()]
        if roles:
            embed.add_field(name=i18n.t("serverlog.field.roles", lang), value=_clip(", ".join(roles), lang), inline=False)
        if member.joined_at is not None:
            stayed = (discord.utils.utcnow() - member.joined_at).total_seconds()
            embed.add_field(
                name=i18n.t("serverlog.field.stay_duration", lang),
                value=format_stay_duration(stayed, lang),
                inline=False,
            )
        await self.emit(member.guild.id, "member_leave", embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.abc.User):
        lang = i18n.lang_for(guild.id)
        embed = self._embed(i18n.t("serverlog.event.member_ban", lang, user=user.mention), discord.Color.dark_red(), lang, user)
        await self.emit(guild.id, "member_ban", embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        lang = i18n.lang_for(guild.id)
        embed = self._embed(i18n.t("serverlog.event.member_unban", lang, user=user.mention), discord.Color.green(), lang, user)
        await self.emit(guild.id, "member_unban", embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        lang = i18n.lang_for(after.guild.id)
        if before.nick != after.nick:
            embed = self._embed(
                i18n.t("serverlog.event.nickname_change", lang, member=after.mention),
                discord.Color.blurple(), lang, after,
            )
            embed.add_field(name=i18n.t("serverlog.field.before", lang), value=_clip(before.nick or before.name, lang), inline=True)
            embed.add_field(name=i18n.t("serverlog.field.after", lang), value=_clip(after.nick or after.name, lang), inline=True)
            await self.emit(after.guild.id, "nickname_change", embed)

        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            if added or removed:
                embed = self._embed(
                    i18n.t(
                        "serverlog.event.roles_change", lang,
                        member=after.mention, display_name=after.display_name,
                    ),
                    discord.Color.blurple(), lang, after,
                )
                if added:
                    embed.add_field(
                        name=i18n.t("serverlog.field.added_roles", lang),
                        value=_clip(", ".join(r.mention for r in added), lang),
                        inline=False,
                    )
                if removed:
                    embed.add_field(
                        name=i18n.t("serverlog.field.removed_roles", lang),
                        value=_clip(", ".join(r.mention for r in removed), lang),
                        inline=False,
                    )
                entry = await _recent_audit_entry(after.guild, discord.AuditLogAction.member_role_update, target_id=after.id)
                self._add_actor_fields(embed, entry, lang)
                await self.emit(after.guild.id, "roles_change", embed)

        if before.timed_out_until != after.timed_out_until:
            now = discord.utils.utcnow()
            was_active = before.timed_out_until is not None and before.timed_out_until > now
            is_active = after.timed_out_until is not None and after.timed_out_until > now
            if is_active and not was_active:
                embed = self._embed(
                    i18n.t("serverlog.event.timeout_given", lang, member=after.mention),
                    discord.Color.red(), lang, after,
                )
                embed.add_field(name=i18n.t("serverlog.field.after", lang), value=f"<t:{int(after.timed_out_until.timestamp())}:F>", inline=False)
                entry = await _recent_audit_entry(after.guild, discord.AuditLogAction.member_update, target_id=after.id)
                self._add_actor_fields(embed, entry, lang)
                await self.emit(after.guild.id, "member_timeout", embed)
            elif was_active and not is_active:
                embed = self._embed(
                    i18n.t("serverlog.event.timeout_removed", lang, member=after.mention),
                    discord.Color.green(), lang, after,
                )
                await self.emit(after.guild.id, "member_timeout", embed)

    # ────────────────── Войс ──────────────────

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        lang = i18n.lang_for(member.guild.id)

        if before.channel is None and after.channel is not None:
            embed = self._embed(
                i18n.t("serverlog.event.voice_join", lang, member=member.mention, channel=after.channel.mention),
                discord.Color.teal(), lang, member,
            )
            await self.emit(member.guild.id, "voice_join", embed)

        elif before.channel is not None and after.channel is None:
            if not (event_channel_id(member.guild.id, "voice_leave") or event_channel_id(member.guild.id, "voice_disconnect_admin")):
                return
            entry = await _recent_audit_entry(member.guild, discord.AuditLogAction.member_disconnect)
            if entry is not None and entry.user is not None:
                embed = self._embed(
                    i18n.t(
                        "serverlog.event.voice_disconnect_admin", lang,
                        member=member.mention, channel=before.channel.mention,
                    ),
                    discord.Color.red(), lang, member,
                )
                embed.add_field(
                    name=i18n.t("serverlog.field.by_whom", lang),
                    value=f"{entry.user.mention} ({entry.user})",
                    inline=False,
                )
                await self.emit(member.guild.id, "voice_disconnect_admin", embed)
            else:
                embed = self._embed(
                    i18n.t(
                        "serverlog.event.voice_leave", lang,
                        member=member.mention, channel=before.channel.mention,
                    ),
                    discord.Color.dark_grey(), lang, member,
                )
                await self.emit(member.guild.id, "voice_leave", embed)

        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            if not (event_channel_id(member.guild.id, "voice_move") or event_channel_id(member.guild.id, "voice_move_admin")):
                return
            entry = await _recent_audit_entry(member.guild, discord.AuditLogAction.member_move, channel=after.channel)
            if entry is not None and entry.user is not None:
                embed = self._embed(
                    i18n.t("serverlog.event.voice_move_admin", lang, member=member.mention),
                    discord.Color.red(), lang, member,
                )
                embed.add_field(name=i18n.t("serverlog.field.from", lang), value=before.channel.mention, inline=True)
                embed.add_field(name=i18n.t("serverlog.field.to", lang), value=after.channel.mention, inline=True)
                embed.add_field(
                    name=i18n.t("serverlog.field.by_whom", lang),
                    value=f"{entry.user.mention} ({entry.user})",
                    inline=False,
                )
                await self.emit(member.guild.id, "voice_move_admin", embed)
            else:
                embed = self._embed(
                    i18n.t("serverlog.event.voice_move_self", lang, member=member.mention),
                    discord.Color.teal(), lang, member,
                )
                embed.add_field(name=i18n.t("serverlog.field.from", lang), value=before.channel.mention, inline=True)
                embed.add_field(name=i18n.t("serverlog.field.to", lang), value=after.channel.mention, inline=True)
                await self.emit(member.guild.id, "voice_move", embed)

        else:
            changes = []
            if before.mute != after.mute:
                key = "serverlog.voice.muted" if after.mute else "serverlog.voice.unmuted"
                changes.append(i18n.t(key, lang))
            if before.deaf != after.deaf:
                key = "serverlog.voice.deafened" if after.deaf else "serverlog.voice.undeafened"
                changes.append(i18n.t(key, lang))
            if changes and after.channel is not None:
                embed = self._embed(
                    i18n.t("serverlog.event.voice_state", lang, member=member.mention),
                    discord.Color.dark_grey(), lang, member,
                )
                embed.add_field(name=i18n.t("serverlog.field.channel", lang), value=after.channel.mention, inline=False)
                embed.add_field(name=i18n.t("serverlog.field.changes", lang), value="\n".join(changes), inline=False)
                await self.emit(member.guild.id, "voice_state", embed)

    # ────────────────── Роли ──────────────────

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        lang = i18n.lang_for(role.guild.id)
        embed = self._embed(i18n.t("serverlog.event.role_create", lang, role=role.mention), discord.Color.green(), lang)
        embed.add_field(name=i18n.t("serverlog.field.role", lang), value=f"{role.mention} (`{role.id}`)", inline=False)
        await self.emit(role.guild.id, "role_create", embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        lang = i18n.lang_for(role.guild.id)
        embed = self._embed(i18n.t("serverlog.event.role_delete", lang, name=role.name), discord.Color.red(), lang)
        embed.add_field(name=i18n.t("serverlog.field.role", lang), value=f"{role.name} (`{role.id}`)", inline=False)
        await self.emit(role.guild.id, "role_delete", embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        lang = i18n.lang_for(after.guild.id)
        changes = []
        if before.name != after.name:
            changes.append(i18n.t("serverlog.role.name_change", lang, before=before.name, after=after.name))
        if before.color != after.color:
            changes.append(i18n.t("serverlog.role.color_change", lang, before=before.color, after=after.color))
        if before.permissions != after.permissions:
            changes.append(i18n.t("serverlog.role.permissions_changed", lang))
        if before.hoist != after.hoist:
            changes.append(i18n.t("serverlog.role.hoist", lang, value=after.hoist))
        if before.mentionable != after.mentionable:
            changes.append(i18n.t("serverlog.role.mentionable", lang, value=after.mentionable))
        if not changes:
            return
        embed = self._embed(i18n.t("serverlog.event.role_update", lang, role=after.mention), discord.Color.orange(), lang)
        embed.add_field(name=i18n.t("serverlog.field.role", lang), value=f"{after.mention} (`{after.id}`)", inline=False)
        embed.add_field(name=i18n.t("serverlog.field.changes", lang), value=_clip("\n".join(changes), lang), inline=False)
        await self.emit(after.guild.id, "role_update", embed)

    # ────────────────── Каналы ──────────────────

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        lang = i18n.lang_for(channel.guild.id)
        embed = self._embed(i18n.t("serverlog.event.channel_create", lang, channel=channel.mention), discord.Color.green(), lang)
        embed.add_field(name=i18n.t("serverlog.field.channel", lang), value=f"{channel.mention} (`{channel.id}`)", inline=False)
        await self.emit(channel.guild.id, "channel_create", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        lang = i18n.lang_for(channel.guild.id)
        embed = self._embed(i18n.t("serverlog.event.channel_delete", lang, name=channel.name), discord.Color.red(), lang)
        embed.add_field(name=i18n.t("serverlog.field.channel", lang), value=f"#{channel.name} (`{channel.id}`)", inline=False)
        await self.emit(channel.guild.id, "channel_delete", embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        lang = i18n.lang_for(after.guild.id)
        changes = []
        if before.name != after.name:
            changes.append(i18n.t("serverlog.channel.name_change", lang, before=before.name, after=after.name))
        if getattr(before, "topic", None) != getattr(after, "topic", None):
            changes.append(i18n.t("serverlog.channel.topic_changed", lang))
        if changes:
            embed = self._embed(i18n.t("serverlog.event.channel_update", lang, channel=after.mention), discord.Color.orange(), lang)
            embed.add_field(name=i18n.t("serverlog.field.channel", lang), value=f"{after.mention} (`{after.id}`)", inline=False)
            embed.add_field(name=i18n.t("serverlog.field.changes", lang), value=_clip("\n".join(changes), lang), inline=False)
            await self.emit(after.guild.id, "channel_update", embed)

        if before.overwrites != after.overwrites:
            embed = self._embed(
                i18n.t("serverlog.event.channel_permissions", lang, channel=after.mention),
                discord.Color.orange(), lang,
            )
            embed.add_field(name=i18n.t("serverlog.field.channel", lang), value=f"{after.mention} (`{after.id}`)", inline=False)
            await self.emit(after.guild.id, "channel_permissions_update", embed)

    # ────────────────── Треды ──────────────────

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        lang = i18n.lang_for(thread.guild.id)
        embed = self._embed(i18n.t("serverlog.event.thread_create", lang, thread=thread.mention), discord.Color.green(), lang)
        embed.add_field(name=i18n.t("serverlog.field.thread", lang), value=f"{thread.mention} (`{thread.id}`)", inline=False)
        parent = thread.parent
        if parent is not None:
            embed.add_field(name=i18n.t("serverlog.field.channel", lang), value=parent.mention, inline=False)
        await self.emit(thread.guild.id, "thread_create", embed)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        lang = i18n.lang_for(thread.guild.id)
        embed = self._embed(i18n.t("serverlog.event.thread_delete", lang, name=thread.name), discord.Color.red(), lang)
        embed.add_field(name=i18n.t("serverlog.field.thread", lang), value=f"{thread.name} (`{thread.id}`)", inline=False)
        await self.emit(thread.guild.id, "thread_delete", embed)

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        lang = i18n.lang_for(after.guild.id)
        changes = []
        if before.name != after.name:
            changes.append(i18n.t("serverlog.thread.name_change", lang, before=before.name, after=after.name))
        if before.archived != after.archived:
            key = "serverlog.thread.archived" if after.archived else "serverlog.thread.unarchived"
            changes.append(i18n.t(key, lang))
        if before.locked != after.locked:
            key = "serverlog.thread.locked" if after.locked else "serverlog.thread.unlocked"
            changes.append(i18n.t(key, lang))
        if not changes:
            return
        embed = self._embed(i18n.t("serverlog.event.thread_update", lang, thread=after.mention), discord.Color.orange(), lang)
        embed.add_field(name=i18n.t("serverlog.field.thread", lang), value=f"{after.mention} (`{after.id}`)", inline=False)
        embed.add_field(name=i18n.t("serverlog.field.changes", lang), value=_clip("\n".join(changes), lang), inline=False)
        await self.emit(after.guild.id, "thread_update", embed)

    # ────────────────── Сервер ──────────────────

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        lang = i18n.lang_for(after.id)
        changes = []
        if before.name != after.name:
            changes.append(i18n.t("serverlog.guild.name_change", lang, before=before.name, after=after.name))
        if before.icon != after.icon:
            changes.append(i18n.t("serverlog.guild.icon_changed", lang))
        if before.verification_level != after.verification_level:
            changes.append(i18n.t(
                "serverlog.guild.verification_change", lang,
                before=before.verification_level, after=after.verification_level,
            ))
        if before.afk_channel != after.afk_channel:
            changes.append(i18n.t("serverlog.guild.afk_changed", lang))
        if before.system_channel != after.system_channel:
            changes.append(i18n.t("serverlog.guild.system_channel_changed", lang))
        if not changes:
            return
        embed = self._embed(i18n.t("serverlog.event.guild_update", lang), discord.Color.orange(), lang)
        embed.add_field(name=i18n.t("serverlog.field.changes", lang), value=_clip("\n".join(changes), lang), inline=False)
        await self.emit(after.id, "guild_update", embed)

    # ────────────────── Команды модерации ──────────────────

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command):
        if not isinstance(command, app_commands.Command) or not _is_moderation_command(command):
            return
        if interaction.guild is None:
            return
        lang = i18n.lang_for(interaction.guild.id)
        embed = self._embed(
            i18n.t("serverlog.event.moderation_command", lang, user=interaction.user.mention),
            discord.Color.blurple(), lang, interaction.user,
        )
        embed.add_field(name=i18n.t("serverlog.field.command", lang), value=f"`/{command.qualified_name}`", inline=False)
        channel = interaction.channel
        if channel is not None:
            embed.add_field(
                name=i18n.t("serverlog.field.channel", lang),
                value=getattr(channel, "mention", str(channel)),
                inline=False,
            )
        await self.emit(interaction.guild.id, "moderation_command", embed)

    # ────────────────── Эмодзи и приглашения ──────────────────

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before, after):
        lang = i18n.lang_for(guild.id)
        added = [e for e in after if e not in before]
        removed = [e for e in before if e not in after]
        if not added and not removed:
            return
        embed = self._embed(i18n.t("serverlog.event.emoji_update", lang), discord.Color.blurple(), lang)
        if added:
            embed.add_field(name=i18n.t("serverlog.field.added", lang), value=_clip(" ".join(str(e) for e in added[:20]), lang), inline=False)
        if removed:
            embed.add_field(name=i18n.t("serverlog.field.removed", lang), value=_clip(", ".join(e.name for e in removed[:20]), lang), inline=False)
        await self.emit(guild.id, "emoji_update", embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        lang = i18n.lang_for(invite.guild.id)
        if invite.inviter:
            desc = i18n.t("serverlog.event.invite_create", lang, inviter=invite.inviter.mention)
        else:
            desc = i18n.t("serverlog.event.invite_create_anon", lang)
        embed = self._embed(desc, discord.Color.green(), lang, invite.inviter)
        embed.add_field(name=i18n.t("serverlog.field.code", lang), value=f"`{invite.code}`", inline=True)
        if invite.channel:
            embed.add_field(
                name=i18n.t("serverlog.field.channel", lang),
                value=getattr(invite.channel, "mention", str(invite.channel)),
                inline=True,
            )
        if invite.max_uses:
            embed.add_field(name=i18n.t("serverlog.field.max_uses", lang), value=str(invite.max_uses), inline=True)
        await self.emit(invite.guild.id, "invite_create", embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        lang = i18n.lang_for(invite.guild.id)
        embed = self._embed(i18n.t("serverlog.event.invite_delete", lang), discord.Color.red(), lang)
        embed.add_field(name=i18n.t("serverlog.field.code", lang), value=f"`{invite.code}`", inline=True)
        await self.emit(invite.guild.id, "invite_delete", embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerLog(bot))
