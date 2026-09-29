"""DB tests for relations marriages / proposals."""

from __future__ import annotations

import bot.modules.games.relations_db as rdb


def test_marriage_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setenv("RELATIONS_DB_PATH", str(tmp_path / "rel.db"))
    rdb.init()
    assert rdb.get_spouse(1, 10) is None
    m = rdb.create_marriage(1, 10, 20)
    assert m["user_a"] == 10 and m["user_b"] == 20
    assert rdb.are_married(1, 20, 10)
    spouse = rdb.get_spouse(1, 10)
    assert spouse is not None
    assert spouse["spouse_id"] == 20
    assert rdb.marriage_count(1, 10) == 1
    assert rdb.dissolve_marriage(1, 10, 20)
    assert not rdb.are_married(1, 10, 20)


def test_proposal_and_top(tmp_path, monkeypatch):
    monkeypatch.setenv("RELATIONS_DB_PATH", str(tmp_path / "rel2.db"))
    rdb.init()
    rdb.upsert_proposal(1, 5, 6, 120)
    prop = rdb.get_proposal(1, 5, 6)
    assert prop is not None
    assert rdb.has_outgoing_proposal(1, 5)
    assert rdb.has_incoming_proposal(1, 6)
    rdb.create_marriage(1, 5, 6)
    assert rdb.get_proposal(1, 5, 6) is None
    top = rdb.top_marriages(1, 10)
    assert len(top) == 1
    assert top[0]["user_a"] == 5
