"""Discord Message Components V2 helpers.

discord.py 2.6+ exposes LayoutView / Container / TextDisplay / etc. and sets
MessageFlags.components_v2 automatically when the view has V2 children.

V2 messages cannot carry classic embeds or top-level content — text goes into
TextDisplay components. Interactive controls live in ActionRows inside a
Container (or as top-level ActionRows on the LayoutView).
"""

from __future__ import annotations

import re
from typing import Any

import discord
from discord import MediaGalleryItem

_MASKED_LINK_RE = re.compile(r"^\[([^\]\n]+)\]\(https?://[^)]+\)$")
_OVER_ESCAPED = (
    ("\\_", "_"),
    ("\\*", "*"),
    ("\\[", "["),
    ("\\]", "]"),
    ("\\(", "("),
    ("\\)", ")"),
    ("\\~", "~"),
    ("\\`", "`"),
)

VERSION_V1 = "v1"
VERSION_V2 = "v2"

# Discord TextDisplay content limit
_TEXT_DISPLAY_MAX = 4000
# Soft budget for one logical block before splitting
_BLOCK_SOFT_MAX = 3800


def normalize_version(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in (VERSION_V2, "2", "components_v2", "message_components_v2"):
        return VERSION_V2
    return VERSION_V1


def is_v2(value: Any) -> bool:
    return normalize_version(value) == VERSION_V2


def _colour_value(embed: discord.Embed | None) -> int | None:
    if embed is None or embed.colour is None:
        return None
    return int(embed.colour.value)


def _chunk_text(text: str, limit: int = _TEXT_DISPLAY_MAX) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    rest = text
    while rest:
        if len(rest) <= limit:
            chunks.append(rest)
            break
        cut = rest.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip("\n")
    return chunks


def embed_to_text_blocks(embed: discord.Embed | None, *, content: str | None = None) -> list[str]:
    """Map classic embed (+ optional message content) to markdown TextDisplay blocks."""
    blocks: list[str] = []
    if content and str(content).strip():
        blocks.extend(_chunk_text(str(content).strip()))

    if embed is None:
        return blocks

    header_parts: list[str] = []
    author = embed.author
    if author and author.name:
        header_parts.append(f"**{author.name}**")
    if embed.title:
        title = embed.title
        if embed.url:
            title = f"[{title}]({embed.url})"
        header_parts.append(f"## {title}")
    if embed.description:
        header_parts.append(embed.description)
    if header_parts:
        blocks.extend(_chunk_text("\n".join(header_parts)))

    inline_buf: list[str] = []
    for field in embed.fields:
        name = field.name or "\u200b"
        value = field.value or "\u200b"
        piece = f"**{name}**\n{value}"
        if field.inline:
            inline_buf.append(piece)
            if len(inline_buf) >= 3:
                blocks.extend(_chunk_text("\n\n".join(inline_buf)))
                inline_buf = []
        else:
            if inline_buf:
                blocks.extend(_chunk_text("\n\n".join(inline_buf)))
                inline_buf = []
            blocks.extend(_chunk_text(piece))
    if inline_buf:
        blocks.extend(_chunk_text("\n\n".join(inline_buf)))

    footer = embed.footer
    if footer and footer.text:
        blocks.extend(_chunk_text(f"-# {footer.text}"))

    return blocks


def v2_plain_text(text: str | None) -> str:
    """Keep V2 titles readable: unwrap `[text](url)` and undo over-escaped markdown."""
    if not text:
        return ""
    s = str(text)
    match = _MASKED_LINK_RE.fullmatch(s.strip())
    if match:
        s = match.group(1)
    for escaped, raw in _OVER_ESCAPED:
        s = s.replace(escaped, raw)
    return s


def stream_card_text_blocks(embed: discord.Embed | None) -> list[str]:
    """Juniper-style card body: heading, stream title, compact stats. No author, no markdown link title."""
    if embed is None:
        return []
    blocks: list[str] = []
    if embed.title:
        blocks.extend(_chunk_text(f"## {v2_plain_text(embed.title)}"))
    if embed.description:
        blocks.extend(_chunk_text(v2_plain_text(embed.description)))
    stats = _format_stream_fields(embed)
    if stats:
        blocks.extend(_chunk_text(stats))
    footer = embed.footer
    if footer and footer.text:
        blocks.extend(_chunk_text(f"-# {v2_plain_text(footer.text)}"))
    return blocks


def _format_stream_fields(embed: discord.Embed) -> str:
    fields = [
        (v2_plain_text(field.name) or "\u200b", v2_plain_text(field.value) or "\u200b")
        for field in embed.fields
    ]
    if not fields:
        return ""
    if len(fields) >= 2:
        left, right = fields[0], fields[1]
        text = f"**{left[0]}** | **{right[0]}**\n{left[1]} | {right[1]}"
        for name, value in fields[2:]:
            text += f"\n**{name}**\n{value}"
        return text
    name, value = fields[0]
    return f"**{name}**\n{value}"


def _clone_button(src: discord.ui.Button) -> discord.ui.Button:
    return discord.ui.Button(
        style=src.style,
        label=src.label,
        disabled=src.disabled,
        custom_id=src.custom_id,
        url=src.url,
        emoji=src.emoji,
    )


def _clone_select(src: discord.ui.Select) -> discord.ui.Select:
    kwargs: dict[str, Any] = {
        "custom_id": src.custom_id,
        "placeholder": src.placeholder,
        "min_values": src.min_values,
        "max_values": src.max_values,
        "options": list(src.options),
        "disabled": src.disabled,
    }
    # discord.py 2.7 Select accepts required=; older call sites may omit it.
    try:
        return discord.ui.Select(**kwargs, required=getattr(src, "required", True))
    except TypeError:
        return discord.ui.Select(**kwargs)


def interactive_rows_from_view(
    view: discord.ui.View | None,
    *,
    keep_callbacks: bool = False,
) -> list[discord.ui.ActionRow]:
    """Build ActionRows from a classic View's children, grouped by row index."""
    if view is None:
        return []

    by_row: dict[int, list[discord.ui.Item]] = {}
    for item in list(view.children):
        row = item.row if item.row is not None else 0
        by_row.setdefault(int(row), []).append(item)

    rows: list[discord.ui.ActionRow] = []
    for row_idx in sorted(by_row):
        action_row = discord.ui.ActionRow()
        for item in by_row[row_idx]:
            if isinstance(item, discord.ui.Button):
                if keep_callbacks:
                    # Move the live button into the ActionRow (preserves callback).
                    view.remove_item(item)
                    action_row.add_item(item)
                else:
                    action_row.add_item(_clone_button(item))
            elif isinstance(item, discord.ui.Select):
                if keep_callbacks:
                    view.remove_item(item)
                    action_row.add_item(item)
                else:
                    action_row.add_item(_clone_select(item))
        if action_row.children:
            rows.append(action_row)
    return rows


def _embed_container(
    embed: discord.Embed | None,
    *,
    content: str | None = None,
    image_files: list[discord.File] | None = None,
) -> discord.ui.Container:
    """One Container mirroring a classic embed (text blocks, then media gallery)."""
    container = discord.ui.Container(accent_colour=_colour_value(embed))

    for block in embed_to_text_blocks(embed, content=content):
        if len(block) > _BLOCK_SOFT_MAX:
            for chunk in _chunk_text(block):
                container.add_item(discord.ui.TextDisplay(chunk))
        else:
            container.add_item(discord.ui.TextDisplay(block))

    gallery_items: list[MediaGalleryItem] = []
    if embed is not None:
        if embed.image and embed.image.url:
            gallery_items.append(MediaGalleryItem(embed.image.url))
        elif image_files:
            for f in image_files[:10]:
                gallery_items.append(MediaGalleryItem(f))
        if embed.thumbnail and embed.thumbnail.url and not gallery_items:
            gallery_items.append(MediaGalleryItem(embed.thumbnail.url))
    elif image_files:
        for f in image_files[:10]:
            gallery_items.append(MediaGalleryItem(f))

    if gallery_items:
        container.add_item(discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.MediaGallery(*gallery_items))
    return container


def build_layout_view(
    *,
    embed: discord.Embed | None = None,
    embeds: list[discord.Embed] | None = None,
    content: str | None = None,
    source_view: discord.ui.View | None = None,
    keep_callbacks: bool = False,
    timeout: float | None = None,
    image_files: list[discord.File] | None = None,
) -> discord.ui.LayoutView:
    """Compose a LayoutView that visually mirrors classic embed(s) + components.

    Each embed becomes its own Container; message content leads the first one and
    interactive rows close the last one. `embeds` wins over `embed` when given.
    """
    layout = discord.ui.LayoutView(timeout=timeout)
    embed_list = list(embeds) if embeds is not None else ([embed] if embed is not None else [])

    if embed_list:
        containers = [
            _embed_container(
                item,
                content=content if index == 0 else None,
                image_files=image_files if index == 0 else None,
            )
            for index, item in enumerate(embed_list)
        ]
    else:
        containers = [_embed_container(None, content=content, image_files=image_files)]

    for action_row in interactive_rows_from_view(source_view, keep_callbacks=keep_callbacks):
        containers[-1].add_item(action_row)

    for container in containers:
        # Empty container is invalid; ensure at least one text node.
        if not container.children:
            container.add_item(discord.ui.TextDisplay("\u200b"))
        layout.add_item(container)
    return layout


# Discord limits for one Components V2 message.
V2_MAX_COMPONENTS = 40
V2_MAX_TEXT = 4000


class LayoutTooLargeError(ValueError):
    """Raised (only with enforce_limits=True) when a layout cannot fit one V2 message."""


def layout_limit_error(layout: discord.ui.LayoutView) -> str | None:
    """Return "v2_too_large" when the layout exceeds Discord's per-message V2 limits.

    discord.py already refuses to build a layout with more than 40 components
    (ValueError from add_item), so in practice this catches the text limit.
    """
    components = 0
    text_length = 0
    for item in layout.walk_children():
        components += 1
        if isinstance(item, discord.ui.TextDisplay):
            text_length += len(item.content or "")
    if components > V2_MAX_COMPONENTS or text_length > V2_MAX_TEXT:
        return "v2_too_large"
    return None


def _build_checked_layout(enforce_limits: bool, **layout_kwargs: Any) -> discord.ui.LayoutView:
    """build_layout_view; with enforce_limits an oversized layout raises LayoutTooLargeError."""
    if not enforce_limits:
        return build_layout_view(**layout_kwargs)
    try:
        layout = build_layout_view(**layout_kwargs)
    except ValueError as exc:  # discord.py: "maximum number of children exceeded (40)"
        raise LayoutTooLargeError("v2_too_large") from exc
    if layout_limit_error(layout):
        raise LayoutTooLargeError("v2_too_large")
    return layout


def build_stream_layout_view(
    *,
    embed: discord.Embed | None = None,
    content: str | None = None,
    source_view: discord.ui.View | None = None,
    keep_callbacks: bool = False,
    timeout: float | None = None,
    image_files: list[discord.File] | None = None,
) -> discord.ui.LayoutView:
    """Classic Juniper layout: greeting above the card, card without thumbnail or `[title](url)`."""
    layout = discord.ui.LayoutView(timeout=timeout)
    rows = interactive_rows_from_view(source_view, keep_callbacks=keep_callbacks)

    for block in _chunk_text(content or ""):
        if len(block) > _BLOCK_SOFT_MAX:
            for chunk in _chunk_text(block):
                layout.add_item(discord.ui.TextDisplay(chunk))
        else:
            layout.add_item(discord.ui.TextDisplay(block))

    if embed is not None:
        accent = _colour_value(embed)
        container = discord.ui.Container(accent_colour=accent)
        for block in stream_card_text_blocks(embed):
            if len(block) > _BLOCK_SOFT_MAX:
                for chunk in _chunk_text(block):
                    container.add_item(discord.ui.TextDisplay(chunk))
            else:
                container.add_item(discord.ui.TextDisplay(block))

        gallery_items: list[MediaGalleryItem] = []
        if embed.image and embed.image.url:
            gallery_items.append(MediaGalleryItem(embed.image.url))
        elif image_files:
            for f in image_files[:10]:
                gallery_items.append(MediaGalleryItem(f))
        # Intentionally ignore embed.thumbnail — Juniper card has no top-right avatar.

        if gallery_items:
            container.add_item(discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))
            container.add_item(discord.ui.MediaGallery(*gallery_items))

        for action_row in rows:
            container.add_item(action_row)

        if not container.children:
            container.add_item(discord.ui.TextDisplay("\u200b"))
        layout.add_item(container)
    else:
        for action_row in rows:
            layout.add_item(action_row)

    if not layout.children:
        layout.add_item(discord.ui.TextDisplay("\u200b"))
    return layout


