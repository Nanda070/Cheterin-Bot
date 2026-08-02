"""Тесты кога «Развлечения»: русская рулетка (исходы, таймаут, кулдаун) и эмодзи-рулетка."""

from datetime import timedelta

import pytest

import economy_core
import economy_db
import fun_core
import settings_db
from fun import FunCog
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember

GUILD_ID = 1


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    monkeypatch.setenv("ECONOMY_DB_PATH", str(tmp_path / "economy.db"))
    economy_db.init()


class FakeResponse:
    def __init__(self):
        self.messages = []

    async def send_message(self, content=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "ephemeral": ephemeral})


class FakeInteraction:
    def __init__(self, user, guild):
        self.user = user
        self.guild = guild
        self.guild_id = guild.id
        self.response = FakeResponse()


def build(enabled=True, timeout_minutes=1, cooldown_sec=0):
    player = FakeMember(20, name="player")
    guild = FakeGuild(members=[player])
    fun_core.save_config(guild.id, {
        "enabled": enabled,
        "roulette_timeout_minutes": timeout_minutes,
        "roulette_cooldown_sec": cooldown_sec,
    })
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
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: False)
    cog, player, guild = build()
    interaction = FakeInteraction(player, guild)

    await FunCog.russian_roulette.callback(cog, interaction)

    message = interaction.response.messages[0]["content"]
    assert "щёлк" in message
    assert player.action_calls == []  # таймаут не выдавался


@pytest.mark.asyncio
async def test_roulette_death_applies_configured_timeout(monkeypatch):
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: True)
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
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: True)
    cog, player, guild = build(timeout_minutes=0)
    interaction = FakeInteraction(player, guild)

    await FunCog.russian_roulette.callback(cog, interaction)

    assert player.action_calls == []
    assert "минутой молчания" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_roulette_death_survives_timeout_failure(monkeypatch):
    import discord

    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: True)
    cog, player, guild = build(timeout_minutes=5)
    player.action_raises = discord.HTTPException.__new__(discord.HTTPException)
    interaction = FakeInteraction(player, guild)

    await FunCog.russian_roulette.callback(cog, interaction)

    assert "неуязвим" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_roulette_cooldown(monkeypatch):
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: False)
    cog, player, guild = build(cooldown_sec=60)
    first = FakeInteraction(player, guild)
    second = FakeInteraction(player, guild)

    await FunCog.russian_roulette.callback(cog, first)
    await FunCog.russian_roulette.callback(cog, second)

    assert second.response.messages[0]["ephemeral"] is True
    assert "Барабан ещё крутится" in second.response.messages[0]["content"]


# ────────────────────────── Авто-Эмодзи ──────────────────────────

class FakeMsg:
    def __init__(self, author, guild, channel_id=500):
        self.id = 1
        self.author = author
        self.guild = guild
        self.channel = type("C", (), {"id": channel_id})()
        self.reactions_added = []
        self.reactions_removed = []

    async def add_reaction(self, emoji):
        self.reactions_added.append(str(emoji))

    async def remove_reaction(self, emoji, member):
        self.reactions_removed.append(str(emoji))


def _auto_emoji_config(guild_id=1, **overrides):
    data = {
        "enabled": True,
        "auto_emoji_enabled": True,
        "auto_emoji_chance_percent": 100,
        "auto_emoji_min_interval_sec": 0,
        "auto_emoji_remove_after_sec": 0,
    }
    data.update(overrides)
    fun_core.save_config(guild_id, data)  # 1 — совпадает с дефолтным FakeGuild.id ниже


@pytest.mark.asyncio
async def test_auto_emoji_reacts_to_human_message():
    _auto_emoji_config()
    player = FakeMember(20, name="player")
    guild = FakeGuild(members=[player])
    guild.emojis = ["<:pepe:1>"]
    cog = FunCog(FakeBot(guild))
    message = FakeMsg(player, guild)

    await cog.on_message(message)

    assert message.reactions_added == ["<:pepe:1>"]


@pytest.mark.asyncio
async def test_auto_emoji_ignores_bots_and_dms():
    _auto_emoji_config()
    bot_author = FakeMember(21, name="botty", bot=True)
    human = FakeMember(20, name="human")
    guild = FakeGuild(members=[human])
    cog = FunCog(FakeBot(guild))

    bot_message = FakeMsg(bot_author, guild)
    await cog.on_message(bot_message)
    assert bot_message.reactions_added == []

    dm_message = FakeMsg(human, None)
    await cog.on_message(dm_message)
    assert dm_message.reactions_added == []


