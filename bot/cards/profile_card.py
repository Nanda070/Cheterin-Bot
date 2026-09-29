"""Premium MEE6-style profile / rank card (PNG + short looping GIF).

Cheterin crimson/dark aesthetic. Optional guild background via
``xp_core.get_card_bg_path``. Cosmetics: frame ring colour + title badge.
"""

from __future__ import annotations

import io
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import bot.core.i18n as i18n
import bot.modules.levels.xp_core as xp_core

CARD_W, CARD_H = 1000, 360
# Soft crimson accent (matches dashboard --color-primary)
ACCENT = (212, 69, 86)
ACCENT_DIM = (140, 40, 55)
DEFAULT_RING = ACCENT
PANEL = (10, 12, 18, 175)
TEXT = (236, 232, 230)
MUTED = (160, 150, 148)
BAR_TRACK = (32, 28, 34)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


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


def _font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _background(guild_id: int) -> Image.Image:
    path = xp_core.get_card_bg_path(guild_id)
    if os.path.exists(path):
        try:
            bg = Image.open(path).convert("RGB").resize((CARD_W, CARD_H))
            overlay = Image.new("RGB", (CARD_W, CARD_H), (12, 10, 14))
            return Image.blend(bg, overlay, 0.50)
        except OSError:
            pass

    # Horizontal crimson wash (fast scanline gradient)
    bg = Image.new("RGB", (CARD_W, CARD_H), (14, 10, 14))
    draw = ImageDraw.Draw(bg)
    for x in range(CARD_W):
        t = x / CARD_W
        r = _lerp(16, ACCENT[0], t * 0.40)
        g = _lerp(11, ACCENT[1], t * 0.26)
        b = _lerp(15, ACCENT[2], t * 0.30)
        draw.line([(x, 0), (x, CARD_H)], fill=(r, g, b))
    return bg


