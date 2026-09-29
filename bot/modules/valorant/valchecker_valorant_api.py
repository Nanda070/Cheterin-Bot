"""valorant-api.com asset lookups (agents / maps / competitive tiers)."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import aiohttp

VALORANT_API_BASE = "https://valorant-api.com/v1"
TTL = 1000 * 60 * 60 * 6 / 1000  # seconds

_cache: dict[str, tuple[float, Any]] = {}
_agents_by_uuid: dict[str, Any] | None = None
_maps_by_url: dict[str, Any] | None = None
_maps_by_name: dict[str, Any] | None = None
_ranks_by_tier: dict[int, Any] | None = None


async def _get(session: aiohttp.ClientSession, path: str) -> Any:
    hit = _cache.get(path)
    if hit and time.monotonic() - hit[0] < TTL:
        return hit[1]
    async with session.get(f"{VALORANT_API_BASE}{path}") as res:
        if res.status >= 400:
            raise RuntimeError(f"valorant-api.com {res.status}")
        json_body = await res.json()
    data = json_body.get("data")
    _cache[path] = (time.monotonic(), data)
    return data


async def load_assets(session: aiohttp.ClientSession | None = None) -> dict[str, int]:
    global _agents_by_uuid, _maps_by_url, _maps_by_name, _ranks_by_tier
    owns = False
    if session is None:
        session = aiohttp.ClientSession()
        owns = True
    try:
        agents, maps, competitive_tiers = await asyncio.gather(
            _get(session, "/agents?isPlayableCharacter=true"),
            _get(session, "/maps"),
            _get(session, "/competitivetiers"),
        )
        _agents_by_uuid = {a["uuid"]: a for a in agents}
        _maps_by_url = {}
        _maps_by_name = {}
        for m in maps:
            _maps_by_name[m["displayName"].lower()] = m
            if m.get("mapUrl"):
                _maps_by_url[m["mapUrl"].lower()] = m
        latest = competitive_tiers[-1]
        _ranks_by_tier = {t["tier"]: t for t in latest["tiers"]}
        return {
            "agents": len(agents),
            "maps": len(maps),
            "ranks": len(_ranks_by_tier),
        }
    finally:
        if owns:
            await session.close()


def agent_by_uuid(uuid: str | None) -> dict | None:
    if not uuid or not _agents_by_uuid:
        return None
    return _agents_by_uuid.get(uuid)


def agent_by_name(name: str | None) -> dict | None:
    if not _agents_by_uuid or not name:
        return None
    n = name.lower()
    for a in _agents_by_uuid.values():
        if a.get("displayName", "").lower() == n:
            return a
    return None


def map_by_path_or_name(path_or_name: str | None) -> dict | None:
    if not path_or_name:
        return None
    s = str(path_or_name).lower()
    if _maps_by_url and s in _maps_by_url:
        return _maps_by_url[s]
    short = s.split("/")[-1]
    if _maps_by_url:
        for k, v in _maps_by_url.items():
            if k.endswith(f"/{short}") or short in k:
                return v
    if _maps_by_name:
        return _maps_by_name.get(s) or _maps_by_name.get(short)
    return None


def rank_by_tier(tier) -> dict | None:
    if _ranks_by_tier is None:
        return None
    try:
        return _ranks_by_tier.get(int(tier))
    except (TypeError, ValueError):
        return None
