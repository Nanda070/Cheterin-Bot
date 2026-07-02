import discord
import pytest

import lockdown_core
from dashboard.backend.routes.lockdown import routes as lockdown_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def isolated_backup(tmp_path, monkeypatch):
    monkeypatch.setattr(lockdown_core, "BACKUP_FILE", str(tmp_path / "antispam_backup.json"))


def build(roles=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator], roles=roles or []))
    return bot, make_moderation_app(bot, [lockdown_routes])


@pytest.mark.asyncio
async def test_status_inactive_by_default(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.get("/api/lockdown/status")
    assert resp.status == 200
    assert await resp.json() == {"active": False, "role_count": 0}


@pytest.mark.asyncio
async def test_activate_then_status_then_deactivate(aiohttp_client):
    noisy = FakeRole(2, position=5)
    noisy.permissions.mention_everyone = True
    bot, app = build(roles=[noisy])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/lockdown/activate")
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert body["modified_count"] == 1
    assert len(bot.sent_logs) == 1

    resp = await client.get("/api/lockdown/status")
    assert (await resp.json())["active"] is True

    resp = await client.post("/api/lockdown/deactivate")
    assert resp.status == 200
    assert (await resp.json())["ok"] is True
    assert len(bot.sent_logs) == 2


@pytest.mark.asyncio
async def test_deactivate_without_backup_409(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.post("/api/lockdown/deactivate")
    assert resp.status == 409


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/lockdown/status")
    assert resp.status == 401


class _StubForbidden(discord.Forbidden):
    def __init__(self):
        pass


@pytest.mark.asyncio
async def test_activate_with_partial_errors_logs_error_field(aiohttp_client):
    """Test that partial failures are logged with Ошибки field in embed."""
    role1 = FakeRole(2, position=5)
    role1.permissions.mention_everyone = True
    role2 = FakeRole(3, position=6)
    role2.permissions.mention_everyone = True
    role2.edit_raises = _StubForbidden()

    bot, app = build(roles=[role1, role2])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/lockdown/activate")
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert body["modified_count"] == 1
    assert len(body["errors"]) > 0

    # Verify logged embed contains error field
    assert len(bot.sent_logs) == 1
    embed = bot.sent_logs[0]
    error_field_found = any(f.name == "Ошибки" for f in embed.fields)
    assert error_field_found, "Embed should contain 'Ошибки' field when errors exist"


@pytest.mark.asyncio
async def test_deactivate_with_partial_errors_logs_error_field(aiohttp_client):
    """Test that partial failures during deactivate are logged with Ошибки field in embed."""
    noisy = FakeRole(2, position=5)
    noisy.permissions.mention_everyone = True

    bot, app = build(roles=[noisy])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    # First, activate lockdown to save the backup
    resp = await client.post("/api/lockdown/activate")
    assert resp.status == 200
    assert (await resp.json())["ok"] is True
    assert len(bot.sent_logs) == 1

    # Now simulate restore failure by making the role uneditable
    noisy.permissions.mention_everyone = False
    noisy.edit_raises = _StubForbidden()

    # Deactivate should partially fail and log the error
    resp = await client.post("/api/lockdown/deactivate")
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert len(body["errors"]) > 0

    # Verify the deactivate log embed (last one) contains error field
    assert len(bot.sent_logs) == 2
    embed = bot.sent_logs[-1]
    error_field_found = any(f.name == "Ошибки" for f in embed.fields)
    assert error_field_found, "Embed should contain 'Ошибки' field when errors exist"


@pytest.mark.asyncio
async def test_activate_guild_unavailable_503(aiohttp_client):
    """Test that activate returns 503 when guild is unavailable."""
    bot = FakeBot(FakeGuild(members=[FakeMember(10, name="mod", role_ids=[111])]))
    bot.get_guild = lambda gid: None
    app = make_moderation_app(bot, [lockdown_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/lockdown/activate")
    assert resp.status == 503