def detach_layout_after_send(view: discord.ui.LayoutView | None) -> None:
    """Stop listening on a just-sent LayoutView so persistent classic Views handle clicks.

    Use when buttons were cloned with the same custom_ids as a bot.add_view(...)
    persistent View (customs lobby / map vote / score). Do NOT use when callbacks
    live only on the LayoutView (events participation).
    """
    if view is None:
        return
    try:
        view.stop()
    except Exception:
        pass


async def send_message(
    destination,
    *,
    version: Any = VERSION_V1,
    content: str | None = None,
    embed: discord.Embed | None = None,
    view: discord.ui.View | None = None,
    files: list[discord.File] | None = None,
    allowed_mentions: discord.AllowedMentions | None = None,
    keep_callbacks: bool = False,
    detach_layout: bool = True,
    stream_card: bool = False,
    embeds: list[discord.Embed] | None = None,
    enforce_limits: bool = False,
) -> discord.Message:
    """Send a classic (V1) or Components V2 message.

    Pass `embeds` (instead of `embed`) for a multi-embed message. With
    `enforce_limits`, an oversized V2 layout raises LayoutTooLargeError before sending.
    """
    if not is_v2(version):
        kwargs: dict[str, Any] = {"content": content, "view": view}
        if embeds is not None:
            kwargs["embeds"] = embeds
        else:
            kwargs["embed"] = embed
        if files:
            kwargs["files"] = files
        if allowed_mentions is not None:
            kwargs["allowed_mentions"] = allowed_mentions
        return await destination.send(**kwargs)

    layout_kwargs: dict[str, Any] = {
        "embed": embed,
        "content": content,
        "source_view": view,
        "keep_callbacks": keep_callbacks,
        "timeout": getattr(view, "timeout", None) if view is not None else None,
        "image_files": files,
    }
    if stream_card:
        layout = build_stream_layout_view(**layout_kwargs)
    else:
        layout = _build_checked_layout(enforce_limits, embeds=embeds, **layout_kwargs)
    kwargs = {"view": layout}
    # Attachments still work with V2 when referenced from MediaGallery via File.
    if files:
        kwargs["files"] = files
    if allowed_mentions is not None:
        kwargs["allowed_mentions"] = allowed_mentions
    message = await destination.send(**kwargs)
    if detach_layout and not keep_callbacks:
        detach_layout_after_send(layout)
    return message


