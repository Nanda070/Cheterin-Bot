"""Тесты кога приветствий: канал/тумблеры/тексты берутся строго из настроек
сервера события (Фаза 2.4). Проверяем, что действия на одном сервере не
подтягивают настройки другого."""

import pytest

import bot.config as bot_config
import bot.core.settings_db as settings_db
from bot.modules.community.welcome import Welcome
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build_cog(guilds):
    bot = FakeBot(guilds[0], guilds=guilds)

    def get_channel(channel_id):
        for g in guilds:
            found = g.get_channel(channel_id)
            if found is not None:
                return found
        return None

    bot.get_channel = get_channel
    cog = Welcome(bot)
    return cog, bot


def make_joining_member(guild, member_id=777):
    member = FakeMember(member_id, name="newbie")
    member.guild = guild
    return member


@pytest.mark.asyncio
async def test_welcome_posts_to_event_guild_channel_with_its_name():
    channel = FakeChannel(500, name="welcome")
    guild = FakeGuild(channels=[channel], guild_id=100, name="Первый сервер")
    bot_config.save_config(100, {"WELCOME_CHANNEL_ID": "500"})
    cog, _ = build_cog([guild])

    await cog.on_member_join(make_joining_member(guild))

    assert len(channel.send_calls) == 1
    assert "Первый сервер" in channel.send_calls[0]["content"]


@pytest.mark.asyncio
async def test_dm_title_uses_event_guild_name():
    channel = FakeChannel(500, name="welcome")
    guild = FakeGuild(channels=[channel], guild_id=100, name="Второй сервер")
    bot_config.save_config(100, {"WELCOME_CHANNEL_ID": "500"})
    cog, _ = build_cog([guild])
    member = make_joining_member(guild)

    await cog.on_member_join(member)

    assert member.send_calls, "приветственная ЛС должна отправляться при WELCOME_DM_ENABLED по умолчанию"
    embed = member.send_calls[-1]["embed"]
    assert embed.title == "Добро пожаловать на Второй сервер"


@pytest.mark.asyncio
async def test_welcome_channel_toggle_off_suppresses_public_message():
    channel = FakeChannel(500, name="welcome")
    guild = FakeGuild(channels=[channel], guild_id=100, name="Сервер")
    bot_config.save_config(100, {"WELCOME_CHANNEL_ID": "500", "WELCOME_CHANNEL_ENABLED": False})
    cog, _ = build_cog([guild])

    await cog.on_member_join(make_joining_member(guild))

    assert channel.send_calls == []


@pytest.mark.asyncio
async def test_dm_toggle_off_suppresses_dm():
    channel = FakeChannel(500, name="welcome")
    guild = FakeGuild(channels=[channel], guild_id=100, name="Сервер")
    bot_config.save_config(100, {"WELCOME_CHANNEL_ID": "500", "WELCOME_DM_ENABLED": False})
    cog, _ = build_cog([guild])
    member = make_joining_member(guild)

    await cog.on_member_join(member)

    assert member.send_calls == []


@pytest.mark.asyncio
async def test_per_guild_isolation_of_welcome_channel():
    ch1 = FakeChannel(500, name="welcome-1")
    ch2 = FakeChannel(600, name="welcome-2")
    g1 = FakeGuild(channels=[ch1], guild_id=100, name="G1")
    g2 = FakeGuild(channels=[ch2], guild_id=200, name="G2")
    bot_config.save_config(100, {"WELCOME_CHANNEL_ID": "500"})
    bot_config.save_config(200, {"WELCOME_CHANNEL_ID": "600"})
    cog, _ = build_cog([g1, g2])

    await cog.on_member_join(make_joining_member(g2))

    assert ch1.send_calls == []
    assert len(ch2.send_calls) == 1
    assert "G2" in ch2.send_calls[0]["content"]
