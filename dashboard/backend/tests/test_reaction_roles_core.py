import json

import pytest

import reaction_roles


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(reaction_roles, "CONFIG_FILE", str(tmp_path / "reaction_roles.json"))


def test_load_config_returns_empty_dict_when_file_missing():
    assert reaction_roles.load_config() == {}


def test_save_then_load_round_trip():
    data = {"111": {"channel_id": "222", "pairs": [{"emoji": "📖", "role_id": "333"}]}}
    reaction_roles.save_config(data)
    assert reaction_roles.load_config() == data


def test_load_config_returns_empty_dict_on_corrupt_json():
    with open(reaction_roles.CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("{not valid json")
    assert reaction_roles.load_config() == {}


def test_get_pairs_for_message_returns_pairs_when_present():
    pairs = [{"emoji": "📖", "role_id": "333"}]
    reaction_roles.save_config({"111": {"channel_id": "222", "pairs": pairs}})
    assert reaction_roles.get_pairs_for_message("111") == pairs


def test_get_pairs_for_message_returns_none_when_absent():
    reaction_roles.save_config({})
    assert reaction_roles.get_pairs_for_message("999") is None


def test_find_pair_by_emoji_matches():
    pairs = [{"emoji": "📖", "role_id": "aaa"}, {"emoji": "✅", "role_id": "bbb"}]
    assert reaction_roles.find_pair_by_emoji(pairs, "✅") == {"emoji": "✅", "role_id": "bbb"}


def test_find_pair_by_emoji_no_match():
    pairs = [{"emoji": "📖", "role_id": "aaa"}]
    assert reaction_roles.find_pair_by_emoji(pairs, "❌") is None


def test_has_duplicate_emoji_true():
    pairs = [{"emoji": "📖", "role_id": "aaa"}, {"emoji": "📖", "role_id": "bbb"}]
    assert reaction_roles.has_duplicate_emoji(pairs) is True


def test_has_duplicate_emoji_false():
    pairs = [{"emoji": "📖", "role_id": "aaa"}, {"emoji": "✅", "role_id": "bbb"}]
    assert reaction_roles.has_duplicate_emoji(pairs) is False
