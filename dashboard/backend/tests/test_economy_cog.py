"""Тесты кога «Экономика»: /баланс /перевести /монеты-топ /магазин — через .callback()."""

import pytest

import economy_core
import economy_db
import settings_db
from economy import EconomyCog
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, FakeRole

GUILD_ID = 1


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("ECONOMY_DB_PATH", str(tmp_path / "economy.db"))
    economy_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


class FakeResponse:
    def __init__(self):
        self.messages = []

    async def send_message(self, content=None, embed=None, view=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "embed": embed, "view": view, "ephemeral": ephemeral})


class FakeInteraction:
    guild_id = 1
    def __init__(self, user, guild):
        self.user = user
        self.guild = guild
        self.response = FakeResponse()


def build(enabled=True, **extra):
    player = FakeMember(20, name="player", display_name="Player")
    friend = FakeMember(21, name="friend", display_name="Friend")
    guild = FakeGuild(members=[player, friend])
    economy_core.save_config(guild.id, {"enabled": enabled, **extra})
    bot = FakeBot(guild)
    cog = EconomyCog(bot)
    return cog, guild, player, friend


# ────────────────────────── /daily ──────────────────────────

@pytest.mark.asyncio
async def test_daily_disabled_module():
    cog, guild, player, friend = build(enabled=False)
    interaction = FakeInteraction(player, guild)
    await EconomyCog.daily_command.callback(cog, interaction)
    assert "«Экономика» отключён" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_daily_bonus_disabled_flag():
    cog, guild, player, friend = build(daily_bonus_enabled=False)
    interaction = FakeInteraction(player, guild)
    await EconomyCog.daily_command.callback(cog, interaction)
    assert "Ежедневный бонус отключён" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_daily_first_claim(monkeypatch):
    cog, guild, player, friend = build()
    monkeypatch.setattr(economy_core, "today_msk_date", lambda *_a, **_k: "2026-01-10")
    interaction = FakeInteraction(player, guild)

    await EconomyCog.daily_command.callback(cog, interaction)

    assert economy_db.get_balance(GUILD_ID, player.id) == 50
    content = interaction.response.messages[0]["content"]
    assert "50" in content
    assert "Стрик: **1** день" in content


@pytest.mark.asyncio
async def test_daily_already_claimed_today(monkeypatch):
    cog, guild, player, friend = build()
    monkeypatch.setattr(economy_core, "today_msk_date", lambda *_a, **_k: "2026-01-10")
    await EconomyCog.daily_command.callback(cog, FakeInteraction(player, guild))

    interaction = FakeInteraction(player, guild)
    await EconomyCog.daily_command.callback(cog, interaction)

    assert "уже получен" in interaction.response.messages[0]["content"]
    assert economy_db.get_balance(GUILD_ID, player.id) == 50  # второй раз не начислено


@pytest.mark.asyncio
async def test_daily_streak_grows_next_day(monkeypatch):
    cog, guild, player, friend = build()
    monkeypatch.setattr(economy_core, "today_msk_date", lambda *_a, **_k: "2026-01-10")
    await EconomyCog.daily_command.callback(cog, FakeInteraction(player, guild))

    monkeypatch.setattr(economy_core, "today_msk_date", lambda *_a, **_k: "2026-01-11")
    interaction = FakeInteraction(player, guild)
    await EconomyCog.daily_command.callback(cog, interaction)

    assert economy_db.get_balance(GUILD_ID, player.id) == 50 + 75
    assert "Стрик: **2** дня" in interaction.response.messages[0]["content"]


# ────────────────────────── /баланс ──────────────────────────

@pytest.mark.asyncio
async def test_balance_disabled_module():
    cog, guild, player, friend = build(enabled=False)
    interaction = FakeInteraction(player, guild)
    await EconomyCog.balance_command.callback(cog, interaction, None)
    assert "отключён" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_balance_shows_amount_and_rank():
    cog, guild, player, friend = build()
    economy_db.add(GUILD_ID, player.id, 250, "seed")
    interaction = FakeInteraction(player, guild)

    await EconomyCog.balance_command.callback(cog, interaction, None)

    embed = interaction.response.messages[0]["embed"]
    assert "250" in embed.description
    assert "#1" in embed.description


