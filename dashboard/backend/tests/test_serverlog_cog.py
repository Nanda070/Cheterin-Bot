"""Тесты кога «Логирование»: стиль эмбедов (description+footer+thumbnail),
форматирование длительности пребывания и атрибуция «Кто изменил»/«Причина»
через фейковый audit log."""

from datetime import datetime, timedelta, timezone

import discord
import pytest

import embed_style
import serverlog
import settings_db
from serverlog import ServerLog
from dashboard.backend.tests.fakes import (
    FakeAuditLogEntry,
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    FakeRole,
)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def enable(guild_id, *event_types: str, channel_id: int = 500):
    serverlog.save_config(guild_id, {
        "events": {et: {"enabled": True, "channel_id": str(channel_id)} for et in event_types}
    })


def build(*event_types: str, channel_id: int = 500, members=None, roles=None):
    channel = FakeChannel(channel_id, name="logs")
    guild = FakeGuild(members=members or [], roles=roles or [], channels=[channel])
    enable(guild.id, *event_types, channel_id=channel_id)
    bot = FakeBot(guild)
    cog = ServerLog(bot)
    return cog, guild, channel


def last_embed(channel: FakeChannel) -> discord.Embed:
    return channel.send_calls[-1]["embed"]


# ────────────────────────── format_stay_duration ──────────────────────────

@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "0 секунд"),
        (1, "1 секунда"),
        (2, "2 секунды"),
        (5, "5 секунд"),
        (11, "11 секунд"),
        (21, "21 секунда"),
        (59, "59 секунд"),
        (60, "1 минута"),
        (120, "2 минуты"),
        (5 * 60, "5 минут"),
        (3600, "1 час"),
        (2 * 3600, "2 часа"),
        (5 * 3600, "5 часов"),
        (24 * 3600, "1 день"),
        (3 * 24 * 3600, "3 дня"),
        (21 * 24 * 3600, "21 день"),
    ],
)
def test_format_stay_duration(seconds, expected):
    assert serverlog.format_stay_duration(seconds) == expected


def test_format_stay_duration_negative_clamped_to_zero():
    assert serverlog.format_stay_duration(-5) == "0 секунд"


# ────────────────────────── on_member_join ──────────────────────────

@pytest.mark.asyncio
async def test_member_join_embed_style():
    cog, guild, channel = build("member_join")
    member = FakeMember(20, name="newbie", display_name="Newbie")
    member.guild = guild

    await cog.on_member_join(member)

    embed = last_embed(channel)
    assert "Newbie" in embed.description
    assert "присоединился к серверу" in embed.description
    assert embed.footer.text == "ID участника: 20"
    assert embed.thumbnail.url == member.display_avatar.url
    assert embed.color == embed_style.SUCCESS
    field_names = [f.name for f in embed.fields]
    assert "Дата регистрации" in field_names
    assert "Участников" in field_names


# ────────────────────────── on_member_remove ──────────────────────────

@pytest.mark.asyncio
async def test_member_remove_embed_style_with_roles_and_duration():
    cog, guild, channel = build("member_leave")
    role = FakeRole(50, name="Homie")
    member = FakeMember(20, name="leaver", display_name="Leaver", role_ids=[50])
    member.guild = guild
    member.joined_at = datetime.now(timezone.utc) - timedelta(seconds=31)
    member.roles = [guild.default_role, role]

    await cog.on_member_remove(member)

    embed = last_embed(channel)
    assert "покинул сервер" in embed.description
    assert embed.color == embed_style.GOLD
    fields = {f.name: f.value for f in embed.fields}
    assert role.mention in fields["Роли"]
    assert fields["Пробыл на сервере"] == "31 секунда"
    assert embed.footer.text == "ID участника: 20"


# ────────────────────────── roles_change (Mod-Log стиль) ──────────────────────────

@pytest.mark.asyncio
async def test_roles_change_attributes_actor_and_reason():
    cog, guild, channel = build("roles_change")
    role = FakeRole(60, name="NoName")
    moderator = FakeMember(10, name="Cheterin")
    before = FakeMember(20, name="member", display_name="Member")
    after = FakeMember(20, name="member", display_name="Member")
    after.roles = [before.roles[0], role]
    after.guild = guild
    guild.audit_log_entries.append(
        FakeAuditLogEntry(
            user=moderator, action=discord.AuditLogAction.member_role_update,
            reason="Авто-роль при входе", target=after,
        )
    )

    await cog.on_member_update(before, after)

    embed = last_embed(channel)
    assert "были изменены" in embed.description
    fields = {f.name: f.value for f in embed.fields}
    assert role.mention in fields["Добавлены роли"]
    assert "Cheterin" in fields["Кто изменил"]
    assert fields["Причина"] == "Авто-роль при входе"


