"""PNG quote cards — dark Cheterin crimson aesthetic."""

from __future__ import annotations

import io
import os

from PIL import Image, ImageDraw, ImageFont, ImageOps

CARD_W = 900
PAD = 40
AVATAR = 96
ACCENT = (212, 69, 86)
BG = (14, 12, 16)
PANEL = (22, 18, 24)
TEXT = (236, 232, 230)
MUTED = (160, 150, 148)
QUOTE_MARK = (212, 69, 86, 180)
# Keep photos readable on Discord clients (was easy to miss at 200px).
MAX_ATTACH_W = CARD_W - 2 * PAD - 24
MAX_ATTACH_H = 360

FONT_BOLD = [
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_REG = [
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

MAX_QUOTE_CHARS = 500


def _font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _load_rgb(image_bytes: bytes) -> Image.Image:
    """Decode first frame; honour EXIF orientation (phone photos)."""
    raw = Image.open(io.BytesIO(image_bytes))
    try:
        raw.seek(0)
    except EOFError:
        pass
    raw = ImageOps.exif_transpose(raw) or raw
    return raw.convert("RGB")


def _circle_avatar(avatar_bytes: bytes | None, size: int) -> Image.Image:
    if avatar_bytes:
        try:
            avatar = _load_rgb(avatar_bytes).resize((size, size), Image.LANCZOS)
        except OSError:
            avatar = Image.new("RGB", (size, size), (60, 50, 55))
    else:
        avatar = Image.new("RGB", (size, size), (60, 50, 55))
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    avatar.putalpha(mask)
    return avatar


def _truncate(text: str, max_len: int = MAX_QUOTE_CHARS) -> str:
    text = (text or "").strip()
    if not text:
        return "…"
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _wrap_lines(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    # Character wrap with measured width (CJK-safe enough via char chunks)
    words = text.replace("\r", "").split("\n")
    lines: list[str] = []
    for paragraph in words:
        if not paragraph:
            lines.append("")
            continue
        # Prefer space wrap; fall back to char wrap for long tokens
        chunks = paragraph.split(" ")
        current = ""
        for chunk in chunks:
            candidate = f"{current} {chunk}".strip() if current else chunk
            if draw.textlength(candidate, font=font) <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            # Long single token
            if draw.textlength(chunk, font=font) <= max_width:
                current = chunk
            else:
                buf = ""
                for ch in chunk:
                    if draw.textlength(buf + ch, font=font) <= max_width:
                        buf += ch
                    else:
                        if buf:
                            lines.append(buf)
                        buf = ch
                current = buf
        if current:
            lines.append(current)
    if not lines:
        lines = ["…"]
    return lines[:18]


def render_quote_card(
    *,
    display_name: str,
    quote_text: str,
    avatar_bytes: bytes | None = None,
    attachment_bytes: bytes | None = None,
) -> bytes:
    """Render a dark quote PNG; returns PNG bytes."""
    name = (display_name or "Unknown").strip() or "Unknown"
    quote = _truncate(quote_text)

    font_name = _font(FONT_BOLD, 28)
    font_quote = _font(FONT_REG, 26)
    font_mark = _font(FONT_BOLD, 120)

    text_x = PAD + AVATAR + 28
    text_max_w = CARD_W - text_x - PAD

    # Measure quote height with a temporary draw surface
    probe = Image.new("RGB", (CARD_W, 200), BG)
    probe_draw = ImageDraw.Draw(probe)
    lines = _wrap_lines(probe_draw, quote, font_quote, text_max_w)
    line_h = 34
    quote_h = max(line_h, len(lines) * line_h)

    thumb_h = 0
    thumb_img = None
    if attachment_bytes:
        try:
            raw = _load_rgb(attachment_bytes)
            scale = min(MAX_ATTACH_W / max(1, raw.width), MAX_ATTACH_H / max(1, raw.height), 1.0)
            tw = max(1, int(raw.width * scale))
            th = max(1, int(raw.height * scale))
            thumb_img = raw.resize((tw, th), Image.LANCZOS)
            thumb_h = th + 24
        except OSError:
            thumb_img = None

    header_h = max(AVATAR, 48) + 16
    # Extra space for oversized opening quote mark above the body
    card_h = PAD + header_h + 28 + quote_h + thumb_h + PAD + 8

    card = Image.new("RGB", (CARD_W, card_h), BG)
    draw = ImageDraw.Draw(card)

    # Accent bar on left
    draw.rectangle((0, 0, 8, card_h), fill=ACCENT)

    # Soft panel
    draw.rounded_rectangle(
        (16, 16, CARD_W - 16, card_h - 16),
        radius=20,
        fill=PANEL,
        outline=(40, 32, 38),
        width=1,
    )

    # Avatar
    avatar = _circle_avatar(avatar_bytes, AVATAR)
    card_rgba = card.convert("RGBA")
    card_rgba.paste(avatar, (PAD, PAD), avatar)

    # Name + accent underline
    name_y = PAD + 18
    draw = ImageDraw.Draw(card_rgba)
    draw.text((text_x, name_y), name, font=font_name, fill=TEXT)
    name_w = int(draw.textlength(name, font=font_name))
    draw.rectangle(
        (text_x, name_y + 36, text_x + min(name_w, 220), name_y + 40),
        fill=ACCENT,
    )

    # Large quote mark (taller glyph so it reads as a design accent)
    draw.text((text_x - 6, PAD + header_h - 28), "“", font=font_mark, fill=QUOTE_MARK)

    # Quote body — leave room under the oversized mark
    qy = PAD + header_h + 36
    for i, line in enumerate(lines):
        draw.text((text_x, qy + i * line_h), line, font=font_quote, fill=TEXT)

    # Optional attachment photo (full-width under the quote text)
    if thumb_img is not None:
        ty = qy + quote_h + 12
        tx = PAD + 24
        card_rgba.paste(thumb_img.convert("RGBA"), (tx, ty))

    out = io.BytesIO()
    card_rgba.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()
