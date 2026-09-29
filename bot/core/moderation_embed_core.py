"""Unified Discord embeds for the moderation log channel.

Layout: Who / Target / Reason (if set) / Details (if set) — same as slash commands
and dashboard manual actions. Prefer this over ad-hoc Embed field layouts.
"""

from __future__ import annotations

from typing import Any

import discord

import bot.core.embed_style as embed_style
import bot.core.i18n as i18n
import bot.modules.moderation.moderation_commands_core as moderation_commands_core


def actor_ref(
    actor: Any | None,
    *,
    lang: str,
    automatic_key: str = "moderation.embed.automatic",
) -> str:
    """Format moderator/system actor for the Who field."""
    if actor is None:
        return i18n.t(automatic_key, lang)
    name = getattr(actor, "name", None) or getattr(actor, "display_name", None) or str(getattr(actor, "id", "?"))
    user_id = getattr(actor, "id", None)
    mention = getattr(actor, "mention", None)
    if user_id is None:
        return str(name)
    return moderation_commands_core.format_user_ref(str(name), int(user_id), mention)


def target_ref(
    *,
    name: str,
    user_id: int,
    mention: str | None = None,
) -> str:
    return moderation_commands_core.format_user_ref(name, user_id, mention)


def build_action_log_embed(
    lang: str,
    *,
    title: str,
    who_value: str,
    target_value: str,
    reason: str = "",
    extra: str = "",
    color: discord.Color | int | None = None,
    footer: str | None = None,
    timestamp: Any | None = None,
) -> discord.Embed:
    """Build a Who/Target/Reason/Details embed for the guild log channel."""
    color = embed_style.as_color(color, default=embed_style.DANGER)

    embed = discord.Embed(
        title=(title or "")[:256],
        color=color,
        timestamp=timestamp if timestamp is not None else discord.utils.utcnow(),
    )
    for name, value in moderation_commands_core.action_log_fields(
        lang,
        who_value,
        target_value,
        reason=reason,
        extra=extra,
    ):
        embed.add_field(name=name, value=str(value)[:1024], inline=False)
    if footer:
        embed.set_footer(text=footer[:2048])
    return embed


def build_user_action_embed(
    lang: str,
    *,
    title: str,
    actor: Any | None,
    target_name: str,
    target_id: int,
    target_mention: str | None = None,
    reason: str = "",
    extra: str = "",
    color: discord.Color | int | None = None,
    footer_key: str = "moderation.embed.footer",
    timestamp: Any | None = None,
) -> discord.Embed:
    """Convenience: format actor + target refs then build_action_log_embed."""
    return build_action_log_embed(
        lang,
        title=title,
        who_value=actor_ref(actor, lang=lang),
        target_value=target_ref(name=target_name, user_id=target_id, mention=target_mention),
        reason=reason,
        extra=extra,
        color=color,
        footer=i18n.t(footer_key, lang),
        timestamp=timestamp,
    )
