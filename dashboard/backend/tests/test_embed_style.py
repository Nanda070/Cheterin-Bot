"""Shared embed_style palette and helpers."""

import discord

import bot.core.embed_style as embed_style


def test_semantic_palette_matches_discord_ui_hex():
    assert embed_style.INFO.value == 0x5865F2
    assert embed_style.SUCCESS.value == 0x57F287
    assert embed_style.DANGER.value == 0xED4245
    assert embed_style.WARN.value == 0xE67E22
    assert embed_style.GOLD.value == 0xFEE75C
    assert embed_style.NEUTRAL.value == 0x2B2D31
    assert embed_style.ACCENT.value == 0xD44556


def test_theme_exceptions():
    assert embed_style.WORDLE.value == 0x538D4E
    assert embed_style.TWITCH.value == 0x9146FF
    assert embed_style.YOUTUBE.value == embed_style.DANGER.value


def test_make_embed_defaults_timestamp_and_color():
    embed = embed_style.make_embed(title="Hi", description="Body")
    assert embed.title == "Hi"
    assert embed.color == embed_style.INFO
    assert embed.timestamp is not None


def test_make_embed_accepts_int_color_and_footer():
    embed = embed_style.make_embed(
        title="X",
        color=embed_style.DANGER_INT,
        footer=embed_style.module_footer("Moderation", "Command"),
        timestamp=False,
    )
    assert embed.color == embed_style.DANGER
    assert embed.footer.text == "Moderation · Command"
    assert embed.timestamp is None


def test_as_color_default_and_passthrough():
    assert embed_style.as_color(None, default=embed_style.DANGER) == embed_style.DANGER
    assert embed_style.as_color(embed_style.SUCCESS) == embed_style.SUCCESS
    assert isinstance(embed_style.as_color(0x123456), discord.Color)
