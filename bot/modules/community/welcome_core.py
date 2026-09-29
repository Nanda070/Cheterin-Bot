"""Welcome / goodbye message customization (dashboard + bot)."""

from __future__ import annotations

import bot.core.settings_db as settings_db
from bot.core.message_template_core import embed_spec_has_content, normalize_embed_spec, substitute, substitute_embed_spec
from bot.core.embed_builder import build_embed

import bot.core.i18n as i18n

MODULE_NAME = "welcome_messages"
DEFAULT_DM_THUMBNAIL_URL = "https://i.imgur.com/4ydti00.png"


def _load_raw(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return data if isinstance(data, dict) else {}


def save_settings(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    raw = _load_raw(guild_id)
    return {
        "channel_mode": str(raw.get("channel_mode") or "text"),
        "channel_text": str(raw.get("channel_text") or ""),
        "channel_embed": normalize_embed_spec(raw.get("channel_embed")),
        "dm_content": str(raw.get("dm_content") or ""),
        "dm_embed": normalize_embed_spec(raw.get("dm_embed")),
        "dm_thumbnail_url": str(raw.get("dm_thumbnail_url") or ""),
        "dm_fallback_thumbnail_url": str(raw.get("dm_fallback_thumbnail_url") or ""),
        "dm_footer_text": str(raw.get("dm_footer_text") or ""),
        "dm_use_guild_icon": bool(raw.get("dm_use_guild_icon", True)),
        "goodbye_text": str(raw.get("goodbye_text") or ""),
    }


def resolve_dm_thumbnail_url(settings: dict) -> str:
    custom = (settings.get("dm_thumbnail_url") or "").strip()
    if custom:
        return custom
    fallback = (settings.get("dm_fallback_thumbnail_url") or "").strip()
    if fallback:
        return fallback
    return DEFAULT_DM_THUMBNAIL_URL


def resolve_dm_footer_text(settings: dict, lang: str) -> str:
    custom = (settings.get("dm_footer_text") or "").strip()
    if custom:
        return custom
    return i18n.t("welcome.dm_footer", lang)


def channel_variables(member, guild) -> dict[str, str]:
    return {
        "mention": member.mention,
        "name": member.display_name,
        "guild_name": guild.name,
        "member_count": str(guild.member_count or 0),
    }


def dm_variables(member, guild, bot_config_get) -> dict[str, str]:
    base = channel_variables(member, guild)

    def ch(channel_key: str) -> str:
        raw = bot_config_get(guild.id, channel_key)
        return f"<#{raw}>" if raw else "—"

    base.update(
        {
            "announcements_channel": ch("ANNOUNCEMENTS_CHANNEL_ID"),
            "rules_channel": ch("RULES_CHANNEL_ID"),
            "roles_channel": ch("ROLES_CHANNEL_ID"),
            "search_channel": ch("SEARCH_PLAYERS_CHANNEL_ID"),
        }
    )
    return base


def default_channel_text(lang: str) -> str:
    return i18n.t("welcome.channel_message", lang, mention="{mention}", guild_name="{guild_name}", member_count="{member_count}")


def default_goodbye_text(lang: str) -> str:
    return i18n.t("welcome.goodbye_message", lang, mention="{mention}", name="{name}")


def default_dm_embed_spec(lang: str, bot_config_get=None, guild_id: int = 0, settings: dict | None = None) -> dict:
    """Server 404-style welcome DM constructor defaults (placeholders substituted at send time)."""
    settings = settings or {}
    _ = bot_config_get, guild_id
    fields = [
        {
            "name": i18n.t("welcome.dm_field_announcements", lang),
            "value": i18n.t("welcome.dm_field_announcements_value", lang),
            "inline": False,
        },
        {
            "name": i18n.t("welcome.dm_field_rules", lang),
            "value": i18n.t("welcome.dm_field_rules_value", lang),
            "inline": False,
        },
        {
            "name": i18n.t("welcome.dm_field_roles", lang),
            "value": i18n.t("welcome.dm_field_roles_value", lang),
            "inline": False,
        },
        {
            "name": i18n.t("welcome.dm_field_search", lang),
            "value": i18n.t("welcome.dm_field_search_value", lang),
            "inline": False,
        },
        {
            "name": i18n.t("welcome.dm_field_levels", lang),
            "value": i18n.t("welcome.dm_field_levels_value", lang),
            "inline": False,
        },
        {
            "name": i18n.t("welcome.dm_field_tips", lang),
            "value": i18n.t("welcome.dm_field_tips_value", lang),
            "inline": False,
        },
    ]
    return {
        "title": i18n.t("welcome.dm_title", lang, guild_name="{guild_name}"),
        "description": i18n.t("welcome.dm_description", lang),
        "url": "",
        "color": "#1a4a8a",
        "author": {"name": "", "url": "", "icon_url": ""},
        "footer": {"text": resolve_dm_footer_text(settings, lang), "icon_url": ""},
        "image": {"url": ""},
        "thumbnail": {"url": resolve_dm_thumbnail_url(settings)},
        "timestamp": True,
        "fields": fields,
    }


def preview_dm_embed_spec(lang: str, settings: dict | None = None) -> dict:
    """Static defaults for dashboard preview (no guild context)."""
    return default_dm_embed_spec(lang, settings=settings)


def build_channel_payload(settings: dict, member, guild, lang: str, bot_config_get):
    variables = channel_variables(member, guild)
    mode = settings.get("channel_mode") or "text"
    if mode == "embed":
        spec = settings.get("channel_embed") or {}
        if not embed_spec_has_content(spec):
            spec = {
                "title": i18n.t("welcome.title", lang, guild_name="{guild_name}"),
                "description": default_channel_text(lang),
                "color": "#D44556",
                "thumbnail": {"url": ""},
                "fields": [],
            }
        spec = substitute_embed_spec(spec, variables)
        embed = build_embed({**spec, "timestamp": spec.get("timestamp") or None})
        thumb = (spec.get("thumbnail") or {}).get("url")
        if not thumb and settings.get("dm_use_guild_icon", True) and guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        return {"embed": embed}

    text = settings.get("channel_text") or default_channel_text(lang)
    return {"content": substitute(text, variables)}


def build_dm_payload(settings: dict, member, guild, lang: str, bot_config_get):
    variables = dm_variables(member, guild, bot_config_get)
    content = substitute(settings.get("dm_content") or "", variables)

    spec = settings.get("dm_embed") or {}
    use_timestamp = bool(spec.get("timestamp"))
    if not embed_spec_has_content(spec):
        spec = default_dm_embed_spec(lang, bot_config_get, guild.id, settings)
        use_timestamp = True
    else:
        spec = dict(spec)

    spec = substitute_embed_spec(spec, variables)
    embed = build_embed({k: v for k, v in spec.items() if k != "timestamp"})
    if use_timestamp:
        embed.timestamp = __import__("discord").utils.utcnow()

    thumb_url = (settings.get("dm_thumbnail_url") or "").strip()
    if not thumb_url:
        thumb_url = ((spec.get("thumbnail") or {}).get("url") or "").strip()
    if not thumb_url and settings.get("dm_use_guild_icon", True) and guild.icon:
        thumb_url = guild.icon.url
    if not thumb_url:
        thumb_url = resolve_dm_thumbnail_url(settings)
    if thumb_url:
        embed.set_thumbnail(url=thumb_url)

    return {"content": content or None, "embed": embed}


def build_goodbye_text(settings: dict, member, guild, lang: str) -> str:
    variables = channel_variables(member, guild)
    text = settings.get("goodbye_text") or default_goodbye_text(lang)
    return substitute(text, variables)
