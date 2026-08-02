"""Quote settings and mention/reply gate."""

import quote_card
import quote_core
import settings_db

GUILD_ID = 9101


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_defaults(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    assert quote_core.get_settings(GUILD_ID) == {
        "enabled": True,
        "delete_trigger": False,
        "min_length": 0,
    }


def test_save_settings(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    out = quote_core.save_settings(
        GUILD_ID,
        {"enabled": False, "delete_trigger": True, "min_length": 12},
    )
    assert out == {"enabled": False, "delete_trigger": True, "min_length": 12}


def test_bot_is_mentioned():
    class U:
        def __init__(self, uid):
            self.id = uid

    assert quote_core.bot_is_mentioned(bot_user_id=5, mentions=[U(5)], content="") is True
    assert quote_core.bot_is_mentioned(bot_user_id=5, mentions=[], content="<@5> hi") is True
    assert quote_core.bot_is_mentioned(bot_user_id=5, mentions=[], content="<@!5>") is True
    assert quote_core.bot_is_mentioned(bot_user_id=5, mentions=[U(9)], content="hello") is False
    assert quote_core.bot_is_mentioned(bot_user_id=None, mentions=[], content="<@1>") is False


def test_should_quote_gate(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    class U:
        id = 42

    base = dict(
        guild_id=GUILD_ID,
        author_is_bot=False,
        bot_user_id=42,
        mentions=[U()],
        content="@bot",
        has_reference=True,
        referenced_text="hello world",
    )
    assert quote_core.should_quote(**base) is True
    assert quote_core.should_quote(**{**base, "author_is_bot": True}) is False
    assert quote_core.should_quote(**{**base, "guild_id": None}) is False
    assert quote_core.should_quote(**{**base, "has_reference": False}) is False
    assert quote_core.should_quote(**{**base, "mentions": [], "content": "no ping"}) is False

    quote_core.save_settings(GUILD_ID, {"enabled": False, "delete_trigger": False, "min_length": 0})
    assert quote_core.should_quote(**base) is False

    quote_core.save_settings(GUILD_ID, {"enabled": True, "delete_trigger": False, "min_length": 20})
    assert quote_core.should_quote(**{**base, "referenced_text": "short"}) is False
    assert quote_core.should_quote(**{**base, "referenced_text": "x" * 20}) is True


def test_render_quote_card_png_bytes():
    png = quote_card.render_quote_card(
        display_name="Ada",
        quote_text="Hello from the quoted message.",
        avatar_bytes=None,
        attachment_bytes=None,
    )
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 200
