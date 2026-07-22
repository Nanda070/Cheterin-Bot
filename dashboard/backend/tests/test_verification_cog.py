"""Тесты кога «Верификация»: выключена по умолчанию, join-роль, кнопка."""

import pytest

import moderation_log
import settings_db
import verification_core
from verification import VerificationCog
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, FakeRole


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    monkeypatch.setattr(moderation_log, "LOG_FILE", str(tmp_path / "moderation_log.json"))


class FakeResponse:
    def __init__(self):
        self.messages = []

    async def send_message(self, content=None, view=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "view": view, "ephemeral": ephemeral})


class FakeInteraction:
    guild_id = 1
    def __init__(self, user, guild, channel=None):
        self.user = user
        self.guild = guild
        self.channel = channel
        self.response = FakeResponse()


UNVERIFIED_ROLE_ID = 111
VERIFIED_ROLE_ID = 222


def build(enabled=True, unverified=True, verified=True):
    roles = [FakeRole(UNVERIFIED_ROLE_ID, name="Unverified"), FakeRole(VERIFIED_ROLE_ID, name="Verified")]
    member = FakeMember(20, name="newbie")
    guild = FakeGuild(members=[member], roles=roles)
    verification_core.save_config(guild.id, {
        "enabled": enabled,
        "unverified_role_id": UNVERIFIED_ROLE_ID if unverified else 0,
        "verified_role_id": VERIFIED_ROLE_ID if verified else 0,
    })
    bot = FakeBot(guild)
    cog = VerificationCog(bot)
    return cog, guild, member, bot


# ────────────────────────── Выключена по умолчанию ──────────────────────────

@pytest.mark.asyncio
async def test_disabled_by_default_no_join_role():
    guild = FakeGuild(members=[], roles=[FakeRole(UNVERIFIED_ROLE_ID, name="Unverified")])
    member = FakeMember(20, name="newbie")
    member.guild = guild
    bot = FakeBot(guild)
    cog = VerificationCog(bot)  # save_config НЕ вызывался — чистый дефолт

    await cog.on_member_join(member)

    assert member.action_calls == []


@pytest.mark.asyncio
async def test_explicitly_disabled_no_join_role():
    cog, guild, member, bot = build(enabled=False)
    await cog.on_member_join(member)
    assert member.action_calls == []


# ────────────────────────── Роль при входе ──────────────────────────

@pytest.mark.asyncio
async def test_join_assigns_unverified_role():
    cog, guild, member, bot = build()
    await cog.on_member_join(member)

    assert len(member.action_calls) == 1
    action, kwargs = member.action_calls[0]
    assert action == "add_roles"
    assert kwargs["role"].id == UNVERIFIED_ROLE_ID


@pytest.mark.asyncio
async def test_join_without_unverified_role_configured_does_nothing():
    cog, guild, member, bot = build(unverified=False)
    await cog.on_member_join(member)
    assert member.action_calls == []


# ────────────────────────── Кнопка «Я не бот» ──────────────────────────

@pytest.mark.asyncio
async def test_verify_disabled_module():
    cog, guild, member, bot = build(enabled=False)
    interaction = FakeInteraction(member, guild)
    await cog.handle_verify(interaction)
    assert "отключён" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_verify_not_configured():
    cog, guild, member, bot = build(verified=False)
    interaction = FakeInteraction(member, guild)
    await cog.handle_verify(interaction)
    assert "не настроена" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_verify_happy_path_swaps_roles():
    cog, guild, member, bot = build()
    unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)
    member.roles.append(unverified_role)
    interaction = FakeInteraction(member, guild)

    await cog.handle_verify(interaction)

    actions = [a for a, _ in member.action_calls]
    assert "add_roles" in actions
    assert "remove_roles" in actions
    add_kwargs = next(k for a, k in member.action_calls if a == "add_roles")
    assert add_kwargs["role"].id == VERIFIED_ROLE_ID
    remove_kwargs = next(k for a, k in member.action_calls if a == "remove_roles")
    assert remove_kwargs["role"].id == UNVERIFIED_ROLE_ID
    assert "Добро пожаловать" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_verify_without_unverified_role_present_only_adds():
    cog, guild, member, bot = build()  # у member нет unverified-роли изначально
    interaction = FakeInteraction(member, guild)

    await cog.handle_verify(interaction)

    actions = [a for a, _ in member.action_calls]
    assert actions == ["add_roles"]  # remove_roles не вызывался — нечего снимать


@pytest.mark.asyncio
async def test_verify_already_verified():
    cog, guild, member, bot = build()
    member.roles.append(guild.get_role(VERIFIED_ROLE_ID))
    interaction = FakeInteraction(member, guild)

    await cog.handle_verify(interaction)

    assert "уже верифицированы" in interaction.response.messages[0]["content"]
    assert member.action_calls == []


@pytest.mark.asyncio
async def test_verify_missing_role_on_server():
    cog, guild, member, bot = build()
    guild.roles = [r for r in guild.roles if r.id != VERIFIED_ROLE_ID]  # роль удалили с сервера
    interaction = FakeInteraction(member, guild)

    await cog.handle_verify(interaction)

    assert "не найдена" in interaction.response.messages[0]["content"]


# ────────────────────────── /verify_setup ──────────────────────────

@pytest.mark.asyncio
async def test_setup_disabled_module():
    cog, guild, member, bot = build(enabled=False)
    from dashboard.backend.tests.fakes import FakeChannel

    channel = FakeChannel(500)
    interaction = FakeInteraction(member, guild, channel)

    await VerificationCog.verify_setup.callback(cog, interaction)

    assert "отключён" in interaction.response.messages[0]["content"]
    assert channel.send_calls == []


@pytest.mark.asyncio
async def test_setup_posts_panel_when_configured():
    cog, guild, member, bot = build()
    from dashboard.backend.tests.fakes import FakeChannel

    channel = FakeChannel(500)
    interaction = FakeInteraction(member, guild, channel)

    await VerificationCog.verify_setup.callback(cog, interaction)

    assert "установлена" in interaction.response.messages[0]["content"]
    assert len(channel.send_calls) == 1
    view = channel.send_calls[0]["view"]
    assert view is not None
    assert view.children[0].label == "Я не бот"


@pytest.mark.asyncio
async def test_setup_posts_panel_with_english_button_when_guild_language_en():
    import language_core
    from dashboard.backend.tests.fakes import FakeChannel

    language_core.set_language(1, "en")
    cog, guild, member, bot = build()
    channel = FakeChannel(500)
    interaction = FakeInteraction(member, guild, channel)

    await VerificationCog.verify_setup.callback(cog, interaction)

    view = channel.send_calls[0]["view"]
    button = view.children[0]
    assert button.label == "I'm not a bot"
