import socket
from unittest.mock import patch

import pytest

import dashboard.backend.app as app_module
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
    http_session = runner.app["http_session"]
    assert http_session.closed is False
    await runner.cleanup()
    assert http_session.closed is True


@pytest.mark.asyncio
async def test_start_dashboard_returns_none_on_unexpected_error():
    """A non-ConfigError, non-OSError failure during app construction/startup
    must still be swallowed by start_dashboard's broad `except Exception`
    guard, since a dashboard startup failure must never crash the bot.
    """

    def broken_create_app(bot, config, guild_id):
        raise RuntimeError("simulated unexpected failure in app construction")

    with patch.object(app_module, "create_app", side_effect=broken_create_app):
        runner = await start_dashboard(FakeBot(), guild_id=1, env=VALID_ENV)

    assert runner is None


@pytest.mark.asyncio
async def test_start_dashboard_closes_http_session_on_bind_failure():
    """On a real port-bind conflict (OSError from TCPSite.start), the
    http_session created inside create_app must be closed as a result of
    start_dashboard's cleanup handling -- not just that start_dashboard
    returns None.
    """
    # Bind a raw socket to a free port first, to force a genuine bind
    # conflict for TCPSite.start (a real OSError, not a mocked one).
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("0.0.0.0", 0))
    blocker.listen(1)
    port = blocker.getsockname()[1]

    env = dict(VALID_ENV)
    env["DASHBOARD_PORT"] = str(port)

    captured = {}
    orig_create_app = app_module.create_app

    def spy_create_app(bot, config, guild_id):
        app = orig_create_app(bot, config, guild_id)
        captured["app"] = app
        return app

    try:
        with patch.object(app_module, "create_app", side_effect=spy_create_app):
            runner = await start_dashboard(FakeBot(), guild_id=1, env=env)

        assert runner is None
        http_session = captured["app"]["http_session"]
        assert http_session.closed is True
    finally:
        blocker.close()
