import pytest

import bot_config
from dashboard.backend.routes.config import routes as config_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_config_file(tmp_path, monkeypatch):
    monkeypatch.setattr(bot_config, "CONFIG_FILE", str(tmp_path / "config.json"))


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    return guild, make_moderation_app(FakeBot(guild), [config_routes])


@pytest.mark.asyncio
async def test_get_config_returns_defaults_when_file_missing(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/config")
    assert resp.status == 200
    body = await resp.json()
    assert body["LOG_CHANNEL_ID"] == ""
    assert body["SPAM_EXCEPTION_CHANNELS"] == []
    assert body["BUTTON_WEBHOOK_URL"] == ""


@pytest.mark.asyncio
async def test_get_config_returns_stored_values(aiohttp_client):
    bot_config.save_config(
        {
            "LOG_CHANNEL_ID": "500",
            "SPAM_EXCEPTION_CHANNELS": ["600", "700"],
            "SERVER_INVITE_LINK": "https://discord.gg/example",
        }
    )
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/config")
    body = await resp.json()
    assert body["LOG_CHANNEL_ID"] == "500"
    assert body["SPAM_EXCEPTION_CHANNELS"] == ["600", "700"]
    assert body["SERVER_INVITE_LINK"] == "https://discord.gg/example"


@pytest.mark.asyncio
async def test_get_config_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/config")
    assert resp.status == 401