def _vignette(size: tuple[int, int], strength: int = 140) -> Image.Image:
    w, h = size
    layer = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(layer)
    draw.ellipse((-w // 5, -h // 4, w + w // 5, h + h // 3), fill=255)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=48))
    # Invert so edges are dark
    inv = Image.eval(layer, lambda p: 255 - p)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.putalpha(Image.eval(inv, lambda p: min(strength, p)))
    return out


def _circle_avatar(avatar_bytes: bytes, size: int) -> Image.Image:
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGB").resize((size, size), Image.LANCZOS)
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


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _progress(xp_into_level: int, xp_step: int) -> float:
    if xp_step <= 0:
        return 1.0
    return max(0.0, min(1.0, xp_into_level / xp_step))


def _draw_stat_chip(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    label: str,
    value: str,
    font_label: ImageFont.ImageFont,
    font_value: ImageFont.ImageFont,
    accent: tuple[int, int, int],
) -> int:
    """Draw a compact label/value chip; returns width consumed."""
    x, y = xy
    pad_x, pad_y = 14, 8
    gap = 4
    lw = draw.textlength(label, font=font_label)
    vw = draw.textlength(value, font=font_value)
    chip_w = int(max(lw, vw) + pad_x * 2)
    chip_h = 52
    draw.rounded_rectangle(
        (x, y, x + chip_w, y + chip_h),
        radius=12,
        fill=(20, 16, 22, 200),
        outline=(*accent, 90),
        width=1,
    )
    draw.text((x + pad_x, y + pad_y), label, font=font_label, fill=MUTED)
    draw.text((x + pad_x, y + pad_y + 18 + gap), value, font=font_value, fill=TEXT)
    return chip_w


def _compose_card(
    guild_id: int,
    avatar_bytes: bytes | None,
    display_name: str,
    level: int,
    xp_into_level: int,
    xp_step: int,
    rank: int | None,
    total_members: int,
    voice_time_text: str,
    *,
    frame_color: str | None = None,
    title_text: str | None = None,
    messages: int | None = None,
    balance: int | None = None,
    streak: int | None = None,
    lang: str = "ru",
    glow_boost: float = 0.0,
    shimmer_t: float = 0.0,
) -> Image.Image:
    """Build one RGBA frame. ``glow_boost`` 0–1 pulses ring glow; ``shimmer_t`` 0–1 moves XP sheen."""
    card = _background(guild_id).convert("RGBA")

    # Soft accent wash top-right
    wash = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    wash_draw = ImageDraw.Draw(wash)
    for i in range(220):
        a = int(28 * (1 - i / 220))
        wash_draw.ellipse(
            (CARD_W - 380 + i, -80 + i // 2, CARD_W + 40 - i // 3, 260 - i // 2),
            fill=(*ACCENT, a),
        )
    card = Image.alpha_composite(card, wash)
    card = Image.alpha_composite(card, _vignette((CARD_W, CARD_H), strength=150))

    panel = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle(
        (18, 18, CARD_W - 18, CARD_H - 18),
        radius=28,
        fill=PANEL,
        outline=(*ACCENT_DIM, 70),
        width=1,
    )
    card = Image.alpha_composite(card, panel)
    draw = ImageDraw.Draw(card)

    ring_color = _hex_to_rgb(frame_color) if frame_color else DEFAULT_RING
    avatar_size = 196
    ax, ay = 52, (CARD_H - avatar_size) // 2
    ring_pad = 14
    glow_alpha = int(90 + 80 * glow_boost)

    # Outer soft glow
    glow = _soft_glow(ring_color, avatar_size + ring_pad * 2, blur=22, alpha=glow_alpha)
    card.alpha_composite(glow, (ax - ring_pad - 22, ay - ring_pad - 22))

    # Ring
    ring_box = (
        ax - ring_pad,
        ay - ring_pad,
        ax + avatar_size + ring_pad,
        ay + avatar_size + ring_pad,
    )
    draw.ellipse(ring_box, outline=(*ring_color, 255), width=5)
    # Inner thin highlight
    draw.ellipse(
        (ax - 4, ay - 4, ax + avatar_size + 4, ay + avatar_size + 4),
        outline=(255, 255, 255, 40),
        width=2,
    )

    if avatar_bytes:
        try:
            card.alpha_composite(_circle_avatar(avatar_bytes, avatar_size), (ax, ay))
        except OSError:
            draw.ellipse((ax, ay, ax + avatar_size, ay + avatar_size), fill=(40, 32, 38))
    else:
        draw.ellipse((ax, ay, ax + avatar_size, ay + avatar_size), fill=(40, 32, 38))
        initial = (display_name[:1] or "?").upper()
        font_init = _font(FONT_CANDIDATES_BOLD, 72)
        tw = draw.textlength(initial, font=font_init)
        draw.text(
            (ax + (avatar_size - tw) / 2, ay + avatar_size / 2 - 40),
            initial,
            font=font_init,
            fill=ring_color,
        )

    font_name = _font(FONT_CANDIDATES_BOLD, 40)
    font_title = _font(FONT_CANDIDATES_BOLD, 18)
    font_level = _font(FONT_CANDIDATES_BOLD, 28)
    font_small = _font(FONT_CANDIDATES_REGULAR, 20)
    font_chip_label = _font(FONT_CANDIDATES_REGULAR, 14)
    font_chip_value = _font(FONT_CANDIDATES_BOLD, 18)
    font_xp = _font(FONT_CANDIDATES_REGULAR, 18)

    text_x = ax + avatar_size + ring_pad + 36
    name = _truncate(display_name, 24)
    name_y = 48
    draw.text((text_x, name_y), name, font=font_name, fill=TEXT)

    if title_text:
        tag = _truncate(title_text, 28)
        name_w = draw.textlength(name, font=font_name)
        tag_w = draw.textlength(tag, font=font_title)
        tag_x = text_x + name_w + 16
        tag_y = name_y + 8
        pad = 10
        draw.rounded_rectangle(
            (tag_x, tag_y, tag_x + tag_w + pad * 2, tag_y + 28),
            radius=10,
            fill=(*ring_color, 55),
            outline=(*ring_color, 200),
            width=1,
        )
        draw.text((tag_x + pad, tag_y + 4), tag, font=font_title, fill=TEXT)

    rank_text = f"#{rank}" if rank else "—"
    level_label = i18n.t("xp.card.level", lang, level=level)
    rank_label = i18n.t("xp.card.rank", lang, rank=rank_text, total=total_members)
    draw.text((text_x, 104), level_label, font=font_level, fill=ring_color)
    level_w = draw.textlength(level_label, font=font_level)
    draw.text((text_x + level_w + 22, 110), rank_label, font=font_small, fill=MUTED)

    # XP bar
    progress = _progress(xp_into_level, xp_step)
    bar_x0, bar_y0 = text_x, 158
    bar_x1, bar_y1 = CARD_W - 48, 186
    bar_h = bar_y1 - bar_y0
    draw.rounded_rectangle((bar_x0, bar_y0, bar_x1, bar_y1), radius=14, fill=BAR_TRACK)

    fill_w = bar_x1 - bar_x0
    if progress >= 1.0 and xp_step <= 0:
        fill_x1 = bar_x1
        xp_text = "MAX"
        pct_text = "100%"
    else:
        fill_x1 = bar_x0 + max(28, int(fill_w * progress))
        xp_text = f"{xp_into_level} / {xp_step} XP"
        pct_text = f"{int(progress * 100)}%"

    # Gradient-ish fill via two rounded rects
    draw.rounded_rectangle((bar_x0, bar_y0, fill_x1, bar_y1), radius=14, fill=ring_color)
    # Lighter top edge
    mid_y = bar_y0 + bar_h // 2
    draw.rounded_rectangle(
        (bar_x0 + 2, bar_y0 + 2, fill_x1 - 2, mid_y),
        radius=10,
        fill=(*tuple(min(255, c + 40) for c in ring_color), 90),
    )

    # Shimmer band on fill
    if fill_x1 > bar_x0 + 40:
        sheen_w = 36
        sheen_x = bar_x0 + int((fill_x1 - bar_x0 - sheen_w) * shimmer_t)
        sheen = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
        ImageDraw.Draw(sheen).rectangle(
            (sheen_x, bar_y0 + 2, sheen_x + sheen_w, bar_y1 - 2),
            fill=(255, 255, 255, 55),
        )
        sheen = sheen.filter(ImageFilter.GaussianBlur(radius=6))
        # Clip to bar fill roughly via mask
        mask = Image.new("L", (CARD_W, CARD_H), 0)
        ImageDraw.Draw(mask).rounded_rectangle((bar_x0, bar_y0, fill_x1, bar_y1), radius=14, fill=255)
        sheen.putalpha(Image.composite(sheen.split()[3], Image.new("L", (CARD_W, CARD_H), 0), mask))
        card = Image.alpha_composite(card, sheen)
        draw = ImageDraw.Draw(card)

    xp_w = draw.textlength(xp_text, font=font_xp)
    draw.text((bar_x0, bar_y0 - 26), pct_text, font=font_xp, fill=MUTED)
    draw.text((bar_x1 - xp_w, bar_y0 - 26), xp_text, font=font_xp, fill=MUTED)

    # Stat chips
    chip_y = 214
    chip_x = text_x
    chips: list[tuple[str, str]] = []
    if messages is not None:
        chips.append((i18n.t("xp.card.messages", lang), f"{messages:,}"))
    chips.append((i18n.t("xp.card.voice_label", lang), voice_time_text))
    if balance is not None:
        chips.append((i18n.t("xp.card.balance", lang), f"{balance:,}"))
    if streak is not None and streak > 0:
        chips.append((i18n.t("xp.card.streak", lang), f"{streak}"))

    for label, value in chips:
        w = _draw_stat_chip(
            draw, (chip_x, chip_y), label, value, font_chip_label, font_chip_value, ring_color
        )
        chip_x += w + 10
        if chip_x > CARD_W - 80:
            break

    # Brand whisper bottom-right
    brand = _font(FONT_CANDIDATES_REGULAR, 14)
    brand_text = "CHETERIN"
    bw = draw.textlength(brand_text, font=brand)
    draw.text((CARD_W - 48 - bw, CARD_H - 42), brand_text, font=brand, fill=(ACCENT[0], ACCENT[1], ACCENT[2], 110))

    return card


def render_profile_card(
    guild_id: int,
    avatar_bytes: bytes | None,
    display_name: str,
    level: int,
    xp_into_level: int,
    xp_step: int,
    rank: int | None,
    total_members: int,
    voice_time_text: str,
    *,
    frame_color: str | None = None,
    title_text: str | None = None,
    messages: int | None = None,
    balance: int | None = None,
    streak: int | None = None,
    lang: str = "ru",
) -> bytes:
    card = _compose_card(
        guild_id,
        avatar_bytes,
        display_name,
        level,
        xp_into_level,
        xp_step,
        rank,
        total_members,
        voice_time_text,
        frame_color=frame_color,
        title_text=title_text,
        messages=messages,
        balance=balance,
        streak=streak,
        lang=lang,
        glow_boost=0.35,
        shimmer_t=0.35,
    )
    out = io.BytesIO()
    card.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()


def render_profile_card_gif(
    guild_id: int,
    avatar_bytes: bytes | None,
    display_name: str,
    level: int,
    xp_into_level: int,
    xp_step: int,
    rank: int | None,
    total_members: int,
    voice_time_text: str,
    *,
    frame_color: str | None = None,
    title_text: str | None = None,
    messages: int | None = None,
    balance: int | None = None,
    streak: int | None = None,
    lang: str = "ru",
    frames: int = 10,
    duration_ms: int = 90,
) -> bytes:
    """Short looping GIF: avatar-ring glow pulse + XP bar shimmer."""
    frames = max(6, min(14, frames))
    images: list[Image.Image] = []
    for i in range(frames):
        phase = i / frames
        glow = 0.25 + 0.55 * (0.5 + 0.5 * math.sin(phase * math.tau))
        shimmer = (phase + 0.15) % 1.0
        frame = _compose_card(
            guild_id,
            avatar_bytes,
            display_name,
            level,
            xp_into_level,
            xp_step,
            rank,
            total_members,
            voice_time_text,
            frame_color=frame_color,
            title_text=title_text,
            messages=messages,
            balance=balance,
            streak=streak,
            lang=lang,
            glow_boost=glow,
            shimmer_t=shimmer,
        )
        # Palette GIF keeps size reasonable
        images.append(frame.convert("P", palette=Image.ADAPTIVE, colors=196))

    out = io.BytesIO()
    images[0].save(
        out,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return out.getvalue()
