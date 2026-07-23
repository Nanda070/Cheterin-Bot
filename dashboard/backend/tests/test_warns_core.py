from datetime import datetime, timedelta, timezone

import pytest

import warns_core
import warns_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(warns_db, "get_db_path", lambda: str(tmp_path / "warns.db"))
    warns_db.db_init()


def test_add_and_get_warn():
    warn = warns_core.add_warn(1, 100, "Спам", 10, source="manual")
    assert warn["guild_id"] == "1"
    assert warn["user_id"] == "100"
    assert warn["reason"] == "Спам"
    assert warn["moderator_id"] == "10"
    assert warn["source"] == "manual"
    assert warn["removed"] is False
    assert warn["expires_at"] is None

    warns = warns_core.get_warns(1, 100)
    assert len(warns) == 1
    assert warns[0]["id"] == warn["id"]


def test_add_warn_without_moderator_is_automod():
    warn = warns_core.add_warn(1, 100, "Флуд", None, source="repeated_text", duration_minutes=60)
    assert warn["moderator_id"] is None
    assert warn["source"] == "repeated_text"
    assert warn["expires_at"] is not None


def test_compute_expiry():
    assert warns_core.compute_expiry(0) is None
    assert warns_core.compute_expiry(-5) is None
    assert warns_core.compute_expiry(60) is not None


def test_active_warn_count_excludes_expired_and_removed():
    warns_core.add_warn(1, 100, "Бессрочный", None)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    warns_db.add_warn(1, 100, "Истёкший", None, "manual", past)
    removed = warns_core.add_warn(1, 100, "Снятый", None)
    warns_core.remove_warn(removed["id"], 999)

    assert warns_core.get_active_warn_count(1, 100) == 1


def test_remove_warn():
    warn = warns_core.add_warn(1, 100, "Причина", None)
    assert warns_core.remove_warn(warn["id"], 5) is True
    assert warns_core.remove_warn(warn["id"], 5) is False
    assert warns_core.remove_warn(999999, 5) is False

    fetched = warns_core.get_warn(warn["id"])
    assert fetched["removed"] is True
    assert fetched["removed_by"] == "5"


def test_remove_warn_guild_scoped():
    warn = warns_core.add_warn(1, 100, "Причина", None)
    assert warns_core.remove_warn(warn["id"], 5, guild_id=999) is False
    assert warns_core.get_warn(warn["id"])["removed"] is False
    assert warns_core.remove_warn(warn["id"], 5, guild_id=1) is True
    assert warns_core.get_warn(warn["id"])["removed"] is True


def test_get_warns_scoped_by_guild_and_user():
    warns_core.add_warn(1, 100, "guild1-user100", None)
    warns_core.add_warn(2, 100, "guild2-user100", None)
    warns_core.add_warn(1, 200, "guild1-user200", None)

    assert len(warns_core.get_warns(1, 100)) == 1
    assert len(warns_core.get_warns(2, 100)) == 1
    assert len(warns_core.get_warns(1, 200)) == 1
    assert warns_core.get_warns(1, 999) == []


def test_get_warn_missing_returns_none():
    assert warns_core.get_warn(999999) is None
