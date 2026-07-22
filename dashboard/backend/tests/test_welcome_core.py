import welcome_core
from message_template_core import substitute


def test_substitute_placeholders():
    assert substitute("Hi {mention} on {guild_name}", {"mention": "@U", "guild_name": "G"}) == "Hi @U on G"


def test_welcome_settings_defaults():
    settings = welcome_core.get_settings(999001)
    assert settings["channel_mode"] == "text"
    assert settings["dm_use_guild_icon"] is True
    assert settings["dm_fallback_thumbnail_url"] == ""
    assert settings["dm_footer_text"] == ""


def test_resolve_dm_footer_uses_custom_text():
    settings = {"dm_footer_text": "Contact @admin"}
    assert welcome_core.resolve_dm_footer_text(settings, "ru") == "Contact @admin"


def test_resolve_dm_thumbnail_uses_custom_fallback():
    settings = {"dm_fallback_thumbnail_url": "https://example.com/thumb.png"}
    assert welcome_core.resolve_dm_thumbnail_url(settings) == "https://example.com/thumb.png"


def test_resolve_dm_thumbnail_returns_empty_without_custom():
    assert welcome_core.resolve_dm_thumbnail_url({}) == ""


def test_build_goodbye_uses_custom_text():
    welcome_core.save_settings(999002, {"goodbye_text": "Bye {name}!"})
    class M:
        mention = "@x"
        display_name = "Alice"

    class G:
        name = "Srv"
        member_count = 1

    text = welcome_core.build_goodbye_text(welcome_core.get_settings(999002), M(), G(), "ru")
    assert text == "Bye Alice!"
