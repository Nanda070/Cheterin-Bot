import pytest
from aiohttp import web

from dashboard.backend.discord_oauth import (
    DiscordOAuthError,
    exchange_code_for_token,
    fetch_discord_identity,
)


async def fake_token_endpoint(request):
    data = await request.post()
    if data.get("code") != "valid-code":
        return web.json_response({"error": "invalid_grant"}, status=400)
    return web.json_response({"access_token": "fake-access-token", "token_type": "Bearer"})


async def fake_identity_endpoint(request):
    auth_header = request.headers.get("Authorization")
    if auth_header != "Bearer fake-access-token":
        return web.json_response({"message": "401: Unauthorized"}, status=401)
    return web.json_response({"id": "111222333", "username": "tester"})


@pytest.fixture
async def stub_discord_server(aiohttp_client):
    app = web.Application()
    app.router.add_post("/oauth2/token", fake_token_endpoint)
    app.router.add_get("/users/@me", fake_identity_endpoint)
    client = await aiohttp_client(app)
    return client


@pytest.mark.asyncio
async def test_exchange_code_for_token_success(stub_discord_server):
    result = await exchange_code_for_token(
        stub_discord_server.session,
        code="valid-code",
        client_id="id",
        client_secret="secret",
        redirect_uri="http://localhost/cb",
        api_base=str(stub_discord_server.make_url("")),
    )
    assert result["access_token"] == "fake-access-token"


@pytest.mark.asyncio
async def test_exchange_code_for_token_failure_raises(stub_discord_server):
    with pytest.raises(DiscordOAuthError):
        await exchange_code_for_token(
            stub_discord_server.session,
            code="bad-code",
            client_id="id",
            client_secret="secret",
            redirect_uri="http://localhost/cb",
            api_base=str(stub_discord_server.make_url("")),
        )


@pytest.mark.asyncio
async def test_fetch_discord_identity_success(stub_discord_server):
    identity = await fetch_discord_identity(
        stub_discord_server.session,
        access_token="fake-access-token",
        api_base=str(stub_discord_server.make_url("")),
    )
    assert identity["id"] == "111222333"


@pytest.mark.asyncio
async def test_fetch_discord_identity_failure_raises(stub_discord_server):
    with pytest.raises(DiscordOAuthError):
        await fetch_discord_identity(
            stub_discord_server.session,
            access_token="wrong-token",
            api_base=str(stub_discord_server.make_url("")),
        )