@pytest.mark.asyncio
async def test_auto_emoji_respects_module_and_feature_toggles():
    player = FakeMember(20, name="player")
    guild = FakeGuild(members=[player])
    cog = FunCog(FakeBot(guild))

    _auto_emoji_config(enabled=False)
    message = FakeMsg(player, guild)
    await cog.on_message(message)
    assert message.reactions_added == []

    _auto_emoji_config(auto_emoji_enabled=False)
    message = FakeMsg(player, guild)
    await cog.on_message(message)
    assert message.reactions_added == []


@pytest.mark.asyncio
async def test_auto_emoji_zero_chance_never_reacts():
    _auto_emoji_config(auto_emoji_chance_percent=0)
    player = FakeMember(20, name="player")
    guild = FakeGuild(members=[player])
    cog = FunCog(FakeBot(guild))

    for _ in range(20):
        message = FakeMsg(player, guild)
        await cog.on_message(message)
        assert message.reactions_added == []


@pytest.mark.asyncio
async def test_auto_emoji_channel_interval_limits_frequency():
    _auto_emoji_config(auto_emoji_min_interval_sec=3600)
    player = FakeMember(20, name="player")
    guild = FakeGuild(members=[player])
    cog = FunCog(FakeBot(guild))

    first = FakeMsg(player, guild, channel_id=500)
    second = FakeMsg(player, guild, channel_id=500)
    other_channel = FakeMsg(player, guild, channel_id=501)

    await cog.on_message(first)
    await cog.on_message(second)
    await cog.on_message(other_channel)

    assert len(first.reactions_added) == 1
    assert second.reactions_added == []  # интервал канала ещё не прошёл
    assert len(other_channel.reactions_added) == 1  # другой канал — свой интервал


@pytest.mark.asyncio
async def test_auto_emoji_removes_reaction_after_delay(monkeypatch):
    _auto_emoji_config(auto_emoji_remove_after_sec=1)

    slept_for = []

    async def instant_sleep(delay):
        slept_for.append(delay)

    import fun as fun_module
    monkeypatch.setattr(fun_module.asyncio, "sleep", instant_sleep)

    player = FakeMember(20, name="player")
    guild = FakeGuild(members=[player])
    cog = FunCog(FakeBot(guild))
    message = FakeMsg(player, guild)

    await cog.on_message(message)
    assert len(message.reactions_added) == 1

    # Логика отложенного снятия — прямым вызовом (create_task в on_message её лишь планирует).
    await cog._remove_auto_emoji(message, message.reactions_added[0], 1)

    assert slept_for and slept_for[-1] == 1
    assert message.reactions_removed == message.reactions_added


# ────────────────────────── Барабан без проворота ──────────────────────────

def test_spin_trigger_guaranteed_on_last_chamber():
    # После 5 осечек остаётся одна камора — выстрел гарантирован
    assert all(fun_core.spin_trigger(5) for _ in range(50))


def test_spin_trigger_chance_grows(monkeypatch):
    seen = []
    monkeypatch.setattr(fun_core.random, "randrange", lambda n: seen.append(n) or 1)
    fun_core.spin_trigger(0)
    fun_core.spin_trigger(3)
    assert seen == [6, 3]


@pytest.mark.asyncio
async def test_roulette_empty_cylinder_survives_all_six(monkeypatch):
    cog, player, guild = build()
    monkeypatch.setattr(fun_core, "roll_empty_cylinder", lambda: True)
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: False)
    for _ in range(5):
        await FunCog.russian_roulette.callback(cog, FakeInteraction(player, guild))
    assert cog._roulette_clicks[(guild.id, player.id)] == 5
    assert cog._roulette_empty[(guild.id, player.id)] is True

    sixth = FakeInteraction(player, guild)
    await FunCog.russian_roulette.callback(cog, sixth)
    assert cog._roulette_clicks[(guild.id, player.id)] == 0
    assert (guild.id, player.id) not in cog._roulette_empty
    assert "пустой" in sixth.response.messages[0]["content"].lower() or "empty" in sixth.response.messages[0]["content"].lower() or "6/6" in sixth.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_roulette_click_counter_grows_and_resets(monkeypatch):
    cog, player, guild = build()
    key = (guild.id, player.id)
    monkeypatch.setattr(fun_core, "roll_empty_cylinder", lambda: False)
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: False)
    await FunCog.russian_roulette.callback(cog, FakeInteraction(player, guild))
    await FunCog.russian_roulette.callback(cog, FakeInteraction(player, guild))
    assert cog._roulette_clicks[key] == 2

    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: True)
    await FunCog.russian_roulette.callback(cog, FakeInteraction(player, guild))
    assert cog._roulette_clicks[key] == 0
    assert key not in cog._roulette_empty


