from datetime import datetime

import discord


def build_embed(spec: dict) -> discord.Embed:
    color = spec.get("color")
    color_value = int(color.lstrip("#"), 16) if color else None
    embed = discord.Embed(
        title=spec.get("title") or None,
        description=spec.get("description") or None,
        url=spec.get("url") or None,
        color=color_value,
    )

    author = spec.get("author") or {}
    if author.get("name"):
        embed.set_author(
            name=author["name"], url=author.get("url") or None, icon_url=author.get("icon_url") or None
        )

    footer = spec.get("footer") or {}
    if footer.get("text"):
        embed.set_footer(text=footer["text"], icon_url=footer.get("icon_url") or None)

    image = spec.get("image") or {}
    if image.get("url"):
        embed.set_image(url=image["url"])

    thumbnail = spec.get("thumbnail") or {}
    if thumbnail.get("url"):
        embed.set_thumbnail(url=thumbnail["url"])

    if spec.get("timestamp"):
        embed.timestamp = datetime.fromisoformat(spec["timestamp"].replace("Z", "+00:00"))

    for field in spec.get("fields") or []:
        embed.add_field(
            name=field.get("name") or " ",
            value=field.get("value") or " ",
            inline=bool(field.get("inline")),
        )

    return embed


def embed_to_spec(embed: discord.Embed) -> dict:
    data = embed.to_dict()
    color_value = data.get("color")
    author = data.get("author", {})
    footer = data.get("footer", {})
    image = data.get("image", {})
    thumbnail = data.get("thumbnail", {})
    return {
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "url": data.get("url", ""),
        "color": f"#{color_value:06x}" if color_value is not None else "",
        "author": {
            "name": author.get("name", ""),
            "url": author.get("url", ""),
            "icon_url": author.get("icon_url", ""),
        },
        "footer": {"text": footer.get("text", ""), "icon_url": footer.get("icon_url", "")},
        "image": {"url": image.get("url", "")},
        "thumbnail": {"url": thumbnail.get("url", "")},
        "timestamp": data.get("timestamp"),
        "fields": [
            {"name": f.get("name", ""), "value": f.get("value", ""), "inline": bool(f.get("inline"))}
            for f in data.get("fields", [])
        ],
    }


def is_embed_spec_empty(spec: dict) -> bool:
    title = spec.get("title") or ""
    description = spec.get("description") or ""
    image_url = (spec.get("image") or {}).get("url") or ""
    thumbnail_url = (spec.get("thumbnail") or {}).get("url") or ""
    fields = spec.get("fields") or []
    return not (title or description or fields or image_url or thumbnail_url)


def validate_embed_spec(spec: dict, content: str = "") -> str | None:
    title = spec.get("title") or ""
    description = spec.get("description") or ""
    author_name = (spec.get("author") or {}).get("name") or ""
    footer_text = (spec.get("footer") or {}).get("text") or ""
    fields = spec.get("fields") or []

    if is_embed_spec_empty(spec) and not content.strip():
        return "empty_embed"
    if len(title) > 256:
        return "title_too_long"
    if len(description) > 4096:
        return "description_too_long"
    if len(footer_text) > 2048:
        return "footer_too_long"
    if len(author_name) > 256:
        return "author_name_too_long"
    if len(fields) > 25:
        return "too_many_fields"

    total_length = len(title) + len(description) + len(footer_text) + len(author_name)
    for field in fields:
        name = field.get("name") or ""
        value = field.get("value") or ""
        if len(name) > 256:
            return "field_name_too_long"
        if len(value) > 1024:
            return "field_value_too_long"
        total_length += len(name) + len(value)

    if total_length > 6000:
        return "embed_too_large"

    return None


def build_role_button_view(guild, role_ids: list[int]) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    for role_id in role_ids:
        role = guild.get_role(role_id)
        label = role.name[:80] if role else str(role_id)
        view.add_item(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id=f"btn_role_{role_id}",
            )
        )
    return view


def parse_role_button_ids(message) -> list[int]:
    role_ids = []
    for row in getattr(message, "components", []) or []:
        for child in getattr(row, "children", []):
            custom_id = getattr(child, "custom_id", "") or ""
            if custom_id.startswith("btn_role_"):
                try:
                    role_ids.append(int(custom_id.removeprefix("btn_role_")))
                except ValueError:
                    continue
    return role_ids


# ────────────────────────── Шаблоны эмбедов ──────────────────────────

import settings_db

MODULE_NAME = "embed_templates"  # должно совпадать с ключом в settings_migration.MODULE_FILE_MAP
MAX_TEMPLATES = 50


def _load_templates_data(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    data.setdefault("seq", 0)
    data.setdefault("templates", [])
    return data


def _save_templates_data(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def list_templates(guild_id: int) -> list[dict]:
    return [
        {
            "id": str(t.get("id") or ""),
            "name": str(t.get("name") or ""),
            "content": str(t.get("content") or ""),
            "embed": t.get("embed") or {},
            "role_ids": [str(r) for r in t.get("role_ids", [])],
        }
        for t in _load_templates_data(guild_id)["templates"]
    ]


def save_template(guild_id: int, name: str, content: str, embed_spec: dict, role_ids: list[str]) -> dict | str:
    """Сохраняет шаблон. Возвращает шаблон или код ошибки строкой."""
    data = _load_templates_data(guild_id)
    if len(data["templates"]) >= MAX_TEMPLATES:
        return "too_many_templates"
    if any(t.get("name") == name for t in data["templates"]):
        return "duplicate_name"
    data["seq"] += 1
    template = {
        "id": str(data["seq"]),
        "name": name,
        "content": content,
        "embed": embed_spec,
        "role_ids": list(role_ids),
    }
    data["templates"].append(template)
    _save_templates_data(guild_id, data)
    return template


def delete_template(guild_id: int, template_id: str) -> bool:
    data = _load_templates_data(guild_id)
    before = len(data["templates"])
    data["templates"] = [t for t in data["templates"] if str(t.get("id")) != str(template_id)]
    if len(data["templates"]) != before:
        _save_templates_data(guild_id, data)
        return True
    return False
