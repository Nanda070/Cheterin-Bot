"""Basic isolation and route smoke tests for lookup-api."""

from __future__ import annotations

import os

import pytest
from aiohttp import web


@pytest.fixture
async def api_client(aiohttp_client, monkeypatch):
    monkeypatch.delenv("LOOKUP_DISCORD_TOKEN", raising=False)
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    from app import create_app

    app = create_app()
    return await aiohttp_client(app)


async def test_health(api_client):
    resp = await api_client.get("/api/lookup/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["ok"] is True
    assert data["token_configured"] is False


async def test_config(api_client):
    resp = await api_client.get("/api/lookup/config")
    assert resp.status == 200
    data = await resp.json()
    assert "lookup_client_id" in data
    assert data["rate_limit_per_minute"] == 30


async def test_plugins_empty(api_client):
    resp = await api_client.get("/api/lookup/plugins")
    assert resp.status == 200
    data = await resp.json()
    assert data["plugins"] == []


async def test_user_without_token_is_503(api_client):
    resp = await api_client.get("/api/lookup/user/123456789012345678")
    assert resp.status == 503


async def test_server_rejects_guild_id(api_client):
    resp = await api_client.get("/api/lookup/server/123456789012345678")
    assert resp.status == 400
    data = await resp.json()
    assert data["error"] == "invite_required"


async def test_does_not_import_bot_modules():
    import sys

    # Ensure forbidden modules are not pulled in by create_app
    forbidden = ["antiraid", "valchecker", "dashboard.backend.app", "member_lookup"]
    from app import create_app

    create_app()
    for name in forbidden:
        assert name not in sys.modules


def test_normalize_invite():
    from app import normalize_invite

    assert normalize_invite("abcDEF") == "abcDEF"
    assert normalize_invite("https://discord.gg/abcDEF") == "abcDEF"
    assert normalize_invite("https://discord.com/invite/abcDEF") == "abcDEF"
    assert normalize_invite("123456789012345678") is None
