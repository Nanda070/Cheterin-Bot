"""PNG-карточки Вордла в стиле оригинального Discord-приложения.

Карточка «X играет»: аватар игрока + сетка цветов БЕЗ букв (спойлер-фри).
Сводная карточка дня: несколько игроков рядом — аватар над сеткой.
Шрифты/аватар — те же приёмы, что в xp_card.py.
"""

import io
import os

from PIL import Image, ImageDraw, ImageFont

import wordle_core

# Палитра оригинального Wordle (тёмная тема)
BG = (17, 18, 19)
PANEL = (26, 26, 27)
PANEL_OUTLINE = (58, 58, 60)
TILE_GREEN = (83, 141, 78)
TILE_YELLOW = (181, 159, 59)
TILE_GRAY = (58, 58, 60)
TILE_EMPTY = (34, 34, 36)
TEXT = (232, 234, 240)

TILE_STATE_COLORS = {
    wordle_core.GREEN: TILE_GREEN,
    wordle_core.YELLOW: TILE_YELLOW,
    wordle_core.GRAY: TILE_GRAY,
}

CELL = 40
CELL_GAP = 6

FONT_CANDIDATES_BOLD = [
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES_BOLD:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _circle_avatar(avatar_bytes: bytes, size: int) -> Image.Image:
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGB").resize((size, size))
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4, size * 4), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    avatar.putalpha(mask)
    return avatar


def _placeholder_avatar(size: int) -> Image.Image:
    avatar = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(avatar).ellipse((0, 0, size, size), fill=(88, 101, 242, 255))
    return avatar


def _avatar_image(avatar_bytes: bytes | None, size: int) -> Image.Image:
    if avatar_bytes:
        try:
            return _circle_avatar(avatar_bytes, size)
        except OSError:
            pass
    return _placeholder_avatar(size)


def _grid_size() -> tuple[int, int]:
    w = wordle_core.WORD_LEN * CELL + (wordle_core.WORD_LEN - 1) * CELL_GAP
    h = wordle_core.MAX_ATTEMPTS * CELL + (wordle_core.MAX_ATTEMPTS - 1) * CELL_GAP
    return w, h


def _draw_grid(draw: ImageDraw.ImageDraw, x0: int, y0: int, states_rows: list[str]) -> None:
    """Сетка 6×5: заполненные ряды цветами, остальные — пустые клетки."""
    for row in range(wordle_core.MAX_ATTEMPTS):
        states = states_rows[row] if row < len(states_rows) else ""
        for col in range(wordle_core.WORD_LEN):
            cx = x0 + col * (CELL + CELL_GAP)
            cy = y0 + row * (CELL + CELL_GAP)
            if col < len(states):
                color = TILE_STATE_COLORS.get(states[col], TILE_EMPTY)
                draw.rounded_rectangle((cx, cy, cx + CELL, cy + CELL), radius=6, fill=color)
            else:
                draw.rounded_rectangle(
                    (cx, cy, cx + CELL, cy + CELL), radius=6, fill=TILE_EMPTY, outline=PANEL_OUTLINE, width=2
                )


def render_playing_card(avatar_bytes: bytes | None, day_no: int, states_rows: list[str]) -> bytes:
    """Карточка «X играет»: заголовок, аватар слева, сетка справа."""
    grid_w, grid_h = _grid_size()
    avatar_size = 170
    pad = 36
    title_h = 64

    panel_w = pad + avatar_size + pad + grid_w + pad
    panel_h = max(avatar_size, grid_h) + pad * 2
    card_w = panel_w + 80
    card_h = title_h + panel_h + 40

    card = Image.new("RGB", (card_w, card_h), BG)
    draw = ImageDraw.Draw(card)

    title = f"Вордл №{day_no}"
    font_title = _font(28)
    title_w = draw.textlength(title, font=font_title)
    draw.text(((card_w - title_w) // 2, 22), title, font=font_title, fill=TEXT)

    px0, py0 = 40, title_h
    draw.rounded_rectangle(
        (px0, py0, px0 + panel_w, py0 + panel_h), radius=24, fill=PANEL, outline=PANEL_OUTLINE, width=2
    )

    card_rgba = card.convert("RGBA")
    avatar = _avatar_image(avatar_bytes, avatar_size)
    card_rgba.alpha_composite(avatar, (px0 + pad, py0 + (panel_h - avatar_size) // 2))

    draw = ImageDraw.Draw(card_rgba)
    _draw_grid(draw, px0 + pad + avatar_size + pad, py0 + (panel_h - grid_h) // 2, states_rows)

    out = io.BytesIO()
    card_rgba.convert("RGB").save(out, format="PNG")
    return out.getvalue()


def render_summary_card(day_no: int, players: list[dict]) -> bytes:
    """Сводная карточка дня: до 5 игроков рядом, аватар над сеткой.

    players: [{"avatar_bytes": bytes|None, "states_rows": list[str]}, ...]
    """
    players = players[:5]
    grid_w, grid_h = _grid_size()
    avatar_size = 120
    pad = 24
    gap = 24
    title_h = 64

    tile_w = max(grid_w, avatar_size) + pad * 2
    tile_h = pad + avatar_size + 18 + grid_h + pad

    total_w = len(players) * tile_w + (len(players) - 1) * gap
    card_w = total_w + 80
    card_h = title_h + tile_h + 40

    card = Image.new("RGB", (card_w, card_h), BG)
    draw = ImageDraw.Draw(card)

    title = f"Вордл №{day_no}"
    font_title = _font(28)
    title_w = draw.textlength(title, font=font_title)
    draw.text(((card_w - title_w) // 2, 22), title, font=font_title, fill=TEXT)

    card_rgba = card.convert("RGBA")
    for i, player in enumerate(players):
        tx0 = 40 + i * (tile_w + gap)
        ty0 = title_h
        ImageDraw.Draw(card_rgba).rounded_rectangle(
            (tx0, ty0, tx0 + tile_w, ty0 + tile_h), radius=20, fill=PANEL, outline=PANEL_OUTLINE, width=2
        )
        avatar = _avatar_image(player.get("avatar_bytes"), avatar_size)
        card_rgba.alpha_composite(avatar, (tx0 + (tile_w - avatar_size) // 2, ty0 + pad))
        _draw_grid(
            ImageDraw.Draw(card_rgba),
            tx0 + (tile_w - grid_w) // 2,
            ty0 + pad + avatar_size + 18,
            player.get("states_rows", []),
        )

    out = io.BytesIO()
    card_rgba.convert("RGB").save(out, format="PNG")
    return out.getvalue()
