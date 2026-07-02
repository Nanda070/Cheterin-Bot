import discord
import pytest

import reaction_roles
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, FakeMessage, FakeRole


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(reaction_roles, "CONFIG_FILE", str(tmp_path / "reaction_roles.json"))


class FakePayload:
    def __init__(self, message_id, user_id, guild_id, emoji, member=None):
        self.message_id = message_id
        self.user_id = user_id
        self.guild_id = guild_id
        self.emoji = emoji
        self.member = member


def _setup_config(message_id, role_id, emoji="📖"):
    reaction_roles.save_config(
        {str(message_id): {"channel_id": "500", "pairs": [{"emoji": emoji, "role_id": str(role_id)}]}}
    )


@pytest.mark.asyncio
async def test_handle_reaction_change_add_grants_role_using_payload_member():
    role = FakeRole(7, name="VIP", position=5)
    reactor = FakeMember(50, name="reactor")
    guild = FakeGuild(members=[reactor], roles=[role])
    bot = FakeBot(guild)
    _setup_config(999, 7)

    payload = FakePayload(message_id=999, user_id=50, guild_id=1, emoji="📖", member=reactor)
    await reaction_roles.handle_reaction_change(bot, payload, "add")

    action, kwargs = reactor.action_calls[0]
    assert action == "add_roles"
    assert kwargs["role"].id == 7
    assert "Reaction role: add" in kwargs["reason"]


@pytest.mark.asyncio
async def test_handle_reaction_change_remove_revokes_role_by_resolving_member():
    role = FakeRole(7, name="VIP", position=5)
    reactor = FakeMember(50, name="reactor")
    guild = FakeGuild(members=[reactor], roles=[role])
    bot = FakeBot(guild)
    _setup_config(999, 7)

    # on_raw_reaction_remove never carries payload.member — must resolve via guild
    payload = FakePayload(message_id=999, user_id=50, guild_id=1, emoji="📖", member=None)
    await reaction_roles.handle_reaction_change(bot, payload, "remove")

    action, kwargs = reactor.action_calls[0]
    assert action == "remove_roles"
    assert kwargs["role"].id == 7


@pytest.mark.asyncio
async def test_handle_reaction_change_ignores_bots_own_reaction():
    role = FakeRole(7, name="VIP", position=5)
    guild = FakeGuild(roles=[role])
    bot = FakeBot(guild)
    _setup_config(999, 7)

    payload = FakePayload(message_id=999, user_id=bot.user.id, guild_id=1, emoji="📖")
    await reaction_roles.handle_reaction_change(bot, payload, "add")
    # No exception, and nothing to assert on since no member was touched — the
    # test's job is to prove this path returns early without crashing when
    # bot.get_guild/get_member would otherwise be exercised.


@pytest.mark.asyncio
async def test_handle_reaction_change_ignores_unconfigured_message():
    guild = FakeGuild()
    bot = FakeBot(guild)
    payload = FakePayload(message_id=12345, user_id=50, guild_id=1, emoji="📖")
    await reaction_roles.handle_reaction_change(bot, payload, "add")
    # No config exists for this message — should be a silent no-op.


@pytest.mark.asyncio
async def test_handle_reaction_change_ignores_unmatched_emoji():
    role = FakeRole(7, name="VIP", position=5)
    reactor = FakeMember(50, name="reactor")
    guild = FakeGuild(members=[reactor], roles=[role])
    bot = FakeBot(guild)
    _setup_config(999, 7, emoji="📖")

    payload = FakePayload(message_id=999, user_id=50, guild_id=1, emoji="❌", member=reactor)
    await reaction_roles.handle_reaction_change(bot, payload, "add")
    assert reactor.action_calls == []


@pytest.mark.asyncio
async def test_cleanup_missing_messages_removes_entries_for_deleted_messages():
    channel = FakeChannel(500, messages={})  # message 999 does NOT exist
    guild = FakeGuild(channels=[channel])
    bot = FakeBot(guild)
    _setup_config(999, 7)

    removed = await reaction_roles.cleanup_missing_messages(bot, guild_id=1)

    assert removed == 1
    assert reaction_roles.load_config() == {}


@pytest.mark.asyncio
async def test_cleanup_missing_messages_keeps_entries_for_existing_messages():
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    guild = FakeGuild(channels=[channel])
    bot = FakeBot(guild)
    _setup_config(999, 7)

    removed = await reaction_roles.cleanup_missing_messages(bot, guild_id=1)

    assert removed == 0
    assert "999" in reaction_roles.load_config()
