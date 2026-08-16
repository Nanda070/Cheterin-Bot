"""Focused tests: rank-from-roles, map pool, team balancer, team codes."""

from __future__ import annotations

import settings_db
import customs_core


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_rank_from_roles_picks_highest():
    rank_roles = {
        "iron": "1",
        "gold": "2",
        "radiant": "3",
        "bronze": "",
        "silver": "",
        "platinum": "",
        "diamond": "",
        "ascendant": "",
        "immortal": "",
    }
    got = customs_core.rank_from_role_ids({"1", "2", "99"}, rank_roles)
    assert got is not None
    assert got["id"] == "gold"
    assert got["weight"] == 4

    none = customs_core.rank_from_role_ids({"99"}, rank_roles)
    assert none is None


def test_fair_split_balances_mmr():
    players = [
        {"user_id": "1", "weight": 9},
        {"user_id": "2", "weight": 1},
        {"user_id": "3", "weight": 8},
        {"user_id": "4", "weight": 2},
    ]
    a, b, diff = customs_core.fair_split(players)
    assert len(a) == 2 and len(b) == 2
    assert diff <= 2
    assert {p["user_id"] for p in a + b} == {"1", "2", "3", "4"}


def test_fair_split_keeps_team_codes_together():
    players = [
        {"user_id": "1", "weight": 9, "team_code": "AAAA"},
        {"user_id": "2", "weight": 8, "team_code": "AAAA"},
        {"user_id": "3", "weight": 2, "team_code": "BBBB"},
        {"user_id": "4", "weight": 1, "team_code": "BBBB"},
        {"user_id": "5", "weight": 5, "team_code": ""},
        {"user_id": "6", "weight": 4, "team_code": ""},
    ]
    a, b, _ = customs_core.fair_split(players)
    a_ids = {p["user_id"] for p in a}
    b_ids = {p["user_id"] for p in b}
    # Stack AAAA stays on one side; BBBB on one side.
    assert ({"1", "2"} <= a_ids) or ({"1", "2"} <= b_ids)
    assert ({"3", "4"} <= a_ids) or ({"3", "4"} <= b_ids)


def test_random_presets_return_distinct():
    players = [{"user_id": str(i), "weight": i} for i in range(1, 11)]
    presets = customs_core.random_presets(players, count=3)
    assert 1 <= len(presets) <= 3
    assert presets[0]["label"] == "fair"


