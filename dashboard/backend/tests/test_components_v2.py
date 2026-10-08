import discord
import pytest

import bot.core.components_v2 as components_v2
from dashboard.backend.tests.fakes import FakeChannel


def test_normalize_version_defaults_to_v1():
    assert components_v2.normalize_version(None) == "v1"
    assert components_v2.normalize_version("") == "v1"
    assert components_v2.normalize_version("v1") == "v1"
    assert components_v2.normalize_version("V2") == "v2"
    assert components_v2.normalize_version("components_v2") == "v2"


def test_embed_to_text_blocks_maps_title_fields_footer():
    embed = discord.Embed(title="Hello", description="World", color=0xFF4655)
    embed.add_field(name="A", value="1", inline=True)
    embed.add_field(name="B", value="2", inline=True)
    embed.set_footer(text="footer")
    blocks = components_v2.embed_to_text_blocks(embed, content="@everyone")
    joined = "\n".join(blocks)
    assert "@everyone" in joined
    assert "## Hello" in joined
    assert "World" in joined
    assert "**A**" in joined
    assert "-# footer" in joined


def test_build_layout_view_sets_components_v2_flag_path():
    embed = discord.Embed(title="Lobby", description="desc", color=0xFF4655)
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Join", custom_id="customs:join", style=discord.ButtonStyle.success))
    layout = components_v2.build_layout_view(embed=embed, source_view=view, keep_callbacks=False)
    assert layout.has_components_v2()
    payload = layout.to_components()
    assert payload
    assert payload[0]["type"] == discord.ComponentType.container.value


def test_interactive_rows_clone_custom_ids():
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="A", custom_id="customs:join", row=0))
    view.add_item(discord.ui.Button(label="B", custom_id="customs:leave", row=0))
    rows = components_v2.interactive_rows_from_view(view, keep_callbacks=False)
    assert len(rows) == 1
    ids = [c.custom_id for c in rows[0].children]
    assert ids == ["customs:join", "customs:leave"]
    # Original view untouched when cloning
    assert len(view.children) == 2


def test_v2_plain_text_unescapes_and_unwraps_link():
    assert components_v2.v2_plain_text("SNAPE\\_CHAT") == "SNAPE_CHAT"
    assert components_v2.v2_plain_text("[Hello](https://twitch.tv/x)") == "Hello"
    assert "🎮" in components_v2.v2_plain_text("Ranked 🎮")


def test_build_stream_layout_view_looks_like_juniper_card():
    embed = discord.Embed(
        title="Juniper started streaming on Twitch!",
        description="SNAPE_CHAT \\o/ 🎮",
        url="https://www.twitch.tv/juniper",
        color=0x9146FF,
    )
    embed.set_author(name="Juniper — Twitch", icon_url="https://example.com/avatar.jpg")
    embed.add_field(name="Viewers", value="12", inline=True)
    embed.add_field(name="Game", value="VALORANT", inline=True)
    embed.set_image(url="https://example.com/preview.jpg")
    embed.set_thumbnail(url="https://example.com/avatar.jpg")
    view = discord.ui.View()
    view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Watch", url="https://www.twitch.tv/juniper"))

    layout = components_v2.build_stream_layout_view(
        embed=embed,
        content="Hey **Juniper** come join!",
        source_view=view,
    )
    assert layout.has_components_v2()
    payload = layout.to_components()
    blob = str(payload)
    types = _component_types(payload)

    assert payload[0]["type"] == discord.ComponentType.text_display.value
    assert "Hey **Juniper** come join!" in payload[0]["content"]
    assert payload[1]["type"] == discord.ComponentType.container.value
    container_blob = str(payload[1])
    assert "Hey **Juniper** come join!" not in container_blob
    assert "## Juniper started streaming on Twitch!" in blob
    assert "[Juniper started streaming on Twitch!](" not in blob
    assert "SNAPE_CHAT" in blob
    assert "SNAPE\\_CHAT" not in blob
    assert "🎮" in blob
    assert "**Viewers** | **Game**" in blob
    assert "preview.jpg" in blob
    assert "avatar.jpg" not in blob
    assert discord.ComponentType.thumbnail.value not in types
    assert "https://www.twitch.tv/juniper" in blob


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


