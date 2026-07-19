"""Тесты рендера карточки ранга: базовый рендер, кастомная рамка и титул."""

import xp_card


def test_hex_to_rgb():
    assert xp_card._hex_to_rgb("#FF00AA") == (255, 0, 170)
    assert xp_card._hex_to_rgb("00ff00") == (0, 255, 0)


def test_render_rank_card_without_cosmetics_produces_png():
    png = xp_card.render_rank_card(None, "Player", 5, 30, 100, 1, 10, "1ч 30м")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_rank_card_with_custom_frame_and_title():
    png = xp_card.render_rank_card(
        None, "Player", 5, 30, 100, 1, 10, "1ч 30м",
        frame_color="#FF00AA", title_text="Легенда сервера",
    )
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_rank_card_long_title_does_not_crash():
    long_title = "О" * 60
    png = xp_card.render_rank_card(None, "Player", 5, 30, 100, 1, 10, "0м", title_text=long_title)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
