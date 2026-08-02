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


def test_render_quote_card_with_attachment():
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (320, 240), (200, 40, 40)).save(buf, format="PNG")
    att = buf.getvalue()
    png = quote_card.render_quote_card(
        display_name="Ada",
        quote_text="13414",
        avatar_bytes=None,
        attachment_bytes=att,
    )
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    # With a photo the card should be taller than a text-only quote.
    tall = Image.open(io.BytesIO(png))
    short = Image.open(
        io.BytesIO(
            quote_card.render_quote_card(
                display_name="Ada",
                quote_text="13414",
                avatar_bytes=None,
                attachment_bytes=None,
            )
        )
    )
    assert tall.size[1] > short.size[1]


def test_attachment_is_image_helpers():
    import quote as quote_cog

    class Att:
        def __init__(self, content_type="", filename="", width=None, height=None):
            self.content_type = content_type
            self.filename = filename
            self.width = width
            self.height = height

    assert quote_cog._attachment_is_image(Att(content_type="image/png")) is True
    assert quote_cog._attachment_is_image(Att(filename="shot.JPEG")) is True
    assert quote_cog._attachment_is_image(Att(width=100, height=80)) is True
    assert quote_cog._attachment_is_image(Att(content_type="text/plain", filename="a.txt")) is False
