"""Async HenrikDev API client — semaphore + gap + in-job 429 retry (no nested queue)."""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any
from urllib.parse import quote, urlencode

import aiohttp

HENRIK_BASE = "https://api.henrikdev.xyz"
MAX_CONCURRENT = 3
MIN_GAP_MS = 250
USER_AGENT = "Cheterin-ValChecker/1.0"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=18, sock_connect=8, sock_read=15)


class HenrikError(Exception):
    def __init__(self, status: int, message: str, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body = body


def friendly_error(exc: BaseException, lang: str = "en") -> str:
    """Map Henrik / network errors to a short user-facing string."""
    import i18n

    if isinstance(exc, HenrikError):
        if exc.status == 401:
            return i18n.t("valchecker.err.api_key", lang)
        if exc.status == 404:
            return i18n.t("valchecker.err.not_found", lang)
        if exc.status == 429:
            return i18n.t("valchecker.err.rate_limit", lang)
        return str(exc) or i18n.t("valchecker.err.generic", lang)
    return str(exc) or i18n.t("valchecker.err.generic", lang)


class HenrikClient:
    def __init__(self, session: aiohttp.ClientSession | None = None):
        self._session = session
        self._owns_session = False
        self._sem = asyncio.Semaphore(MAX_CONCURRENT)
        self._gap_lock = asyncio.Lock()
        self._last_start = 0.0

    async def ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=REQUEST_TIMEOUT)
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    def _api_key(self) -> str:
        return (os.getenv("HENRIK_API_KEY") or "").strip()

    async def _throttle(self) -> None:
        """Enforce MIN_GAP between request starts without sleeping under the lock."""
        while True:
            async with self._gap_lock:
                gap = MIN_GAP_MS / 1000.0 - (time.monotonic() - self._last_start)
                if gap <= 0:
                    self._last_start = time.monotonic()
                    return
            await asyncio.sleep(gap)

    async def request(
        self,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        throttle: bool = True,
    ) -> Any:
        key = self._api_key()
        if not key:
            raise HenrikError(401, "API key is not configured on the bot.")

        url = path if path.startswith("http") else f"{HENRIK_BASE}{path}"
        if query:
            filtered = {
                k: str(v)
                for k, v in query.items()
                if v is not None and v != ""
            }
            if filtered:
                url = f"{url}?{urlencode(filtered)}"

        headers = {
            "Authorization": key,
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }

        for attempt in range(4):
            # Gap first (does not hold the concurrency semaphore), then fetch.
            if throttle:
                await self._throttle()
            async with self._sem:
                session = await self.ensure_session()
                async with session.get(url, headers=headers) as res:
                    text = await res.text()
                    try:
                        body = json.loads(text) if text else None
                    except Exception:
                        body = {"raw": text}

                    if res.status == 429 and attempt < 3:
                        retry_after = float(res.headers.get("Retry-After") or 2)
                    elif res.status >= 400:
                        msg = None
                        if isinstance(body, dict) and body.get("errors"):
                            msg = (body.get("errors") or [{}])[0].get("message")
                        if not msg and isinstance(body, dict):
                            msg = body.get("message")
                        if not msg:
                            msg = res.reason or "Henrik API error"
                        raise HenrikError(res.status, str(msg), body)
                    else:
                        return body
            # Sleep for 429 outside the semaphore so other requests can proceed.
            await asyncio.sleep(max(0.5, retry_after))

        raise HenrikError(429, "Rate limited by Henrik API.")

    async def request_many(self, specs: list[dict[str, Any]]) -> list[Any]:
        """Run several GETs; throttle once, then fan out under the concurrency sem."""
        if not specs:
            return []
        await self._throttle()

        async def one(spec: dict[str, Any]):
            return await self.request(
                spec["path"],
                query=spec.get("query"),
                throttle=False,
            )

        return await asyncio.gather(*[one(s) for s in specs], return_exceptions=True)


def _enc(s: str) -> str:
    return quote(str(s), safe="")


_client: HenrikClient | None = None


def get_client() -> HenrikClient:
    global _client
    if _client is None:
        _client = HenrikClient()
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


async def account(name: str, tag: str, *, throttle: bool = True):
    return await get_client().request(
        f"/valorant/v2/account/{_enc(name)}/{_enc(tag)}", throttle=throttle
    )


async def account_by_puuid(puuid: str, *, throttle: bool = True):
    return await get_client().request(
        f"/valorant/v2/by-puuid/account/{_enc(puuid)}", throttle=throttle
    )


async def mmr_by_puuid(region: str, platform: str, puuid: str, *, throttle: bool = True):
    return await get_client().request(
        f"/valorant/v3/by-puuid/mmr/{region}/{platform}/{_enc(puuid)}",
        throttle=throttle,
    )


async def matches_by_puuid(
    region: str,
    platform: str,
    puuid: str,
    *,
    size: int | None = None,
    mode: str | None = None,
    map: str | None = None,
    start: int | None = None,
    throttle: bool = True,
):
    return await get_client().request(
        f"/valorant/v4/by-puuid/matches/{region}/{platform}/{_enc(puuid)}",
        query={"size": size, "mode": mode, "map": map, "start": start},
        throttle=throttle,
    )


async def profile_bundle(region: str, platform: str, puuid: str, *, size: int = 5) -> list[Any]:
    """MMR + matches in one throttle window (account/card loaded separately if needed)."""
    return await get_client().request_many(
        [
            {"path": f"/valorant/v3/by-puuid/mmr/{region}/{platform}/{_enc(puuid)}"},
            {
                "path": f"/valorant/v4/by-puuid/matches/{region}/{platform}/{_enc(puuid)}",
                "query": {"size": size},
            },
        ]
    )


async def status(region: str):
    return await get_client().request(f"/valorant/v1/status/{region}")


async def queue_status(region: str):
    return await get_client().request(f"/valorant/v1/queue-status/{region}")
