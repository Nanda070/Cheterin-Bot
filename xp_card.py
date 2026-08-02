"""Rank card PNG — thin wrapper over the premium profile card renderer.

Kept for backward-compatible imports (`render_rank_card`, `_hex_to_rgb`).
"""

from __future__ import annotations

import profile_card

CARD_W, CARD_H = profile_card.CARD_W, profile_card.CARD_H
DEFAULT_RING_COLOR = profile_card.DEFAULT_RING

_hex_to_rgb = profile_card._hex_to_rgb


def render_rank_card(
    guild_id: int,
    avatar_bytes: bytes | None,
    display_name: str,
    level: int,
    xp_into_level: int,
    xp_step: int,
    rank: int | None,
    total_members: int,
    voice_time_text: str,
    frame_color: str | None = None,
    title_text: str | None = None,
    lang: str = "ru",
    *,
    messages: int | None = None,
    balance: int | None = None,
    streak: int | None = None,
) -> bytes:
    return profile_card.render_profile_card(
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
    )
