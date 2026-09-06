"""Unit tests for TokenPool round-robin and 429-rotation logic."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import only the TokenPool class (avoids loading aiohttp app at module level)
from app import TokenPool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_resp(status: int, body: dict, retry_after: str | None = None) -> MagicMock:
    """Build a mock aiohttp response context-manager."""
    resp = MagicMock()
    resp.status = status
    resp.headers = {}
    if retry_after is not None:
        resp.headers["Retry-After"] = retry_after
    resp.json = AsyncMock(return_value=body)
    # Support `async with session.get(...) as resp`
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def make_session(*responses) -> MagicMock:
    """Return a mock session whose .get() yields responses in order."""
    session = MagicMock()
    session.get = MagicMock(side_effect=list(responses))
    return session


# ---------------------------------------------------------------------------
# Basic construction
# ---------------------------------------------------------------------------

def test_empty_pool():
    pool = TokenPool([])
    assert not pool
    assert len(pool) == 0


def test_single_token():
    pool = TokenPool(["tok1"])
    assert pool
    assert len(pool) == 1


def test_filters_blank_tokens():
    pool = TokenPool(["tok1", "", "  ", "tok2"])
    # __init__ filters via `if t`; blank strings are falsy
    assert len(pool) == 2


def test_five_tokens():
    tokens = [f"tok{i}" for i in range(5)]
    pool = TokenPool(tokens)
    assert len(pool) == 5


# ---------------------------------------------------------------------------
# Round-robin pointer
# ---------------------------------------------------------------------------

def test_round_robin_advances():
    pool = TokenPool(["a", "b", "c"])
    slots = [pool._pick()[0] for _ in range(6)]
    assert slots == [0, 1, 2, 0, 1, 2], f"got {slots}"


def test_pick_returns_correct_token():
    pool = TokenPool(["alpha", "beta"])
    slot0, tok0 = pool._pick()
    slot1, tok1 = pool._pick()
    assert tok0 == "alpha" and slot0 == 0
    assert tok1 == "beta"  and slot1 == 1


# ---------------------------------------------------------------------------
# discord_get — success path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_discord_get_success():
    pool = TokenPool(["mytoken"])
    session = make_session(make_resp(200, {"id": "123"}))
    status, data = await pool.discord_get(session, "/users/123")
    assert status == 200
    assert data["id"] == "123"


@pytest.mark.asyncio
async def test_discord_get_round_robins_on_success():
    """Each successive call uses the next token."""
    pool = TokenPool(["t1", "t2", "t3"])
    captured: list[str] = []

    def fake_get(url, headers):
        captured.append(headers["Authorization"])
        return make_resp(200, {})

    session = MagicMock()
    session.get = MagicMock(side_effect=fake_get)

    for _ in range(3):
        await pool.discord_get(session, "/users/1")

    assert captured == ["Bot t1", "Bot t2", "Bot t3"]


# ---------------------------------------------------------------------------
# discord_get — 429 rotation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_discord_get_rotates_on_429():
    """First token 429s; second token succeeds — no sleep needed."""
    pool = TokenPool(["bad", "good"])
    used: list[str] = []

    def fake_get(url, headers):
        used.append(headers["Authorization"])
        if headers["Authorization"] == "Bot bad":
            return make_resp(429, {}, retry_after="1")
        return make_resp(200, {"id": "ok"})

    session = MagicMock()
    session.get = MagicMock(side_effect=fake_get)

    status, data = await pool.discord_get(session, "/users/1")
    assert status == 200
    assert data["id"] == "ok"
    assert "Bot bad" in used
    assert "Bot good" in used


@pytest.mark.asyncio
async def test_discord_get_all_429_returns_429():
    """All tokens 429 → final return is 429."""
    pool = TokenPool(["t1", "t2"])

    def fake_get(url, headers):
        return make_resp(429, {}, retry_after="0.01")

    session = MagicMock()
    session.get = MagicMock(side_effect=fake_get)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        status, data = await pool.discord_get(session, "/users/1")

    assert status == 429


# ---------------------------------------------------------------------------
# discord_get — empty pool
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_discord_get_empty_pool_returns_503():
    pool = TokenPool([])
    session = MagicMock()
    status, data = await pool.discord_get(session, "/users/1")
    assert status == 503
    assert "missing" in data.get("message", "")