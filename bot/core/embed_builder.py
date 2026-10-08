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
    return _v2_nodes_to_spec(_root_components(message))


def _top_level_nodes(message) -> list:
    """Top-level components; unwraps a typeless wrapper (e.g. a LayoutView) one level."""
    nodes: list = []
    for root in _root_components(message):
        if _component_type_value(root) is None and _node_children(root):
            nodes.extend(_node_children(root))
        else:
            nodes.append(root)
    return nodes


def v2_message_to_specs(message) -> tuple[list[dict], str, bool]:
    """Like v2_message_to_spec, but one spec per top-level Container.

    Returns (specs, extracted_content, saw_v2_layout). Best-effort: text that leads
    the first Container is message content, in later Containers it is description.
    """
    top_level = _top_level_nodes(message)
    containers = [node for node in top_level if _component_type_value(node) == _TYPE_CONTAINER]
    if len(containers) < 2:
        spec, content, saw_v2 = v2_message_to_spec(message)
        return [spec], content, saw_v2

    loose = [node for node in top_level if _component_type_value(node) != _TYPE_CONTAINER]
    _, content, _ = _v2_nodes_to_spec(loose)
    specs: list[dict] = []
    for index, container in enumerate(containers):
        spec, leading_text, _ = _v2_nodes_to_spec([container])
        if leading_text:
            if index == 0:
                content = f"{content}\n\n{leading_text}" if content else leading_text
            else:
                spec["description"] = (
                    f"{leading_text}\n{spec['description']}" if spec["description"] else leading_text
                )
        if not is_embed_spec_empty(spec):
            specs.append(spec)
    return (specs or [empty_embed_spec()])[:MAX_EMBEDS], content, True


def _v2_nodes_to_spec(nodes: list) -> tuple[dict, str, bool]:
    spec = empty_embed_spec()
    text_blocks: list[str] = []
    image_urls: list[str] = []
    thumbnail_url = ""
    saw_v2 = False

    for node in _walk_components(nodes):
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


def _safe_embed_to_spec(embed) -> dict:
    try:
        return embed_to_spec(embed)
    except Exception:
        logger.exception("embed_to_spec failed; returning empty spec")
        return empty_embed_spec()


