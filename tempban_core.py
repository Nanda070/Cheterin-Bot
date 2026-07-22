"""Tempban: DM customization + fixed log embed (not dashboard-editable)."""

from __future__ import annotations

import discord

import i18n
import settings_db
from message_template_core import substitute

MODULE_NAME = "tempban_messages"

# Fixed ban reason for Discord API + recovery after bot restart (do not customize).
BAN_REASON_MARKER = "chetbot:tempban:v1"
LEGACY_BAN_REASONS = (
    "Автоматический Tempban (Сброс сообщений за 20 мин.)",
    "Automatic Tempban (20 min message purge)",
)


def _load_raw(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return data if isinstance(data, dict) else {}


def save_settings(guild_id: int, data: dict) -> None:
    # Preserve legacy log_embed in storage if present, but never use it for rendering.
    raw = _load_raw(guild_id)
    payload = {
        "dm_enabled": bool(data.get("dm_enabled", True)),
        "dm_message": str(data.get("dm_message") or ""),
        "log_enabled": bool(data.get("log_enabled", True)),
        "unban_reason": str(data.get("unban_reason") or ""),
    }
    if "log_embed" in raw:
        payload["log_embed"] = raw["log_embed"]
    settings_db.put(guild_id, MODULE_NAME, payload)


def get_settings(guild_id: int) -> dict:
    raw = _load_raw(guild_id)
    lang = i18n.lang_for(guild_id)
    dm_message = str(raw.get("dm_message") or "").strip()
    unban = str(raw.get("unban_reason") or "").strip()
    return {
        "dm_enabled": bool(raw.get("dm_enabled", True)),
        "dm_message": dm_message or default_dm_message(lang),
        "log_enabled": bool(raw.get("log_enabled", True)),
        "unban_reason": unban or i18n.t("tempban.unban_reason", lang),
    }


def is_tempban_ban_reason(reason: str | None) -> bool:
    if not reason:
        return False
    if reason == BAN_REASON_MARKER:
        return True
    return reason in LEGACY_BAN_REASONS


def ban_reason_for_api() -> str:
    return BAN_REASON_MARKER


def dm_variables(member, guild, invite_link: str) -> dict[str, str]:
    return {
        "mention": member.mention,
        "name": member.display_name,
        "guild": guild.name,
        "guild_name": guild.name,
        "invite": invite_link,
        "user_id": str(member.id),
    }


def default_dm_message(lang: str) -> str:
    return i18n.t("tempban.dm_message", lang)


def build_log_embed(lang: str, variables: dict[str, str]) -> discord.Embed:
    """Fixed Tempban log layout — always the same structure as the product screenshot."""
    embed = discord.Embed(
        title=i18n.t("tempban.embed.title", lang),
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(
        name=i18n.t("tempban.embed.user", lang),
        value=f"{variables['name']} (ID: {variables['user_id']})",
        inline=False,
    )
    embed.add_field(
        name=i18n.t("tempban.embed.ban_time", lang),
        value=variables["ban_time"],
        inline=True,
    )
    embed.add_field(
        name=i18n.t("tempban.embed.unban_time", lang),
        value=variables["unban_time"],
        inline=True,
    )
    embed.add_field(
        name=i18n.t("tempban.embed.channel", lang),
        value=variables["channel"],
        inline=False,
    )
    embed.add_field(
        name=i18n.t("tempban.embed.dm_status", lang),
        value=variables["dm_status"],
        inline=True,
    )
    embed.add_field(
        name=i18n.t("tempban.embed.message", lang),
        value=variables["message_preview"] or "—",
        inline=False,
    )
    embed.set_footer(text=i18n.t("tempban.embed.footer", lang))
    return embed


def unban_reason(settings: dict, lang: str) -> str:
    custom = (settings.get("unban_reason") or "").strip()
    if custom:
        return substitute(custom, {})
    return i18n.t("tempban.unban_reason", lang)
