"""Bot profile core: nick / image data-URI parsing."""

import base64

import pytest

import bot.core.bot_profile_core as bot_profile_core
import bot.core.settings_db as settings_db

GUILD_ID = 6601


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_defaults():
    assert bot_profile_core.get_settings(GUILD_ID) == {
        "nick": "",
        "has_custom_avatar": False,
        "has_custom_banner": False,
    }


def test_save_settings():
    out = bot_profile_core.save_settings(
        GUILD_ID, nick="Chet", has_custom_avatar=True, has_custom_banner=False,
    )
    assert out["nick"] == "Chet"
    assert out["has_custom_avatar"] is True


def test_normalize_nick():
    assert bot_profile_core.normalize_nick("  Hi  ") == "Hi"
    assert bot_profile_core.normalize_nick("") == ""
    with pytest.raises(ValueError, match="nick_too_long"):
        bot_profile_core.normalize_nick("x" * 33)


def test_parse_image_data_uri_ok():
    raw = b"\x89PNG" + b"\x00" * 20
    b64 = base64.b64encode(raw).decode()
    uri = f"data:image/png;base64,{b64}"
    payload, decoded = bot_profile_core.parse_image_data_uri(uri)
    assert payload.startswith("data:image/png;base64,")
    assert decoded == raw


def test_parse_image_clear():
    payload, raw = bot_profile_core.parse_image_data_uri(None)
    assert payload is None
    assert raw is None


def test_parse_image_too_large():
    raw = b"x" * (bot_profile_core.MAX_IMAGE_BYTES + 1)
    b64 = base64.b64encode(raw).decode()
    with pytest.raises(ValueError, match="image_too_large"):
        bot_profile_core.parse_image_data_uri(f"data:image/png;base64,{b64}")


def test_parse_image_invalid():
    with pytest.raises(ValueError, match="invalid_image"):
        bot_profile_core.parse_image_data_uri("not-a-data-uri")
