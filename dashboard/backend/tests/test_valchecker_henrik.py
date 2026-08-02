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


@pytest.mark.asyncio
async def test_nested_gather_under_outer_sem_deadlocks_with_max_2():
    """outer sem=2 + each worker gather(hold, need) with global sem=2 deadlocks.

    Mirrors the old /val-lb pattern that froze /val-profile.
    """
    global_sem = asyncio.Semaphore(2)
    outer = asyncio.Semaphore(2)
    holds = 0
    holds_lock = asyncio.Lock()
    both_held = asyncio.Event()

    async def pair():
        nonlocal holds
        async with outer:
            async def hold():
                nonlocal holds
                async with global_sem:
                    async with holds_lock:
                        holds += 1
                        if holds >= 2:
                            both_held.set()
                    await asyncio.Event().wait()  # park while holding a global slot

            async def need():
                await both_held.wait()
                async with global_sem:
                    return True

            await asyncio.gather(hold(), need())

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(asyncio.gather(pair(), pair()), timeout=0.5)


@pytest.mark.asyncio
async def test_nested_gather_safe_with_outer_sem_1():
    global_sem = asyncio.Semaphore(2)
    outer = asyncio.Semaphore(1)

    async def pair():
        async with outer:
            async def one():
                async with global_sem:
                    await asyncio.sleep(0.01)

            await asyncio.gather(one(), one())

    await asyncio.wait_for(asyncio.gather(pair(), pair(), pair()), timeout=2)


def test_friendly_error_mapping():
    assert "API" in henrik.friendly_error(henrik.HenrikError(401, "x"), "en")
    assert "not found" in henrik.friendly_error(henrik.HenrikError(404, "x"), "en").lower()
    assert "rate" in henrik.friendly_error(henrik.HenrikError(429, "x"), "en").lower()


@pytest.mark.asyncio
async def test_request_many_throttles_once(monkeypatch):
    client = henrik.HenrikClient()
    calls = {"throttle": 0, "get": 0}

    async def fake_throttle():
        calls["throttle"] += 1

    class FakeResp:
        status = 200
        reason = "OK"
        headers = {}

        async def text(self):
            return '{"ok":true}'

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    class FakeSession:
        def get(self, url, headers=None):
            calls["get"] += 1
            return FakeResp()

        @property
        def closed(self):
            return False

        async def close(self):
            return None

    async def ensure():
        return FakeSession()

    monkeypatch.setattr(client, "_throttle", fake_throttle)
    monkeypatch.setattr(client, "ensure_session", ensure)
    monkeypatch.setattr(client, "_api_key", lambda: "test-key")
    monkeypatch.setattr(henrik, "MIN_GAP_MS", 0)

    out = await client.request_many(
        [{"path": "/a"}, {"path": "/b"}, {"path": "/c"}]
    )
    assert calls["throttle"] == 1
    assert calls["get"] == 3
    assert all(isinstance(x, dict) for x in out)
    await client.close()
