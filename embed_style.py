"""Shared Discord embed styling for bot-authored messages.

Semantic palette (Discord UI colors) plus Cheterin brand accent.
User-authored EmbedSpec (builder / welcome / feedback) keeps caller colors;
empty-spec defaults use ACCENT_HEX on the frontend.

Theme exceptions (Wordle green, Twitch/YouTube) stay module-specific.
"""

from __future__ import annotations

from typing import Any

import discord

# Brand (profile cards, empty EmbedSpec default, accent moments)
ACCENT_HEX = "#D44556"
ACCENT_RGB = (212, 69, 86)
ACCENT_INT = 0xD44556
ACCENT = discord.Color(ACCENT_INT)

# Semantic — Discord brand palette (same hex as Discord client UI)
INFO_INT = 0x5865F2
SUCCESS_INT = 0x57F287
DANGER_INT = 0xED4245
WARN_INT = 0xE67E22
GOLD_INT = 0xFEE75C
NEUTRAL_INT = 0x2B2D31
MUTED_INT = 0x99AAB5
TEAL_INT = 0x1ABC9C

INFO = discord.Color(INFO_INT)
SUCCESS = discord.Color(SUCCESS_INT)
DANGER = discord.Color(DANGER_INT)
WARN = discord.Color(WARN_INT)
GOLD = discord.Color(GOLD_INT)
NEUTRAL = discord.Color(NEUTRAL_INT)
MUTED = discord.Color(MUTED_INT)
TEAL = discord.Color(TEAL_INT)

# Kept theme identities (not forced to brand/semantic)
WORDLE = discord.Color(0x538D4E)
VALORANT = discord.Color(0xFF4655)
TWITCH = discord.Color(0x9146FF)
YOUTUBE = DANGER


def as_color(value: discord.Color | int | None, *, default: discord.Color = INFO) -> discord.Color:
    if value is None:
        return default
    if isinstance(value, discord.Color):
        return value
    return discord.Color(int(value))


def make_embed(
    *,
    title: str | None = None,
    description: str | None = None,
    color: discord.Color | int | None = INFO,
    url: str | None = None,
    footer: str | None = None,
    footer_icon: str | None = None,
    thumbnail: str | None = None,
    image: str | None = None,
    author_name: str | None = None,
    author_icon: str | None = None,
    author_url: str | None = None,
    timestamp: bool | Any = True,
) -> discord.Embed:
    """Build a bot embed with shared defaults (timestamp on by default)."""
    embed = discord.Embed(
        title=(title[:256] if title else None),
        description=(description[:4096] if description else None),
        color=as_color(color),
        url=url or None,
    )
    if timestamp is True:
        embed.timestamp = discord.utils.utcnow()
    elif timestamp not in (False, None):
        embed.timestamp = timestamp
    if footer:
        embed.set_footer(text=footer[:2048], icon_url=footer_icon or None)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)
    if author_name:
        embed.set_author(name=author_name[:256], icon_url=author_icon or None, url=author_url or None)
    return embed


def module_footer(module: str, detail: str = "") -> str:
    """Footer chrome: ``Moderation · Command`` style."""
    module = (module or "").strip()
    detail = (detail or "").strip()
    if module and detail:
        return f"{module} · {detail}"[:2048]
    return (module or detail)[:2048]
