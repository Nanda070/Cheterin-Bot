"""Henrik client concurrency / retry behaviour."""

from __future__ import annotations

import asyncio

import pytest

import valchecker_henrik as henrik


@pytest.mark.asyncio
async def test_henrik_semaphore_no_deadlock(monkeypatch):
    """Concurrent jobs must finish; throttle must not hold the concurrency slot."""
    monkeypatch.setattr(henrik, "MIN_GAP_MS", 0)
    client = henrik.HenrikClient()
    finished = 0

    async def job():
        nonlocal finished
        await client._throttle()
        async with client._sem:
            await asyncio.sleep(0.01)
            finished += 1
            return True

    results = await asyncio.wait_for(asyncio.gather(*[job() for _ in range(12)]), timeout=3)
    assert all(results)
    assert finished == 12
    await client.close()


def test_friendly_error_mapping():
    assert "API" in henrik.friendly_error(henrik.HenrikError(401, "x"), "en")
    assert "not found" in henrik.friendly_error(henrik.HenrikError(404, "x"), "en").lower()
    assert "rate" in henrik.friendly_error(henrik.HenrikError(429, "x"), "en").lower()
