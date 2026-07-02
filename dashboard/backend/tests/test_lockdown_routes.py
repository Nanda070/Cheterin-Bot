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
