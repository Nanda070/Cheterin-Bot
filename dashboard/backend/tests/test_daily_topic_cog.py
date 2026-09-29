"""Тесты устойчивости планировщика «Ежедневной рубрики»: цикл не умирает от исключений."""

import pytest

import bot.modules.community.daily_topic_core as daily_topic_core
import bot.core.settings_db as settings_db
from bot.modules.community.daily_topic import DailyTopicCog
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build():
    channel = FakeChannel(500, name="topics")
    guild = FakeGuild(channels=[channel])
    bot = FakeBot(guild)
    cog = DailyTopicCog.__new__(DailyTopicCog)  # без __init__, чтобы не стартовать реальный loop
    cog.bot = bot
    return cog, guild, channel


@pytest.mark.asyncio
async def test_loop_body_survives_get_settings_exception(monkeypatch):
    cog, _, _ = build()
    monkeypatch.setattr(daily_topic_core, "get_settings", lambda guild_id: (_ for _ in ()).throw(OSError("boom")))
    # Не должно поднять исключение — иначе tasks.loop остановился бы навсегда.
    await DailyTopicCog.daily_topic_loop.coro(cog)


@pytest.mark.asyncio
async def test_loop_body_survives_should_post_now_exception(monkeypatch):
    cog, guild, _ = build()
    daily_topic_core.update_settings(guild.id, enabled=True, channel_id="500", post_times=["00:00"])
    monkeypatch.setattr(
        daily_topic_core, "should_post_now", lambda guild_id: (_ for _ in ()).throw(RuntimeError("race")),
    )
    await DailyTopicCog.daily_topic_loop.coro(cog)


@pytest.mark.asyncio
async def test_loop_posts_when_time_reached(monkeypatch):
    cog, guild, channel = build()
    daily_topic_core.update_settings(guild.id, enabled=True, channel_id="500", post_times=["00:00"])
    daily_topic_core.add_topic(guild.id, "Какой ваш любимый фильм?")
    monkeypatch.setattr(daily_topic_core, "should_post_now", lambda guild_id: True)

    await DailyTopicCog.daily_topic_loop.coro(cog)

    assert len(channel.send_calls) == 1
    assert "Какой ваш любимый фильм?" in channel.send_calls[0]["content"]
    assert daily_topic_core.already_posted_today(guild.id) is True
