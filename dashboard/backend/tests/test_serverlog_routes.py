import pytest

import serverlog
import settings_db
from dashboard.backend.routes.serverlog import routes as serverlog_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator]))
    return bot, make_moderation_app(bot, [serverlog_routes])


@pytest.mark.asyncio
async def test_get_defaults_all_disabled(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/serverlog")
    assert resp.status == 200
    body = await resp.json()
    assert set(body["events"].keys()) == set(serverlog.EVENT_TYPES.keys())
    assert all(not e["enabled"] for e in body["events"].values())
    assert body["labels"]["message_edit"]


@pytest.mark.asyncio
async def test_put_then_get(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    events = {t: {"enabled": False, "channel_id": ""} for t in serverlog.EVENT_TYPES}
    events["message_delete"] = {"enabled": True, "channel_id": "500"}

    resp = await client.put("/api/serverlog", json={"events": events})
    assert resp.status == 200
    body = await resp.json()
    assert body["events"]["message_delete"] == {"enabled": True, "channel_id": "500"}

    assert serverlog.event_channel_id(1, "message_delete") == 500
    assert serverlog.event_channel_id(1, "message_edit") == 0


@pytest.mark.asyncio
async def test_put_validation(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    events = {t: {"enabled": False, "channel_id": ""} for t in serverlog.EVENT_TYPES}
    events["voice_join"] = {"enabled": True, "channel_id": ""}  # включено без канала
    resp = await client.put("/api/serverlog", json={"events": events})
    assert resp.status == 400

    events["voice_join"] = {"enabled": True, "channel_id": "abc"}
    resp = await client.put("/api/serverlog", json={"events": events})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/serverlog")
    assert resp.status == 401
