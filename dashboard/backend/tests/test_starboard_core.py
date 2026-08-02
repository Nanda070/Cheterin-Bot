"""Starboard core: settings, threshold, emoji matching, channel validation."""

import pytest

import settings_db
import starboard_core

GUILD_ID = 7701


class _Emoji:
    def __init__(self, name=None, emoji_id=None, as_str=None):
        self.name = name
        self.id = emoji_id
        self._as_str = as_str

    def __str__(self):
        if self._as_str is not None:
            return self._as_str
        if self.id is not None:
            return f"<:{self.name}:{self.id}>"
        return self.name or ""


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_defaults_disabled():
    settings = starboard_core.get_settings(GUILD_ID)
    assert settings["enabled"] is False
    assert settings["channel_id"] == ""
    assert settings["emoji"] == "⭐"
    assert settings["threshold"] == 3
    assert settings["self_star"] is False
    assert settings["ignore_nsfw"] is False


def test_save_roundtrip():
    out = starboard_core.save_config(GUILD_ID, {
        "enabled": True,
        "channel_id": "123",
        "emoji": "🔥",
        "threshold": 5,
        "self_star": True,
        "ignore_nsfw": True,
    })
    assert out["enabled"] is True
    assert out["channel_id"] == "123"
    assert out["emoji"] == "🔥"
    assert out["threshold"] == 5
    assert out["self_star"] is True
    assert out["ignore_nsfw"] is True


def test_validate_channel_id():
    assert starboard_core.validate_channel_id("", required=False) is None
    assert starboard_core.validate_channel_id("", required=True) == "channel_required"
    assert starboard_core.validate_channel_id("abc", required=False) == "invalid_channel"
    assert starboard_core.validate_channel_id("42", required=True) is None


def test_validate_threshold():
    assert starboard_core.validate_threshold(3) == 3
    assert starboard_core.validate_threshold(0) is None
    assert starboard_core.validate_threshold(True) is None
    assert starboard_core.validate_threshold(101) is None


def test_count_meets_threshold():
    assert starboard_core.count_meets_threshold(3, 3) is True
    assert starboard_core.count_meets_threshold(2, 3) is False


def test_emoji_matches_unicode():
    assert starboard_core.emoji_matches("⭐", _Emoji(name="⭐")) is True
    assert starboard_core.emoji_matches("⭐", _Emoji(name="🔥")) is False


def test_emoji_matches_custom():
    assert starboard_core.emoji_matches(
        "<:pepe:555>", _Emoji(name="pepe", emoji_id=555)
    ) is True
    assert starboard_core.emoji_matches(
        "<a:wave:999>", _Emoji(name="wave", emoji_id=999, as_str="<a:wave:999>")
    ) is True
    assert starboard_core.emoji_matches(
        "<:pepe:555>", _Emoji(name="pepe", emoji_id=556)
    ) is False


def test_should_include_reactor():
    assert starboard_core.should_include_reactor(
        reactor_id=1, author_id=2, reactor_is_bot=False, self_star=False,
    ) is True
    assert starboard_core.should_include_reactor(
        reactor_id=1, author_id=1, reactor_is_bot=False, self_star=False,
    ) is False
    assert starboard_core.should_include_reactor(
        reactor_id=1, author_id=1, reactor_is_bot=False, self_star=True,
    ) is True
    assert starboard_core.should_include_reactor(
        reactor_id=3, author_id=1, reactor_is_bot=True, self_star=True,
    ) is False
