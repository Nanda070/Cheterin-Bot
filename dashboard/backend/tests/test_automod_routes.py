import pytest

import automod_core
from dashboard.backend.routes.automod import routes as automod_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(automod_core, "CONFIG_FILE", str(tmp_path / "automod_config.json"))


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator]))
    return bot, make_moderation_app(bot, [automod_routes])


@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/automod")
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is False
    assert set(body["filters"].keys()) == set(automod_core.FILTER_KEYS)
    assert body["escalation"] == []


@pytest.mark.asyncio
async def test_update_module_enabled(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/automod", json={"enabled": True})
    assert resp.status == 200
    assert (await resp.json())["enabled"] is True

    resp = await client.put("/api/automod", json={"enabled": "yes"})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_update_filter(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/automod/filters/bad_words",
        json={"enabled": True, "words": ["плохое", "  ", "слово"], "punishment": "mute", "duration_minutes": 60},
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is True
    assert body["words"] == ["плохое", "слово"]
    assert body["punishment"] == "mute"
    assert body["duration_minutes"] == 60


@pytest.mark.asyncio
async def test_update_filter_not_found(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/automod/filters/unknown", json={"enabled": True})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_update_filter_validation(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/automod/filters/links", json={"punishment": "explode"})
    assert resp.status == 400
    resp = await client.put("/api/automod/filters/links", json={"duration_minutes": -1})
    assert resp.status == 400
    resp = await client.put("/api/automod/filters/links", json={"notify_channel_id": "abc"})
    assert resp.status == 400
    resp = await client.put("/api/automod/filters/links", json={"notify_template": ""})
    assert resp.status == 400
    resp = await client.put("/api/automod/filters/caps_lock", json={"max_percent": 0})
    assert resp.status == 400
    resp = await client.put("/api/automod/filters/repeated_text", json={"max_repeats": 0})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_update_manual_warn_duration(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/automod/manual-warn-duration", json={"duration_minutes": 4320})
    assert resp.status == 200
    assert (await resp.json())["manual_warn_duration_minutes"] == 4320

    resp = await client.put("/api/automod/manual-warn-duration", json={"duration_minutes": -1})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_escalation_crud(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/automod/escalation", json={"count": 3, "action": "mute", "duration_minutes": 1440})
    assert resp.status == 201
    rule = await resp.json()
    assert rule["count"] == 3

    resp = await client.patch(f"/api/automod/escalation/{rule['id']}", json={"action": "kick"})
    assert resp.status == 200
    assert (await resp.json())["action"] == "kick"

    resp = await client.patch("/api/automod/escalation/999", json={"action": "kick"})
    assert resp.status == 404

    resp = await client.delete(f"/api/automod/escalation/{rule['id']}")
    assert resp.status == 200
    resp = await client.delete(f"/api/automod/escalation/{rule['id']}")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_escalation_validation(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/automod/escalation", json={"count": 0, "action": "mute", "duration_minutes": 0})
    assert resp.status == 400
    resp = await client.post("/api/automod/escalation", json={"count": 3, "action": "warn", "duration_minutes": 0})
    assert resp.status == 400
    resp = await client.post("/api/automod/escalation", json={"count": 3, "action": "mute", "duration_minutes": -1})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/automod")
    assert resp.status == 401
