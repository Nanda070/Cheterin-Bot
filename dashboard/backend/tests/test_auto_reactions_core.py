"""Auto-reactions core: channel matching and keyword helpers."""

import pytest

import bot.modules.community.auto_reactions_core as auto_reactions_core
import bot.core.settings_db as settings_db

GUILD_ID = 8801


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_defaults():
    settings = auto_reactions_core.get_settings(GUILD_ID)
    assert settings == {"enabled": False, "rules": []}


def test_channel_matches_all_with_exclusions():
    rule = {
        "channel_mode": "all",
        "channel_ids": [],
        "exclude_channel_ids": ["10", "20"],
    }
    assert auto_reactions_core.channel_matches_rule(rule, 1) is True
    assert auto_reactions_core.channel_matches_rule(rule, "10") is False
    assert auto_reactions_core.channel_matches_rule(rule, 20) is False


def test_channel_matches_include_mode():
    rule = {
        "channel_mode": "include",
        "channel_ids": ["5", "6"],
        "exclude_channel_ids": ["6"],
    }
    assert auto_reactions_core.channel_matches_rule(rule, 5) is True
    assert auto_reactions_core.channel_matches_rule(rule, 6) is False  # excluded wins
    assert auto_reactions_core.channel_matches_rule(rule, 7) is False


def test_keywords_match():
    assert auto_reactions_core.keywords_match([], "anything") is True
    assert auto_reactions_core.keywords_match(["hello"], "Say HELLO there") is True
    assert auto_reactions_core.keywords_match(["bye"], "hello") is False


def test_matching_rules_for_message():
    auto_reactions_core.save_config(
        GUILD_ID,
        enabled=True,
        rules=[
            {
                "id": "r1",
                "emojis": ["👍"],
                "keywords": [],
                "channel_mode": "all",
                "channel_ids": [],
                "exclude_channel_ids": ["99"],
                "ignore_bots": True,
            },
            {
                "id": "r2",
                "emojis": ["🔥"],
                "keywords": ["fire"],
                "channel_mode": "include",
                "channel_ids": ["1"],
                "exclude_channel_ids": [],
                "ignore_bots": True,
            },
        ],
    )
    settings = auto_reactions_core.get_settings(GUILD_ID)

    matched = auto_reactions_core.matching_rules_for_message(
        settings, channel_id=1, content="hello", author_is_bot=False,
    )
    assert [r["id"] for r in matched] == ["r1"]

    matched = auto_reactions_core.matching_rules_for_message(
        settings, channel_id=1, content="on fire!", author_is_bot=False,
    )
    assert {r["id"] for r in matched} == {"r1", "r2"}

    matched = auto_reactions_core.matching_rules_for_message(
        settings, channel_id=99, content="hello", author_is_bot=False,
    )
    assert matched == []

    matched = auto_reactions_core.matching_rules_for_message(
        settings, channel_id=1, content="hello", author_is_bot=True,
    )
    assert matched == []


def test_save_drops_rules_without_emojis():
    out = auto_reactions_core.save_config(
        GUILD_ID,
        enabled=True,
        rules=[{"id": "x", "emojis": [], "keywords": [], "channel_mode": "all"}],
    )
    assert out["rules"] == []


def test_all_guild_emoji_mode():
    out = auto_reactions_core.save_config(
        GUILD_ID,
        enabled=True,
        rules=[
            {
                "id": "all",
                "emoji_mode": "all_guild",
                "emojis": ["👍"],
                "keywords": [],
                "channel_mode": "all",
                "channel_ids": [],
                "exclude_channel_ids": [],
                "ignore_bots": True,
            }
        ],
    )
    assert out["rules"][0]["emoji_mode"] == "all_guild"
    assert out["rules"][0]["emojis"] == []

    matched = auto_reactions_core.matching_rules_for_message(
        out, channel_id=1, content="hi", author_is_bot=False,
    )
    assert [r["id"] for r in matched] == ["all"]

    class Emoji:
        def __init__(self, emoji_id):
            self.id = emoji_id

    tokens = auto_reactions_core.guild_emoji_tokens([Emoji(i) for i in range(25)])
    assert len(tokens) == auto_reactions_core.MAX_GUILD_EMOJIS_REACT