@pytest.mark.asyncio
async def test_roulette_state_is_isolated_per_guild(monkeypatch):
    monkeypatch.setattr(fun_core, "roll_empty_cylinder", lambda: False)
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: False)
    cog, player, guild = build()
    other = FakeGuild(members=[player], guild_id=999)
    fun_core.save_config(other.id, {"enabled": True, "roulette_timeout_minutes": 0, "roulette_cooldown_sec": 0})

    await FunCog.russian_roulette.callback(cog, FakeInteraction(player, guild))
    assert cog._roulette_clicks[(guild.id, player.id)] == 1
    assert (other.id, player.id) not in cog._roulette_clicks

    await FunCog.russian_roulette.callback(cog, FakeInteraction(player, other))
    assert cog._roulette_clicks[(guild.id, player.id)] == 1
    assert cog._roulette_clicks[(other.id, player.id)] == 1


@pytest.mark.asyncio
async def test_roulette_shows_chamber_number(monkeypatch):
    cog, player, guild = build()
    monkeypatch.setattr(fun_core, "roll_empty_cylinder", lambda: False)
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: False)
    interaction = FakeInteraction(player, guild)
    await FunCog.russian_roulette.callback(cog, interaction)
    assert "1/6" in interaction.response.messages[0]["content"]


# ────────────────────────── Ставки монет ──────────────────────────

def enable_economy(guild_id, max_bet=1000):
    economy_core.save_config(guild_id, {"enabled": True, "roulette_max_bet": max_bet})


@pytest.mark.asyncio
async def test_roulette_bet_requires_economy(monkeypatch):
    cog, player, guild = build()
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: False)
    interaction = FakeInteraction(player, guild)
    await FunCog.russian_roulette.callback(cog, interaction, ставка=10)
    assert "Экономика" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_roulette_bet_survive_doubles(monkeypatch):
    cog, player, guild = build()
    enable_economy(guild.id)
    economy_db.add(GUILD_ID, player.id, 100, "seed")
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: False)

    interaction = FakeInteraction(player, guild)
    await FunCog.russian_roulette.callback(cog, interaction, ставка=40)

    assert economy_db.get_balance(GUILD_ID, player.id) == 140  # -40 ставка, +80 выигрыш
    assert "Ставка сыграла" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_roulette_bet_death_burns(monkeypatch):
    cog, player, guild = build(timeout_minutes=0)
    enable_economy(guild.id)
    economy_db.add(GUILD_ID, player.id, 100, "seed")
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: True)

    interaction = FakeInteraction(player, guild)
    await FunCog.russian_roulette.callback(cog, interaction, ставка=40)

    assert economy_db.get_balance(GUILD_ID, player.id) == 60
    assert "сгорела" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_roulette_bet_insufficient_funds(monkeypatch):
    cog, player, guild = build(cooldown_sec=30)
    enable_economy(guild.id)
    economy_db.add(GUILD_ID, player.id, 5, "seed")
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: False)

    interaction = FakeInteraction(player, guild)
    await FunCog.russian_roulette.callback(cog, interaction, ставка=50)

    assert "Недостаточно" in interaction.response.messages[0]["content"]
    assert economy_db.get_balance(GUILD_ID, player.id) == 5
    # ставка отклонена ДО кулдауна — можно сразу сыграть снова
    retry = FakeInteraction(player, guild)
    await FunCog.russian_roulette.callback(cog, retry, ставка=5)
    assert "Ставка сыграла" in retry.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_roulette_bet_over_max(monkeypatch):
    cog, player, guild = build()
    enable_economy(guild.id, max_bet=100)
    economy_db.add(GUILD_ID, player.id, 5000, "seed")
    monkeypatch.setattr(fun_core, "spin_trigger", lambda clicks=0, empty_cylinder=False: False)

    interaction = FakeInteraction(player, guild)
    await FunCog.russian_roulette.callback(cog, interaction, ставка=500)
    assert "Максимальная ставка" in interaction.response.messages[0]["content"]
