import json

import pytest

import lockdown_core
from dashboard.backend.tests.fakes import FakeGuild, FakeRole


@pytest.fixture(autouse=True)
def isolated_backup(tmp_path, monkeypatch):
    monkeypatch.setattr(lockdown_core, "BACKUP_FILE", str(tmp_path / "antispam_backup.json"))


def _role(role_id, *, mention_everyone=False, mentionable=False, position=5, **kw):
    role = FakeRole(role_id, position=position, **kw)
    role.permissions.mention_everyone = mention_everyone
    role.mentionable = mentionable
    return role


@pytest.mark.asyncio
async def test_activate_strips_permissions_and_saves_backup():
    noisy = _role(2, mention_everyone=True, mentionable=True)
    quiet = _role(3)
    guild = FakeGuild(roles=[_role(0, default=True), noisy, quiet])

    modified, errors = await lockdown_core.activate_antispam(guild, set(), set())

    assert modified == 1
    assert errors == []
    assert noisy.edit_calls  # got edited
    assert quiet.edit_calls == []
    active, count = lockdown_core.antispam_status(1)
    assert active is True
    assert count == 1


@pytest.mark.asyncio
async def test_activate_respects_exempts():
    exempt = _role(5, mention_everyone=True)
    guild = FakeGuild(roles=[exempt])

    modified, _ = await lockdown_core.activate_antispam(guild, {5}, set())
    assert modified == 0
    assert exempt.edit_calls == []


@pytest.mark.asyncio
async def test_deactivate_restores_from_backup():
    noisy = _role(2, mention_everyone=True, mentionable=True)
    guild = FakeGuild(roles=[noisy])
    await lockdown_core.activate_antispam(guild, set(), set())
    noisy.permissions.mention_everyone = False
    noisy.mentionable = False

    result = await lockdown_core.deactivate_antispam(guild)
    assert result is not None
    restored, errors = result
    assert restored == 1
    assert errors == []
    active, _ = lockdown_core.antispam_status(1)
    assert active is False


@pytest.mark.asyncio
async def test_deactivate_without_backup_returns_none():
    guild = FakeGuild(roles=[])
    assert await lockdown_core.deactivate_antispam(guild) is None


@pytest.mark.asyncio
async def test_activate_collects_errors_and_continues():
    import discord

    class _StubForbidden(discord.Forbidden):
        def __init__(self):
            pass

    broken = _role(6, mention_everyone=True)
    broken.edit_raises = _StubForbidden()
    fine = _role(7, mention_everyone=True)
    guild = FakeGuild(roles=[broken, fine])

    modified, errors = await lockdown_core.activate_antispam(guild, set(), set())
    assert modified == 1
    assert len(errors) == 1