@pytest.mark.asyncio
async def test_roles_change_without_matching_audit_entry_omits_actor_fields():
    cog, guild, channel = build("roles_change")
    role = FakeRole(60, name="NoName")
    before = FakeMember(20, name="member", display_name="Member")
    after = FakeMember(20, name="member", display_name="Member")
    after.roles = [before.roles[0], role]
    after.guild = guild
    # audit_log_entries пуст — запись не найдена

    await cog.on_member_update(before, after)

    embed = last_embed(channel)
    field_names = [f.name for f in embed.fields]
    assert "Кто изменил" not in field_names
    assert "Причина" not in field_names


@pytest.mark.asyncio
async def test_roles_change_ignores_stale_audit_entry():
    cog, guild, channel = build("roles_change")
    role = FakeRole(60, name="NoName")
    moderator = FakeMember(10, name="Cheterin")
    before = FakeMember(20, name="member", display_name="Member")
    after = FakeMember(20, name="member", display_name="Member")
    after.roles = [before.roles[0], role]
    after.guild = guild
    stale = datetime.now(timezone.utc) - timedelta(seconds=serverlog.AUDIT_LOOKUP_WINDOW_SECONDS + 5)
    guild.audit_log_entries.append(
        FakeAuditLogEntry(
            user=moderator, action=discord.AuditLogAction.member_role_update,
            reason="Слишком старое", target=after, created_at=stale,
        )
    )

    await cog.on_member_update(before, after)

    embed = last_embed(channel)
    assert "Кто изменил" not in [f.name for f in embed.fields]


# ────────────────────────── Войс ──────────────────────────

@pytest.mark.asyncio
async def test_voice_join():
    cog, guild, channel = build("voice_join")
    voice_channel = FakeChannel(700, name="voice")
    member = FakeMember(20, name="talker")
    member.guild = guild
    before = type("VS", (), {"channel": None})()
    after = type("VS", (), {"channel": voice_channel})()

    await cog.on_voice_state_update(member, before, after)

    embed = last_embed(channel)
    assert "зашёл в голосовой канал" in embed.description
    assert embed.color == embed_style.TEAL


@pytest.mark.asyncio
async def test_voice_leave_without_admin_disconnect():
    cog, guild, channel = build("voice_leave")
    voice_channel = FakeChannel(700, name="voice")
    member = FakeMember(20, name="talker")
    member.guild = guild
    before = type("VS", (), {"channel": voice_channel})()
    after = type("VS", (), {"channel": None})()

    await cog.on_voice_state_update(member, before, after)

    embed = last_embed(channel)
    assert "покинул голосовой канал" in embed.description


@pytest.mark.asyncio
async def test_voice_leave_attributed_to_admin_disconnect():
    cog, guild, channel = build("voice_disconnect_admin")
    voice_channel = FakeChannel(700, name="voice")
    moderator = FakeMember(10, name="Cheterin")
    member = FakeMember(20, name="talker")
    member.guild = guild
    guild.audit_log_entries.append(
        FakeAuditLogEntry(user=moderator, action=discord.AuditLogAction.member_disconnect)
    )
    before = type("VS", (), {"channel": voice_channel})()
    after = type("VS", (), {"channel": None})()

    await cog.on_voice_state_update(member, before, after)

    embed = last_embed(channel)
    assert "отключён от голосового канала" in embed.description
    fields = {f.name: f.value for f in embed.fields}
    assert "Cheterin" in fields["Кем"]


@pytest.mark.asyncio
async def test_voice_move_attributed_to_admin():
    cog, guild, channel = build("voice_move_admin")
    from_channel = FakeChannel(700, name="voice-a")
    to_channel = FakeChannel(701, name="voice-b")
    moderator = FakeMember(10, name="Cheterin")
    member = FakeMember(20, name="talker")
    member.guild = guild
    guild.audit_log_entries.append(
        FakeAuditLogEntry(user=moderator, action=discord.AuditLogAction.member_move, channel=to_channel)
    )
    before = type("VS", (), {"channel": from_channel})()
    after = type("VS", (), {"channel": to_channel})()

    await cog.on_voice_state_update(member, before, after)

    embed = last_embed(channel)
    assert "перемещён администратором" in embed.description
    fields = {f.name: f.value for f in embed.fields}
    assert "Cheterin" in fields["Кем"]
