import pytest

import settings_db
import warns_core
import warns_db
from dashboard.backend.routes.warns import routes as warns_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(warns_db, "get_db_path", lambda: str(tmp_path / "warns.db"))
    warns_db.db_init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


class FakeAutoModCog:
    def __init__(self):
        self.escalation_checks = []

    async def apply_escalation_if_needed(self, guild, member):
        self.escalation_checks.append((guild.id, member.id))


def build(with_cog=True):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    member = FakeMember(100, name="fighter", display_name="Fighter")
    bot = FakeBot(FakeGuild(members=[moderator, member]))
    cog = FakeAutoModCog() if with_cog else None
    bot.get_cog = lambda name: cog
    return bot, cog, make_moderation_app(bot, [warns_routes])


@pytest.mark.asyncio
async def test_list_warns_empty(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/members/100/warns")
    assert resp.status == 200
    body = await resp.json()
    assert body == {"warns": [], "active_count": 0}


@pytest.mark.asyncio
async def test_create_warn(aiohttp_client):
    _, cog, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/100/warns", json={"reason": "Спам в чате"})
    assert resp.status == 201
    body = await resp.json()
    assert body["warn"]["reason"] == "Спам в чате"
    assert body["warn"]["moderator_id"] == "10"
    assert body["active_count"] == 1
    assert cog.escalation_checks == [(1, 100)]

    resp = await client.get("/api/members/100/warns")
    body = await resp.json()
    assert len(body["warns"]) == 1
    assert body["active_count"] == 1


@pytest.mark.asyncio
async def test_create_warn_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/100/warns", json={"reason": " "})
    assert resp.status == 400
    resp = await client.post("/api/members/100/warns", json={"reason": "x" * 501})
    assert resp.status == 400
    resp = await client.post("/api/members/abc/warns", json={"reason": "ok"})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_create_warn_without_cog_still_succeeds(aiohttp_client):
    _, _, app = build(with_cog=False)
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/100/warns", json={"reason": "Спам"})
    assert resp.status == 201


@pytest.mark.asyncio
async def test_delete_warn(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/100/warns", json={"reason": "Спам"})
    warn_id = (await resp.json())["warn"]["id"]

    resp = await client.delete(f"/api/warns/{warn_id}")
    assert resp.status == 200

    resp = await client.get("/api/members/100/warns")
    assert (await resp.json())["active_count"] == 0

    resp = await client.delete(f"/api/warns/{warn_id}")
    assert resp.status == 404
    resp = await client.delete("/api/warns/abc")
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/members/100/warns")
    assert resp.status == 401
