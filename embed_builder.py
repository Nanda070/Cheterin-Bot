from datetime import datetime
import logging
import re

import discord

logger = logging.getLogger(__name__)

_LINK_TITLE_RE = re.compile(r"^\[(.+)\]\((https?://[^)]+)\)$")

# Discord component type values (stable even if enum names differ across discord.py).
_TYPE_SECTION = 9
_TYPE_TEXT_DISPLAY = 10
_TYPE_THUMBNAIL = 11
_TYPE_MEDIA_GALLERY = 12
_TYPE_CONTAINER = 17
_V2_LAYOUT_TYPES = {_TYPE_SECTION, _TYPE_TEXT_DISPLAY, _TYPE_THUMBNAIL, _TYPE_MEDIA_GALLERY, _TYPE_CONTAINER}


def empty_embed_spec() -> dict:
    """Complete editor-shaped spec so the dashboard never receives missing nested keys."""
    return {
        "title": "",
        "description": "",
        "url": "",
        "color": "",
        "author": {"name": "", "url": "", "icon_url": ""},
        "footer": {"text": "", "icon_url": ""},
        "image": {"url": ""},
        "thumbnail": {"url": ""},
        "timestamp": None,
        "fields": [],
    }


def _color_hex(value) -> str:
    if value is None:
        return ""
    try:
        return f"#{int(value):06x}"
    except (TypeError, ValueError):
        return ""


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
    try:
        data = embed.to_dict() if embed is not None else {}
    except Exception:
        logger.exception("embed.to_dict() failed")
        return empty_embed_spec()
    if not isinstance(data, dict):
        return empty_embed_spec()

    spec = empty_embed_spec()
    spec["title"] = data.get("title") or ""
    spec["description"] = data.get("description") or ""
    spec["url"] = data.get("url") or ""
    spec["color"] = _color_hex(data.get("color"))
    spec["timestamp"] = data.get("timestamp")

    author = data.get("author") or {}
    if isinstance(author, dict):
        spec["author"] = {
            "name": author.get("name") or "",
            "url": author.get("url") or "",
            "icon_url": author.get("icon_url") or "",
        }

    footer = data.get("footer") or {}
    if isinstance(footer, dict):
        spec["footer"] = {
            "text": footer.get("text") or "",
            "icon_url": footer.get("icon_url") or "",
        }

    image = data.get("image") or {}
    if isinstance(image, dict):
        spec["image"] = {"url": image.get("url") or ""}

    thumbnail = data.get("thumbnail") or {}
    if isinstance(thumbnail, dict):
        spec["thumbnail"] = {"url": thumbnail.get("url") or ""}

    fields = data.get("fields") or []
    if isinstance(fields, list):
        spec["fields"] = [
            {
                "name": (f.get("name") or "") if isinstance(f, dict) else "",
                "value": (f.get("value") or "") if isinstance(f, dict) else "",
                "inline": bool(f.get("inline")) if isinstance(f, dict) else False,
            }
            for f in fields
        ]
    return spec


def _component_type_value(node) -> int | None:
    if isinstance(node, dict):
        raw = node.get("type")
    else:
        raw = getattr(node, "type", None)
        raw = getattr(raw, "value", raw)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _node_children(node) -> list:
    kids: list = []
    if isinstance(node, dict):
        for key in ("components", "children", "items"):
            val = node.get(key)
            if val:
                kids.extend(val if isinstance(val, (list, tuple)) else [val])
        accessory = node.get("accessory")
        if accessory:
            kids.append(accessory)
        media = node.get("media")
        if media:
            kids.append(media)
        return kids

    children = getattr(node, "children", None)
    if children is None:
        children = getattr(node, "components", None)
    if children:
        try:
            kids.extend(list(children))
        except TypeError:
            kids.append(children)
    items = getattr(node, "items", None)
    if items:
        try:
            kids.extend(list(items))
        except TypeError:
            kids.append(items)
    accessory = getattr(node, "accessory", None)
    if accessory is not None:
        kids.append(accessory)
    media = getattr(node, "media", None)
    if media is not None:
        kids.append(media)
    return kids


