"""Spam trap / honeypot: action modes, custom messages, ban counter, warning panel."""

from __future__ import annotations

import re

import discord

import bot.core.embed_style as embed_style
import bot.core.i18n as i18n
import bot.core.moderation_embed_core as moderation_embed_core
import bot.core.settings_db as settings_db
from bot.core.message_template_core import substitute

MODULE_NAME = "tempban_messages"

ACTION_SOFTBAN = "softban"
ACTION_BAN = "ban"
ACTION_DISABLED = "disabled"
ACTION_MODES = frozenset({ACTION_SOFTBAN, ACTION_BAN, ACTION_DISABLED})

# Softban marker — recovery on_ready will unban these after bot restart.
BAN_REASON_MARKER = "chetbot:tempban:v1"
# Permanent ban marker — must NOT be auto-unbanned on restart.
PERMANENT_BAN_REASON_MARKER = "chetbot:tempban:permanent:v1"
LEGACY_BAN_REASONS = (
    "Автоматический Tempban (Сброс сообщений за 20 мин.)",
    "Automatic Tempban (20 min message purge)",
)

_DOUBLE_BRACE_RE = re.compile(r"\{\{([a-zA-Z0-9_]+)(?::[^}]*)?\}\}")


def render_template(text: str, variables: dict[str, str]) -> str:
    """Substitute `{var}`, `{{var}}`, and `{{var:hint}}` placeholders."""
    if not text:
        return text

    def repl_double(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    out = _DOUBLE_BRACE_RE.sub(repl_double, text)
    return substitute(out, variables)


def _load_raw(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return data if isinstance(data, dict) else {}


def _normalize_action(raw) -> str:
    action = str(raw or ACTION_SOFTBAN).strip().lower()
    if action not in ACTION_MODES:
        return ACTION_SOFTBAN
    return action


def save_settings(guild_id: int, data: dict) -> None:
    raw = _load_raw(guild_id)
    # Preserve counters / message ids unless explicitly provided
    ban_count = raw.get("ban_count", 0)
    if "ban_count" in data:
        try:
            ban_count = max(0, int(data["ban_count"]))
        except (TypeError, ValueError):
            ban_count = 0

    warning_message_id = raw.get("warning_message_id") or ""
    if "warning_message_id" in data:
        warning_message_id = str(data.get("warning_message_id") or "")

    payload = {
        "action": _normalize_action(data.get("action", raw.get("action", ACTION_SOFTBAN))),
        "dm_enabled": bool(data.get("dm_enabled", True)),
        "dm_message": str(data.get("dm_message") or ""),
        "log_enabled": bool(data.get("log_enabled", True)),
        "log_message": str(data.get("log_message") or ""),
        "unban_reason": str(data.get("unban_reason") or ""),
        "warning_message": str(data.get("warning_message") or ""),
        "warning_thumbnail_url": str(data.get("warning_thumbnail_url") or ""),
        "warning_message_id": warning_message_id,
        "ban_count": ban_count,
    }
    if "log_embed" in raw:
        payload["log_embed"] = raw["log_embed"]
    settings_db.put(guild_id, MODULE_NAME, payload)


def get_settings(guild_id: int) -> dict:
    raw = _load_raw(guild_id)
    lang = i18n.lang_for(guild_id)
    dm_message = str(raw.get("dm_message") or "").strip()
    unban = str(raw.get("unban_reason") or "").strip()
    warning = str(raw.get("warning_message") or "").strip()
    log_message = str(raw.get("log_message") or "").strip()
    try:
        ban_count = max(0, int(raw.get("ban_count", 0)))
    except (TypeError, ValueError):
        ban_count = 0
    warning_message_id = str(raw.get("warning_message_id") or "").strip()
    if warning_message_id and not warning_message_id.isdigit():
        warning_message_id = ""

    return {
        "action": _normalize_action(raw.get("action")),
        "dm_enabled": bool(raw.get("dm_enabled", True)),
        "dm_message": dm_message or default_dm_message(lang),
        "log_enabled": bool(raw.get("log_enabled", True)),
        "log_message": log_message,
        "unban_reason": unban or i18n.t("tempban.unban_reason", lang),
        "warning_message": warning or default_warning_message(lang),
        "warning_thumbnail_url": str(raw.get("warning_thumbnail_url") or "").strip(),
        "warning_message_id": warning_message_id,
        "ban_count": ban_count,
    }


def increment_ban_count(guild_id: int) -> int:
    raw = _load_raw(guild_id)
    try:
        count = max(0, int(raw.get("ban_count", 0)))
    except (TypeError, ValueError):
        count = 0
    count += 1
    raw["ban_count"] = count
    settings_db.put(guild_id, MODULE_NAME, raw)
    return count


def set_warning_message_id(guild_id: int, message_id: int | str | None) -> None:
    raw = _load_raw(guild_id)
    raw["warning_message_id"] = str(message_id) if message_id else ""
    settings_db.put(guild_id, MODULE_NAME, raw)


def is_tempban_ban_reason(reason: str | None) -> bool:
    """True for softban reasons that should be recovered (unbanned) on restart."""
    if not reason:
        return False
    if reason == BAN_REASON_MARKER:
        return True
    return reason in LEGACY_BAN_REASONS


def is_permanent_trap_ban_reason(reason: str | None) -> bool:
    return bool(reason) and reason == PERMANENT_BAN_REASON_MARKER


def ban_reason_for_api(action: str = ACTION_SOFTBAN) -> str:
    if action == ACTION_BAN:
        return PERMANENT_BAN_REASON_MARKER
    return BAN_REASON_MARKER


def action_label(action: str, lang: str) -> str:
    if action == ACTION_BAN:
        return i18n.t("tempban.action_label.ban", lang)
    if action == ACTION_DISABLED:
        return i18n.t("tempban.action_label.disabled", lang)
    return i18n.t("tempban.action_label.softban", lang)


def dm_variables(member, guild, invite_link: str, *, action: str = ACTION_SOFTBAN, ban_count: int = 0) -> dict[str, str]:
    lang = i18n.lang_for(guild.id)
    return {
        "mention": member.mention,
        "name": member.display_name,
        "guild": guild.name,
        "guild_name": guild.name,
        "invite": invite_link,
        "user_id": str(member.id),
        "action": action_label(action, lang),
        "channel": "",
        "ban_count": str(ban_count),
    }


def warning_variables(guild, channel, *, action: str, ban_count: int) -> dict[str, str]:
    lang = i18n.lang_for(guild.id)
    return {
        "guild": guild.name,
        "guild_name": guild.name,
        "channel": channel.mention if channel else "",
        "action": action_label(action, lang),
        "ban_count": str(ban_count),
    }


def default_dm_message(lang: str) -> str:
    return i18n.t("tempban.dm_message", lang)


def default_warning_message(lang: str) -> str:
    return i18n.t("tempban.warning_default", lang)


def split_title_description(text: str) -> tuple[str, str]:
    """First paragraph = title when separated by a blank line; else title empty."""
    text = (text or "").strip()
    if not text:
        return "", ""
    if "\n\n" in text:
        title, _, rest = text.partition("\n\n")
        return title.strip(), rest.strip()
    return "", text


def build_warning_embed(lang: str, settings: dict, variables: dict[str, str]) -> discord.Embed:
    raw = settings.get("warning_message") or default_warning_message(lang)
    rendered = render_template(raw, variables)
    title, description = split_title_description(rendered)
    if not title:
        title = i18n.t("tempban.warning_title", lang)
    embed = discord.Embed(
        title=title[:256],
        description=(description or rendered)[:4096],
        color=embed_style.ACCENT,
    )
    thumb = (settings.get("warning_thumbnail_url") or "").strip()
    if thumb.startswith(("http://", "https://")):
        embed.set_thumbnail(url=thumb)
    ban_count = variables.get("ban_count", "0")
    embed.set_footer(text=i18n.t("tempban.warning_footer", lang, count=ban_count))
    return embed


def build_log_embed(lang: str, variables: dict[str, str], *, custom_message: str = "") -> discord.Embed:
    """Structured log embed; optional custom_message overrides title/description."""
    custom = (custom_message or "").strip()
    if custom:
        rendered = render_template(custom, variables)
        title, description = split_title_description(rendered)
        embed = discord.Embed(
            title=(title or i18n.t("tempban.embed.title", lang))[:256],
            description=(description or rendered)[:4096],
            color=embed_style.DANGER,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=i18n.t("tempban.embed.footer", lang))
        return embed

    extra = "\n".join([
        f"{i18n.t('tempban.embed.ban_time', lang)}: {variables['ban_time']}",
        f"{i18n.t('tempban.embed.unban_time', lang)}: {variables.get('unban_time') or '—'}",
        f"{i18n.t('tempban.embed.channel', lang)}: {variables['channel']}",
        f"{i18n.t('tempban.embed.dm_status', lang)}: {variables['dm_status']}",
        f"{i18n.t('tempban.embed.message', lang)}: {variables['message_preview'] or '—'}",
    ])
    try:
        target_id = int(variables["user_id"])
    except (TypeError, ValueError):
        target_id = 0
    return moderation_embed_core.build_action_log_embed(
        lang,
        title=i18n.t("tempban.embed.title", lang),
        who_value=i18n.t("moderation.embed.automatic", lang),
        target_value=moderation_embed_core.target_ref(
            name=variables["name"],
            user_id=target_id,
        ),
        reason=variables.get("action") or i18n.t("tempban.embed.title", lang),
        extra=extra,
        color=embed_style.DANGER,
        footer=i18n.t("tempban.embed.footer", lang),
    )


def unban_reason(settings: dict, lang: str) -> str:
    custom = (settings.get("unban_reason") or "").strip()
    if custom:
        return render_template(custom, {})
    return i18n.t("tempban.unban_reason", lang)


def should_process_trap(settings: dict) -> bool:
    return _normalize_action(settings.get("action")) != ACTION_DISABLED
