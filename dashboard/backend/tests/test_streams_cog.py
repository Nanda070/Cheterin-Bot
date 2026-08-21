"""Стрим-уведомления уходят через LayoutView, без классического embed."""

import discord
import pytest

from streams import Streams
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
