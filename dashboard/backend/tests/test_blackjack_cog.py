"""Тесты кога «Блэкджек»: гейты, ставки, натуральный BJ, кнопки Ещё/Стоп/Удвоить."""

import time

import pytest

import blackjack_core as bj
import casino_core
import casino_db
import economy_core
import economy_db
import settings_db
from blackjack import BlackjackCog, BlackjackView
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


class FakeMessage:
    def __init__(self):
        self.embeds = []
        self.edits = []

    async def edit(self, **kwargs):
        self.edits.append(kwargs)


class FakeResponse:
    def __init__(self):
        self.messages = []
        self.edits = []
        self.deferred = False

    async def send_message(self, content=None, embed=None, view=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "embed": embed, "view": view, "ephemeral": ephemeral})

    async def edit_message(self, embed=None, view=None, **kwargs):
        self.edits.append({"embed": embed, "view": view})

    async def defer(self):
        self.deferred = True


class FakeInteraction:
    guild_id = 1
    def __init__(self, user, guild):
        self.user = user
        self.guild = guild
        self.response = FakeResponse()
        self._message = FakeMessage()

    async def original_response(self):
        return self._message


def build(casino_enabled=True, economy_enabled=True, **casino_extra):
    player = FakeMember(20, name="player")
    guild = FakeGuild(members=[player])
    casino_core.save_config(guild.id, {"enabled": casino_enabled, **casino_extra})
    economy_core.save_config(guild.id, {"enabled": economy_enabled})
    bot = FakeBot(guild)
    cog = BlackjackCog(bot)
    bot.cogs["BlackjackCog"] = cog
    return cog, player, guild


def make_game(player_cards, dealer_cards, deck=None, bet=100):
    return bj.BlackjackGame(deck=deck or [], player=list(player_cards), dealer=list(dealer_cards), bet=bet)


# ────────────────────────── Гейты ──────────────────────────

@pytest.mark.asyncio
async def test_disabled_module():
    cog, player, guild = build(casino_enabled=False)
    interaction = FakeInteraction(player, guild)
    await BlackjackCog.blackjack_command.callback(cog, interaction, 50)
    assert "«Казино» отключён" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_requires_economy():
    cog, player, guild = build(economy_enabled=False)
    interaction = FakeInteraction(player, guild)
    await BlackjackCog.blackjack_command.callback(cog, interaction, 50)
    assert "Экономика" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_active_game_blocks_second():
    cog, player, guild = build()
    cog._games[(guild.id, player.id)] = make_game(["10♠", "7♦"], ["9♣", "5♥"])
    interaction = FakeInteraction(player, guild)
    await BlackjackCog.blackjack_command.callback(cog, interaction, 50)
    assert "уже идёт партия" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_active_game_is_isolated_per_guild(monkeypatch):
    cog, player, guild = build()
    other_guild_id = 999
    cog._games[(other_guild_id, player.id)] = make_game(["10♠", "7♦"], ["9♣", "5♥"])
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    monkeypatch.setattr(bj, "new_game", lambda bet: make_game(["10♠", "7♦"], ["9♣", "5♥"], deck=["2♠"], bet=bet))
    interaction = FakeInteraction(player, guild)

    assert not cog.has_active_game(guild.id, player.id)
    assert cog.has_active_game(other_guild_id, player.id)

    await BlackjackCog.blackjack_command.callback(cog, interaction, 100)
    assert isinstance(interaction.response.messages[0]["view"], BlackjackView)
    assert cog.has_active_game(guild.id, player.id)
    assert cog.has_active_game(other_guild_id, player.id)
@pytest.mark.asyncio
async def test_cooldown_blocks_new_game():
    cog, player, guild = build(cooldown_sec=30)
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    cog._cooldowns[(guild.id, player.id)] = time.monotonic() + 30
    interaction = FakeInteraction(player, guild)
    await BlackjackCog.blackjack_command.callback(cog, interaction, 50)
    assert "отдыхает" in interaction.response.messages[0]["content"]
    assert economy_db.get_balance(GUILD_ID, player.id) == 1000


@pytest.mark.asyncio
async def test_cooldown_is_per_guild(monkeypatch):
    cog, player, guild = build(cooldown_sec=30)
    other = FakeGuild(guild_id=99, members=[player])
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    economy_db.add(99, player.id, 1000, "seed")
    economy_core.save_config(99, {"enabled": True})
    casino_core.save_config(99, {"enabled": True, "cooldown_sec": 30, "min_bet": 10, "max_bet": 1000})
    cog._cooldowns[(guild.id, player.id)] = time.monotonic() + 30
    monkeypatch.setattr(
        bj, "new_game",
        lambda bet: make_game(["10♠", "7♦"], ["9♣", "5♥"], deck=["2♠"], bet=bet),
    )

    blocked = FakeInteraction(player, guild)
    await BlackjackCog.blackjack_command.callback(cog, blocked, 50)
    assert "отдыхает" in blocked.response.messages[0]["content"]

    ok = FakeInteraction(player, other)
    ok.guild_id = other.id
    await BlackjackCog.blackjack_command.callback(cog, ok, 50)
    assert isinstance(ok.response.messages[0]["view"], BlackjackView)
    assert economy_db.get_balance(99, player.id) == 950
    assert economy_db.get_balance(GUILD_ID, player.id) == 1000


@pytest.mark.asyncio
async def test_bet_below_min_rejected():
    cog, player, guild = build(min_bet=10)
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    interaction = FakeInteraction(player, guild)
    await BlackjackCog.blackjack_command.callback(cog, interaction, 1)
    assert "Минимальная" in interaction.response.messages[0]["content"]
    assert economy_db.get_balance(GUILD_ID, player.id) == 1000


