import discord
import pytest

from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeCustomEmoji,
    FakeGuild,
    FakeMember,
    FakeMessage,
)


def test_fake_custom_emoji_str_format():
    emoji = FakeCustomEmoji(555, "pepehands")
    assert str(emoji) == "<:pepehands:555>"


@pytest.mark.asyncio
async def test_fake_message_records_add_reaction():
    message = FakeMessage(1)
    await message.add_reaction("📖")
    assert message.reaction_calls == [("add", "📖")]


@pytest.mark.asyncio
async def test_fake_message_records_remove_reaction():
    message = FakeMessage(1)
    bot_user = FakeMember(2, name="bot")
    await message.remove_reaction("📖", bot_user)
    assert message.reaction_calls == [("remove", "📖")]


@pytest.mark.asyncio
async def test_fake_channel_fetch_message_returns_existing():
    message = FakeMessage(42)
    channel = FakeChannel(1, messages={42: message})
    fetched = await channel.fetch_message(42)
    assert fetched is message


@pytest.mark.asyncio
async def test_fake_channel_fetch_message_raises_not_found():
    channel = FakeChannel(1, messages={})
    with pytest.raises(discord.NotFound):
        await channel.fetch_message(999)


def test_fake_guild_get_channel_and_defaults():
    channel = FakeChannel(10, name="general")
    emoji = FakeCustomEmoji(20, "wave")
    guild = FakeGuild(channels=[channel], emojis=[emoji])
    assert guild.get_channel(10) is channel
    assert guild.get_channel(999) is None
    assert guild.emojis == [emoji]
    # Backward compatibility: no channels/emojis passed still works
    bare_guild = FakeGuild()
    assert bare_guild.channels == []
    assert bare_guild.emojis == []


def test_fake_bot_has_user_by_default():
    guild = FakeGuild()
    bot = FakeBot(guild)
    assert bot.user.name == "ChetBot"
    assert bot.user.bot is True
