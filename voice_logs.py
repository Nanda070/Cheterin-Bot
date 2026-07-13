import logging

import discord

import bot_config

logger = logging.getLogger("voice-rooms")


class VCTheme:
    COLOR = discord.Color.from_str("#B75CFF")
    SUCCESS = discord.Color.green()
    WARN = discord.Color.orange()
    ERROR = discord.Color.red()

    EMO = {
        "openroom": discord.PartialEmoji(name="openroom", id=1424844208371667187),
        "name": discord.PartialEmoji(name="name", id=1424828518516260864),
        "miceoff": discord.PartialEmoji(name="miceoff", id=1424847908842504375),
        "mice": discord.PartialEmoji(name="mice", id=1424828555522736138),
        "lockuser": discord.PartialEmoji(name="lockuser", id=1424828572123795467),
        "lock": discord.PartialEmoji(name="lock", id=1424828596190580786),
        "limit": discord.PartialEmoji(name="limit", id=1424828623658946692),
        "kick": discord.PartialEmoji(name="kick", id=1424828642500018207),
        "owner": discord.PartialEmoji(name="human", id=1424828659415384075),
        "404": discord.PartialEmoji(name="404", id=1387913004850483341),
    }


def get_log_channel_id() -> int:
    raw = bot_config.get("VOICE_LOG_CHANNEL_ID") or bot_config.get("LOG_CHANNEL_ID")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


async def send_log_embed(bot: discord.Client, title: str, description: str, color: discord.Color):
    log_channel_id = get_log_channel_id()
    channel = bot.get_channel(log_channel_id)
    if not channel:
        logger.warning("Log channel not found: %s", log_channel_id)
        return

    embed = discord.Embed(title=title, description=description, color=color)
    await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())


async def log_action(bot: discord.Client, actor: discord.abc.User | None, action: str, channel: discord.VoiceChannel | None = None, target: discord.abc.User | None = None, color: discord.Color | None = None):
    lines = []
    if actor: lines.append(f"**Кто:** {actor.mention} (`{actor.id}`)")
    if channel: lines.append(f"**Канал:** {channel.name} (`{channel.id}`)")
    if target: lines.append(f"**Цель:** {target.mention} (`{target.id}`)")
    lines.append(f"**Действие:** {action}")

    await send_log_embed(bot, "Лог приватных комнат", "\n".join(lines), color or VCTheme.COLOR)


async def log_security(bot: discord.Client, actor: discord.abc.User | None, reason: str, channel: discord.VoiceChannel | None = None):
    lines = []
    if actor: lines.append(f"**Пользователь:** {actor.mention} (`{actor.id}`)")
    if channel: lines.append(f"**Канал:** {channel.name} (`{channel.id}`)")
    lines.append(f"**Событие:** {reason}")

    await send_log_embed(bot, "Безопасность / отклонённое действие", "\n".join(lines), VCTheme.ERROR)


async def log_error(bot: discord.Client, context: str, exc: Exception):
    await send_log_embed(bot, "Ошибка", f"**Контекст:** {context}\n**Ошибка:** `{type(exc).__name__}: {exc}`", VCTheme.ERROR)


async def log_unhide_action(bot: discord.Client, actor: discord.Member, channel: discord.VoiceChannel):
    await log_action(
        bot,
        actor=actor,
        action="Попытка скрыть канал (бот автоматически вернул видимость)",
        channel=channel,
        color=VCTheme.WARN
    )
