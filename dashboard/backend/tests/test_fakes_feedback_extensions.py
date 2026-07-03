import discord
import pytest

from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, FakeThread


@pytest.mark.asyncio
async def test_fake_thread_send_creates_and_stores_message():
    thread = FakeThread(700, next_message_id=3000)
    embed = discord.Embed(title="Hello")
    message = await thread.send(embed=embed)
    assert message.id == 3000
    assert message.embeds == [embed]
    fetched = await thread.fetch_message(3000)
    assert fetched is message


@pytest.mark.asyncio
async def test_fake_thread_edit_records_archived_and_locked():
    thread = FakeThread(700)
    await thread.edit(archived=True, locked=True)
    assert thread.archived is True
    assert thread.locked is True
    assert thread.edit_calls == [{"archived": True, "locked": True}]


@pytest.mark.asyncio
async def test_fake_thread_send_raises_when_configured():
    thread = FakeThread(700)
    thread.send_raises = discord.HTTPException.__new__(discord.HTTPException)
    with pytest.raises(discord.HTTPException):
        await thread.send(content="hi")


@pytest.mark.asyncio
async def test_fake_thread_fetch_message_raises_not_found():
    thread = FakeThread(700, messages={})
    with pytest.raises(discord.NotFound):
        await thread.fetch_message(999)


def test_fake_bot_get_channel_finds_channel_and_thread():
    channel = FakeChannel(500)
    thread = FakeThread(700)
    guild = FakeGuild(channels=[channel], threads=[thread])
    bot = FakeBot(guild)
    assert bot.get_channel(500) is channel
    assert bot.get_channel(700) is thread
    assert bot.get_channel(999) is None


@pytest.mark.asyncio
async def test_fake_bot_fetch_user_falls_back_when_not_in_guild():
    submitter = FakeMember(50, name="gone")
    guild = FakeGuild(members=[])
    bot = FakeBot(guild, fetchable_users=[submitter])
    user = await bot.fetch_user(50)
    assert user is submitter


@pytest.mark.asyncio
async def test_fake_bot_fetch_user_raises_when_nowhere_found():
    guild = FakeGuild()
    bot = FakeBot(guild)
    with pytest.raises(discord.NotFound):
        await bot.fetch_user(999)


@pytest.mark.asyncio
async def test_fake_bot_update_file_records_calls():
    guild = FakeGuild()
    bot = FakeBot(guild)
    await bot.update_file()
    await bot.update_file()
    assert bot.update_file_calls == 2


@pytest.mark.asyncio
async def test_fake_member_send_records_dm():
    member = FakeMember(50, name="user")
    embed = discord.Embed(title="DM")
    await member.send(embed=embed)
    assert member.send_calls == [{"embed": embed}]


@pytest.mark.asyncio
async def test_fake_member_send_raises_when_configured():
    member = FakeMember(50, name="user")
    member.send_raises = discord.HTTPException.__new__(discord.HTTPException)
    with pytest.raises(discord.HTTPException):
        await member.send(content="hi")
