import pytest

import bot.modules.community.giveaway_core as giveaway_core

G = 404
G2 = 777


def test_parse_duration_valid_formats():
    assert giveaway_core.parse_duration("45s") == 45
    assert giveaway_core.parse_duration("10m") == 600
    assert giveaway_core.parse_duration("2h") == 7200
    assert giveaway_core.parse_duration("1d") == 86400


def test_parse_duration_invalid_formats():
    for value in ["10", "10x", "m10", "-5m", "abc", ""]:
        with pytest.raises(ValueError):
            giveaway_core.parse_duration(value)


def test_create_and_get_giveaway():
    giveaway = giveaway_core.create_giveaway(G, 1, "Discord Nitro", "10m", 1)
    assert giveaway["id"] == "1"
    assert giveaway["status"] == "active"
    assert giveaway["prize"] == "Discord Nitro"
    assert giveaway["winners_count"] == 1
    assert giveaway["entrants"] == []
    assert giveaway["target_ts"] > 0
    assert giveaway["guild_id"] == str(G)

    second = giveaway_core.create_giveaway(G, 2, "Steam-ключ", "1h", 2)
    assert second["id"] == "2"
    assert len(giveaway_core.list_active(G)) == 2


def test_giveaways_isolated_per_guild():
    giveaway_core.create_giveaway(G, 1, "A", "10m", 1)
    other = giveaway_core.create_giveaway(G2, 1, "B", "10m", 1)
    assert other["id"] == "1"  # своя последовательность id
    assert len(giveaway_core.list_active(G)) == 1
    assert len(giveaway_core.list_active(G2)) == 1
    assert giveaway_core.get_giveaway(G2, "1")["prize"] == "B"


def test_get_giveaway_by_message():
    giveaway = giveaway_core.create_giveaway(G, 1, "Приз", "10m", 1)
    giveaway_core.update_giveaway(G, giveaway["id"], channel_id="500", message_id="999")
    assert giveaway_core.get_giveaway_by_message(G, 999)["id"] == giveaway["id"]
    assert giveaway_core.get_giveaway_by_message(G, 111) is None
    assert giveaway_core.get_giveaway_by_message(G2, 999) is None


def test_join_and_leave_giveaway():
    giveaway = giveaway_core.create_giveaway(G, 1, "Приз", "10m", 1)
    gid = giveaway["id"]

    assert giveaway_core.join_giveaway(G, gid, 20) == "joined"
    assert giveaway_core.join_giveaway(G, gid, 20) == "already"
    assert giveaway_core.get_giveaway(G, gid)["entrants"] == ["20"]

    assert giveaway_core.leave_giveaway(G, gid, 20) == "left"
    assert giveaway_core.leave_giveaway(G, gid, 20) == "not_in_list"
    assert giveaway_core.get_giveaway(G, gid)["entrants"] == []


def test_join_leave_unknown_and_closed():
    assert giveaway_core.join_giveaway(G, "999", 1) == "not_found"
    assert giveaway_core.leave_giveaway(G, "999", 1) == "not_found"

    giveaway = giveaway_core.create_giveaway(G, 1, "Приз", "10m", 1)
    giveaway_core.close_giveaway(G, giveaway["id"], status="cancelled")
    assert giveaway_core.join_giveaway(G, giveaway["id"], 20) == "closed"
    assert giveaway_core.leave_giveaway(G, giveaway["id"], 20) == "closed"


def test_draw_winners_capped_by_pool_size():
    giveaway = giveaway_core.create_giveaway(G, 1, "Приз", "10m", 5)
    for uid in (10, 20, 30):
        giveaway_core.join_giveaway(G, giveaway["id"], uid)

    winners = giveaway_core.draw_winners(G, giveaway["id"])
    assert len(winners) == 3
    assert set(winners) == {"10", "20", "30"}


def test_draw_winners_empty_pool_returns_empty():
    giveaway = giveaway_core.create_giveaway(G, 1, "Приз", "10m", 1)
    assert giveaway_core.draw_winners(G, giveaway["id"]) == []


def test_close_giveaway_finished_picks_winners():
    giveaway = giveaway_core.create_giveaway(G, 1, "Приз", "10m", 1)
    giveaway_core.join_giveaway(G, giveaway["id"], 20)

    closed = giveaway_core.close_giveaway(G, giveaway["id"], status="finished")
    assert closed["status"] == "finished"
    assert closed["winners"] == ["20"]
    assert closed["past_winners"] == ["20"]
    assert closed["closed_at"] is not None


def test_close_giveaway_cancelled_has_no_winners():
    giveaway = giveaway_core.create_giveaway(G, 1, "Приз", "10m", 1)
    giveaway_core.join_giveaway(G, giveaway["id"], 20)

    closed = giveaway_core.close_giveaway(G, giveaway["id"], status="cancelled")
    assert closed["status"] == "cancelled"
    assert closed["winners"] == []


def test_close_giveaway_already_closed_returns_none():
    giveaway = giveaway_core.create_giveaway(G, 1, "Приз", "10m", 1)
    giveaway_core.close_giveaway(G, giveaway["id"], status="finished")
    assert giveaway_core.close_giveaway(G, giveaway["id"], status="finished") is None


def test_reroll_excludes_past_winners():
    giveaway = giveaway_core.create_giveaway(G, 1, "Приз", "10m", 1)
    giveaway_core.join_giveaway(G, giveaway["id"], 10)
    giveaway_core.join_giveaway(G, giveaway["id"], 20)
    closed = giveaway_core.close_giveaway(G, giveaway["id"], status="finished")
    first_winner = closed["winners"][0]

    for _ in range(5):
        rerolled = giveaway_core.reroll_giveaway(G, giveaway["id"])
        assert rerolled is not None
        assert first_winner not in rerolled

    final = giveaway_core.get_giveaway(G, giveaway["id"])
    assert set(final["past_winners"]) == {"10", "20"}


def test_reroll_not_finished_returns_none():
    giveaway = giveaway_core.create_giveaway(G, 1, "Приз", "10m", 1)
    assert giveaway_core.reroll_giveaway(G, giveaway["id"]) is None


def test_reroll_no_remaining_entrants_returns_empty():
    giveaway = giveaway_core.create_giveaway(G, 1, "Приз", "10m", 1)
    giveaway_core.join_giveaway(G, giveaway["id"], 10)
    giveaway_core.close_giveaway(G, giveaway["id"], status="finished")

    assert giveaway_core.reroll_giveaway(G, giveaway["id"]) == []


def test_list_history_and_active():
    a = giveaway_core.create_giveaway(G, 1, "A", "10m", 1)
    b = giveaway_core.create_giveaway(G, 2, "B", "10m", 1)
    giveaway_core.close_giveaway(G, b["id"], status="finished")

    active_ids = {g["id"] for g in giveaway_core.list_active(G)}
    history_ids = {g["id"] for g in giveaway_core.list_history(G)}
    assert active_ids == {a["id"]}
    assert history_ids == {b["id"]}
