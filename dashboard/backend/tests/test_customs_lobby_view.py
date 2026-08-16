"""Lobby embed buttons: back-to-lobby appears only when live or team VCs exist."""

from collections import Counter

import i18n
import customs
import customs_core


class _DummyCog:
    pass


def _custom_ids(view: customs.CustomsLobbyView) -> list[str]:
    return [item.custom_id for item in view.children]


def _row_counts(view: customs.CustomsLobbyView) -> dict[int, int]:
    return dict(Counter(item.row for item in view.children))


def test_show_back_to_lobby_when_live_or_team_vc():
    assert customs._show_back_to_lobby({"status": "open"}) is False
    assert customs._show_back_to_lobby({"status": customs_core.STATUS_LIVE}) is True
    assert customs._show_back_to_lobby({"status": "open", "team_a_vc_id": "123"}) is True
    assert customs._show_back_to_lobby({"status": "ready", "team_b_vc_id": "456"}) is True


def test_match_team_user_ids_prefers_teams():
    lobby = {
        "team_a": [{"user_id": "10"}, {"user_id": "11"}],
        "team_b": [{"user_id": "20"}],
        "players": [{"user_id": "10"}, {"user_id": "99"}],
    }
    assert customs._match_team_user_ids(lobby) == ["10", "11", "20"]


def test_match_team_user_ids_falls_back_to_players():
    lobby = {"players": [{"user_id": "1"}, {"user_id": "2"}], "team_a": [], "team_b": []}
    assert customs._match_team_user_ids(lobby) == ["1", "2"]


def test_open_lobby_has_no_back_button():
    view = customs.CustomsLobbyView(_DummyCog(), status=customs_core.STATUS_OPEN)
    ids = _custom_ids(view)
    assert customs.CID_BACK_LOBBY not in ids
    assert customs.CID_JOIN in ids
    assert customs.CID_LEAVE in ids
    assert customs.CID_RANK in ids
    assert customs.CID_BALANCE in ids
    assert customs.CID_MAP in ids
    assert customs.CID_START in ids
    assert customs.CID_CANCEL in ids
    assert customs.CID_SCORE not in ids
    assert max(_row_counts(view).values()) <= 5
    assert max(_row_counts(view)) <= 1


def test_live_lobby_adds_back_and_score_without_overflow():
    view = customs.CustomsLobbyView(_DummyCog(), status=customs_core.STATUS_LIVE)
    ids = _custom_ids(view)
    assert customs.CID_BACK_LOBBY in ids
    assert customs.CID_SCORE in ids
    assert customs.CID_JOIN in ids
    assert customs.CID_START in ids
    counts = _row_counts(view)
    assert counts.get(2, 0) == 1
    assert max(counts.values()) <= 5
    back = next(item for item in view.children if item.custom_id == customs.CID_BACK_LOBBY)
    assert back.label == i18n.t("customs.btn.back_lobby", "ru")
    assert back.label == "Назад в лобби"


def test_team_vc_flag_shows_back_before_live():
    view = customs.CustomsLobbyView(
        _DummyCog(),
        status=customs_core.STATUS_READY,
        show_back_to_lobby=True,
    )
    assert customs.CID_BACK_LOBBY in _custom_ids(view)
    assert customs.CID_SCORE not in _custom_ids(view)
    assert max(_row_counts(view).values()) <= 5


def test_persistent_view_registers_back_lobby():
    view = customs.CustomsLobbyView.persistent(_DummyCog())
    ids = _custom_ids(view)
    assert customs.CID_BACK_LOBBY in ids
    assert customs.CID_SCORE in ids
    assert max(_row_counts(view).values()) <= 5


def test_lobby_view_for_uses_team_vc():
    cog = _DummyCog()
    lobby = {
        "join_mode": customs_core.JOIN_MODE_SOLO,
        "status": customs_core.STATUS_OPEN,
        "team_a_vc_id": "9",
        "team_b_vc_id": "",
    }
    view = customs.CustomsCog.lobby_view_for(cog, lobby, "ru")  # type: ignore[arg-type]
    assert customs.CID_BACK_LOBBY in _custom_ids(view)
