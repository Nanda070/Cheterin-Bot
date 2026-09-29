"""Shared helpers for admin fake-lobby test games (Bunker / Mafia).

Builds a seat list: one real host + N-1 bot players with stable names and
placeholder avatar URLs so public player dashboards can show a full roster.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

# Negative Discord-style IDs never collide with real snowflakes.
FAKE_USER_ID_BASE = -1_000_000_000_000_000

DEFAULT_BUNKER_PLAYERS = 6
DEFAULT_MAFIA_PLAYERS = 6

BUNKER_PLAYERS_MIN = 4
BUNKER_PLAYERS_MAX = 8
MAFIA_PLAYERS_MIN = 5
MAFIA_PLAYERS_MAX = 7

FAKE_PLAYER_NAMES: tuple[str, ...] = (
    "Alex Bot",
    "Sam Bot",
    "Jordan Bot",
    "Casey Bot",
    "Riley Bot",
    "Morgan Bot",
    "Quinn Bot",
    "Avery Bot",
    "Blake Bot",
    "Drew Bot",
    "Cameron Bot",
    "Reese Bot",
)


@dataclass(frozen=True)
class FakeSeat:
    user_id: int
    display_name: str
    avatar_url: str | None
    is_host: bool


def fake_avatar_url(seed: str) -> str:
    """Stable placeholder PFP (Dicebear). PNG works in <img> tags."""
    return f"https://api.dicebear.com/7.x/thumbs/png?seed={quote(seed, safe='')}&size=128"


def fake_user_id(index: int) -> int:
    """Deterministic negative id for bot seat ``index`` (0-based among bots)."""
    if index < 0:
        raise ValueError("index must be >= 0")
    return FAKE_USER_ID_BASE - index


def clamp_player_count(count: int, floor: int, ceil: int) -> int:
    return max(floor, min(ceil, count))


def build_fake_seats(
    total_players: int,
    *,
    host_user_id: int,
    host_display_name: str,
    host_avatar_url: str | None = None,
    names: tuple[str, ...] = FAKE_PLAYER_NAMES,
) -> list[FakeSeat]:
    """Return ``total_players`` seats: host first, then bots.

    Raises ValueError if total_players < 2 (need at least one bot for a useful test)
    or if there are not enough names for the bot seats.
    """
    if total_players < 2:
        raise ValueError("total_players must be at least 2")
    bot_count = total_players - 1
    if bot_count > len(names):
        raise ValueError(f"need {bot_count} bot names, only {len(names)} available")

    seats: list[FakeSeat] = [
        FakeSeat(
            user_id=host_user_id,
            display_name=host_display_name,
            avatar_url=host_avatar_url,
            is_host=True,
        )
    ]
    for i in range(bot_count):
        name = names[i]
        seats.append(
            FakeSeat(
                user_id=fake_user_id(i),
                display_name=name,
                avatar_url=fake_avatar_url(name),
                is_host=False,
            )
        )
    return seats
