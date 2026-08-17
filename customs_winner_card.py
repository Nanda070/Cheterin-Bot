"""Animated customs result card — dark VALORANT frame, winner line, and score."""

from __future__ import annotations

import os
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

CARD_W, CARD_H = 800, 360
BG = "#10131a"
ACCENT = "#ff4655"
ACCENT_SOFT = "#ff7680"
TEXT = "#e8e8e8"
MUTED = "#9ca3af"
SCORE = "#ffffff"
BRAND = "VALORANTCUSTOMS"

FONT_BOLD = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_REG = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def build_winner_gif(title: str, winner_line: str, score_a: int, score_b: int) -> BytesIO:
    """Return a two-frame GIF. Layout matches the customs result mock (text, no agent art)."""
    title_font = _font(FONT_REG, 22)
    winner_font = _font(FONT_BOLD, 36)
    score_font = _font(FONT_BOLD, 64)
    brand_font = _font(FONT_REG, 18)
    frames: list[Image.Image] = []
    for accent in (ACCENT, ACCENT_SOFT):
        image = Image.new("RGB", (CARD_W, CARD_H), BG)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, CARD_W, 16), fill=accent)
        draw.rectangle((32, 52, CARD_W - 32, CARD_H - 36), outline=accent, width=3)
        draw.text((55, 72), (title or "")[:72], fill=TEXT, font=title_font)
        draw.text((55, 118), (winner_line or "")[:64], fill=accent, font=winner_font)
        draw.text((55, 178), f"{score_a} : {score_b}", fill=SCORE, font=score_font)
        draw.text((55, 270), BRAND, fill=MUTED, font=brand_font)
        frames.append(image)
    output = BytesIO()
    frames[0].save(output, format="GIF", save_all=True, append_images=frames[1:], duration=550, loop=0)
    output.seek(0)
    output.name = "customs-winner.gif"
    return output
