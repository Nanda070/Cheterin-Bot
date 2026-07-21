"""Тесты stats_db: per-guild изоляция XP/войс/аудита и миграция старой схемы.

Фаза 2.2а MULTIGUILD_PLAN.md: xp_members/voice_sessions/audit_log получили guild_id;
существующие (глобальные) строки при миграции присваиваются мейн-серверу (guild 404).
"""

import sqlite3
from contextlib import closing

import pytest

import stats_db

MAIN = 404
OTHER = 777


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("STATS_DB_PATH", str(tmp_path / "stats.db"))
    stats_db.init()


# ────────────────────────── XP: изоляция по гильдиям ──────────────────────────

def test_xp_add_text_and_get_scoped_per_guild():
    stats_db.xp_add_text(MAIN, 10, 50, 1000)
    stats_db.xp_add_text(OTHER, 10, 200, 1000)

    assert stats_db.xp_get_member(MAIN, 10)["xp"] == 50
    assert stats_db.xp_get_member(OTHER, 10)["xp"] == 200
    # тот же user_id на другом (не заведённом) сервере — отдельная (отсутствующая) строка
    assert stats_db.xp_get_member(999, 10) is None


def test_xp_add_text_increments_messages_and_ts():
    stats_db.xp_add_text(MAIN, 10, 15, 1000)
    stats_db.xp_add_text(MAIN, 10, 20, 2000)
    row = stats_db.xp_get_member(MAIN, 10)
    assert row["xp"] == 35
    assert row["messages"] == 2
    assert row["last_text_xp_ts"] == 2000


def test_xp_add_voice_accumulates_seconds():
    stats_db.xp_add_voice(MAIN, 10, 30, 600)
    stats_db.xp_add_voice(MAIN, 10, 30, 600)
    row = stats_db.xp_get_member(MAIN, 10)
    assert row["xp"] == 60
    assert row["voice_seconds"] == 1200


def test_xp_set_level_and_set_xp():
    stats_db.xp_set_xp(MAIN, 10, 500, 5)
    row = stats_db.xp_get_member(MAIN, 10)
    assert row["xp"] == 500 and row["level"] == 5
    stats_db.xp_set_level(MAIN, 10, 7)
    assert stats_db.xp_get_member(MAIN, 10)["level"] == 7


def test_xp_reset_member_only_targets_one_guild():
    stats_db.xp_add_text(MAIN, 10, 50, 1000)
    stats_db.xp_add_text(OTHER, 10, 50, 1000)
    stats_db.xp_reset_member(MAIN, 10)
    assert stats_db.xp_get_member(MAIN, 10) is None
    assert stats_db.xp_get_member(OTHER, 10) is not None


def test_xp_reset_all_only_targets_one_guild():
    stats_db.xp_add_text(MAIN, 10, 50, 1000)
    stats_db.xp_add_text(MAIN, 20, 50, 1000)
    stats_db.xp_add_text(OTHER, 10, 50, 1000)
    stats_db.xp_reset_all(MAIN)
    assert stats_db.xp_member_count(MAIN) == 0
    assert stats_db.xp_member_count(OTHER) == 1


def test_xp_leaderboard_and_rank_scoped_per_guild():
    stats_db.xp_add_text(MAIN, 10, 100, 1000)
    stats_db.xp_add_text(MAIN, 20, 300, 1000)
    stats_db.xp_add_text(MAIN, 30, 200, 1000)
    stats_db.xp_add_text(OTHER, 40, 9999, 1000)

    board = stats_db.xp_leaderboard(MAIN)
    assert [r["user_id"] for r in board] == [20, 30, 10]
    assert stats_db.xp_rank_of(MAIN, 20) == 1
    assert stats_db.xp_rank_of(MAIN, 10) == 3
    # участник другого сервера не влияет на рейтинг мейна
    assert stats_db.xp_rank_of(MAIN, 40) is None
    assert stats_db.xp_member_count(MAIN) == 3


def test_voice_leaderboard_orders_by_voice_seconds():
    stats_db.xp_add_voice(MAIN, 10, 10, 100)
    stats_db.xp_add_voice(MAIN, 20, 10, 500)
    board = stats_db.voice_leaderboard(MAIN)
    assert [r["user_id"] for r in board] == [20, 10]


def test_xp_all_members_returns_only_guild_rows():
    stats_db.xp_add_text(MAIN, 10, 50, 1000)
    stats_db.xp_add_text(OTHER, 20, 50, 1000)
    rows = stats_db.xp_all_members(MAIN)
    assert {r["user_id"] for r in rows} == {10}


# ────────────────────────── Войс-сессии ──────────────────────────

def test_voice_sessions_since_scoped_per_guild():
    stats_db.voice_session_add(MAIN, 10, 1, "general", 1000, 1600, 600)
    stats_db.voice_session_add(OTHER, 10, 1, "general", 1000, 1600, 600)
    main_sessions = stats_db.voice_sessions_since(MAIN, 0)
    assert len(main_sessions) == 1
    assert main_sessions[0]["guild_id"] == MAIN


def test_voice_sessions_since_filters_by_left_ts():
    stats_db.voice_session_add(MAIN, 10, 1, "old", 100, 200, 100)
    stats_db.voice_session_add(MAIN, 10, 1, "new", 1000, 1600, 600)
    recent = stats_db.voice_sessions_since(MAIN, 500)
    assert [s["channel_name"] for s in recent] == ["new"]


