import pytest

from dashboard.backend.app import create_app, start_dashboard

VALID_ENV = {
    "DASHBOARD_PORT": "0",  # port 0 = OS picks a free ephemeral port, avoids clashes in CI
    "DISCORD_CLIENT_ID": "id",
    "DISCORD_CLIENT_SECRET": "secret",
    "DISCORD_OAUTH_REDIRECT_URI": "http://localhost:8080/api/auth/discord/callback",
    "SESSION_SECRET": "x" * 32,
    "DASHBOARD_ACCESS_ROLE_IDS": "111",
}


class FakeBot:
    def get_guild(self, guild_id):
        return None


@pytest.mark.asyncio
async def test_health_endpoint(aiohttp_client):
    from dashboard.backend.config import load_dashboard_config

    config = load_dashboard_config(VALID_ENV)
    app = create_app(FakeBot(), config, guild_id=1)
    client = await aiohttp_client(app)
    resp = await client.get("/api/health")
    assert resp.status == 200
    body = await resp.json()
    assert body == {"status": "ok"}


@pytest.mark.asyncio
async def test_start_dashboard_returns_none_on_invalid_config():
    incomplete_env = {"DASHBOARD_PORT": "8080"}
    runner = await start_dashboard(FakeBot(), guild_id=1, env=incomplete_env)
    assert runner is None


@pytest.mark.asyncio
async def test_start_dashboard_returns_runner_on_valid_config():
    runner = await start_dashboard(FakeBot(), guild_id=1, env=VALID_ENV)
    assert runner is not None
    await runner.cleanup()
