import pytest

import mafia_core
import settings_db


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_get_settings_defaults():
    settings = mafia_core.get_settings(404)
    assert settings["enabled"] is False
    assert settings["default_min_players"] == mafia_core.DEFAULT_MIN_PLAYERS
    assert settings["default_max_players"] == mafia_core.DEFAULT_MAX_PLAYERS
    assert settings["default_night_timer_sec"] == mafia_core.DEFAULT_NIGHT_TIMER_SEC
    assert settings["log_channel_id"] == ""


def test_save_config_roundtrip():
    mafia_core.save_config(404, {"enabled": True, "default_min_players": 6, "log_channel_id": "123"})
    settings = mafia_core.get_settings(404)
    assert settings["enabled"] is True
    assert settings["default_min_players"] == 6
    assert settings["log_channel_id"] == "123"


@pytest.mark.parametrize("n", range(mafia_core.PLAYERS_FLOOR, mafia_core.PLAYERS_CEIL + 1))
def test_scale_roles_sweep(n):
    counts = mafia_core.scale_roles(n)
    assert counts["doctor"] == 1
    assert counts["sheriff"] == 1
    assert counts["mafia"] >= 1
    assert counts["citizen"] >= 0
    assert counts["mafia"] + counts["doctor"] + counts["sheriff"] + counts["citizen"] == n


def test_scale_roles_specific_values():
    assert mafia_core.scale_roles(5) == {"mafia": 1, "doctor": 1, "sheriff": 1, "citizen": 2}
    assert mafia_core.scale_roles(20) == {"mafia": 5, "doctor": 1, "sheriff": 1, "citizen": 13}
    assert mafia_core.scale_roles(99) == {"mafia": 25, "doctor": 1, "sheriff": 1, "citizen": 72}


def test_assign_roles_matches_scale_and_covers_all_players():
    player_ids = list(range(100, 120))
    assignment = mafia_core.assign_roles(player_ids)
    assert set(assignment.keys()) == set(player_ids)

    counts = mafia_core.scale_roles(len(player_ids))
    role_counts = {"mafia": 0, "doctor": 0, "sheriff": 0, "citizen": 0}
    for role in assignment.values():
        role_counts[role] += 1
    assert role_counts == counts


def test_resolve_mafia_kill_majority():
    assert mafia_core.resolve_mafia_kill({1: 100, 2: 100, 3: 200}) == 100


def test_resolve_mafia_kill_tie_returns_none():
    assert mafia_core.resolve_mafia_kill({1: 100, 2: 200}) is None


def test_resolve_mafia_kill_all_none_returns_none():
    assert mafia_core.resolve_mafia_kill({1: None, 2: None}) is None


def test_resolve_mafia_kill_empty_returns_none():
    assert mafia_core.resolve_mafia_kill({}) is None


def test_resolve_mafia_kill_solo():
    assert mafia_core.resolve_mafia_kill({1: 100}) == 100


def test_resolve_day_vote_majority():
    assert mafia_core.resolve_day_vote({1: 10, 2: 10, 3: 20, 4: None}) == 10


def test_resolve_day_vote_tie_returns_none():
    assert mafia_core.resolve_day_vote({1: 10, 2: 20}) is None


def test_resolve_day_vote_all_skip_returns_none():
    assert mafia_core.resolve_day_vote({1: None, 2: None}) is None


def test_check_win_condition_town_wins_when_no_mafia():
    assert mafia_core.check_win_condition(["citizen", "doctor", "sheriff"]) == "town"


def test_check_win_condition_mafia_wins_at_parity():
    assert mafia_core.check_win_condition(["mafia", "citizen"]) == "mafia"


def test_check_win_condition_no_winner_yet():
    assert mafia_core.check_win_condition(["mafia", "citizen", "citizen"]) is None


def test_role_label_known_and_unknown():
    assert mafia_core.role_label("mafia") == "Мафия"
    assert mafia_core.role_label("unknown") == "unknown"


class _FakePermissions:
    def __init__(self, manage_guild=False, administrator=False):
        self.manage_guild = manage_guild
        self.administrator = administrator


class _FakeMember:
    def __init__(self, manage_guild=False, administrator=False):
        self.guild_permissions = _FakePermissions(manage_guild, administrator)


def test_has_moderator_access():
    assert mafia_core.has_moderator_access(_FakeMember(manage_guild=True)) is True
    assert mafia_core.has_moderator_access(_FakeMember(administrator=True)) is True
    assert mafia_core.has_moderator_access(_FakeMember()) is False
