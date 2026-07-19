"""Тесты кога слэш-команд модерации: /ban /kick /unban /clear.

Команды вызываются напрямую через .callback(cog, interaction, ...), минуя реальный
Discord-диспетчер — тот же паттерн, что и в test_fun_cog.py/test_bunker_cog.py.
"""

import time

import discord
import pytest

import ban_db
import moderation_commands_core
from moderation_commands import ModerationCommandsCog
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("BAN_DB_PATH", str(tmp_path / "moderation_bans.db"))
    ban_db.init()
    monkeypatch.setattr("moderation_log.LOG_FILE", str(tmp_path / "moderation_log.json"))


class FakeResponse:
    def __init__(self):
        self.messages = []
        self.deferred = False

    async def send_message(self, content=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "ephemeral": ephemeral})

    async def defer(self, ephemeral=False, **kwargs):
        self.deferred = True


class FakeFollowup:
    def __init__(self):
        self.messages = []

    async def send(self, content=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "ephemeral": ephemeral})


class FakeInteraction:
    def __init__(self, user, guild, channel=None):
        self.user = user
        self.guild = guild
        self.channel = channel
        self.response = FakeResponse()
        self.followup = FakeFollowup()

    def all_messages(self):
        return self.response.messages + self.followup.messages


def build(guild_id=1):
    moderator = FakeMember(10, name="mod")
    channel = FakeChannel(500, name="general")
    guild = FakeGuild(members=[moderator], channels=[channel], guild_id=guild_id)
    bot = FakeBot(guild)
    cog = ModerationCommandsCog(bot)
    return bot, guild, channel, moderator, cog


# ────────────────────────── /ban ──────────────────────────

@pytest.mark.asyncio
async def test_ban_permanent_default():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.ban_command.callback(cog, interaction, target, reason="спам", time_str=None)

    assert len(guild.ban_calls) == 1
    assert guild.ban_calls[0]["user"] is target
    assert "спам" in guild.ban_calls[0]["reason"]
    assert "mod" in guild.ban_calls[0]["reason"]
    assert "10" in guild.ban_calls[0]["reason"]
    assert target.id not in [m.id for m in guild.members]  # удалён из участников

    text = interaction.all_messages()[0]["content"]
    assert "навсегда" in text
    assert ban_db.get_by_user(guild.id, target.id) is None  # не запланирован разбан


@pytest.mark.asyncio
async def test_ban_with_duration_schedules_unban():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.ban_command.callback(cog, interaction, target, reason=None, time_str="10m")

    row = ban_db.get_by_user(guild.id, target.id)
    assert row is not None
    assert row["unban_at_ts"] > int(time.time())

    text = interaction.all_messages()[0]["content"]
    assert "10 мин." in text
    assert moderation_commands_core.DEFAULT_REASON in text

    task = cog._unban_timers.get(row["id"])
    if task:
        task.cancel()


@pytest.mark.asyncio
async def test_ban_invalid_duration_format():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.ban_command.callback(cog, interaction, target, reason=None, time_str="soon")

    assert interaction.response.deferred is False
    assert guild.ban_calls == []
    assert "Неверный формат" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_ban_requires_guild_context():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    interaction = FakeInteraction(moderator, guild=None, channel=channel)

    await ModerationCommandsCog.ban_command.callback(cog, interaction, target)

    assert "только на сервере" in interaction.response.messages[0]["content"]


@pytest.mark.asyncio
async def test_ban_forbidden_reports_ephemeral_error():
    bot, guild, channel, moderator, cog = build()
    guild.ban_raises = discord.Forbidden.__new__(discord.Forbidden)
    target = FakeMember(20, name="troll")
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.ban_command.callback(cog, interaction, target)

    assert "Недостаточно прав" in interaction.followup.messages[0]["content"]


# ────────────────────────── /kick ──────────────────────────

@pytest.mark.asyncio
async def test_kick_happy_path():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.kick_command.callback(cog, interaction, target, reason="токсичность")

    assert len(target.action_calls) == 1
    action, kwargs = target.action_calls[0]
    assert action == "kick"
    assert "токсичность" in kwargs["reason"]
    assert "Кикнут" not in interaction.all_messages()[0]["content"]  # sanity: сообщение своё, не заглушка
    assert "кикнут" in interaction.all_messages()[0]["content"]


@pytest.mark.asyncio
async def test_kick_forbidden():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    target.action_raises = discord.Forbidden.__new__(discord.Forbidden)
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.kick_command.callback(cog, interaction, target)

    assert "Недостаточно прав" in interaction.followup.messages[0]["content"]


# ────────────────────────── /mute ──────────────────────────

@pytest.mark.asyncio
async def test_mute_happy_path():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.mute_command.callback(cog, interaction, target, "2h", reason="флуд")

    assert len(target.action_calls) == 1
    action, kwargs = target.action_calls[0]
    assert action == "timeout"
    assert "флуд" in kwargs["reason"]
    assert target.is_timed_out() is True
    assert "2 ч." in interaction.all_messages()[0]["content"]


