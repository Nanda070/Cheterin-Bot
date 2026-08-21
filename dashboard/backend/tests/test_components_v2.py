import discord

import components_v2


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