def test_map_pool_avoids_immediate_repeat(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    guild_id = 42
    pool = {m["id"]: False for m in customs_core.valorant_maps.MAPS}
    pool["ascent"] = True
    pool["bind"] = True
    customs_core.save_settings(guild_id, {"enabled": True, "map_pool": pool})
    first = customs_core.pick_random_map(guild_id)
    assert first["id"] in ("ascent", "bind")
    data = customs_core.load_data(guild_id)
    data["last_map_id"] = first["id"]
    customs_core.save_data(guild_id, data)
    second = customs_core.pick_random_map(guild_id)
    assert second["id"] in ("ascent", "bind")
    assert second["id"] != first["id"]


def test_lobby_join_requires_rank(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    guild_id = 7
    customs_core.save_settings(guild_id, {"enabled": True, "require_rank_role": True})
    lobby = customs_core.create_lobby(guild_id, host_id=1, name="Test")
    status, _ = customs_core.join_lobby(guild_id, lobby["id"], 2, None)
    assert status == "no_rank"
    rank = {"id": "gold", "name": "Gold", "weight": 4}
    status, lobby = customs_core.join_lobby(guild_id, lobby["id"], 2, rank)
    assert status == "joined"
    assert lobby is not None
    assert lobby["players"][0]["rank"] == "gold"


def test_team_code_create_and_join(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    guild_id = 9
    customs_core.save_settings(guild_id, {"enabled": True, "require_rank_role": True})
    lobby = customs_core.create_lobby(
        guild_id, host_id=1, name="Stack", join_mode=customs_core.JOIN_MODE_TEAM_CODE
    )
    rank = {"id": "gold", "name": "Gold", "weight": 4}
    status, lobby = customs_core.join_lobby(
        guild_id, lobby["id"], 10, rank, create_code=True
    )
    assert status == "joined"
    assert lobby is not None
    code = lobby["players"][0]["team_code"]
    assert len(code) == customs_core.TEAM_CODE_LEN

    status2, lobby2 = customs_core.join_lobby(
        guild_id, lobby["id"], 11, rank, team_code=code
    )
    assert status2 == "joined"
    assert lobby2 is not None
    assert lobby2["players"][1]["team_code"] == code


def test_settings_drop_legacy_captains_feature(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    guild_id = 3
    settings = customs_core.save_settings(
        guild_id,
        {
            "enabled": True,
            "default_mode": "team_code",
            "features": {"voting": True, "side_random": False, "captains": True, "veto": True},
        },
    )
    assert settings["default_mode"] == "team_code"
    assert "captains" not in settings["features"]
    assert "veto" not in settings["features"]
    assert settings["features"]["voting"] is True
    assert settings["features"]["side_random"] is False


def test_voice_settings_defaults_and_save(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    guild_id = 4
    settings = customs_core.get_settings(guild_id)
    assert settings["auto_lobby_vc"] is True
    assert settings["auto_move_on_start"] is True
    assert settings["voice_category_id"] == ""
    updated = customs_core.save_settings(
        guild_id,
        {
            "voice_category_id": "999",
            "auto_lobby_vc": False,
            "auto_move_on_start": True,
        },
    )
    assert updated["voice_category_id"] == "999"
    assert updated["auto_lobby_vc"] is False
    assert updated["auto_move_on_start"] is True
    lobby = customs_core.create_lobby(guild_id, host_id=1, name="VC")
    assert lobby["lobby_vc_id"] == ""
    assert lobby["team_a_vc_id"] == ""
    assert lobby["team_b_vc_id"] == ""


def test_finish_lobby_and_participants(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    guild_id = 5
    customs_core.save_settings(guild_id, {"enabled": True, "require_rank_role": False})
    lobby = customs_core.create_lobby(guild_id, host_id=1, name="Fin")
    rank = {"id": "gold", "name": "Gold", "weight": 4}
    customs_core.join_lobby(guild_id, lobby["id"], 10, rank)
    customs_core.join_lobby(guild_id, lobby["id"], 11, rank)
    customs_core.apply_balance(guild_id, lobby["id"], 0)
    customs_core.update_lobby(guild_id, lobby["id"], status=customs_core.STATUS_LIVE)
    finished = customs_core.finish_lobby(guild_id, lobby["id"])
    assert finished is not None
    assert finished["status"] == customs_core.STATUS_FINISHED
    ids = customs_core.lobby_participant_ids(finished)
    assert set(ids) >= {"10", "11"}


def test_kick_frees_slot(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    guild_id = 11
    customs_core.save_settings(guild_id, {"enabled": True, "require_rank_role": False})
    lobby = customs_core.create_lobby(guild_id, host_id=1, name="Kick")
    rank = {"id": "gold", "name": "Gold", "weight": 4}
    customs_core.join_lobby(guild_id, lobby["id"], 10, rank)
    customs_core.join_lobby(guild_id, lobby["id"], 11, rank)
    assert customs_core.kick_player(guild_id, lobby["id"], 10) == "kicked"
    lobby = customs_core.get_lobby(guild_id, lobby["id"])
    assert lobby is not None
    assert [p["user_id"] for p in lobby["players"]] == ["11"]


def test_map_bans_and_avoid_last(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    guild_id = 12
    pool = {m["id"]: False for m in customs_core.valorant_maps.MAPS}
    pool["ascent"] = True
    pool["bind"] = True
    pool["haven"] = True
    customs_core.save_settings(
        guild_id,
        {
            "enabled": True,
            "map_pool": pool,
            "avoid_last_map": True,
            "default_banned_maps": ["haven"],
        },
    )
    lobby = customs_core.create_lobby(guild_id, host_id=1, name="Maps")
    customs_core.set_lobby_bans(guild_id, lobby["id"], ["ascent", "bind", "haven"])
    lobby = customs_core.get_lobby(guild_id, lobby["id"])
    assert lobby is not None
    assert len(lobby["banned_maps"]) == 2
    customs_core.set_lobby_bans(guild_id, lobby["id"], ["ascent"])
    lobby = customs_core.get_lobby(guild_id, lobby["id"])
    remaining = customs_core.maps_for_pick(guild_id, lobby=lobby)
    ids = {m["id"] for m in remaining}
    assert ids == {"bind"}

    data = customs_core.load_data(guild_id)
    data["last_map_id"] = "ascent"
    customs_core.save_data(guild_id, data)
    lobby = customs_core.update_lobby(guild_id, lobby["id"], banned_maps=[]) or lobby
    chosen = customs_core.pick_random_map(guild_id, lobby=lobby)
    assert chosen["id"] == "bind"


def test_avoid_last_map_can_be_disabled(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    guild_id = 13
    pool = {m["id"]: False for m in customs_core.valorant_maps.MAPS}
    pool["ascent"] = True
    customs_core.save_settings(guild_id, {"enabled": True, "map_pool": pool, "avoid_last_map": False})
    data = customs_core.load_data(guild_id)
    data["last_map_id"] = "ascent"
    customs_core.save_data(guild_id, data)
    chosen = customs_core.pick_random_map(guild_id)
    assert chosen["id"] == "ascent"


def test_rematch_spec_and_signup(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    guild_id = 14
    customs_core.save_settings(guild_id, {"enabled": True, "default_ping": "participants"})
    lobby = customs_core.create_lobby(
        guild_id,
        host_id=1,
        name="Friday",
        notes="10 man",
        join_mode=customs_core.JOIN_MODE_TEAM_CODE,
        ping="participants",
        signup_minutes=30,
        banned_maps=["ascent"],
    )
    customs_core.update_lobby(guild_id, lobby["id"], channel_id="555")
    lobby = customs_core.get_lobby(guild_id, lobby["id"])
    assert lobby is not None
    assert lobby["signup_ends_at"] > lobby["created_at"]
    spec = customs_core.rematch_spec(lobby)
    assert spec["name"] == "Friday"
    assert spec["join_mode"] == customs_core.JOIN_MODE_TEAM_CODE
    assert spec["ping"] == "participants"
    assert spec["channel_id"] == "555"
    assert spec["signup_minutes"] == 30
    assert "ascent" in spec["banned_maps"]


def test_ping_validation_rejects_everyone(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    assert customs_core.validate_create_spec(
        {"name": "x", "channel_id": "1", "join_mode": "solo", "ping": "everyone"}
    ) == "invalid_ping"
    assert (
        customs_core.validate_create_spec(
            {"name": "x", "channel_id": "1", "join_mode": "solo", "ping": "participants"}
        )
        is None
    )


def test_due_schedules_window(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    from datetime import datetime
    from zoneinfo import ZoneInfo

    guild_id = 15
    customs_core.save_settings(guild_id, {"enabled": True})
    sch = customs_core.upsert_schedule(
        guild_id,
        {
            "enabled": True,
            "weekday": 4,
            "hour": 21,
            "minute": 0,
            "name": "Fri",
            "join_mode": "solo",
            "channel_id": "1",
            "ping": "none",
            "signup_minutes": 15,
        },
    )
    assert sch is not None
    now = datetime(2026, 8, 14, 21, 3, tzinfo=ZoneInfo("Europe/Moscow"))
    assert now.weekday() == 4
    due = customs_core.due_schedules(guild_id, now_local=now)
    assert len(due) == 1
    customs_core.mark_schedule_run(guild_id, sch["id"], "2026-08-14")
    assert customs_core.due_schedules(guild_id, now_local=now) == []


def test_defaults_in_settings(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    guild_id = 16
    settings = customs_core.get_settings(guild_id)
    assert settings["avoid_last_map"] is True
    assert settings["default_ping"] == "none"
    assert settings["default_name"] == "Кастомка"
    saved = customs_core.save_settings(
        guild_id,
        {
            "default_name": "10man",
            "default_ping": "role",
            "ping_role_id": "99",
            "avoid_last_map": True,
            "results_channel_id": "42",
        },
    )
    assert saved["default_name"] == "10man"
    assert saved["default_ping"] == "role"
    assert saved["results_channel_id"] == "42"
