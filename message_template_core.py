"""Placeholder substitution for customizable bot messages."""

from __future__ import annotations

import re
from typing import Any

_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def substitute(text: str, variables: dict[str, str]) -> str:
    if not text:
        return text

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return _PLACEHOLDER_RE.sub(repl, text)


def substitute_embed_spec(spec: dict, variables: dict[str, str]) -> dict:
    """Return a copy of an embed spec with placeholders replaced in string fields."""
    result = dict(spec)
    for key in ("title", "description", "url", "color"):
        if key in result and isinstance(result[key], str):
            result[key] = substitute(result[key], variables)

    author = dict(result.get("author") or {})
    for key in ("name", "url", "icon_url"):
        if key in author and isinstance(author[key], str):
            author[key] = substitute(author[key], variables)
    result["author"] = author

    footer = dict(result.get("footer") or {})
    for key in ("text", "icon_url"):
        if key in footer and isinstance(footer[key], str):
            footer[key] = substitute(footer[key], variables)
    result["footer"] = footer

    image = dict(result.get("image") or {})
    if image.get("url"):
        image["url"] = substitute(str(image["url"]), variables)
    result["image"] = image

    thumbnail = dict(result.get("thumbnail") or {})
    if thumbnail.get("url"):
        thumbnail["url"] = substitute(str(thumbnail["url"]), variables)
    result["thumbnail"] = thumbnail

    fields = []
    for field in result.get("fields") or []:
        fields.append(
            {
                "name": substitute(str(field.get("name") or ""), variables),
                "value": substitute(str(field.get("value") or ""), variables),
                "inline": bool(field.get("inline")),
            }
        )
    result["fields"] = fields
    return result


def normalize_embed_spec(raw: Any) -> dict:
    """Normalize dashboard JSON into embed_builder-compatible spec."""
    if not isinstance(raw, dict):
        raw = {}
    author = raw.get("author") if isinstance(raw.get("author"), dict) else {}
    footer = raw.get("footer") if isinstance(raw.get("footer"), dict) else {}
    image = raw.get("image") if isinstance(raw.get("image"), dict) else {}
    thumbnail = raw.get("thumbnail") if isinstance(raw.get("thumbnail"), dict) else {}
    fields = raw.get("fields") if isinstance(raw.get("fields"), list) else []
    return {
        "title": str(raw.get("title") or ""),
        "description": str(raw.get("description") or ""),
        "url": str(raw.get("url") or ""),
        "color": str(raw.get("color") or ""),
        "author": {
            "name": str(author.get("name") or ""),
            "url": str(author.get("url") or ""),
            "icon_url": str(author.get("icon_url") or ""),
        },
        "footer": {
            "text": str(footer.get("text") or ""),
            "icon_url": str(footer.get("icon_url") or ""),
        },
        "image": {"url": str(image.get("url") or "")},
        "thumbnail": {"url": str(thumbnail.get("url") or "")},
        "timestamp": raw.get("timestamp"),
        "fields": [
            {
                "name": str(f.get("name") or ""),
                "value": str(f.get("value") or ""),
                "inline": bool(f.get("inline")),
            }
            for f in fields
            if isinstance(f, dict)
        ],
    }


def embed_spec_has_content(spec: dict) -> bool:
    if spec.get("title") or spec.get("description"):
        return True
    if (spec.get("image") or {}).get("url") or (spec.get("thumbnail") or {}).get("url"):
        return True
    return bool(spec.get("fields"))