# ────────────────────────── /выдать-баланс ──────────────────────────

@pytest.mark.asyncio
async def test_grant_balance_disabled_module():
    cog, guild, player, friend = build(enabled=False)
    interaction = FakeInteraction(player, guild)
    await EconomyCog.grant_balance_command.callback(cog, interaction, friend, 100)
    assert "отключён" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_grant_balance_rejects_bots():
    cog, guild, player, friend = build()
    bot_member = FakeMember(30, name="botty", bot=True)
    interaction = FakeInteraction(player, guild)
    await EconomyCog.grant_balance_command.callback(cog, interaction, bot_member, 100)
    assert "У ботов нет кошелька" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_grant_balance_adds_from_zero():
    cog, guild, player, friend = build()
    interaction = FakeInteraction(player, guild)

    await EconomyCog.grant_balance_command.callback(cog, interaction, friend, 500)

    assert economy_db.get_balance(GUILD_ID, friend.id) == 500
    assert "500" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_grant_balance_negative_deducts():
    cog, guild, player, friend = build()
    economy_db.add(GUILD_ID, friend.id, 300, "seed")
    interaction = FakeInteraction(player, guild)

    await EconomyCog.grant_balance_command.callback(cog, interaction, friend, -100)

    assert economy_db.get_balance(GUILD_ID, friend.id) == 200


@pytest.mark.asyncio
async def test_grant_balance_negative_does_not_go_below_zero():
    cog, guild, player, friend = build()
    economy_db.add(GUILD_ID, friend.id, 50, "seed")
    interaction = FakeInteraction(player, guild)

    await EconomyCog.grant_balance_command.callback(cog, interaction, friend, -500)

    assert economy_db.get_balance(GUILD_ID, friend.id) == 0


# ────────────────────────── /перевести ──────────────────────────

@pytest.mark.asyncio
async def test_transfer_moves_coins():
    cog, guild, player, friend = build()
    economy_db.add(GUILD_ID, player.id, 100, "seed")
    interaction = FakeInteraction(player, guild)

    await EconomyCog.transfer_command.callback(cog, interaction, friend, 40)

    assert economy_db.get_balance(GUILD_ID, player.id) == 60
    assert economy_db.get_balance(GUILD_ID, friend.id) == 40


@pytest.mark.asyncio
async def test_transfer_takes_fee():
    cog, guild, player, friend = build(transfer_fee_percent=10)
    economy_db.add(GUILD_ID, player.id, 110, "seed")
    interaction = FakeInteraction(player, guild)

    await EconomyCog.transfer_command.callback(cog, interaction, friend, 100)

    assert economy_db.get_balance(GUILD_ID, player.id) == 0  # 100 + 10 комиссии
    assert economy_db.get_balance(GUILD_ID, friend.id) == 100
    assert "Комиссия" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_transfer_rejects_self_bots_disabled():
    cog, guild, player, friend = build(transfer_enabled=False)
    interaction = FakeInteraction(player, guild)
    await EconomyCog.transfer_command.callback(cog, interaction, friend, 10)
    assert "отключены" in interaction.response.messages[0]["content"]

    cog, guild, player, friend = build()
    economy_db.add(GUILD_ID, player.id, 100, "seed")
    interaction = FakeInteraction(player, guild)
    await EconomyCog.transfer_command.callback(cog, interaction, player, 10)
    assert "Себе" in interaction.response.messages[0]["content"]

    bot_member = FakeMember(30, name="botty", bot=True)
    interaction = FakeInteraction(player, guild)
    await EconomyCog.transfer_command.callback(cog, interaction, bot_member, 10)
    assert "Ботам" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_transfer_insufficient():
    cog, guild, player, friend = build()
    economy_db.add(GUILD_ID, player.id, 10, "seed")
    interaction = FakeInteraction(player, guild)
    await EconomyCog.transfer_command.callback(cog, interaction, friend, 50)
    assert "Недостаточно" in interaction.response.messages[0]["content"]
    assert economy_db.get_balance(GUILD_ID, friend.id) == 0


# ────────────────────────── /монеты-топ ──────────────────────────

