"""Quote settings and mention/reply gate."""

import bot.cards.quote_card as quote_card
import bot.modules.utility.quote_core as quote_core
import bot.core.settings_db as settings_db

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


def _quote_gate_base(**overrides):
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
        referenced_author_is_bot=False,
    )
    base.update(overrides)
    return base


def test_should_quote_gate(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    base = _quote_gate_base()
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

    # Reply-to-bot auto-pings the bot; must not create a quote card.
    assert quote_core.should_quote(**{**base, "referenced_author_is_bot": True}) is False


def test_should_quote_requires_bot_mention_and_user_reply(tmp_path, monkeypatch):
    """Quotes only: @bot + reply to a *user* message. Never bot authors or reply-to-bot."""
    _isolate(tmp_path, monkeypatch)

    # Tag bot + reply to a USER message → quote.
    assert quote_core.should_quote(**_quote_gate_base()) is True
    # Mention via content markup only (no mentions list) still counts.
    assert (
        quote_core.should_quote(
            **_quote_gate_base(mentions=[], content="please <@42> quote this")
        )
        is True
    )
    assert (
        quote_core.should_quote(
            **_quote_gate_base(mentions=[], content="<@!42>")
        )
        is True
    )

    # Bot-authored trigger messages must not quote.
    assert quote_core.should_quote(**_quote_gate_base(author_is_bot=True)) is False

    # No reply → no quote (mention alone is not enough).
    assert quote_core.should_quote(**_quote_gate_base(has_reference=False)) is False

    # Reply to bot / quoting bot-authored message → no quote
    # (covers "не из бота" and "не из ответов на его сообщение").
    assert (
        quote_core.should_quote(**_quote_gate_base(referenced_author_is_bot=True))
        is False
    )
    # Discord reply-to-bot auto-ping: mention present but referenced is bot.
    assert (
        quote_core.should_quote(
            **_quote_gate_base(
                content="<@42>",
                referenced_author_is_bot=True,
                referenced_text="I am the bot",
            )
        )
        is False
    )

    # Plain reply to a user without tagging the bot → no quote.
    assert (
        quote_core.should_quote(
            **_quote_gate_base(mentions=[], content="just a reply")
        )
        is False
    )


def test_format_quote_plaintext():
    raw = "<@337654182095880205> — мимо. Баланс: 352000 🪙 🎰⭐🔔🍋"
    out = quote_core.format_quote_plaintext(
        raw,
        user_names={337654182095880205: "Cheterin ( Виталий )"},
    )
    assert "<@" not in out
    assert "@Cheterin ( Виталий )" in out
    assert "—" not in out
    assert "-" in out
    assert "🪙" not in out
    assert "🎰" not in out
    assert "мимо. Баланс: 352000" in out

    assert quote_core.format_quote_plaintext("<@&1> in <#2>", role_names={1: "mod"}, channel_names={2: "general"}) == (
        "@mod in #general"
    )
    assert quote_core.format_quote_plaintext("hi <:wave:123>") == "hi :wave:"


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
    import bot.modules.utility.quote as quote_cog

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
