"""Tempban message customization."""

from __future__ import annotations

import settings_db
from message_template_core import embed_spec_has_content, normalize_embed_spec, substitute, substitute_embed_spec
from embed_builder import build_embed

import i18n

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
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    raw = _load_raw(guild_id)
    return {
        "dm_enabled": bool(raw.get("dm_enabled", True)),
        "dm_message": str(raw.get("dm_message") or ""),
        "log_enabled": bool(raw.get("log_enabled", True)),
        "log_embed": normalize_embed_spec(raw.get("log_embed")),
        "unban_reason": str(raw.get("unban_reason") or ""),
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
    return i18n.t("tempban.dm_message", lang, guild="{guild}", invite="{invite}")


def default_log_embed_spec(lang: str) -> dict:
    return {
        "title": i18n.t("tempban.embed.title", lang),
        "description": "",
        "color": "#ED4245",
        "author": {"name": "", "url": "", "icon_url": ""},
        "footer": {"text": i18n.t("tempban.embed.footer", lang), "icon_url": ""},
        "image": {"url": ""},
        "thumbnail": {"url": ""},
        "timestamp": True,
        "fields": [
            {"name": i18n.t("tempban.embed.user", lang), "value": "{name} (ID: {user_id})", "inline": False},
            {"name": i18n.t("tempban.embed.ban_time", lang), "value": "{ban_time}", "inline": True},
            {"name": i18n.t("tempban.embed.unban_time", lang), "value": "{unban_time}", "inline": True},
            {"name": i18n.t("tempban.embed.channel", lang), "value": "{channel}", "inline": False},
            {"name": i18n.t("tempban.embed.dm_status", lang), "value": "{dm_status}", "inline": True},
            {"name": i18n.t("tempban.embed.message", lang), "value": "{message_preview}", "inline": False},
        ],
    }


def build_log_embed(settings: dict, lang: str, variables: dict[str, str]):
    spec = settings.get("log_embed") or {}
    if not embed_spec_has_content(spec):
        spec = default_log_embed_spec(lang)
    spec = substitute_embed_spec(spec, variables)
    embed = build_embed(spec)
    if spec.get("timestamp") or (settings.get("log_embed") or {}).get("timestamp"):
        embed.timestamp = __import__("discord").utils.utcnow()
    return embed


def unban_reason(settings: dict, lang: str) -> str:
    custom = (settings.get("unban_reason") or "").strip()
    if custom:
        return substitute(custom, {})
    return i18n.t("tempban.unban_reason", lang)
