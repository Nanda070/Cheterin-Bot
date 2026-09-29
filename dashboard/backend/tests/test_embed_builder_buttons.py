import discord

import bot.core.embed_builder as embed_builder
from dashboard.backend.tests.fakes import FakeComponentRow, FakeGuild, FakeMessage, FakeRole


def test_build_role_button_view_creates_buttons_with_role_names():
    role = FakeRole(7, name="VIP")
    guild = FakeGuild(roles=[role])
    view = embed_builder.build_role_button_view(guild, [7])
    assert len(view.children) == 1
    button = view.children[0]
    assert button.custom_id == "btn_role_7"
    assert button.label == "VIP"


def test_build_role_button_view_falls_back_to_id_when_role_missing():
    guild = FakeGuild(roles=[])
    view = embed_builder.build_role_button_view(guild, [999])
    assert view.children[0].label == "999"


def test_parse_role_button_ids_extracts_matching_custom_ids():
    row = FakeComponentRow(
        [
            discord.ui.Button(label="a", custom_id="btn_role_7"),
            discord.ui.Button(label="b", custom_id="btn_role_8"),
        ]
    )
    message = FakeMessage(1, components=[row])
    assert embed_builder.parse_role_button_ids(message) == [7, 8]


def test_parse_role_button_ids_ignores_non_role_buttons():
    row = FakeComponentRow([discord.ui.Button(label="a", custom_id="btn_form_1")])
    message = FakeMessage(1, components=[row])
    assert embed_builder.parse_role_button_ids(message) == []


def test_parse_role_button_ids_handles_no_components():
    message = FakeMessage(1)
    assert embed_builder.parse_role_button_ids(message) == []


def test_parse_role_button_ids_nested_v2_container():
    inner = FakeComponentRow([discord.ui.Button(label="VIP", custom_id="btn_role_7")])
    container = FakeComponentRow([inner])
    message = FakeMessage(1, components=[container])
    assert embed_builder.parse_role_button_ids(message) == [7]


def test_parse_role_button_ids_from_layout_view():
    import bot.core.components_v2 as components_v2

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="VIP", custom_id="btn_role_7"))
    layout = components_v2.build_layout_view(embed=discord.Embed(title="T"), source_view=view)
    message = FakeMessage(1, components=layout, components_v2=True)
    assert embed_builder.parse_role_button_ids(message) == [7]
