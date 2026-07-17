"""Тесты кога «Развлечения»: русская рулетка (исходы, таймаут, кулдаун) и эмодзи-рулетка."""

from datetime import timedelta

import pytest

import fun_core
from fun import FunCog
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(fun_core, "CONFIG_FILE", str(tmp_path / "fun_config.json"))
    monkeypatch.setattr(fun_core, "_cache", None, raising=False)
    monkeypatch.setattr(fun_core, "_cache_mtime", None, raising=False)


class FakeResponse:
    def __init__(self):
        self.messages = []

    async def send_message(self, content=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "ephemeral": ephemeral})


class FakeInteraction:
    def __init__(self, user, guild):
        self.user = user
        self.guild = guild
        self.response = FakeResponse()


def build(enabled=True, timeout_minutes=1, cooldown_sec=0):
    fun_core.save_config({
        "enabled": enabled,
        "roulette_timeout_minutes": timeout_minutes,
        "roulette_cooldown_sec": cooldown_sec,
    })
    player = FakeMember(20, name="player")
    guild = FakeGuild(members=[player])
    bot = FakeBot(guild)
    cog = FunCog(bot)
    return cog, player, guild


@pytest.mark.asyncio
async def test_roulette_disabled_module():
    cog, player, guild = build(enabled=False)
    interaction = FakeInteraction(player, guild)

    await FunCog.russian_roulette.callback(cog, interaction)

    assert interaction.response.messages[0]["ephemeral"] is True
    assert "отключён" in interaction.response.messages[0]["content"]
    assert player.action_calls == []


@pytest.mark.asyncio
async def test_roulette_survive(monkeypatch):
    monkeypatch.setattr(fun_core, "spin_trigger", lambda: False)
    cog, player, guild = build()
    interaction = FakeInteraction(player, guild)

    await FunCog.russian_roulette.callback(cog, interaction)

    message = interaction.response.messages[0]["content"]
    assert "щёлк" in message
    assert player.action_calls == []  # таймаут не выдавался


@pytest.mark.asyncio
async def test_roulette_death_applies_configured_timeout(monkeypatch):
    monkeypatch.setattr(fun_core, "spin_trigger", lambda: True)
    cog, player, guild = build(timeout_minutes=7)
    interaction = FakeInteraction(player, guild)

    await FunCog.russian_roulette.callback(cog, interaction)

    assert len(player.action_calls) == 1
    action, kwargs = player.action_calls[0]
    assert action == "timeout"
    assert kwargs["duration"] == timedelta(minutes=7)

    message = interaction.response.messages[0]["content"]
    assert "7 мин" in message


@pytest.mark.asyncio
async def test_roulette_death_without_punishment(monkeypatch):
    monkeypatch.setattr(fun_core, "spin_trigger", lambda: True)
    cog, player, guild = build(timeout_minutes=0)
    interaction = FakeInteraction(player, guild)

    await FunCog.russian_roulette.callback(cog, interaction)

    assert player.action_calls == []
    assert "минутой молчания" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_roulette_death_survives_timeout_failure(monkeypatch):
    import discord

    monkeypatch.setattr(fun_core, "spin_trigger", lambda: True)
    cog, player, guild = build(timeout_minutes=5)
    player.action_raises = discord.HTTPException.__new__(discord.HTTPException)
    interaction = FakeInteraction(player, guild)

    await FunCog.russian_roulette.callback(cog, interaction)

    assert "неуязвим" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_roulette_cooldown(monkeypatch):
    monkeypatch.setattr(fun_core, "spin_trigger", lambda: False)
    cog, player, guild = build(cooldown_sec=60)
    first = FakeInteraction(player, guild)
    second = FakeInteraction(player, guild)

    await FunCog.russian_roulette.callback(cog, first)
    await FunCog.russian_roulette.callback(cog, second)

    assert second.response.messages[0]["ephemeral"] is True
    assert "Барабан ещё крутится" in second.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_emoji_roulette_uses_guild_emojis():
    cog, player, guild = build()
    guild.emojis = ["<:pepe:123>"]
    interaction = FakeInteraction(player, guild)

    await FunCog.emoji_roulette.callback(cog, interaction)

    assert "<:pepe:123>" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_emoji_roulette_fallback_pool():
    cog, player, guild = build()
    guild.emojis = []
    interaction = FakeInteraction(player, guild)

    await FunCog.emoji_roulette.callback(cog, interaction)

    message = interaction.response.messages[0]["content"]
    assert any(e in message for e in fun_core.FALLBACK_EMOJIS)


@pytest.mark.asyncio
async def test_emoji_roulette_disabled_module():
    cog, player, guild = build(enabled=False)
    interaction = FakeInteraction(player, guild)

    await FunCog.emoji_roulette.callback(cog, interaction)

    assert interaction.response.messages[0]["ephemeral"] is True
