"""Генерация PNG-карточки ранга (аватар, уровень, прогресс-бар, место в топе).

Фон настраивается через дашборд (файл xp_card_bg.png); если фона нет —
рисуется градиент в фирменных цветах.
"""

import io
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import xp_core

CARD_W, CARD_H = 900, 260

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


def _background() -> Image.Image:
    if os.path.exists(xp_core.CARD_BG_FILE):
        try:
            bg = Image.open(xp_core.CARD_BG_FILE).convert("RGB")
            bg = bg.resize((CARD_W, CARD_H))
            # Затемняем, чтобы текст читался на любом фоне
            overlay = Image.new("RGB", (CARD_W, CARD_H), (11, 14, 20))
            return Image.blend(bg, overlay, 0.45)
        except OSError:
            pass

    # Градиентный дефолт в цветах дашборда
    bg = Image.new("RGB", (CARD_W, CARD_H), (11, 14, 20))
    draw = ImageDraw.Draw(bg)
    for x in range(CARD_W):
        t = x / CARD_W
        r = int(19 + (88 - 19) * t * 0.35)
        g = int(23 + (101 - 23) * t * 0.35)
        b = int(34 + (242 - 34) * t * 0.35)
        draw.line([(x, 0), (x, CARD_H)], fill=(r, g, b))
    return bg


def _circle_avatar(avatar_bytes: bytes, size: int) -> Image.Image:
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGB").resize((size, size))
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4, size * 4), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    avatar.putalpha(mask)
    return avatar


def render_rank_card(
    avatar_bytes: bytes | None,
    display_name: str,
    level: int,
    xp_into_level: int,
    xp_step: int,
    rank: int | None,
    total_members: int,
    voice_time_text: str,
) -> bytes:
    card = _background().convert("RGBA")
    draw = ImageDraw.Draw(card)

    # Полупрозрачная плашка
    panel = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle((16, 16, CARD_W - 16, CARD_H - 16), radius=22, fill=(13, 17, 26, 160))
    card = Image.alpha_composite(card, panel)
    draw = ImageDraw.Draw(card)

    # Аватар
    avatar_size = 160
    ax, ay = 46, (CARD_H - avatar_size) // 2
    if avatar_bytes:
        try:
            avatar = _circle_avatar(avatar_bytes, avatar_size)
            # Кольцо вокруг аватара
            ring = Image.new("RGBA", (avatar_size + 12, avatar_size + 12), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse((0, 0, avatar_size + 12, avatar_size + 12), outline=(88, 101, 242, 255), width=4)
            card.alpha_composite(ring, (ax - 6, ay - 6))
            card.alpha_composite(avatar, (ax, ay))
        except OSError:
            pass

    font_name = _font(FONT_CANDIDATES_BOLD, 38)
    font_level = _font(FONT_CANDIDATES_BOLD, 30)
    font_small = _font(FONT_CANDIDATES_REGULAR, 22)

    text_x = ax + avatar_size + 36

    # Имя
    name = display_name if len(display_name) <= 22 else display_name[:21] + "…"
    draw.text((text_x, 52), name, font=font_name, fill=(232, 234, 240))

    # Уровень и место
    rank_text = f"#{rank}" if rank else "—"
    draw.text((text_x, 104), f"Уровень {level}", font=font_level, fill=(88, 101, 242))
    level_w = draw.textlength(f"Уровень {level}", font=font_level)
    draw.text((text_x + level_w + 28, 110), f"Ранг {rank_text} из {total_members}", font=font_small, fill=(139, 147, 167))

    # Войс-время
    draw.text((text_x, 148), f"🔊 В войсе: {voice_time_text}", font=font_small, fill=(139, 147, 167))

    # Прогресс-бар
    bar_x0, bar_y0 = text_x, 196
    bar_x1, bar_y1 = CARD_W - 56, 220
    draw.rounded_rectangle((bar_x0, bar_y0, bar_x1, bar_y1), radius=12, fill=(35, 40, 56))
    if xp_step > 0:
        progress = max(0.0, min(1.0, xp_into_level / xp_step))
        fill_x1 = bar_x0 + max(24, int((bar_x1 - bar_x0) * progress))
        draw.rounded_rectangle((bar_x0, bar_y0, fill_x1, bar_y1), radius=12, fill=(88, 101, 242))
        xp_text = f"{xp_into_level} / {xp_step} XP"
    else:
        draw.rounded_rectangle((bar_x0, bar_y0, bar_x1, bar_y1), radius=12, fill=(88, 101, 242))
        xp_text = "MAX"
    text_w = draw.textlength(xp_text, font=font_small)
    draw.text((bar_x1 - text_w, bar_y0 - 30), xp_text, font=font_small, fill=(139, 147, 167))

    out = io.BytesIO()
    card.convert("RGB").save(out, format="PNG")
    return out.getvalue()
