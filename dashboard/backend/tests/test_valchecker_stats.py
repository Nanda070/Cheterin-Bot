"""Unit tests for ValChecker stats formulas (ACS, HS%, WR, KD)."""

from __future__ import annotations

import valchecker_stats as stats


def test_kd():
    assert stats.kd(10, 5) == "2.00"
    assert stats.kd(0, 0) == "0.00"
    assert stats.kd(7, 0) == "7.00"


def test_pct():
    assert stats.pct(33.333) == "33.3%"
    assert stats.pct(None) == "—"
    assert stats.pct(100, digits=0) == "100%"


def test_bucket_wr():
    assert stats.bucket_wr({"wins": 3, "losses": 1}) == 75.0
    assert stats.bucket_wr({"wins": 0, "losses": 0}) == 0.0
    assert stats.bucket_wr(None) == 0.0


def test_form_strip():
    summaries = [{"won": True}, {"won": False}, {"won": True}, {"won": None}, {"won": False}]
    assert stats.form_strip(summaries, 5) == "WLW?L"
    assert stats.form_strip([], 5) == "—"
    assert stats.form_strip_spaced(summaries, 3) == "W L W"
    assert stats.form_strip_dots(summaries, 3) == "● ○ ●"


def _fake_match(*, won=True, kills=10, deaths=5, assists=2, score=200, hs=5, body=5, legs=0, rounds=10):
    return {
        "metadata": {
            "match_id": "m1",
            "started_at": "2024-01-01T12:00:00Z",
            "is_completed": True,
            "map": {"name": "Ascent"},
            "queue": {"name": "competitive"},
            "season": {"short": "e8a1"},
            "region": "eu",
        },
        "players": [
            {
                "puuid": "p1",
                "name": "Test",
                "tag": "EU",
                "team_id": "Red",
                "agent": {"name": "Jett", "id": None},
                "stats": {
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists,
                    "score": score,
                    "headshots": hs,
                    "bodyshots": body,
                    "legshots": legs,
                },
            }
        ],
        "teams": [
            {"team_id": "Red", "won": won, "rounds": {"won": 13, "lost": 7}},
            {"team_id": "Blue", "won": not won, "rounds": {"won": 7, "lost": 13}},
        ],
        "rounds": [{}] * rounds,
    }


def test_summarize_acs_and_hs():
    match = _fake_match(score=250, rounds=10, hs=20, body=20, legs=10)
    summary = stats.summarize_match(match, "p1", "Test", "EU")
    assert summary["player"]["acs"] == 25.0  # 250 / 10
    assert abs(summary["player"]["hsPct"] - 40.0) < 0.01  # 20/50
    assert summary["won"] is True
    assert summary["player"]["kills"] == 10


def test_aggregate_wr_kd():
    matches = [
        _fake_match(won=True, kills=10, deaths=5),
        _fake_match(won=True, kills=8, deaths=8),
        _fake_match(won=False, kills=2, deaths=10),
    ]
    # Distinct match_ids for sorting
    for i, m in enumerate(matches):
        m["metadata"]["match_id"] = f"m{i}"
        m["metadata"]["started_at"] = f"2024-01-0{i + 1}T12:00:00Z"

    summaries = stats.summaries_from_matches(matches, "p1", "Test", "EU")
    agg = stats.aggregate_stats(summaries)
    assert agg["games"] == 3
    assert agg["wins"] == 2
    assert agg["losses"] == 1
    assert abs(agg["wr"] - (2 / 3) * 100) < 0.01
    assert agg["kills"] == 20
    assert agg["deaths"] == 23
    assert abs(agg["kd"] - (20 / 23)) < 0.001


def test_rank_sort_key():
    assert stats.rank_sort_key("Radiant", 50) > stats.rank_sort_key("Iron 1", 100)
    assert stats.rank_sort_key("Gold 2", 80) > stats.rank_sort_key("Gold 2", 10)


def test_parse_riot_id():
    assert stats.parse_riot_id("Player#1234") == {"name": "Player", "tag": "1234"}
    assert stats.parse_riot_id("bad") is None
    assert stats.parse_riot_id("#tag") is None


def test_normalize_mmr():
    body = {
        "data": {
            "current": {"tier": {"name": "Gold 2", "id": 14}, "rr": 55, "last_change": 18},
            "peak": {"tier": {"name": "Platinum 1", "id": 16}, "rr": 20, "season": {"short": "e8a1"}},
        }
    }
    mmr = stats.normalize_mmr(body)
    assert mmr["rank"] == "Gold 2"
    assert mmr["rr"] == 55
    assert mmr["lastChange"] == 18
    assert mmr["peak"]["name"] == "Platinum 1"


def test_rank_change_info_promote():
    mmr = {"rank": "Gold 1", "rr": 10, "lastChange": 25}
    info = stats.rank_change_info("Silver 3", 90, mmr)
    assert info["movement"] == "promoted"
    assert info["delta"] == 25


def test_to_cache_row_won_none():
    match = _fake_match(won=True)
    summary = stats.summarize_match(match, "p1", "Test", "EU")
    summary["won"] = None
    row = stats.to_cache_row(summary, "eu")
    assert row is not None
    assert row["won"] is None


def test_normalize_mmr_empty():
    mmr = stats.normalize_mmr({})
    assert mmr["rank"] == "Unrated"
    assert mmr["rr"] == 0
