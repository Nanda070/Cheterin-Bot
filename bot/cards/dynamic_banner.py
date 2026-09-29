"""Pillow renderer for Cheterin dynamic Discord server banners.

Discord recommended banner size: 960×540. Cheterin crimson/dark aesthetic
(matches profile_card / dashboard --color-primary). Output is RGB PNG —
Discord often returns 500/internal_error for awkward encodings, not Missing Permissions.
"""

from __future__ import annotations

import io
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from bot.cards.discord_banner_bytes import BANNER_H, BANNER_W, image_to_discord_png

ACCENT = (212, 69, 86)
ACCENT_DIM = (140, 40, 55)
TEXT = (236, 232, 230)
MUTED = (160, 150, 148)
PANEL = (10, 12, 18, 190)

FONT_CANDIDATES_BOLD = [
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_CANDIDATES_REGULAR = [
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

LABELS = {
    "ru": {
        "most_active": "Самый активный",
        "members": "Участники",
        "in_voice": "В войсе",
        "nobody": "Пока никого",
        "brand": "Cheterin",
    },
    "en": {
        "most_active": "Most active",
        "members": "Members",
        "in_voice": "In voice",
        "nobody": "Nobody yet",
        "brand": "Cheterin",
    },
}


def _font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _background() -> Image.Image:
    bg = Image.new("RGB", (BANNER_W, BANNER_H), (14, 10, 14))
    draw = ImageDraw.Draw(bg)
    for x in range(BANNER_W):
        t = x / BANNER_W
        r = _lerp(16, ACCENT[0], t * 0.42)
        g = _lerp(11, ACCENT[1], t * 0.26)
        b = _lerp(15, ACCENT[2], t * 0.30)
        draw.line([(x, 0), (x, BANNER_H)], fill=(r, g, b))
    return bg


def _vignette(size: tuple[int, int], strength: int = 160) -> Image.Image:
    w, h = size
    layer = Image.new("L", (w, h), 0)
    ImageDraw.Draw(layer).ellipse((-w // 5, -h // 4, w + w // 5, h + h // 3), fill=255)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=56))
    inv = Image.eval(layer, lambda p: 255 - p)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.putalpha(Image.eval(inv, lambda p: min(strength, p)))
    return out


def _circle_avatar(avatar_bytes: bytes | None, size: int) -> Image.Image:
    if avatar_bytes:
        try:
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGB").resize((size, size), Image.LANCZOS)
        except OSError:
            avatar = Image.new("RGB", (size, size), ACCENT_DIM)
    else:
        avatar = Image.new("RGB", (size, size), ACCENT_DIM)
        d = ImageDraw.Draw(avatar)
        d.ellipse((size // 4, size // 4, size * 3 // 4, size * 3 // 4), fill=ACCENT)

    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    avatar.putalpha(mask)
    return avatar


def _soft_glow(color: tuple[int, int, int], size: int, blur: int, alpha: int) -> Image.Image:
    pad = blur * 2
    canvas = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(canvas).ellipse(
        (pad, pad, pad + size - 1, pad + size - 1),
        fill=(*color, alpha),
    )
    return canvas.filter(ImageFilter.GaussianBlur(radius=blur))


def _stat_block(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    label: str,
    value: str,
    font_label: ImageFont.ImageFont,
    font_value: ImageFont.ImageFont,
    width: int,
) -> None:
    x, y = xy
    draw.rounded_rectangle(
        (x, y, x + width, y + 88),
        radius=16,
        fill=(20, 16, 22, 210),
        outline=(*ACCENT, 70),
        width=1,
    )
    draw.text((x + 18, y + 14), label, font=font_label, fill=MUTED)
    draw.text((x + 18, y + 40), value, font=font_value, fill=TEXT)


def render_dynamic_banner(
    *,
    display_name: str | None,
    avatar_bytes: bytes | None,
    member_count: int,
    voice_count: int,
    guild_name: str = "",
    lang: str = "ru",
) -> bytes:
    """Return Discord-safe PNG bytes for ``guild.edit(banner=...)``."""
    labels = LABELS.get(lang) or LABELS["ru"]
    card = _background().convert("RGBA")

    wash = Image.new("RGBA", (BANNER_W, BANNER_H), (0, 0, 0, 0))
    wash_draw = ImageDraw.Draw(wash)
    for i in range(260):
        a = int(32 * (1 - i / 260))
        wash_draw.ellipse(
            (BANNER_W - 420 + i, -100 + i // 2, BANNER_W + 60 - i // 3, 300 - i // 2),
            fill=(*ACCENT, a),
        )
    card = Image.alpha_composite(card, wash)
    card = Image.alpha_composite(card, _vignette((BANNER_W, BANNER_H)))

    panel = Image.new("RGBA", (BANNER_W, BANNER_H), (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle(
        (24, 24, BANNER_W - 24, BANNER_H - 24),
        radius=28,
        fill=PANEL,
        outline=(*ACCENT_DIM, 80),
        width=1,
    )
    card = Image.alpha_composite(card, panel)
    draw = ImageDraw.Draw(card)

    font_brand = _font(FONT_CANDIDATES_BOLD, 22)
    font_label = _font(FONT_CANDIDATES_REGULAR, 20)
    font_name = _font(FONT_CANDIDATES_BOLD, 42)
    font_stat_label = _font(FONT_CANDIDATES_REGULAR, 18)
    font_stat_value = _font(FONT_CANDIDATES_BOLD, 32)
    font_guild = _font(FONT_CANDIDATES_REGULAR, 18)

    draw.text((48, 40), labels["brand"], font=font_brand, fill=ACCENT)
    if guild_name:
        draw.text((48, 68), _truncate(guild_name, 42), font=font_guild, fill=MUTED)

    avatar_size = 168
    ax, ay = 56, 140
    ring_pad = 10
    glow = _soft_glow(ACCENT, avatar_size + ring_pad * 2, blur=18, alpha=110)
    card.alpha_composite(glow, (ax - ring_pad - 18, ay - ring_pad - 18))
    draw.ellipse(
        (ax - ring_pad, ay - ring_pad, ax + avatar_size + ring_pad, ay + avatar_size + ring_pad),
        outline=(*ACCENT, 255),
        width=4,
    )
    avatar = _circle_avatar(avatar_bytes, avatar_size)
    card.alpha_composite(avatar, (ax, ay))

    name_x = ax + avatar_size + 36
    draw.text((name_x, ay + 28), labels["most_active"], font=font_label, fill=MUTED)
    shown = _truncate(display_name or labels["nobody"], 22)
    draw.text((name_x, ay + 62), shown, font=font_name, fill=TEXT)

    block_w = 200
    gap = 16
    total_w = block_w * 2 + gap
    bx = BANNER_W - 48 - total_w
    by = BANNER_H - 48 - 88
    _stat_block(draw, (bx, by), labels["members"], f"{member_count:,}", font_stat_label, font_stat_value, block_w)
    _stat_block(
        draw,
        (bx + block_w + gap, by),
        labels["in_voice"],
        str(voice_count),
        font_stat_label,
        font_stat_value,
        block_w,
    )

    return image_to_discord_png(card, size=(BANNER_W, BANNER_H))