def _root_components(message) -> list:
    components = getattr(message, "components", None)
    if not components:
        return []
    if isinstance(components, (list, tuple)):
        return list(components)
    return [components]


def _walk_components(nodes):
    stack = list(nodes)
    seen: set[int] = set()
    while stack:
        node = stack.pop()
        if node is None:
            continue
        if not isinstance(node, dict):
            marker = id(node)
            if marker in seen:
                continue
            seen.add(marker)
        yield node
        stack.extend(reversed(_node_children(node)))


def _node_text(node) -> str:
    if isinstance(node, dict):
        return str(node.get("content") or "")
    return str(getattr(node, "content", None) or "")


def _node_url(node) -> str:
    if isinstance(node, dict):
        url = node.get("url")
        if url:
            return str(url)
        media = node.get("media") or {}
        if isinstance(media, dict) and media.get("url"):
            return str(media["url"])
        return ""
    url = getattr(node, "url", None)
    if url:
        return str(url)
    media = getattr(node, "media", None)
    if media is None:
        return ""
    if isinstance(media, dict):
        return str(media.get("url") or "")
    return str(getattr(media, "url", None) or "")


def _node_accent_hex(node) -> str:
    if isinstance(node, dict):
        return _color_hex(node.get("accent_color") or node.get("accent_colour"))
    colour = getattr(node, "accent_colour", None)
    if colour is None:
        colour = getattr(node, "accent_color", None)
    if colour is None:
        return ""
    return _color_hex(getattr(colour, "value", colour))


def _node_custom_id(node) -> str:
    if isinstance(node, dict):
        return str(node.get("custom_id") or "")
    return str(getattr(node, "custom_id", None) or "")


def _apply_v2_text_blocks(blocks: list[str], spec: dict) -> str:
    """Best-effort reverse of components_v2.embed_to_text_blocks. Returns leftover content."""
    cleaned = [b.strip() for b in blocks if (b or "").strip() and b.strip() != "\u200b"]
    if not cleaned:
        return ""

    if cleaned[-1].startswith("-# "):
        spec["footer"] = {"text": cleaned.pop()[3:].strip(), "icon_url": ""}

    content_parts: list[str] = []
    for block in cleaned:
        lines = block.split("\n")
        first = lines[0]
        has_heading = first.startswith("## ") or any(line.startswith("## ") for line in lines)
        if has_heading:
            desc_lines: list[str] = []
            for line in lines:
                if line.startswith("## "):
                    title = line[3:].strip()
                    match = _LINK_TITLE_RE.match(title)
                    if match:
                        spec["title"] = match.group(1)
                        spec["url"] = match.group(2)
                    else:
                        spec["title"] = title
                elif line.startswith("**") and line.endswith("**") and len(line) >= 4 and not spec["author"]["name"]:
                    spec["author"]["name"] = line[2:-2]
                else:
                    desc_lines.append(line)
            joined = "\n".join(desc_lines).strip()
            if joined:
                spec["description"] = (
                    f"{spec['description']}\n{joined}".strip() if spec["description"] else joined
                )
            continue

        if first.startswith("**") and first.endswith("**") and len(first) >= 4:
            spec["fields"].append(
                {
                    "name": first[2:-2],
                    "value": "\n".join(lines[1:]),
                    "inline": False,
                }
            )
            continue

        if not spec["title"] and not spec["description"] and not spec["fields"]:
            content_parts.append(block)
        elif spec["description"]:
            spec["description"] = f"{spec['description']}\n{block}"
        else:
            spec["description"] = block

    return "\n\n".join(content_parts)


