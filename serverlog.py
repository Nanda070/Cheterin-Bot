"""Тотальное логирование событий сервера.

Каждый тип события включается отдельно и может писать в свой канал.
Настраивается из дашборда (раздел «Логирование»), хранение — serverlog_config.json.
"""

import json
import logging
import os

import discord
from discord.ext import commands

logger = logging.getLogger("serverlog")

CONFIG_FILE = "serverlog_config.json"

# Тип события -> подпись для дашборда. Порядок = порядок в панели.
EVENT_TYPES: dict[str, str] = {
    "message_edit": "Редактирование сообщений",
    "message_delete": "Удаление сообщений",
    "member_join": "Вход участника на сервер",
    "member_leave": "Выход участника с сервера",
    "member_ban": "Бан участника",
    "member_unban": "Разбан участника",
    "nickname_change": "Смена никнейма",
    "roles_change": "Изменение ролей участника",
    "voice_join": "Вход в голосовой канал",
    "voice_leave": "Выход из голосового канала",
    "voice_move": "Перемещение между голосовыми",
    "voice_state": "Мут/деф в голосовых",
    "role_create": "Создание роли",
    "role_delete": "Удаление роли",
    "role_update": "Изменение роли",
    "channel_create": "Создание канала",
    "channel_delete": "Удаление канала",
    "channel_update": "Изменение канала",
    "emoji_update": "Изменение эмодзи",
    "invite_create": "Создание приглашения",
    "invite_delete": "Удаление приглашения",
}

MAX_CONTENT = 1000

_cache: dict | None = None
_cache_mtime: float | None = None


def load_config() -> dict:
    global _cache, _cache_mtime
    if not os.path.exists(CONFIG_FILE):
        _cache, _cache_mtime = None, None
        return {}

    mtime = os.path.getmtime(CONFIG_FILE)
    if _cache is not None and _cache_mtime == mtime:
        return _cache

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    _cache, _cache_mtime = data, mtime
    return data


def save_config(data: dict) -> None:
    global _cache, _cache_mtime
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    _cache = data
    _cache_mtime = os.path.getmtime(CONFIG_FILE)


def get_settings() -> dict:
    """Полные настройки с дефолтами по каждому типу события."""
    data = load_config()
    events = data.get("events", {})
    result = {}
    for event_type in EVENT_TYPES:
        entry = events.get(event_type, {})
        result[event_type] = {
            "enabled": bool(entry.get("enabled", False)),
            "channel_id": str(entry.get("channel_id") or ""),
        }
    return {"events": result}


def event_channel_id(event_type: str) -> int:
    """ID канала для типа события, 0 если тип выключен или канал не задан."""
    entry = get_settings()["events"].get(event_type)
    if not entry or not entry["enabled"]:
        return 0
    try:
        return int(entry["channel_id"])
    except (TypeError, ValueError):
        return 0


def _clip(text: str | None) -> str:
    if not text:
        return "*пусто*"
    return text if len(text) <= MAX_CONTENT else text[:MAX_CONTENT] + "…"


class ServerLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def emit(self, event_type: str, embed: discord.Embed):
        channel_id = event_channel_id(event_type)
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            return
        try:
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException as exc:
            logger.warning("Не удалось отправить лог %s: %s", event_type, exc)

    def _embed(self, title: str, color: discord.Color, member: discord.abc.User | None = None) -> discord.Embed:
        embed = discord.Embed(title=title, color=color, timestamp=discord.utils.utcnow())
        if member is not None:
            embed.set_author(name=f"{member} ({member.id})", icon_url=member.display_avatar.url)
        return embed

    # ────────────────── Сообщения ──────────────────

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.guild is None:
            return
        if before.content == after.content:
            return
        embed = self._embed("✏️ Сообщение отредактировано", discord.Color.orange(), before.author)
        embed.add_field(name="Канал", value=before.channel.mention, inline=False)
        embed.add_field(name="До", value=_clip(before.content), inline=False)
        embed.add_field(name="После", value=_clip(after.content), inline=False)
        embed.add_field(name="Ссылка", value=f"[Перейти]({after.jump_url})", inline=False)
        await self.emit("message_edit", embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        embed = self._embed("🗑️ Сообщение удалено", discord.Color.red(), message.author)
        embed.add_field(name="Канал", value=message.channel.mention, inline=False)
        embed.add_field(name="Содержимое", value=_clip(message.content), inline=False)
        if message.attachments:
            names = ", ".join(a.filename for a in message.attachments[:5])
            embed.add_field(name="Вложения", value=_clip(names), inline=False)
        await self.emit("message_delete", embed)

    # ────────────────── Участники ──────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = self._embed("📥 Участник зашёл", discord.Color.green(), member)
        embed.add_field(name="Аккаунт создан", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Участников", value=str(member.guild.member_count), inline=True)
        await self.emit("member_join", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = self._embed("📤 Участник вышел", discord.Color.dark_grey(), member)
        roles = [r.mention for r in member.roles if not r.is_default()]
        if roles:
            embed.add_field(name="Роли", value=_clip(" ".join(roles)), inline=False)
        await self.emit("member_leave", embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.abc.User):
        embed = self._embed("🔨 Участник забанен", discord.Color.dark_red(), user)
        await self.emit("member_ban", embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        embed = self._embed("🕊️ Участник разбанен", discord.Color.green(), user)
        await self.emit("member_unban", embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.nick != after.nick:
            embed = self._embed("📛 Никнейм изменён", discord.Color.blurple(), after)
            embed.add_field(name="До", value=_clip(before.nick or before.name), inline=True)
            embed.add_field(name="После", value=_clip(after.nick or after.name), inline=True)
            await self.emit("nickname_change", embed)

        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            if added or removed:
                embed = self._embed("🎭 Роли участника изменены", discord.Color.blurple(), after)
                if added:
                    embed.add_field(name="Выданы", value=_clip(" ".join(r.mention for r in added)), inline=False)
                if removed:
                    embed.add_field(name="Сняты", value=_clip(" ".join(r.mention for r in removed)), inline=False)
                await self.emit("roles_change", embed)

    # ────────────────── Войс ──────────────────

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        if before.channel is None and after.channel is not None:
            embed = self._embed("🔊 Зашёл в голосовой", discord.Color.green(), member)
            embed.add_field(name="Канал", value=after.channel.mention, inline=False)
            await self.emit("voice_join", embed)
        elif before.channel is not None and after.channel is None:
            embed = self._embed("🔇 Вышел из голосового", discord.Color.dark_grey(), member)
            embed.add_field(name="Канал", value=before.channel.mention, inline=False)
            await self.emit("voice_leave", embed)
        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            embed = self._embed("↔️ Перешёл между голосовыми", discord.Color.blurple(), member)
            embed.add_field(name="Из", value=before.channel.mention, inline=True)
            embed.add_field(name="В", value=after.channel.mention, inline=True)
            await self.emit("voice_move", embed)
        else:
            changes = []
            if before.self_mute != after.self_mute:
                changes.append("🎙️ выключил микрофон" if after.self_mute else "🎙️ включил микрофон")
            if before.self_deaf != after.self_deaf:
                changes.append("🎧 выключил звук" if after.self_deaf else "🎧 включил звук")
            if before.mute != after.mute:
                changes.append("замьючен сервером" if after.mute else "размьючен сервером")
            if before.deaf != after.deaf:
                changes.append("заглушен сервером" if after.deaf else "разглушен сервером")
            if changes and after.channel is not None:
                embed = self._embed("🎚️ Изменение состояния в войсе", discord.Color.dark_grey(), member)
                embed.add_field(name="Канал", value=after.channel.mention, inline=False)
                embed.add_field(name="Изменения", value="\n".join(changes), inline=False)
                await self.emit("voice_state", embed)

    # ────────────────── Роли ──────────────────

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        embed = self._embed("➕ Роль создана", discord.Color.green())
        embed.add_field(name="Роль", value=f"{role.mention} (`{role.id}`)", inline=False)
        await self.emit("role_create", embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        embed = self._embed("➖ Роль удалена", discord.Color.red())
        embed.add_field(name="Роль", value=f"{role.name} (`{role.id}`)", inline=False)
        await self.emit("role_delete", embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        changes = []
        if before.name != after.name:
            changes.append(f"Название: **{before.name}** → **{after.name}**")
        if before.color != after.color:
            changes.append(f"Цвет: `{before.color}` → `{after.color}`")
        if before.permissions != after.permissions:
            changes.append("Права изменены")
        if before.hoist != after.hoist:
            changes.append(f"Отдельное отображение: {after.hoist}")
        if before.mentionable != after.mentionable:
            changes.append(f"Упоминаемость: {after.mentionable}")
        if not changes:
            return
        embed = self._embed("🎭 Роль изменена", discord.Color.orange())
        embed.add_field(name="Роль", value=f"{after.mention} (`{after.id}`)", inline=False)
        embed.add_field(name="Изменения", value=_clip("\n".join(changes)), inline=False)
        await self.emit("role_update", embed)

    # ────────────────── Каналы ──────────────────

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        embed = self._embed("➕ Канал создан", discord.Color.green())
        embed.add_field(name="Канал", value=f"{channel.mention} (`{channel.id}`)", inline=False)
        await self.emit("channel_create", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        embed = self._embed("➖ Канал удалён", discord.Color.red())
        embed.add_field(name="Канал", value=f"#{channel.name} (`{channel.id}`)", inline=False)
        await self.emit("channel_delete", embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        changes = []
        if before.name != after.name:
            changes.append(f"Название: **#{before.name}** → **#{after.name}**")
        if getattr(before, "topic", None) != getattr(after, "topic", None):
            changes.append("Описание изменено")
        if before.overwrites != after.overwrites:
            changes.append("Права доступа изменены")
        if not changes:
            return
        embed = self._embed("🔧 Канал изменён", discord.Color.orange())
        embed.add_field(name="Канал", value=f"{after.mention} (`{after.id}`)", inline=False)
        embed.add_field(name="Изменения", value=_clip("\n".join(changes)), inline=False)
        await self.emit("channel_update", embed)

    # ────────────────── Эмодзи и приглашения ──────────────────

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before, after):
        added = [e for e in after if e not in before]
        removed = [e for e in before if e not in after]
        if not added and not removed:
            return
        embed = self._embed("😀 Эмодзи изменены", discord.Color.blurple())
        if added:
            embed.add_field(name="Добавлены", value=_clip(" ".join(str(e) for e in added[:20])), inline=False)
        if removed:
            embed.add_field(name="Удалены", value=_clip(", ".join(e.name for e in removed[:20])), inline=False)
        await self.emit("emoji_update", embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        embed = self._embed("🔗 Приглашение создано", discord.Color.green(), invite.inviter)
        embed.add_field(name="Код", value=f"`{invite.code}`", inline=True)
        if invite.channel:
            embed.add_field(name="Канал", value=getattr(invite.channel, "mention", str(invite.channel)), inline=True)
        if invite.max_uses:
            embed.add_field(name="Макс. использований", value=str(invite.max_uses), inline=True)
        await self.emit("invite_create", embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        embed = self._embed("🔗 Приглашение удалено", discord.Color.red())
        embed.add_field(name="Код", value=f"`{invite.code}`", inline=True)
        await self.emit("invite_delete", embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerLog(bot))