# ────────────────────────── Старт партии ──────────────────────────

@pytest.mark.asyncio
async def test_game_starts_deducts_bet_and_sends_view(monkeypatch):
    cog, player, guild = build()
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    monkeypatch.setattr(bj, "new_game", lambda bet: make_game(["10♠", "7♦"], ["9♣", "5♥"], deck=["2♠"], bet=bet))
    interaction = FakeInteraction(player, guild)

    await BlackjackCog.blackjack_command.callback(cog, interaction, 100)

    assert economy_db.get_balance(GUILD_ID, player.id) == 900
    msg = interaction.response.messages[0]
    assert msg["embed"] is not None
    assert isinstance(msg["view"], BlackjackView)
    assert cog.has_active_game(guild.id, player.id)


@pytest.mark.asyncio
async def test_natural_blackjack_pays_and_records_stats(monkeypatch):
    cog, player, guild = build(house_edge_percent=0)
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    monkeypatch.setattr(bj, "new_game", lambda bet: make_game(["A♠", "K♦"], ["9♣", "5♥"], deck=["2♠", "3♠"], bet=bet))
    interaction = FakeInteraction(player, guild)

    await BlackjackCog.blackjack_command.callback(cog, interaction, 100)

    # ×2.5: −100 ставка, +250 приз
    assert economy_db.get_balance(GUILD_ID, player.id) == 1150
    assert casino_db.get_stats(guild.id, player.id)["bj_wins"] == 1
    assert not cog.has_active_game(guild.id, player.id)
    assert cog.cooldown_ready_at(guild.id, player.id) > time.monotonic()


# ────────────────────────── Кнопки ──────────────────────────

def start_view_game(cog, player, guild, player_cards, dealer_cards, deck):
    game = make_game(player_cards, dealer_cards, deck=deck)
    cog._games[(guild.id, player.id)] = game
    view = BlackjackView(cog=cog, player=player, guild_id=guild.id)
    return game, view


@pytest.mark.asyncio
async def test_stand_dealer_loses_pays_double():
    cog, player, guild = build(house_edge_percent=0)
    economy_db.add(GUILD_ID, player.id, 900, "seed")  # ставка 100 уже «списана»
    game, view = start_view_game(cog, player, guild, ["10♠", "9♦"], ["10♣", "7♥"], deck=["2♠"])
    interaction = FakeInteraction(player, guild)

    await view.stand_button.callback(interaction)

    # 19 против 17 → WIN ×2
    assert economy_db.get_balance(GUILD_ID, player.id) == 900 + 200
    assert casino_db.get_stats(guild.id, player.id)["bj_wins"] == 1
    assert not cog.has_active_game(guild.id, player.id)
    assert interaction.response.edits[0]["embed"] is not None


@pytest.mark.asyncio
async def test_hit_bust_loses_and_records():
    cog, player, guild = build()
    economy_db.add(GUILD_ID, player.id, 900, "seed")
    game, view = start_view_game(cog, player, guild, ["10♠", "9♦"], ["10♣", "7♥"], deck=["5♣"])
    interaction = FakeInteraction(player, guild)

    await view.hit_button.callback(interaction)

    # 10+9+5=24 — перебор
    assert economy_db.get_balance(GUILD_ID, player.id) == 900
    assert casino_db.get_stats(guild.id, player.id)["bj_losses"] == 1
    assert not cog.has_active_game(guild.id, player.id)


@pytest.mark.asyncio
async def test_hit_without_bust_continues_game():
    cog, player, guild = build()
    economy_db.add(GUILD_ID, player.id, 900, "seed")
    game, view = start_view_game(cog, player, guild, ["5♠", "9♦"], ["10♣", "7♥"], deck=["2♣"])
    interaction = FakeInteraction(player, guild)

    await view.hit_button.callback(interaction)

    assert cog.has_active_game(guild.id, player.id)
    assert game.player == ["5♠", "9♦", "2♣"]
    assert interaction.response.edits[0]["embed"] is not None


@pytest.mark.asyncio
async def test_double_spends_second_bet_and_finishes():
    cog, player, guild = build(house_edge_percent=0)
    economy_db.add(GUILD_ID, player.id, 900, "seed")
    game, view = start_view_game(cog, player, guild, ["5♠", "6♦"], ["10♥", "8♣"], deck=["10♣"])
    interaction = FakeInteraction(player, guild)

    await view.double_button.callback(interaction)

    # 11 + 10♣ = 21 против 18 → WIN; ставка удвоена до 200, приз 400
    assert game.doubled is True
    assert economy_db.get_balance(GUILD_ID, player.id) == 900 - 100 + 400
    assert not cog.has_active_game(guild.id, player.id)


@pytest.mark.asyncio
async def test_double_rejected_without_funds():
    cog, player, guild = build()
    economy_db.add(GUILD_ID, player.id, 50, "seed")  # на вторую ставку 100 не хватает
    game, view = start_view_game(cog, player, guild, ["5♠", "6♦"], ["10♥", "8♣"], deck=["10♣"])
    interaction = FakeInteraction(player, guild)

    await view.double_button.callback(interaction)

    assert "Недостаточно средств" in interaction.response.messages[0]["content"]
    assert cog.has_active_game(guild.id, player.id)  # партия продолжается


@pytest.mark.asyncio
async def test_interaction_check_rejects_other_user():
    cog, player, guild = build()
    stranger = FakeMember(30, name="stranger")
    view = BlackjackView(cog=cog, player=player, guild_id=guild.id)
    interaction = FakeInteraction(stranger, guild)

    allowed = await view.interaction_check(interaction)

    assert allowed is False
    assert "не твоя партия" in interaction.response.messages[0]["content"]
