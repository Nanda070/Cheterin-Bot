"""Тесты устойчивости планировщика «Ежедневной рубрики»: цикл не умирает от исключений."""

import pytest

import daily_topic_core
from daily_topic import DailyTopicCog
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(daily_topic_core, "CONFIG_FILE", str(tmp_path / "daily_topic_config.json"))


def build():
    channel = FakeChannel(500, name="topics")
    guild = FakeGuild(channels=[channel])
    bot = FakeBot(guild)
    cog = DailyTopicCog.__new__(DailyTopicCog)  # без __init__, чтобы не стартовать реальный loop
    cog.bot = bot
    return cog, channel


@pytest.mark.asyncio
async def test_loop_body_survives_get_settings_exception(monkeypatch):
    cog, _ = build()
    monkeypatch.setattr(daily_topic_core, "get_settings", lambda: (_ for _ in ()).throw(OSError("boom")))
    # Не должно поднять исключение — иначе tasks.loop остановился бы навсегда.
    await DailyTopicCog.daily_topic_loop.coro(cog)


@pytest.mark.asyncio
async def test_loop_body_survives_should_post_now_exception(monkeypatch):
    cog, _ = build()
    daily_topic_core.update_settings(enabled=True, channel_id="500", post_times=["00:00"])
    monkeypatch.setattr(daily_topic_core, "should_post_now", lambda: (_ for _ in ()).throw(RuntimeError("race")))
    await DailyTopicCog.daily_topic_loop.coro(cog)


@pytest.mark.asyncio
async def test_loop_posts_when_time_reached(monkeypatch):
    cog, channel = build()
    daily_topic_core.update_settings(enabled=True, channel_id="500", post_times=["00:00"])
    daily_topic_core.add_topic("Какой ваш любимый фильм?")
    monkeypatch.setattr(daily_topic_core, "should_post_now", lambda: True)

    await DailyTopicCog.daily_topic_loop.coro(cog)

    assert len(channel.send_calls) == 1
    assert "Какой ваш любимый фильм?" in channel.send_calls[0]["content"]
    assert daily_topic_core.already_posted_today() is True


def test_save_config_is_atomic(tmp_path, monkeypatch):
    monkeypatch.setattr(daily_topic_core, "CONFIG_FILE", str(tmp_path / "cfg.json"))
    daily_topic_core.save_config({"enabled": True})
    import os
    assert not os.path.exists(str(tmp_path / "cfg.json") + ".tmp")  # tmp-файл заменён атомарно
    assert daily_topic_core.load_config() == {"enabled": True}


def test_load_config_survives_oserror(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(daily_topic_core, "CONFIG_FILE", str(cfg))

    real_open = open

    def broken_open(*args, **kwargs):
        raise OSError("locked by another process")

    monkeypatch.setattr("builtins.open", broken_open)
    try:
        assert daily_topic_core.load_config() == {}
    finally:
        monkeypatch.setattr("builtins.open", real_open)
