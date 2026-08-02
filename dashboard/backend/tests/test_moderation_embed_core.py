import discord

import moderation_embed_core as core


def test_build_action_log_embed_field_order_ru():
    embed = core.build_action_log_embed(
        "ru",
        title="Тест",
        who_value="мод (`1`)",
        target_value="юзер (`2`)",
        reason="спам",
        extra="Срок: 1 ч.",
    )
    names = [f.name for f in embed.fields]
    assert names == ["Кто", "Кого", "Причина", "Дополнительно"]
    assert embed.fields[2].value == "спам"
    assert embed.fields[3].value == "Срок: 1 ч."


def test_build_action_log_embed_omits_empty_reason():
    embed = core.build_action_log_embed(
        "en",
        title="Test",
        who_value="mod",
        target_value="user",
        reason="",
        extra="Duration: 10 min.",
    )
    names = [f.name for f in embed.fields]
    assert names == ["Moderator", "Target", "Details"]


def test_build_user_action_embed_formats_actor():
    class _User:
        id = 42
        name = "alice"
        mention = "<@42>"

    embed = core.build_user_action_embed(
        "en",
        title="Mute",
        actor=_User(),
        target_name="bob",
        target_id=7,
        target_mention="<@7>",
        reason="flood",
    )
    assert embed.fields[0].value == "<@42> (`42`)"
    assert embed.fields[1].value == "<@7> (`7`)"
    assert isinstance(embed.color, discord.Color)


def test_actor_ref_automatic_when_none():
    assert core.actor_ref(None, lang="en") == "Automatic"
    assert core.actor_ref(None, lang="ru") == "Автоматически"
