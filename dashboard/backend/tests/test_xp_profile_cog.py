"""Тесты /профиль: GIF по умолчанию, fallback на PNG при огромном файле."""

import pytest

import economy_db
import settings_db
import stats_db
import xp_core
from xp import XPCog, _PROFILE_GIF_MAX_BYTES
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember

GUILD_ID = 1


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("STATS_DB_PATH", str(tmp_path / "stats.db"))
    stats_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    monkeypatch.setenv("ECONOMY_DB_PATH", str(tmp_path / "economy.db"))
    economy_db.init()


class FakeResponse:
    def __init__(self):
        self.deferred = False

    async def defer(self, **kwargs):
        self.deferred = True


class FakeFollowup:
    def __init__(self):
        self.messages = []

    async def send(self, content=None, file=None, **kwargs):
        self.messages.append({"content": content, "file": file})


class FakeInteraction:
    guild_id = 1

    def __init__(self, user, guild):
        self.user = user
        self.guild = guild
        self.response = FakeResponse()
        self.followup = FakeFollowup()


def build():
    member = FakeMember(20, name="player", display_name="Player")
    guild = FakeGuild(members=[member])
    xp_core.save_config(guild.id, {"enabled": True})
    bot = FakeBot(guild)
    cog = XPCog(bot)
    return cog, guild, member


@pytest.mark.asyncio
async def test_profile_command_sends_gif(monkeypatch):
    import profile_card

    cog, guild, member = build()
    stats_db.xp_add_text(1, member.id, 100, 1000)

    monkeypatch.setattr(profile_card, "render_profile_card_gif", lambda **k: b"GIF89a" + b"\x00" * 20)
    interaction = FakeInteraction(member, guild)

    await XPCog.profile_command.callback(cog, interaction, None)

    file = interaction.followup.messages[0]["file"]
    assert file is not None
    assert file.filename == "profile.gif"


@pytest.mark.asyncio
async def test_profile_command_falls_back_to_png_when_gif_huge(monkeypatch):
    import profile_card

    cog, guild, member = build()
    stats_db.xp_add_text(1, member.id, 100, 1000)

    monkeypatch.setattr(
        profile_card,
        "render_profile_card_gif",
        lambda **k: b"G" * (_PROFILE_GIF_MAX_BYTES + 1),
    )
    monkeypatch.setattr(profile_card, "render_profile_card", lambda **k: b"\x89PNG" + b"\x00" * 8)
    interaction = FakeInteraction(member, guild)

    await XPCog.profile_command.callback(cog, interaction, None)

    file = interaction.followup.messages[0]["file"]
    assert file.filename == "profile.png"


@pytest.mark.asyncio
async def test_profile_passes_economy_when_enabled(monkeypatch):
    import profile_card
    import economy_core

    cog, guild, member = build()
    stats_db.xp_add_text(1, member.id, 100, 1000)
    economy_core.save_config(GUILD_ID, {"enabled": True, "daily_bonus_enabled": True})
    economy_db.set_balance(GUILD_ID, member.id, 250, "test")
    economy_db.set_daily_bonus(GUILD_ID, member.id, 4, "2026-08-01")

    captured = {}

    def fake_gif(**kwargs):
        captured.update(kwargs)
        return b"GIF89a" + b"\x00" * 8

    monkeypatch.setattr(profile_card, "render_profile_card_gif", fake_gif)
    interaction = FakeInteraction(member, guild)

    await XPCog.profile_command.callback(cog, interaction, None)

    assert captured["balance"] == 250
    assert captured["streak"] == 4
    assert captured["messages"] == 1
