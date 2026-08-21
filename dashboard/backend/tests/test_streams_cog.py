"""Стрим-уведомления уходят через LayoutView, без классического embed."""

import json
import re

import discord
import pytest

import components_v2
import i18n
from streams import Streams, card_title, default_template, render_template, resolve_template
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild


def _cog(channel):
    guild = FakeGuild(channels=[channel])
    bot = FakeBot(guild)
    cog = Streams(bot)
    cog._poll.cancel()
    return cog


def _sub(**extra):
    base = {
        "id": "1",
        "channel_id": 500,
        "platform": "twitch",
        "use_embed": True,
        "mention_everyone": False,
    }
    base.update(extra)
    return base


@pytest.mark.asyncio
async def test_announce_sends_layout_view_not_classic_embed():
    channel = FakeChannel(500)
    cog = _cog(channel)
    embed = discord.Embed(title="Live now", url="https://www.twitch.tv/foo", color=0x9146FF)
    embed.set_author(name="foo — Twitch")
    embed.add_field(name="Game", value="VALORANT", inline=True)
    embed.set_image(url="https://example.com/thumb.jpg")

    ok = await cog._announce(_sub(), "foo is live", embed)

    assert ok is True
    sent = channel.send_calls[0]
    assert sent.get("embed") is None
    assert sent.get("content") is None
    assert sent["view"].has_components_v2()


@pytest.mark.asyncio
async def test_announce_keeps_link_buttons_on_layout():
    channel = FakeChannel(500)
    cog = _cog(channel)
    embed = discord.Embed(title="clip", url="https://www.tiktok.com/@foo/video/1")
    view = discord.ui.View()
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Watch", url="https://www.tiktok.com/@foo/video/1"))

    ok = await cog._announce(_sub(platform="tiktok"), "new video", embed, view=view, tiktok_kind="video")

    assert ok is True
    layout = channel.send_calls[0]["view"]
    assert layout.has_components_v2()
    payload = layout.to_components()
    dumped = str(payload)
    assert "https://www.tiktok.com/@foo/video/1" in dumped


@pytest.mark.asyncio
async def test_announce_without_card_still_uses_layout():
    channel = FakeChannel(500)
    cog = _cog(channel)
    embed = discord.Embed(title="ignored")

    ok = await cog._announce(_sub(use_embed=False), "plain text", embed)

    assert ok is True
    sent = channel.send_calls[0]
    assert sent.get("embed") is None
    assert sent["view"].has_components_v2()


def _payload_blob(view) -> str:
    return json.dumps(view.to_components(), ensure_ascii=False)


def _component_types(obj, acc=None):
    if acc is None:
        acc = []
    if isinstance(obj, dict):
        if "type" in obj:
            acc.append(obj["type"])
        for value in obj.values():
            _component_types(value, acc)
    elif isinstance(obj, list):
        for item in obj:
            _component_types(item, acc)
    return acc


def test_resolve_template_empty_falls_back_to_default():
    lang = "ru"
    default = default_template("twitch", lang)
    assert resolve_template({"template": ""}, lang, "twitch") == default
    assert resolve_template({"template": "   "}, lang, "twitch") == default
    custom = "Кастом **{{channel}}**"
    assert resolve_template({"template": custom}, lang, "twitch") == custom
    rendered = render_template(custom, "Juniper", "title", "game", "https://twitch.tv/j", lang)
    assert rendered == "Кастом **Juniper**"


def test_card_title_is_plain_heading():
    title = card_title("twitch", "Juniper", "ru")
    assert title == "Juniper запустил вещание на Twitch!"
    assert "[" not in title
    assert "](" not in title


@pytest.mark.asyncio
async def test_send_test_announce_empty_template_uses_default_greeting():
    channel = FakeChannel(500)
    cog = _cog(channel)
    sub = _sub(
        display_name="Juniper",
        identifier="juniper",
        template="",
        avatar_url="https://example.com/avatar.jpg",
    )

    err = await cog.send_test_announce(1, sub)

    assert err is None
    layout = channel.send_calls[0]["view"]
    payload = layout.to_components()
    blob = _payload_blob(layout)
    assert payload[0]["type"] == discord.ComponentType.text_display.value
    assert payload[1]["type"] == discord.ComponentType.container.value
    greeting = payload[0]["content"]
    assert "Хей!" in greeting
    assert "**Juniper**" in greeting
    assert "запустил вещание на канале" in greeting
    assert "Хей!" not in str(payload[1])
    assert "Juniper запустил вещание на Twitch!" in blob
    assert "[Juniper запустил вещание на Twitch!](" not in blob
    assert not re.search(r"\[[^\]]+\]\(https?://", blob)
    assert discord.ComponentType.thumbnail.value not in _component_types(payload)
    assert "avatar.jpg" not in blob
    assert i18n.t("streams.test.sample_title", "ru") in blob
    assert "**Зрителей** | **Игра**" in blob


@pytest.mark.asyncio
async def test_send_test_announce_keeps_custom_template():
    channel = FakeChannel(500)
    cog = _cog(channel)
    sub = _sub(
        display_name="Juniper",
        identifier="juniper",
        template="Кастом **{{channel}}** — {{stream}}",
    )

    err = await cog.send_test_announce(1, sub)

    assert err is None
    blob = _payload_blob(channel.send_calls[0]["view"])
    assert "Кастом **Juniper**" in blob
    assert "Хей!" not in blob
    assert "Juniper запустил вещание на Twitch!" in blob


@pytest.mark.asyncio
async def test_announce_stream_card_has_no_markdown_title_or_thumbnail():
    channel = FakeChannel(500)
    cog = _cog(channel)
    embed = discord.Embed(
        title="Juniper запустил вещание на Twitch!",
        description="SNAPE_CHAT",
        url="https://www.twitch.tv/juniper",
        color=0x9146FF,
    )
    embed.set_author(name="Juniper — Twitch", icon_url="https://example.com/avatar.jpg")
    embed.set_thumbnail(url="https://example.com/avatar.jpg")
    embed.set_image(url="https://example.com/preview.jpg")
    embed.add_field(name="Зрителей", value="12", inline=True)
    embed.add_field(name="Игра", value="VALORANT", inline=True)

    ok = await cog._announce(_sub(), "Хей! **Juniper** запустил вещание на канале.", embed)

    assert ok is True
    layout = channel.send_calls[0]["view"]
    payload = layout.to_components()
    blob = _payload_blob(layout)
    assert layout.has_components_v2()
    assert payload[0]["type"] == discord.ComponentType.text_display.value
    assert payload[1]["type"] == discord.ComponentType.container.value
    assert "[Juniper запустил вещание на Twitch!](" not in blob
    assert discord.ComponentType.thumbnail.value not in _component_types(payload)
    assert "preview.jpg" in blob
    assert "avatar.jpg" not in blob
    assert "SNAPE_CHAT" in blob
