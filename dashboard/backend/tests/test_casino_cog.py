"""Тесты кога «Казино»: /слоты и /монетка — через .callback(), паттерн test_fun_cog.py."""

import pytest

import bot.modules.games.casino_core as casino_core
import bot.modules.games.casino_db as casino_db
import bot.modules.games.economy_core as economy_core
import bot.modules.games.economy_db as economy_db
import bot.core.settings_db as settings_db
from bot.modules.games.casino import CasinoCog
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember

GUILD_ID = 1


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    monkeypatch.setenv("ECONOMY_DB_PATH", str(tmp_path / "economy.db"))
    economy_db.init()
    monkeypatch.setenv("CASINO_DB_PATH", str(tmp_path / "casino.db"))
    casino_db.init()


class FakeResponse:
    def __init__(self):
        self.messages = []

    async def send_message(self, content=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "ephemeral": ephemeral})


class FakeInteraction:
    guild_id = 1
    def __init__(self, user, guild):
        self.user = user
        self.guild = guild
        self.response = FakeResponse()


class FakeChoice:
    def __init__(self, value):
        self.value = value


def build(casino_enabled=True, economy_enabled=True, **casino_extra):
    player = FakeMember(20, name="player")
    guild = FakeGuild(members=[player])
    casino_core.save_config(guild.id, {"enabled": casino_enabled, **casino_extra})
    economy_core.save_config(guild.id, {"enabled": economy_enabled})
    bot = FakeBot(guild)
    cog = CasinoCog(bot)
    return cog, player, guild


# ────────────────────────── Гейты ──────────────────────────

@pytest.mark.asyncio
async def test_slots_disabled_module():
    cog, player, guild = build(casino_enabled=False)
    interaction = FakeInteraction(player, guild)
    await CasinoCog.slots_command.callback(cog, interaction, 50)
    assert "«Казино» отключён" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_slots_requires_economy():
    cog, player, guild = build(economy_enabled=False)
    interaction = FakeInteraction(player, guild)
    await CasinoCog.slots_command.callback(cog, interaction, 50)
    assert "Экономика" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_coinflip_disabled_module():
    cog, player, guild = build(casino_enabled=False)
    interaction = FakeInteraction(player, guild)
    await CasinoCog.coinflip_command.callback(cog, interaction, 50, FakeChoice("орел"))
    assert "«Казино» отключён" in interaction.response.messages[0]["content"]


# ────────────────────────── /слоты ──────────────────────────

@pytest.mark.asyncio
async def test_slots_bet_below_min_rejected():
    cog, player, guild = build(min_bet=10)
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    interaction = FakeInteraction(player, guild)
    await CasinoCog.slots_command.callback(cog, interaction, 1)
    assert "Минимальная" in interaction.response.messages[0]["content"]
    assert economy_db.get_balance(GUILD_ID, player.id) == 1000  # ставка не списана


@pytest.mark.asyncio
async def test_slots_win_triple_pays_out(monkeypatch):
    cog, player, guild = build(house_edge_percent=0)
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    monkeypatch.setattr(casino_core, "roll_slots", lambda: ("7️⃣", "7️⃣", "7️⃣"))
    interaction = FakeInteraction(player, guild)

    await CasinoCog.slots_command.callback(cog, interaction, 100)

    assert economy_db.get_balance(GUILD_ID, player.id) == 1000 - 100 + 100 * 50  # ставка списана, выигрыш x50
    assert "Джекпот" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_slots_win_pair_smaller_payout(monkeypatch):
    cog, player, guild = build(house_edge_percent=0)
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    monkeypatch.setattr(casino_core, "roll_slots", lambda: ("🍒", "🍒", "🔔"))
    interaction = FakeInteraction(player, guild)

    await CasinoCog.slots_command.callback(cog, interaction, 100)

    assert economy_db.get_balance(GUILD_ID, player.id) == 1000 - 100 + 150  # x1.5
    assert "Совпадение" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_slots_loss_no_match(monkeypatch):
    cog, player, guild = build()
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    monkeypatch.setattr(casino_core, "roll_slots", lambda: ("🍒", "🔔", "⭐"))
    interaction = FakeInteraction(player, guild)

    await CasinoCog.slots_command.callback(cog, interaction, 100)

    assert economy_db.get_balance(GUILD_ID, player.id) == 900
    assert "мимо" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_slots_insufficient_funds():
    cog, player, guild = build()
    economy_db.add(GUILD_ID, player.id, 5, "seed")
    interaction = FakeInteraction(player, guild)
    await CasinoCog.slots_command.callback(cog, interaction, 50)
    assert "Недостаточно" in interaction.response.messages[0]["content"]
    assert economy_db.get_balance(GUILD_ID, player.id) == 5


@pytest.mark.asyncio
async def test_shared_cooldown_blocks_second_bet(monkeypatch):
    cog, player, guild = build(cooldown_sec=30)
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    monkeypatch.setattr(casino_core, "roll_slots", lambda: ("🍒", "🔔", "⭐"))
    monkeypatch.setattr(casino_core, "flip_coin", lambda: "решка")

    await CasinoCog.slots_command.callback(cog, FakeInteraction(player, guild), 50)
    interaction = FakeInteraction(player, guild)
    await CasinoCog.coinflip_command.callback(cog, interaction, 50, FakeChoice("орел"))

    assert "отдыхает" in interaction.response.messages[0]["content"]
    assert economy_db.get_balance(GUILD_ID, player.id) == 950  # вторая ставка не списана


# ────────────────────────── /монетка ──────────────────────────

@pytest.mark.asyncio
async def test_coinflip_win(monkeypatch):
    cog, player, guild = build(house_edge_percent=0)
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    monkeypatch.setattr(casino_core, "flip_coin", lambda: "орел")
    interaction = FakeInteraction(player, guild)

    await CasinoCog.coinflip_command.callback(cog, interaction, 100, FakeChoice("орел"))

    assert economy_db.get_balance(GUILD_ID, player.id) == 1000 - 100 + 200
    assert "угадал" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_coinflip_loss(monkeypatch):
    cog, player, guild = build()
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    monkeypatch.setattr(casino_core, "flip_coin", lambda: "решка")
    interaction = FakeInteraction(player, guild)

    await CasinoCog.coinflip_command.callback(cog, interaction, 100, FakeChoice("орел"))

    assert economy_db.get_balance(GUILD_ID, player.id) == 900
    assert "не угадал" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_coinflip_house_edge_reduces_payout(monkeypatch):
    cog, player, guild = build(house_edge_percent=10)
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    monkeypatch.setattr(casino_core, "flip_coin", lambda: "решка")
    interaction = FakeInteraction(player, guild)

    await CasinoCog.coinflip_command.callback(cog, interaction, 100, FakeChoice("решка"))

    # ставка -100, выигрыш 100*2*0.9=180
    assert economy_db.get_balance(GUILD_ID, player.id) == 1000 - 100 + 180