@pytest.mark.asyncio
async def test_mute_invalid_duration_format():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.mute_command.callback(cog, interaction, target, "какое-то время")

    assert "Неверный формат" in interaction.response.messages[0]["content"]
    assert target.action_calls == []


@pytest.mark.asyncio
async def test_mute_rejects_over_28_days():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.mute_command.callback(cog, interaction, target, "29d")

    assert "28 дней" in interaction.response.messages[0]["content"]
    assert target.action_calls == []


@pytest.mark.asyncio
async def test_mute_forbidden():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    target.action_raises = discord.Forbidden.__new__(discord.Forbidden)
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.mute_command.callback(cog, interaction, target, "1h")

    assert "Недостаточно прав" in interaction.followup.messages[0]["content"]


# ────────────────────────── /unmute ──────────────────────────

@pytest.mark.asyncio
async def test_unmute_happy_path():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    await target.timeout(object(), reason="test")
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.unmute_command.callback(cog, interaction, target, reason="исправился")

    action, kwargs = target.action_calls[-1]
    assert action == "timeout"
    assert kwargs["duration"] is None
    assert "исправился" in kwargs["reason"]


@pytest.mark.asyncio
async def test_unmute_rejects_when_not_muted():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.unmute_command.callback(cog, interaction, target)

    assert "не под таймаутом" in interaction.response.messages[0]["content"]
    assert target.action_calls == []


# ────────────────────────── /unban ──────────────────────────

@pytest.mark.asyncio
async def test_unban_happy_path():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    await guild.ban(target, reason="test")
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.unban_command.callback(cog, interaction, "20", reason="исправился")

    assert len(guild.unban_calls) == 1
    assert guild.unban_calls[0]["user_id"] == 20
    assert "исправился" in interaction.all_messages()[0]["content"]


@pytest.mark.asyncio
async def test_unban_cancels_scheduled_unban():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    await guild.ban(target)
    row_id = ban_db.add(guild.id, target.id, int(time.time()) + 9999)
    cog._schedule_unban(row_id, guild.id, target.id, int(time.time()) + 9999)
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.unban_command.callback(cog, interaction, "20")

    assert ban_db.get_by_user(guild.id, 20) is None
    assert row_id not in cog._unban_timers


@pytest.mark.asyncio
async def test_unban_not_banned():
    bot, guild, channel, moderator, cog = build()
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.unban_command.callback(cog, interaction, "999")

    assert "не забанен" in interaction.followup.messages[0]["content"]


@pytest.mark.asyncio
async def test_unban_rejects_non_numeric_id():
    bot, guild, channel, moderator, cog = build()
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.unban_command.callback(cog, interaction, "not-a-number")

    assert "числом" in interaction.response.messages[0]["content"]
    assert guild.unban_calls == []


# ────────────────────────── /clear ──────────────────────────

@pytest.mark.asyncio
async def test_clear_deletes_messages():
    bot, guild, channel, moderator, cog = build()
    from dashboard.backend.tests.fakes import FakeMessage
    for i in range(5):
        msg = FakeMessage(2000 + i, content=f"msg{i}")
        channel._messages[msg.id] = msg
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.clear_command.callback(cog, interaction, 3)

    assert channel.purge_calls == [3]
    assert "Удалено сообщений: **3**" in interaction.followup.messages[0]["content"]


@pytest.mark.asyncio
async def test_clear_forbidden():
    bot, guild, channel, moderator, cog = build()
    channel.purge_raises = discord.Forbidden.__new__(discord.Forbidden)
    interaction = FakeInteraction(moderator, guild, channel)

    await ModerationCommandsCog.clear_command.callback(cog, interaction, 10)

    assert "Недостаточно прав" in interaction.followup.messages[0]["content"]


@pytest.mark.asyncio
async def test_clear_unsupported_channel_type():
    bot, guild, channel, moderator, cog = build()
    plain_channel = type("PlainChannel", (), {})()
    interaction = FakeInteraction(moderator, guild, plain_channel)

    await ModerationCommandsCog.clear_command.callback(cog, interaction, 10)

    assert "недоступна" in interaction.response.messages[0]["content"]


# ────────────────────────── Восстановление таймеров ──────────────────────────

@pytest.mark.asyncio
async def test_on_ready_recovers_scheduled_unbans():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    await guild.ban(target)
    row_id = ban_db.add(guild.id, target.id, int(time.time()) + 9999)

    await cog.on_ready()

    assert row_id in cog._unban_timers
    cog._unban_timers[row_id].cancel()


@pytest.mark.asyncio
async def test_run_unban_timer_unbans_and_removes_row():
    bot, guild, channel, moderator, cog = build()
    target = FakeMember(20, name="troll")
    await guild.ban(target)
    row_id = ban_db.add(guild.id, target.id, int(time.time()) - 1)  # уже истёк

    await cog._run_unban_timer(row_id, guild.id, target.id, int(time.time()) - 1)

    assert len(guild.unban_calls) == 1
    assert ban_db.get_by_user(guild.id, target.id) is None
