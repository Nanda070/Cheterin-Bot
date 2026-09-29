import pytest

import bot.modules.community.reaction_roles as reaction_roles
import bot.core.settings_db as settings_db

GUILD_ID = 404


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_load_config_returns_empty_dict_when_file_missing():
    assert reaction_roles.load_config(GUILD_ID) == {}


def test_save_then_load_round_trip():
    data = {"111": {"channel_id": "222", "pairs": [{"emoji": "📖", "role_id": "333"}]}}
    reaction_roles.save_config(GUILD_ID, data)
    assert reaction_roles.load_config(GUILD_ID) == data


def test_get_pairs_for_message_returns_pairs_when_present():
    pairs = [{"emoji": "📖", "role_id": "333"}]
    reaction_roles.save_config(GUILD_ID, {"111": {"channel_id": "222", "pairs": pairs}})
    assert reaction_roles.get_pairs_for_message(GUILD_ID, "111") == pairs


def test_get_pairs_for_message_returns_none_when_absent():
    reaction_roles.save_config(GUILD_ID, {})
    assert reaction_roles.get_pairs_for_message(GUILD_ID, "999") is None


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
