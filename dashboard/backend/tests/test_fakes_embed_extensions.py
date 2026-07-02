import discord
import pytest

from dashboard.backend.tests.fakes import FakeChannel, FakeComponentRow, FakeMessage


@pytest.mark.asyncio
async def test_fake_channel_send_creates_and_stores_message():
    channel = FakeChannel(500, next_message_id=999)
    embed = discord.Embed(title="Hello")
    message = await channel.send(content="hi", embed=embed)
    assert message.id == 999
    assert message.content == "hi"
    assert message.embeds == [embed]
    assert channel.send_calls == [{"content": "hi", "embed": embed}]
    fetched = await channel.fetch_message(999)
    assert fetched is message


@pytest.mark.asyncio
async def test_fake_channel_send_raises_when_configured():
    channel = FakeChannel(500)
    channel.send_raises = discord.HTTPException.__new__(discord.HTTPException)
    with pytest.raises(discord.HTTPException):
        await channel.send(content="hi")


@pytest.mark.asyncio
async def test_fake_message_edit_updates_content_embed_and_components():
    message = FakeMessage(1)
    new_embed = discord.Embed(title="Updated")
    new_view = "some-view-marker"
    await message.edit(content="new content", embed=new_embed, view=new_view)
    assert message.content == "new content"
    assert message.embeds == [new_embed]
    assert message.components == new_view
    assert message.edit_calls == [{"content": "new content", "embed": new_embed, "view": new_view}]


@pytest.mark.asyncio
async def test_fake_message_edit_raises_when_configured():
    message = FakeMessage(1)
    message.edit_raises = discord.HTTPException.__new__(discord.HTTPException)
    with pytest.raises(discord.HTTPException):
        await message.edit(content="x")


def test_fake_message_defaults_to_empty_embeds_and_components():
    message = FakeMessage(1)
    assert message.embeds == []
    assert message.components == []
    assert message.content is None


def test_fake_component_row_holds_children():
    button = discord.ui.Button(label="test", custom_id="btn_role_7")
    row = FakeComponentRow([button])
    assert row.children == [button]
