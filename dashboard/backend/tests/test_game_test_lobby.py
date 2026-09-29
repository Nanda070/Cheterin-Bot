"""Tests for shared fake-lobby seat builder used by bunker/mafia test commands."""

import pytest

import bot.modules.games.game_test_lobby as gtl


def test_fake_user_ids_are_negative_and_unique():
    ids = [gtl.fake_user_id(i) for i in range(8)]
    assert all(uid < 0 for uid in ids)
    assert len(set(ids)) == 8


def test_fake_avatar_url_is_stable_and_https():
    a = gtl.fake_avatar_url("Alex Bot")
    b = gtl.fake_avatar_url("Alex Bot")
    assert a == b
    assert a.startswith("https://")
    assert "Alex" in a or "Alex%20" in a or "Alex+Bot" in a or "seed=" in a


def test_build_fake_seats_host_first_then_bots():
    seats = gtl.build_fake_seats(
        5,
        host_user_id=42,
        host_display_name="Admin",
        host_avatar_url="https://cdn.example/admin.png",
    )
    assert len(seats) == 5
    assert seats[0].is_host is True
    assert seats[0].user_id == 42
    assert seats[0].display_name == "Admin"
    assert seats[0].avatar_url == "https://cdn.example/admin.png"

    bots = seats[1:]
    assert all(not s.is_host for s in bots)
    assert all(s.user_id < 0 for s in bots)
    assert all(s.avatar_url and s.avatar_url.startswith("https://") for s in bots)
    assert [s.display_name for s in bots] == list(gtl.FAKE_PLAYER_NAMES[:4])


def test_build_fake_seats_rejects_too_few():
    with pytest.raises(ValueError):
        gtl.build_fake_seats(1, host_user_id=1, host_display_name="x")


def test_clamp_player_count():
    assert gtl.clamp_player_count(3, 4, 8) == 4
    assert gtl.clamp_player_count(10, 4, 8) == 8
    assert gtl.clamp_player_count(6, 4, 8) == 6
