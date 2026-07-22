"""Feedback panel appearance customization."""

from __future__ import annotations

import settings_db
from message_template_core import embed_spec_has_content, normalize_embed_spec
from embed_builder import build_embed

import i18n

MODULE_NAME = "feedback_panel"


def _load_raw(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    return data if isinstance(data, dict) else {}


def save_settings(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    raw = _load_raw(guild_id)
    return {
        "content": str(raw.get("content") or ""),
        "embed": normalize_embed_spec(raw.get("embed")),
        "banner_url": str(raw.get("banner_url") or ""),
    }


def resolve_banner_url(guild_id: int) -> str:
    return (get_settings(guild_id).get("banner_url") or "").strip()


def default_panel_embed_spec(lang: str, guild_id: int) -> dict:
    return {
        "title": "",
        "description": i18n.t("feedback.panel.description", lang),
        "color": "#2C2F33",
        "author": {"name": "", "url": "", "icon_url": ""},
        "footer": {"text": "", "icon_url": ""},
        "image": {"url": resolve_banner_url(guild_id)},
        "thumbnail": {"url": ""},
        "timestamp": False,
        "fields": [],
    }


def build_panel_payload(guild_id: int, lang: str) -> dict:
    settings = get_settings(guild_id)
    content = settings.get("content") or ""
    spec = settings.get("embed") or {}
    if not embed_spec_has_content(spec):
        spec = default_panel_embed_spec(lang, guild_id)
    else:
        spec = dict(spec)
        image_url = (spec.get("image") or {}).get("url", "").strip()
        if not image_url:
            banner = resolve_banner_url(guild_id)
            if banner:
                spec["image"] = {"url": banner}
    embed = build_embed(spec)
    return {"content": content or None, "embed": embed}


def panel_banner_url(guild_id: int) -> str:
    return resolve_banner_url(guild_id)