async def edit_message(
    message: discord.Message,
    *,
    version: Any = VERSION_V1,
    content: str | None = discord.utils.MISSING,
    embed: discord.Embed | None = discord.utils.MISSING,
    view: discord.ui.View | None = discord.utils.MISSING,
    attachments: list[discord.File] | None = discord.utils.MISSING,
    keep_callbacks: bool = False,
    detach_layout: bool = True,
    embeds: list[discord.Embed] = discord.utils.MISSING,
    enforce_limits: bool = False,
) -> discord.Message:
    """Edit a message as classic V1 or Components V2.

    `embeds` replaces every embed of the message (an empty list removes them all).
    """
    if not is_v2(version):
        kwargs: dict[str, Any] = {}
        if content is not discord.utils.MISSING:
            kwargs["content"] = content
        if embeds is not discord.utils.MISSING:
            kwargs["embeds"] = embeds or []
        elif embed is not discord.utils.MISSING:
            kwargs["embed"] = embed
        if view is not discord.utils.MISSING:
            kwargs["view"] = view
        if attachments is not discord.utils.MISSING:
            kwargs["attachments"] = attachments or []
        return await message.edit(**kwargs)

    # Prefer explicit embed; fall back to existing first embed for V1→V2 migrations.
    resolved_embed = None if embed is discord.utils.MISSING else embed
    if resolved_embed is None and embed is discord.utils.MISSING and message.embeds:
        resolved_embed = message.embeds[0]

    resolved_content = None if content is discord.utils.MISSING else content
    resolved_view = None if view is discord.utils.MISSING else view
    file_list = None if attachments is discord.utils.MISSING else (attachments or None)

    layout = _build_checked_layout(
        enforce_limits,
        embed=resolved_embed,
        embeds=None if embeds is discord.utils.MISSING else (embeds or []),
        content=resolved_content,
        source_view=resolved_view,
        keep_callbacks=keep_callbacks,
        timeout=getattr(resolved_view, "timeout", None) if resolved_view is not None else None,
        image_files=file_list,
    )
    kwargs: dict[str, Any] = {
        "content": None,
        "embeds": [],
        "view": layout,
    }
    if attachments is not discord.utils.MISSING:
        kwargs["attachments"] = attachments or []
    edited = await message.edit(**kwargs)
    if detach_layout and not keep_callbacks:
        detach_layout_after_send(layout)
    return edited
