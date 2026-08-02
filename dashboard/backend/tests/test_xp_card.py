"""Тесты рендера карточки ранга / профиля: PNG, GIF, косметика."""

import profile_card
import xp_card


def test_hex_to_rgb():
    assert xp_card._hex_to_rgb("#FF00AA") == (255, 0, 170)
    assert xp_card._hex_to_rgb("00ff00") == (0, 255, 0)
    assert profile_card._hex_to_rgb("#D44556") == (212, 69, 86)


def test_render_rank_card_without_cosmetics_produces_png():
    png = xp_card.render_rank_card(1, None, "Player", 5, 30, 100, 1, 10, "1ч 30м")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_rank_card_with_custom_frame_and_title():
    png = xp_card.render_rank_card(
        1,
        None, "Player", 5, 30, 100, 1, 10, "1ч 30м",
        frame_color="#FF00AA", title_text="Легенда сервера",
    )
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_rank_card_long_title_does_not_crash():
    long_title = "О" * 60
    png = xp_card.render_rank_card(1, None, "Player", 5, 30, 100, 1, 10, "0м", title_text=long_title)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_profile_card_with_economy_stats():
    png = profile_card.render_profile_card(
        1,
        None,
        "Player",
        12,
        40,
        200,
        3,
        50,
        "2ч 10м",
        frame_color="#D44556",
        title_text="VIP",
        messages=1234,
        balance=500,
        streak=7,
        lang="en",
    )
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 1000


def test_render_profile_card_gif_is_gif():
    gif = profile_card.render_profile_card_gif(
        1,
        None,
        "Player",
        5,
        30,
        100,
        1,
        10,
        "1h",
        messages=10,
        balance=100,
        streak=2,
        lang="en",
        frames=8,
    )
    assert gif[:6] in (b"GIF87a", b"GIF89a")
    assert len(gif) < 3 * 1024 * 1024


def test_rank_card_delegates_to_profile_dimensions():
    assert xp_card.CARD_W == profile_card.CARD_W
    assert xp_card.CARD_H == profile_card.CARD_H
