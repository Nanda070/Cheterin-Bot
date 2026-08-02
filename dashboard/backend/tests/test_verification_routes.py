import pytest

import settings_db
import verification_core
from dashboard.backend.routes.verification import routes as verification_routes
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build(channels=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator], channels=channels or [])
    bot = FakeBot(guild)
    return bot, guild, make_moderation_app(bot, [verification_routes])


@pytest.mark.asyncio
async def test_get_defaults_disabled(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/verification")
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is False
    assert body["verified_role_id"] == ""
    assert body["rules_consent_enabled"] is False
    assert body["reverify_enabled"] is False
    assert body["reverify_days"] == 30


@pytest.mark.asyncio
async def test_put_then_get(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/verification", json={
        "enabled": True,
        "unverified_role_id": "111",
        "verified_role_id": "222",
        "welcome_text": "Жми кнопку",
        "rules_consent_enabled": True,
        "reverify_enabled": True,
        "reverify_days": 14,
    })
    assert resp.status == 200
    body = await resp.json()
    assert body["verified_role_id"] == "222"
    assert body["rules_consent_enabled"] is True
    assert body["reverify_enabled"] is True
    assert body["reverify_days"] == 14

    resp = await client.get("/api/verification")
    assert (await resp.json())["welcome_text"] == "Жми кнопку"


@pytest.mark.asyncio
async def test_put_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    cases = [
        {"enabled": "да"},
        {"enabled": True, "verified_role_id": -1},
        {"enabled": True, "welcome_text": ""},
        {"enabled": True, "welcome_text": "x" * 1001},
        {"enabled": True, "welcome_text": "ok", "rules_consent_enabled": "yes"},
        {"enabled": True, "welcome_text": "ok", "reverify_days": 0},
        {"enabled": True, "welcome_text": "ok", "reverify_days": 400},
        {"enabled": True, "welcome_text": "ok", "reverify_days": True},
    ]
    for body in cases:
        resp = await client.put("/api/verification", json=body)
        assert resp.status == 400, body


@pytest.mark.asyncio
async def test_requires_login(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/verification")
    assert resp.status in (401, 403)


@pytest.mark.asyncio
async def test_publish_rejects_when_module_disabled(aiohttp_client):
    channel = FakeChannel(500)
    _, _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/verification/publish", json={"channel_id": "500"})
    assert resp.status == 409
    assert (await resp.json())["error"] == "module_disabled"
    assert channel.send_calls == []


@pytest.mark.asyncio
async def test_publish_rejects_when_not_configured(aiohttp_client):
    channel = FakeChannel(500)
    _, _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    verification_core.save_config(1, {"enabled": True, "welcome_text": "Жми кнопку"})
    resp = await client.post("/api/verification/publish", json={"channel_id": "500"})
    assert resp.status == 409
    assert (await resp.json())["error"] == "not_configured"


@pytest.mark.asyncio
async def test_publish_rejects_missing_channel(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    verification_core.save_config(1, {"enabled": True, "verified_role_id": "222", "welcome_text": "Жми кнопку"})
    resp = await client.post("/api/verification/publish", json={"channel_id": "999"})
    assert resp.status == 404
    assert (await resp.json())["error"] == "channel_not_found"


@pytest.mark.asyncio
async def test_publish_sends_panel_to_channel(aiohttp_client):
    channel = FakeChannel(500)
    _, _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    verification_core.save_config(1, {"enabled": True, "verified_role_id": "222", "welcome_text": "Жми кнопку"})
    resp = await client.post("/api/verification/publish", json={"channel_id": "500"})
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert body["message_id"]
    assert len(channel.send_calls) == 1
    assert channel.send_calls[0]["content"] == "Жми кнопку"


@pytest.mark.asyncio
async def test_publish_maps_discord_forbidden(aiohttp_client):
    import discord

    channel = FakeChannel(500)
    channel.send_raises = discord.Forbidden.__new__(discord.Forbidden)
    _, _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)
    verification_core.save_config(1, {"enabled": True, "verified_role_id": "222", "welcome_text": "Жми кнопку"})

    resp = await client.post("/api/verification/publish", json={"channel_id": "500"})
    assert resp.status == 403
    assert (await resp.json())["error"] == "forbidden_by_discord"


@pytest.mark.asyncio
async def test_publish_maps_discord_http_exception(aiohttp_client):
    import discord

    channel = FakeChannel(500)
    channel.send_raises = discord.HTTPException.__new__(discord.HTTPException)
    _, _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)
    verification_core.save_config(1, {"enabled": True, "verified_role_id": "222", "welcome_text": "Жми кнопку"})

    resp = await client.post("/api/verification/publish", json={"channel_id": "500"})
    assert resp.status == 502
    assert (await resp.json())["error"] == "publish_failed"