@pytest.mark.asyncio
async def test_top_lists_members():
    cog, guild, player, friend = build()
    economy_db.add(GUILD_ID, player.id, 300, "seed")
    economy_db.add(GUILD_ID, friend.id, 100, "seed")
    interaction = FakeInteraction(player, guild)

    await EconomyCog.top_command.callback(cog, interaction)

    embed = interaction.response.messages[0]["embed"]
    assert "🥇" in embed.description
    assert "Player" in embed.description


# ────────────────────────── /магазин ──────────────────────────

def shop_config(price=100):
    return {
        "enabled": True,
        "shop_items": [{"id": "vip", "role_id": 777, "price": price, "name": "VIP"}],
    }


@pytest.mark.asyncio
async def test_shop_empty():
    cog, guild, player, friend = build()
    interaction = FakeInteraction(player, guild)
    await EconomyCog.shop_command.callback(cog, interaction)
    assert "пуст" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_shop_lists_items_with_buttons():
    cog, guild, player, friend = build()
    economy_core.save_config(guild.id, shop_config())
    guild.roles.append(FakeRole(777, name="VIP"))
    interaction = FakeInteraction(player, guild)

    await EconomyCog.shop_command.callback(cog, interaction)

    msg = interaction.response.messages[0]
    assert "VIP" in msg["embed"].description
    assert msg["view"] is not None


@pytest.mark.asyncio
async def test_purchase_success_assigns_role_and_spends():
    cog, guild, player, friend = build()
    economy_core.save_config(guild.id, shop_config(price=100))
    guild.roles.append(FakeRole(777, name="VIP"))
    economy_db.add(GUILD_ID, player.id, 150, "seed")
    interaction = FakeInteraction(player, guild)

    await cog.handle_purchase(interaction, "vip")

    assert economy_db.get_balance(GUILD_ID, player.id) == 50
    assert any(call[0] == "add_roles" for call in player.action_calls)
    assert "Куплено" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_purchase_insufficient_funds():
    cog, guild, player, friend = build()
    economy_core.save_config(guild.id, shop_config(price=100))
    guild.roles.append(FakeRole(777, name="VIP"))
    economy_db.add(GUILD_ID, player.id, 10, "seed")
    interaction = FakeInteraction(player, guild)

    await cog.handle_purchase(interaction, "vip")

    assert "Не хватает" in interaction.response.messages[0]["content"]
    assert economy_db.get_balance(GUILD_ID, player.id) == 10
    assert player.action_calls == []


@pytest.mark.asyncio
async def test_purchase_refunds_on_role_failure():
    cog, guild, player, friend = build()
    economy_core.save_config(guild.id, shop_config(price=100))
    guild.roles.append(FakeRole(777, name="VIP"))
    economy_db.add(GUILD_ID, player.id, 150, "seed")
    import discord

    player.action_raises = discord.HTTPException.__new__(discord.HTTPException)
    interaction = FakeInteraction(player, guild)

    await cog.handle_purchase(interaction, "vip")

    assert economy_db.get_balance(GUILD_ID, player.id) == 150  # возврат
    assert "возвращены" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_purchase_already_owned():
    cog, guild, player, friend = build()
    economy_core.save_config(guild.id, shop_config())
    vip = FakeRole(777, name="VIP")
    guild.roles.append(vip)
    player.roles.append(vip)
    economy_db.add(GUILD_ID, player.id, 500, "seed")
    interaction = FakeInteraction(player, guild)

    await cog.handle_purchase(interaction, "vip")

    assert "уже есть" in interaction.response.messages[0]["content"]
    assert economy_db.get_balance(GUILD_ID, player.id) == 500


@pytest.mark.asyncio
async def test_purchase_unknown_item():
    cog, guild, player, friend = build()
    economy_core.save_config(guild.id, shop_config())
    interaction = FakeInteraction(player, guild)
    await cog.handle_purchase(interaction, "nope")
    assert "убрали" in interaction.response.messages[0]["content"]


# ────────────────────────── Магазин: косметика ──────────────────────────

def cosmetics_shop_config():
    return {
        "enabled": True,
        "shop_items": [
            {"id": "frame1", "type": "frame_color", "color_hex": "#FF00AA", "price": 200, "name": "Розовая рамка"},
            {"id": "title1", "type": "title", "title_text": "Легенда", "price": 300, "name": "Титул «Легенда»"},
        ],
    }