@pytest.mark.asyncio
async def test_send_message_v2_forwards_allowed_mentions():
    channel = FakeChannel(1)
    embed = discord.Embed(title="Hi")
    allowed = discord.AllowedMentions.none()
    await components_v2.send_message(
        channel,
        version=components_v2.VERSION_V2,
        content="ping",
        embed=embed,
        allowed_mentions=allowed,
    )
    sent = channel.send_calls[0]
    assert sent.get("embed") is None
    assert sent.get("content") is None
    assert sent["view"].has_components_v2()
    assert sent["allowed_mentions"] is allowed


def _containers(layout):
    return [c for c in layout.children if isinstance(c, discord.ui.Container)]


def test_build_layout_view_makes_one_container_per_embed():
    embeds = [discord.Embed(title="A", colour=0x111111), discord.Embed(title="B", colour=0x222222)]
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="R", custom_id="btn_role_7"))
    layout = components_v2.build_layout_view(embeds=embeds, content="hello", source_view=view)
    first, last = _containers(layout)
    assert [int(getattr(c.accent_colour, "value", c.accent_colour)) for c in (first, last)] == [0x111111, 0x222222]
    assert first.children[0].content == "hello"
    assert not any(isinstance(i, discord.ui.ActionRow) for i in first.children)
    assert any(isinstance(i, discord.ui.ActionRow) for i in last.children)


def test_build_layout_view_empty_embeds_list_keeps_single_container():
    layout = components_v2.build_layout_view(embeds=[], content="only text")
    (container,) = _containers(layout)
    assert container.children[0].content == "only text"


def test_layout_limit_error_flags_text_over_4000():
    embeds = [discord.Embed(description="x" * 2100), discord.Embed(description="y" * 2100)]
    assert components_v2.layout_limit_error(components_v2.build_layout_view(embeds=embeds)) == "v2_too_large"
    assert components_v2.layout_limit_error(components_v2.build_layout_view(embed=discord.Embed(title="ok"))) is None


@pytest.mark.asyncio
async def test_send_message_v2_enforce_limits_raises_on_more_than_40_components():
    channel = FakeChannel(1)
    embeds = []
    for i in range(10):
        embed = discord.Embed(title=f"E{i}")
        for j in range(4):
            embed.add_field(name=f"n{j}", value="v", inline=False)
        embeds.append(embed)
    # 10 containers x (header + 4 field blocks) = 60 components; discord.py refuses to build it.
    with pytest.raises(components_v2.LayoutTooLargeError):
        await components_v2.send_message(channel, version="v2", embeds=embeds, enforce_limits=True)
    assert channel.send_calls == []


@pytest.mark.asyncio
async def test_send_message_v1_forwards_embeds_list():
    channel = FakeChannel(1)
    embeds = [discord.Embed(title="A"), discord.Embed(title="B")]
    message = await components_v2.send_message(channel, version="v1", embeds=embeds)
    assert channel.send_calls[0]["embeds"] == embeds
    assert "embed" not in channel.send_calls[0]
    assert message.embeds == embeds


@pytest.mark.asyncio
async def test_send_message_v2_enforce_limits_raises_before_send():
    channel = FakeChannel(1)
    embeds = [discord.Embed(description="x" * 2100), discord.Embed(description="y" * 2100)]
    with pytest.raises(components_v2.LayoutTooLargeError):
        await components_v2.send_message(channel, version="v2", embeds=embeds, enforce_limits=True)
    assert channel.send_calls == []


@pytest.mark.asyncio
async def test_edit_message_v1_empty_embeds_list_clears_existing():
    from dashboard.backend.tests.fakes import FakeMessage

    message = FakeMessage(5, embeds=[discord.Embed(title="old")], content="x")
    await components_v2.edit_message(message, version="v1", content="only text", embeds=[], view=None)
    assert message.embeds == []
    assert "embed" not in message.edit_calls[0]


@pytest.mark.asyncio
async def test_edit_message_v2_uses_embeds_list():
    from dashboard.backend.tests.fakes import FakeMessage

    message = FakeMessage(5, embeds=[discord.Embed(title="old")], content="x")
    embeds = [discord.Embed(title="A"), discord.Embed(title="B")]
    await components_v2.edit_message(message, version="v2", content=None, embeds=embeds, view=None)
    assert len(_containers(message.edit_calls[0]["view"])) == 2