def message_to_editor_payload(message) -> dict:
    """Parse a Discord message into the dashboard embed-editor payload."""
    is_v2 = bool(getattr(getattr(message, "flags", None), "components_v2", False))
    content = getattr(message, "content", None) or ""
    embeds = getattr(message, "embeds", None) or []

    if embeds:
        specs = [_safe_embed_to_spec(embed) for embed in embeds[:MAX_EMBEDS]]
    else:
        try:
            specs, mapped_content, saw_v2 = v2_message_to_specs(message)
        except Exception:
            logger.exception("v2_message_to_specs failed; returning empty spec")
            specs, mapped_content, saw_v2 = [empty_embed_spec()], "", is_v2
        if not content:
            content = mapped_content
        is_v2 = is_v2 or saw_v2

    return {
        "content": content,
        "embeds": specs,
        "embed": specs[0],
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


MAX_EMBEDS = 10
_TOTAL_TEXT_LIMIT = 6000


def _spec_limit_error(spec: dict) -> tuple[str | None, int]:
    """Per-embed Discord limits. Returns (error_code, counted_text_length)."""
    title = spec.get("title") or ""
    description = spec.get("description") or ""
    author_name = (spec.get("author") or {}).get("name") or ""
    footer_text = (spec.get("footer") or {}).get("text") or ""
    fields = spec.get("fields") or []

    if len(title) > 256:
        return "title_too_long", 0
    if len(description) > 4096:
        return "description_too_long", 0
    if len(footer_text) > 2048:
        return "footer_too_long", 0
    if len(author_name) > 256:
        return "author_name_too_long", 0
    if len(fields) > 25:
        return "too_many_fields", 0

    total_length = len(title) + len(description) + len(footer_text) + len(author_name)
    for field in fields:
        if not isinstance(field, dict):
            continue
        name = field.get("name") or ""
        value = field.get("value") or ""
        if len(name) > 256:
            return "field_name_too_long", 0
        if len(value) > 1024:
            return "field_value_too_long", 0
        total_length += len(name) + len(value)
    return None, total_length


def validate_embed_spec(spec: dict, content: str = "") -> str | None:
    if is_embed_spec_empty(spec) and not content.strip():
        return "empty_embed"
    error_code, total_length = _spec_limit_error(spec)
    if error_code:
        return error_code
    if total_length > _TOTAL_TEXT_LIMIT:
        return "embed_too_large"
    return None


def specs_from_body(body: dict) -> list[dict] | None:
    """Embed specs of a request body: `embeds` list, or the legacy single `embed`.

    Empty specs are dropped. Returns None when the shape is not usable.
    """
    raw = body.get("embeds")
    if raw is None:
        raw = [body.get("embed") or {}]
    if not isinstance(raw, list) or not all(isinstance(spec, dict) for spec in raw):
        return None
    return [spec for spec in raw if not is_embed_spec_empty(spec)]


def validate_embed_specs(specs: list[dict], content: str = "") -> str | None:
    """Validate all embeds of one message; Discord's 6000-char limit is shared between them."""
    if not specs and not content.strip():
        return "empty_embed"
    if len(specs) > MAX_EMBEDS:
        return "too_many_embeds"
    total_length = 0
    for spec in specs:
        error_code, length = _spec_limit_error(spec)
        if error_code:
            return error_code
        total_length += length
    if total_length > _TOTAL_TEXT_LIMIT:
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

import bot.core.settings_db as settings_db

MODULE_NAME = "embed_templates"  # должно совпадать с ключом в settings_migration.MODULE_FILE_MAP
MAX_TEMPLATES = 200
MAX_BULK_TEMPLATES = 200
MAX_TEMPLATE_NAME = 60


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


def _template_embeds(template: dict) -> list[dict]:
    """Embed specs of a stored template; records saved before multi-embed carry one `embed`."""
    embeds = template.get("embeds")
    if isinstance(embeds, list):
        return [spec for spec in embeds if isinstance(spec, dict)]
    legacy = template.get("embed")
    return [legacy] if isinstance(legacy, dict) and legacy else []


def _template_payload(template: dict) -> dict:
    embeds = _template_embeds(template)
    return {
        "id": str(template.get("id") or ""),
        "name": str(template.get("name") or ""),
        "content": str(template.get("content") or ""),
        "embeds": embeds,
        "embed": embeds[0] if embeds else {},
        "role_ids": [str(r) for r in template.get("role_ids", [])],
    }


def list_templates(guild_id: int) -> list[dict]:
    return [_template_payload(t) for t in _load_templates_data(guild_id)["templates"]]


def _append_template(data: dict, name: str, content: str, embed_specs: list[dict], role_ids: list[str]) -> dict:
    data["seq"] += 1
    template = {
        "id": str(data["seq"]),
        "name": name,
        "content": content,
        "embeds": list(embed_specs),
        "role_ids": list(role_ids),
    }
    data["templates"].append(template)
    return template


def save_template(
    guild_id: int, name: str, content: str, embed_specs: list[dict], role_ids: list[str]
) -> dict | str:
    """Сохраняет шаблон. Возвращает шаблон или код ошибки строкой."""
    data = _load_templates_data(guild_id)
    if len(data["templates"]) >= MAX_TEMPLATES:
        return "too_many_templates"
    if any(t.get("name") == name for t in data["templates"]):
        return "duplicate_name"
    template = _append_template(data, name, content, embed_specs, role_ids)
    _save_templates_data(guild_id, data)
    return _template_payload(template)


def save_templates_bulk(guild_id: int, items: list) -> dict:
    """Сохраняет пачку шаблонов одной записью. Возвращает {"created": [...], "skipped": [...]}.

    Каждый пропуск — {"name", "reason"}: invalid_request, invalid_name, код валидации
    эмбеда, duplicate_name или too_many_templates.
    """
    data = _load_templates_data(guild_id)
    taken = {t.get("name") for t in data["templates"]}
    created: list[dict] = []
    skipped: list[dict] = []

    for item in items:
        if not isinstance(item, dict):
            skipped.append({"name": "", "reason": "invalid_request"})
            continue
        raw_name = item.get("name")
        name = raw_name.strip()[:MAX_TEMPLATE_NAME].strip() if isinstance(raw_name, str) else ""
        content = item.get("content") or ""
        specs = specs_from_body(item)

        if not name:
            reason = "invalid_name"
        elif specs is None or not isinstance(content, str):
            reason = "invalid_request"
        else:
            reason = validate_embed_specs(specs, content)
            if reason is None and name in taken:
                reason = "duplicate_name"
            if reason is None and len(data["templates"]) >= MAX_TEMPLATES:
                reason = "too_many_templates"
        if reason:
            skipped.append({"name": name, "reason": reason})
            continue

        created.append(_template_payload(_append_template(data, name, content, specs, [])))
        taken.add(name)

    if created:
        _save_templates_data(guild_id, data)
    return {"created": created, "skipped": skipped}


def delete_template(guild_id: int, template_id: str) -> bool:
    data = _load_templates_data(guild_id)
    before = len(data["templates"])
    data["templates"] = [t for t in data["templates"] if str(t.get("id")) != str(template_id)]
    if len(data["templates"]) != before:
        _save_templates_data(guild_id, data)
        return True
    return False
