import pytest

import giveaway_core


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    monkeypatch.setattr(giveaway_core, "DATA_FILE", str(tmp_path / "giveaways_data.json"))


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
    giveaway = giveaway_core.create_giveaway(1, "Discord Nitro", "10m", 1)
    assert giveaway["id"] == "1"
    assert giveaway["status"] == "active"
    assert giveaway["prize"] == "Discord Nitro"
    assert giveaway["winners_count"] == 1
    assert giveaway["entrants"] == []
    assert giveaway["target_ts"] > 0

    second = giveaway_core.create_giveaway(2, "Steam-ключ", "1h", 2)
    assert second["id"] == "2"
    assert len(giveaway_core.list_active()) == 2


def test_get_giveaway_by_message():
    giveaway = giveaway_core.create_giveaway(1, "Приз", "10m", 1)
    giveaway_core.update_giveaway(giveaway["id"], channel_id="500", message_id="999")
    assert giveaway_core.get_giveaway_by_message(999)["id"] == giveaway["id"]
    assert giveaway_core.get_giveaway_by_message(111) is None


def test_join_and_leave_giveaway():
    giveaway = giveaway_core.create_giveaway(1, "Приз", "10m", 1)
    gid = giveaway["id"]

    assert giveaway_core.join_giveaway(gid, 20) == "joined"
    assert giveaway_core.join_giveaway(gid, 20) == "already"
    assert giveaway_core.get_giveaway(gid)["entrants"] == ["20"]

    assert giveaway_core.leave_giveaway(gid, 20) == "left"
    assert giveaway_core.leave_giveaway(gid, 20) == "not_in_list"
    assert giveaway_core.get_giveaway(gid)["entrants"] == []


def test_join_leave_unknown_and_closed():
    assert giveaway_core.join_giveaway("999", 1) == "not_found"
    assert giveaway_core.leave_giveaway("999", 1) == "not_found"

    giveaway = giveaway_core.create_giveaway(1, "Приз", "10m", 1)
    giveaway_core.close_giveaway(giveaway["id"], status="cancelled")
    assert giveaway_core.join_giveaway(giveaway["id"], 20) == "closed"
    assert giveaway_core.leave_giveaway(giveaway["id"], 20) == "closed"


def test_draw_winners_capped_by_pool_size():
    giveaway = giveaway_core.create_giveaway(1, "Приз", "10m", 5)
    for uid in (10, 20, 30):
        giveaway_core.join_giveaway(giveaway["id"], uid)

    winners = giveaway_core.draw_winners(giveaway["id"])
    assert len(winners) == 3
    assert set(winners) == {"10", "20", "30"}


def test_draw_winners_empty_pool_returns_empty():
    giveaway = giveaway_core.create_giveaway(1, "Приз", "10m", 1)
    assert giveaway_core.draw_winners(giveaway["id"]) == []


def test_close_giveaway_finished_picks_winners():
    giveaway = giveaway_core.create_giveaway(1, "Приз", "10m", 1)
    giveaway_core.join_giveaway(giveaway["id"], 20)

    closed = giveaway_core.close_giveaway(giveaway["id"], status="finished")
    assert closed["status"] == "finished"
    assert closed["winners"] == ["20"]
    assert closed["past_winners"] == ["20"]
    assert closed["closed_at"] is not None


def test_close_giveaway_cancelled_has_no_winners():
    giveaway = giveaway_core.create_giveaway(1, "Приз", "10m", 1)
    giveaway_core.join_giveaway(giveaway["id"], 20)

    closed = giveaway_core.close_giveaway(giveaway["id"], status="cancelled")
    assert closed["status"] == "cancelled"
    assert closed["winners"] == []


def test_close_giveaway_already_closed_returns_none():
    giveaway = giveaway_core.create_giveaway(1, "Приз", "10m", 1)
    giveaway_core.close_giveaway(giveaway["id"], status="finished")
    assert giveaway_core.close_giveaway(giveaway["id"], status="finished") is None


def test_reroll_excludes_past_winners():
    giveaway = giveaway_core.create_giveaway(1, "Приз", "10m", 1)
    giveaway_core.join_giveaway(giveaway["id"], 10)
    giveaway_core.join_giveaway(giveaway["id"], 20)
    closed = giveaway_core.close_giveaway(giveaway["id"], status="finished")
    first_winner = closed["winners"][0]

    for _ in range(5):
        rerolled = giveaway_core.reroll_giveaway(giveaway["id"])
        assert rerolled is not None
        assert first_winner not in rerolled

    final = giveaway_core.get_giveaway(giveaway["id"])
    assert set(final["past_winners"]) == {"10", "20"}


def test_reroll_not_finished_returns_none():
    giveaway = giveaway_core.create_giveaway(1, "Приз", "10m", 1)
    assert giveaway_core.reroll_giveaway(giveaway["id"]) is None


def test_reroll_no_remaining_entrants_returns_empty():
    giveaway = giveaway_core.create_giveaway(1, "Приз", "10m", 1)
    giveaway_core.join_giveaway(giveaway["id"], 10)
    giveaway_core.close_giveaway(giveaway["id"], status="finished")

    assert giveaway_core.reroll_giveaway(giveaway["id"]) == []


def test_list_history_and_active():
    a = giveaway_core.create_giveaway(1, "A", "10m", 1)
    b = giveaway_core.create_giveaway(2, "B", "10m", 1)
    giveaway_core.close_giveaway(b["id"], status="finished")

    active_ids = {g["id"] for g in giveaway_core.list_active()}
    history_ids = {g["id"] for g in giveaway_core.list_history()}
    assert active_ids == {a["id"]}
    assert history_ids == {b["id"]}