def v2_message_to_spec(message) -> tuple[dict, str, bool]:
    """Map Components V2 layout (or nested rows) into an editor spec.

    Returns (spec, extracted_content, saw_v2_layout).
    """
    spec = empty_embed_spec()
    text_blocks: list[str] = []
    image_urls: list[str] = []
    thumbnail_url = ""
    saw_v2 = False

    for node in _walk_components(_root_components(message)):
        type_value = _component_type_value(node)
        if type_value in _V2_LAYOUT_TYPES:
            saw_v2 = True
        if type_value == _TYPE_TEXT_DISPLAY:
            text = _node_text(node)
            if text:
                text_blocks.append(text)
        elif type_value is None:
            text = _node_text(node)
            if text and not _node_children(node):
                text_blocks.append(text)
                saw_v2 = True
        if type_value == _TYPE_CONTAINER:
            accent = _node_accent_hex(node)
            if accent:
                spec["color"] = accent
        if type_value == _TYPE_MEDIA_GALLERY:
            url = _node_url(node)
            if url:
                image_urls.append(url)
            for item in _node_children(node):
                item_url = _node_url(item)
                if item_url:
                    image_urls.append(item_url)
        if type_value == _TYPE_THUMBNAIL:
            url = _node_url(node)
            if url:
                thumbnail_url = url

    extracted_content = _apply_v2_text_blocks(text_blocks, spec)
    if image_urls:
        spec["image"] = {"url": image_urls[0]}
        if len(image_urls) > 1 and not thumbnail_url:
            spec["thumbnail"] = {"url": image_urls[1]}
    if thumbnail_url:
        spec["thumbnail"] = {"url": thumbnail_url}
    return spec, extracted_content, saw_v2


def message_to_editor_payload(message) -> dict:
    """Parse a Discord message into the dashboard embed-editor payload."""
    is_v2 = bool(getattr(getattr(message, "flags", None), "components_v2", False))
    content = getattr(message, "content", None) or ""
    spec = empty_embed_spec()
    embeds = getattr(message, "embeds", None) or []

    if embeds:
        try:
            spec = embed_to_spec(embeds[0])
        except Exception:
            logger.exception("embed_to_spec failed; returning empty spec")
            spec = empty_embed_spec()
    else:
        try:
            mapped_spec, mapped_content, saw_v2 = v2_message_to_spec(message)
        except Exception:
            logger.exception("v2_message_to_spec failed; returning empty spec")
            mapped_spec, mapped_content, saw_v2 = empty_embed_spec(), "", is_v2
        spec = mapped_spec
        if not content:
            content = mapped_content
        is_v2 = is_v2 or saw_v2

    return {
        "content": content,
        "embed": spec,
        "role_ids": [str(r) for r in parse_role_button_ids(message)],
        "components_version": "v2" if is_v2 else "v1",
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
        if not isinstance(field, dict):
            continue
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
    seen: set[int] = set()
    for node in _walk_components(_root_components(message)):
        custom_id = _node_custom_id(node)
        if not custom_id.startswith("btn_role_"):
            continue
        try:
            role_id = int(custom_id.removeprefix("btn_role_"))
        except ValueError:
            continue
        if role_id in seen:
            continue
        seen.add(role_id)
        role_ids.append(role_id)
    return role_ids


# ────────────────────────── Шаблоны эмбедов ──────────────────────────

import settings_db

MODULE_NAME = "embed_templates"  # должно совпадать с ключом в settings_migration.MODULE_FILE_MAP
MAX_TEMPLATES = 50


def _load_templates_data(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    data.setdefault("seq", 0)
    data.setdefault("templates", [])
    raw_cv = str(data.get("components_version") or "v1").strip().lower()
    data["components_version"] = "v2" if raw_cv in ("v2", "2", "components_v2") else "v1"
    return data


def _save_templates_data(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_components_version(guild_id: int) -> str:
    return _load_templates_data(guild_id)["components_version"]


def set_components_version(guild_id: int, version: str) -> str:
    data = _load_templates_data(guild_id)
    raw = str(version or "v1").strip().lower()
    data["components_version"] = "v2" if raw in ("v2", "2", "components_v2") else "v1"
    _save_templates_data(guild_id, data)
    return data["components_version"]


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
