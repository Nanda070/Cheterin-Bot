"""Тесты кога «Антирейд»: выключен по умолчанию, детект всплеска, действия."""

from datetime import datetime, timedelta, timezone

import pytest

import antiraid_core
import lockdown_core
import moderation_log
from antiraid import AntiRaidCog
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setattr(antiraid_core, "CONFIG_FILE", str(tmp_path / "antiraid_config.json"))
    monkeypatch.setattr(antiraid_core, "_cache", None, raising=False)
    monkeypatch.setattr(antiraid_core, "_cache_mtime", None, raising=False)
    monkeypatch.setattr(lockdown_core, "BACKUP_FILE", str(tmp_path / "antispam_backup.json"))
    monkeypatch.setattr(moderation_log, "LOG_FILE", str(tmp_path / "moderation_log.json"))


def fresh_member(member_id, joined_at, guild=None):
    member = FakeMember(member_id, name=f"raider{member_id}")
    member.created_at = joined_at - timedelta(minutes=5)  # свежий аккаунт
    member.joined_at = joined_at
    member.guild = guild
    return member


def build(**settings_extra):
    antiraid_core.save_config({"enabled": True, **settings_extra})
    channel = FakeChannel(500, name="general")
    guild = FakeGuild(members=[], channels=[channel])
    bot = FakeBot(guild)
    cog = AntiRaidCog(bot)
    return cog, guild, channel, bot


# ────────────────────────── Выключен по умолчанию ──────────────────────────

@pytest.mark.asyncio
async def test_disabled_by_default_does_nothing():
    channel = FakeChannel(500)
    guild = FakeGuild(members=[], channels=[channel])
    bot = FakeBot(guild)
    cog = AntiRaidCog(bot)  # antiraid_core.save_config НЕ вызывался — чистый дефолт

    for i in range(20):
        await cog.on_member_join(fresh_member(i, antiraid_core.utcnow()))

    assert bot.sent_logs == []
    assert channel.edit_calls == []


@pytest.mark.asyncio
async def test_explicitly_disabled_ignores_burst():
    cog, guild, channel, bot = build(enabled=False, join_threshold=3)

    for i in range(10):
        await cog.on_member_join(fresh_member(i, antiraid_core.utcnow()))

    assert bot.sent_logs == []


# ────────────────────────── Срабатывание ──────────────────────────

@pytest.mark.asyncio
async def test_triggers_lockdown_on_burst():
    cog, guild, channel, bot = build(join_threshold=3, join_window_sec=10)
    now = antiraid_core.utcnow()

    await cog.on_member_join(fresh_member(1, now, guild))
    await cog.on_member_join(fresh_member(2, now, guild))
    await cog.on_member_join(fresh_member(3, now, guild))

    assert len(bot.sent_logs) == 1
    assert "Антирейд" in bot.sent_logs[0].title
    is_active, _ = lockdown_core.antispam_status()
    assert is_active is True


@pytest.mark.asyncio
async def test_below_threshold_does_not_trigger():
    cog, guild, channel, bot = build(join_threshold=5)
    now = antiraid_core.utcnow()

    for i in range(4):
        await cog.on_member_join(fresh_member(i, now, guild))

    assert bot.sent_logs == []


@pytest.mark.asyncio
async def test_old_accounts_are_not_counted():
    cog, guild, channel, bot = build(join_threshold=3, min_account_age_hours=24)
    now = antiraid_core.utcnow()

    for i in range(5):
        member = FakeMember(i, name=f"old{i}")
        member.created_at = now - timedelta(days=365)  # старый аккаунт
        member.joined_at = now
        member.guild = guild
        await cog.on_member_join(member)

    assert bot.sent_logs == []


@pytest.mark.asyncio
async def test_slowmode_applied_when_configured():
    cog, guild, channel, bot = build(join_threshold=2, action_slowmode_sec=60, action_lockdown=False)
    now = antiraid_core.utcnow()

    await cog.on_member_join(fresh_member(1, now, guild))
    await cog.on_member_join(fresh_member(2, now, guild))

    assert channel.slowmode_delay == 60


@pytest.mark.asyncio
async def test_lockdown_disabled_skips_activation():
    cog, guild, channel, bot = build(join_threshold=2, action_lockdown=False)
    now = antiraid_core.utcnow()

    await cog.on_member_join(fresh_member(1, now, guild))
    await cog.on_member_join(fresh_member(2, now, guild))

    is_active, _ = lockdown_core.antispam_status()
    assert is_active is False
    assert len(bot.sent_logs) == 1  # лог всё равно пишется


@pytest.mark.asyncio
async def test_cooldown_prevents_immediate_retrigger():
    cog, guild, channel, bot = build(join_threshold=2, cooldown_minutes=30)
    now = antiraid_core.utcnow()

    await cog.on_member_join(fresh_member(1, now, guild))
    await cog.on_member_join(fresh_member(2, now, guild))
    assert len(bot.sent_logs) == 1

    await cog.on_member_join(fresh_member(3, now, guild))
    await cog.on_member_join(fresh_member(4, now, guild))
    assert len(bot.sent_logs) == 1  # кулдаун ещё не истёк — второго срабатывания нет


@pytest.mark.asyncio
async def test_window_expiry_resets_burst_count():
    cog, guild, channel, bot = build(join_threshold=3, join_window_sec=5)
    now = antiraid_core.utcnow()

    await cog.on_member_join(fresh_member(1, now, guild))
    await cog.on_member_join(fresh_member(2, now + timedelta(seconds=10), guild))  # вне окна — счётчик сброшен
    await cog.on_member_join(fresh_member(3, now + timedelta(seconds=11), guild))

    assert bot.sent_logs == []  # только 2 входа реально попали в одно окно