@pytest.mark.asyncio
async def test_purchase_frame_color_grants_cosmetic():
    cog, guild, player, friend = build()
    economy_core.save_config(guild.id, cosmetics_shop_config())
    economy_db.add(GUILD_ID, player.id, 200, "seed")
    interaction = FakeInteraction(player, guild)

    await cog.handle_purchase(interaction, "frame1")

    assert economy_db.get_balance(GUILD_ID, player.id) == 0
    assert economy_db.owns_cosmetic(GUILD_ID, player.id, "frame1") is True
    assert "Куплено" in interaction.response.messages[0]["content"]
    assert player.action_calls == []  # косметика не выдаёт ролей


@pytest.mark.asyncio
async def test_purchase_title_grants_cosmetic():
    cog, guild, player, friend = build()
    economy_core.save_config(guild.id, cosmetics_shop_config())
    economy_db.add(GUILD_ID, player.id, 300, "seed")
    interaction = FakeInteraction(player, guild)

    await cog.handle_purchase(interaction, "title1")

    assert economy_db.owns_cosmetic(GUILD_ID, player.id, "title1") is True


@pytest.mark.asyncio
async def test_purchase_cosmetic_already_owned():
    cog, guild, player, friend = build()
    economy_core.save_config(guild.id, cosmetics_shop_config())
    economy_db.add(GUILD_ID, player.id, 1000, "seed")
    interaction = FakeInteraction(player, guild)

    await cog.handle_purchase(interaction, "frame1")
    balance_after_first = economy_db.get_balance(GUILD_ID, player.id)
    await cog.handle_purchase(interaction, "frame1")

    assert economy_db.get_balance(GUILD_ID, player.id) == balance_after_first  # второй раз не списано
    assert "уже есть" in interaction.response.messages[-1]["content"]


@pytest.mark.asyncio
async def test_purchase_cosmetic_insufficient_funds():
    cog, guild, player, friend = build()
    economy_core.save_config(guild.id, cosmetics_shop_config())
    economy_db.add(GUILD_ID, player.id, 10, "seed")
    interaction = FakeInteraction(player, guild)

    await cog.handle_purchase(interaction, "frame1")

    assert "Не хватает" in interaction.response.messages[0]["content"]
    assert economy_db.owns_cosmetic(GUILD_ID, player.id, "frame1") is False


# ────────────────────────── /косметика ──────────────────────────

@pytest.mark.asyncio
async def test_cosmetics_command_empty():
    cog, guild, player, friend = build()
    interaction = FakeInteraction(player, guild)
    await EconomyCog.cosmetics_command.callback(cog, interaction)
    assert "нет купленной косметики" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_cosmetics_command_lists_owned():
    cog, guild, player, friend = build()
    economy_db.grant_cosmetic(GUILD_ID, player.id, "frame1", "frame_color", "#FF00AA", "Розовая рамка")
    interaction = FakeInteraction(player, guild)

    await EconomyCog.cosmetics_command.callback(cog, interaction)

    assert interaction.response.messages[0]["view"] is not None


@pytest.mark.asyncio
async def test_handle_equip_sets_and_clears():
    cog, guild, player, friend = build()
    economy_db.grant_cosmetic(GUILD_ID, player.id, "frame1", "frame_color", "#FF00AA", "Розовая рамка")

    interaction = FakeInteraction(player, guild)
    await cog.handle_equip(interaction, "frame_color", "frame1")
    assert economy_db.get_equipped(GUILD_ID, player.id, "frame_color")["item_id"] == "frame1"
    assert "применён" in interaction.response.messages[0]["content"]

    interaction2 = FakeInteraction(player, guild)
    await cog.handle_equip(interaction2, "frame_color", None)
    assert economy_db.get_equipped(GUILD_ID, player.id, "frame_color") is None
    assert "снят" in interaction2.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_handle_equip_rejects_unowned_item():
    cog, guild, player, friend = build()
    interaction = FakeInteraction(player, guild)

    await cog.handle_equip(interaction, "title", "not-owned")

    assert "не владеете" in interaction.response.messages[0]["content"]
    assert economy_db.get_equipped(GUILD_ID, player.id, "title") is None