def test_voice_sessions_prune_is_global():
    stats_db.voice_session_add(MAIN, 10, 1, "old", 100, 200, 100)
    stats_db.voice_session_add(OTHER, 10, 1, "old", 100, 200, 100)
    stats_db.voice_session_add(MAIN, 10, 1, "new", 1000, 1600, 600)
    stats_db.voice_sessions_prune(500)
    assert len(stats_db.voice_sessions_since(MAIN, 0)) == 1
    assert len(stats_db.voice_sessions_since(OTHER, 0)) == 0


# ────────────────────────── Аудит ──────────────────────────

def test_audit_add_list_count_scoped_per_guild():
    stats_db.audit_add(MAIN, 1000, 1, "mod", "POST", "/api/x", "act", 200)
    stats_db.audit_add(OTHER, 1000, 1, "mod", "POST", "/api/x", "act", 200)
    assert stats_db.audit_count(MAIN) == 1
    assert stats_db.audit_count(OTHER) == 1
    rows = stats_db.audit_list(MAIN)
    assert len(rows) == 1 and rows[0]["guild_id"] == MAIN


def test_audit_list_orders_desc_and_filters_by_moderator():
    stats_db.audit_add(MAIN, 1000, 1, "a", "POST", "/api/x", "act", 200)
    stats_db.audit_add(MAIN, 2000, 2, "b", "POST", "/api/y", "act", 200)
    stats_db.audit_add(MAIN, 3000, 1, "a", "POST", "/api/z", "act", 200)
    rows = stats_db.audit_list(MAIN)
    assert [r["ts"] for r in rows] == [3000, 2000, 1000]
    only_1 = stats_db.audit_list(MAIN, moderator_id=1)
    assert {r["moderator_id"] for r in only_1} == {1}
    assert stats_db.audit_count(MAIN, moderator_id=1) == 2


# ────────────────────────── Миграция старой (глобальной) схемы ──────────────────────────

def _create_legacy_schema(path: str):
    """Схема до Фазы 2.2а: без guild_id (как в проде на мейн-сервере)."""
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(
            """CREATE TABLE xp_members (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 0,
                messages INTEGER NOT NULL DEFAULT 0,
                voice_seconds INTEGER NOT NULL DEFAULT 0,
                last_text_xp_ts INTEGER NOT NULL DEFAULT 0
            )"""
        )
        conn.execute(
            "INSERT INTO xp_members (user_id, xp, level, messages, voice_seconds, last_text_xp_ts) VALUES (?, ?, ?, ?, ?, ?)",
            (10, 500, 5, 42, 3600, 12345),
        )
        conn.execute(
            """CREATE TABLE voice_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                channel_name TEXT NOT NULL DEFAULT '',
                joined_ts INTEGER NOT NULL,
                left_ts INTEGER NOT NULL,
                active_seconds INTEGER NOT NULL DEFAULT 0
            )"""
        )
        conn.execute(
            "INSERT INTO voice_sessions (user_id, channel_id, channel_name, joined_ts, left_ts, active_seconds) VALUES (?, ?, ?, ?, ?, ?)",
            (10, 1, "general", 1000, 1600, 600),
        )
        conn.execute(
            """CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                moderator_name TEXT NOT NULL,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                action TEXT NOT NULL,
                status INTEGER NOT NULL,
                details TEXT NOT NULL DEFAULT ''
            )"""
        )
        conn.execute(
            "INSERT INTO audit_log (ts, moderator_id, moderator_name, method, path, action, status, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (1000, 1, "mod", "POST", "/api/x", "act", 200, ""),
        )


def test_migration_assigns_legacy_rows_to_main_guild(tmp_path, monkeypatch):
    db_path = str(tmp_path / "legacy_stats.db")
    monkeypatch.setenv("STATS_DB_PATH", db_path)
    _create_legacy_schema(db_path)

    stats_db.init()  # должна выполнить миграцию идемпотентно

    xp_row = stats_db.xp_get_member(MAIN, 10)
    assert xp_row is not None
    assert xp_row["xp"] == 500 and xp_row["level"] == 5
    assert xp_row["messages"] == 42 and xp_row["voice_seconds"] == 3600
    assert xp_row["last_text_xp_ts"] == 12345

    voice = stats_db.voice_sessions_since(MAIN, 0)
    assert len(voice) == 1 and voice[0]["guild_id"] == MAIN

    audit = stats_db.audit_list(MAIN)
    assert len(audit) == 1 and audit[0]["guild_id"] == MAIN


def test_migration_is_idempotent(tmp_path, monkeypatch):
    db_path = str(tmp_path / "legacy_stats2.db")
    monkeypatch.setenv("STATS_DB_PATH", db_path)
    _create_legacy_schema(db_path)

    stats_db.init()
    stats_db.init()  # повторный вызов не должен падать и не должен дублировать строки

    assert stats_db.xp_member_count(MAIN) == 1
    assert len(stats_db.voice_sessions_since(MAIN, 0)) == 1
    assert stats_db.audit_count(MAIN) == 1


def test_xp_members_primary_key_is_composite(tmp_path, monkeypatch):
    """После миграции один user_id может существовать на разных серверах."""
    db_path = str(tmp_path / "legacy_stats3.db")
    monkeypatch.setenv("STATS_DB_PATH", db_path)
    _create_legacy_schema(db_path)
    stats_db.init()

    # тот же user_id 10, но другой сервер — отдельная строка, без конфликта PK
    stats_db.xp_add_text(OTHER, 10, 77, 1000)
    assert stats_db.xp_get_member(MAIN, 10)["xp"] == 500
    assert stats_db.xp_get_member(OTHER, 10)["xp"] == 77
