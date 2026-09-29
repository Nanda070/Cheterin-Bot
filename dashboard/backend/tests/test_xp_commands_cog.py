"""Тесты команд /xp (add/set/clear) и /leaders в XPCog — вызов через .callback(),
тот же паттерн, что и в test_moderation_commands_cog.py."""

import pytest

import bot.core.settings_db as settings_db
import bot.core.stats_db as stats_db
import bot.modules.levels.xp_core as xp_core
from bot.modules.levels.xp import XPCog
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("STATS_DB_PATH", str(tmp_path / "stats.db"))
    stats_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


class FakeResponse:
    def __init__(self):
        self.messages = []

    async def send_message(self, content=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "ephemeral": ephemeral})

    async def defer(self, ephemeral=False, **kwargs):
        pass


class FakeFollowup:
    def __init__(self):
        self.messages = []

    async def send(self, content=None, embed=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "embed": embed, "ephemeral": ephemeral})


class FakeInteraction:
    guild_id = 1
    def __init__(self, user, guild):
        self.user = user
        self.guild = guild
        self.response = FakeResponse()
        self.followup = FakeFollowup()

    def all_messages(self):
        return self.response.messages + self.followup.messages


class Choice:
    def __init__(self, value: str):
        self.value = value


def build(enabled=True):
    member = FakeMember(20, name="player", display_name="Player")
    admin = FakeMember(10, name="admin")
    guild = FakeGuild(members=[member, admin])
    xp_core.save_config(guild.id, {"enabled": enabled})
    bot = FakeBot(guild)
    cog = XPCog(bot)
    return cog, guild, member, admin


# ────────────────────────── /xp add ──────────────────────────

@pytest.mark.asyncio
async def test_xp_add_increases_from_zero():
    cog, guild, member, admin = build()
    interaction = FakeInteraction(admin, guild)

    await XPCog.xp_command.callback(cog, interaction, Choice("add"), member, 150)

    row = stats_db.xp_get_member(1, member.id)
    assert row["xp"] == 150
    assert "0 → **150**" in interaction.all_messages()[0]["content"]


@pytest.mark.asyncio
async def test_xp_add_negative_does_not_go_below_zero():
    cog, guild, member, admin = build()
    stats_db.xp_add_text(1, member.id, 50, 1000)
    interaction = FakeInteraction(admin, guild)

    await XPCog.xp_command.callback(cog, interaction, Choice("add"), member, -500)

    row = stats_db.xp_get_member(1, member.id)
    assert row["xp"] == 0


@pytest.mark.asyncio
async def test_xp_add_disabled_module():
    cog, guild, member, admin = build(enabled=False)
    interaction = FakeInteraction(admin, guild)

    await XPCog.xp_command.callback(cog, interaction, Choice("add"), member, 100)

    assert "отключена" in interaction.response.messages[0]["content"]
    assert stats_db.xp_get_member(1, member.id) is None


@pytest.mark.asyncio
async def test_xp_add_rejects_bots():
    cog, guild, member, admin = build()
    bot_member = FakeMember(30, name="botty", bot=True)
    interaction = FakeInteraction(admin, guild)

    await XPCog.xp_command.callback(cog, interaction, Choice("add"), bot_member, 100)

    assert "ботов" in interaction.response.messages[0]["content"]


# ────────────────────────── /xp set ──────────────────────────

@pytest.mark.asyncio
async def test_xp_set_exact_value():
    cog, guild, member, admin = build()
    interaction = FakeInteraction(admin, guild)

    await XPCog.xp_command.callback(cog, interaction, Choice("set"), member, 777)

    row = stats_db.xp_get_member(1, member.id)
    assert row["xp"] == 777
    assert "**777**" in interaction.all_messages()[0]["content"]


# ────────────────────────── /xp clear ──────────────────────────

@pytest.mark.asyncio
async def test_xp_clear_resets_member():
    cog, guild, member, admin = build()
    stats_db.xp_add_text(1, member.id, 999, 1000)
    interaction = FakeInteraction(admin, guild)

    await XPCog.xp_command.callback(cog, interaction, Choice("clear"), member, None)

    assert stats_db.xp_get_member(1, member.id) is None
    assert "обнулён" in interaction.all_messages()[0]["content"]


@pytest.mark.asyncio
async def test_xp_clear_disabled_module():
    cog, guild, member, admin = build(enabled=False)
    interaction = FakeInteraction(admin, guild)

    await XPCog.xp_command.callback(cog, interaction, Choice("clear"), member, None)

    assert "отключена" in interaction.response.messages[0]["content"]


# ────────────────────────── /leaders ──────────────────────────

@pytest.mark.asyncio
async def test_leaders_shows_ranked_members():
    cog, guild, member, admin = build()
    stats_db.xp_add_text(1, member.id, 500, 1000)
    stats_db.xp_add_text(1, admin.id, 200, 1000)
    interaction = FakeInteraction(member, guild)

    await XPCog.leaders_command.callback(cog, interaction)

    embed = interaction.followup.messages[0]["embed"]
    assert "#1." in embed.description
    assert "#2." in embed.description
    assert "Опыт: 500" in embed.description
    assert "Опыт: 200" in embed.description


@pytest.mark.asyncio
async def test_leaders_disabled_module():
    cog, guild, member, admin = build(enabled=False)
    interaction = FakeInteraction(member, guild)

    await XPCog.leaders_command.callback(cog, interaction)

    assert "отключена" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_leaders_empty_leaderboard():
    cog, guild, member, admin = build()
    interaction = FakeInteraction(member, guild)

    await XPCog.leaders_command.callback(cog, interaction)

    assert "никто не заработал" in interaction.followup.messages[0]["content"]


@pytest.mark.asyncio
async def test_leaders_footer_shows_page_and_total():
    cog, guild, member, admin = build()
    stats_db.xp_add_text(1, member.id, 500, 1000)
    stats_db.xp_add_text(1, admin.id, 200, 1000)
    interaction = FakeInteraction(member, guild)

    await XPCog.leaders_command.callback(cog, interaction)

    embed = interaction.followup.messages[0]["embed"]
    assert "Страница 1 из 1" in embed.footer.text
    assert "Всего участников: 2" in embed.footer.text
