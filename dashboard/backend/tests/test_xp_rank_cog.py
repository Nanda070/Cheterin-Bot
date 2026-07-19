"""Тесты /ранг: подтягивание экипированной косметики (рамка/титул) из магазина."""

import pytest

import economy_db
import stats_db
import xp_card
import xp_core
from xp import XPCog
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("STATS_DB_PATH", str(tmp_path / "stats.db"))
    stats_db.init()
    monkeypatch.setattr(xp_core, "CONFIG_FILE", str(tmp_path / "xp_config.json"))
    monkeypatch.setattr(xp_core, "_cache", None, raising=False)
    monkeypatch.setattr(xp_core, "_cache_mtime", None, raising=False)
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
    def __init__(self, user, guild):
        self.user = user
        self.guild = guild
        self.response = FakeResponse()
        self.followup = FakeFollowup()


def build():
    xp_core.save_config({"enabled": True})
    member = FakeMember(20, name="player", display_name="Player")
    guild = FakeGuild(members=[member])
    bot = FakeBot(guild)
    cog = XPCog(bot)
    return cog, guild, member


@pytest.mark.asyncio
async def test_rank_command_without_cosmetics_passes_none(monkeypatch):
    cog, guild, member = build()
    stats_db.xp_add_text(member.id, 100, 1000)
    captured = {}

    def fake_render(*args, **kwargs):
        captured.update(kwargs)
        return b"PNG"

    monkeypatch.setattr(xp_card, "render_rank_card", fake_render)
    interaction = FakeInteraction(member, guild)

    await XPCog.rank_command.callback(cog, interaction, None)

    assert captured["frame_color"] is None
    assert captured["title_text"] is None
    assert interaction.followup.messages[0]["file"] is not None


@pytest.mark.asyncio
async def test_rank_command_passes_equipped_frame_and_title(monkeypatch):
    cog, guild, member = build()
    stats_db.xp_add_text(member.id, 100, 1000)
    economy_db.grant_cosmetic(member.id, "frame1", "frame_color", "#FF00AA", "Розовая рамка")
    economy_db.set_equipped(member.id, "frame_color", "frame1")
    economy_db.grant_cosmetic(member.id, "title1", "title", "Легенда", "Титул «Легенда»")
    economy_db.set_equipped(member.id, "title", "title1")

    captured = {}

    def fake_render(*args, **kwargs):
        captured.update(kwargs)
        return b"PNG"

    monkeypatch.setattr(xp_card, "render_rank_card", fake_render)
    interaction = FakeInteraction(member, guild)

    await XPCog.rank_command.callback(cog, interaction, None)

    assert captured["frame_color"] == "#FF00AA"
    assert captured["title_text"] == "Легенда"


@pytest.mark.asyncio
async def test_rank_command_ignores_unequipped_owned_cosmetics(monkeypatch):
    cog, guild, member = build()
    stats_db.xp_add_text(member.id, 100, 1000)
    economy_db.grant_cosmetic(member.id, "frame1", "frame_color", "#FF00AA", "Розовая рамка")  # куплено, но не надето

    captured = {}
    monkeypatch.setattr(xp_card, "render_rank_card", lambda *a, **k: captured.update(k) or b"PNG")
    interaction = FakeInteraction(member, guild)

    await XPCog.rank_command.callback(cog, interaction, None)

    assert captured["frame_color"] is None
