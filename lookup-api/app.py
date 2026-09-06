"""Cheterin Lookup API — isolated aiohttp service.

Supports LOOKUP_DISCORD_TOKENS (comma-list) or LOOKUP_DISCORD_TOKEN (single). Never imports bot cogs, dashboard.backend, or ValChecker. Never imports bot cogs, dashboard.backend, or ValChecker.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from aiohttp import ClientSession, ClientTimeout, web
from dotenv import load_dotenv

from dsa import (
    DSA_CACHE_TTL,
    fetch_discord_statements,
    source_meta as dsa_source_meta,
)

# Load lookup-api/.env then repo-root .env (without overriding existing env)
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
load_dotenv(_HERE / ".env")
load_dotenv(_ROOT / ".env")

log = logging.getLogger("lookup-api")


# ── Token pool ───────────────────────────────────────────────────────────────

class TokenPool:
    """Round-robin Discord bot-token pool with 429-aware rotation.

    Tokens are loaded from ``LOOKUP_DISCORD_TOKENS`` (comma-separated, preferred)
    or ``LOOKUP_DISCORD_TOKEN`` (single-token fallback).  Each call to
    :meth:`discord_get` advances the round-robin pointer so consecutive requests
    spread across all configured tokens.  On HTTP 429 the failing slot is skipped
    and the next token is tried immediately; if every token is exhausted the pool
    waits ``min(Retry-After, 5 s)`` before one final attempt.
    """

    def __init__(self, tokens: list[str]) -> None:
        self._tokens: list[str] = [t.strip() for t in tokens if t and t.strip()]
        self._idx: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    def __bool__(self) -> bool:
        return bool(self._tokens)

    def __len__(self) -> int:
        return len(self._tokens)

    def _pick(self) -> tuple[int, str]:
        """Return ``(slot, token)`` and advance the pointer. Call under ``self._lock``."""
        n = len(self._tokens)
        slot = self._idx % n
        self._idx = (slot + 1) % n
        return slot, self._tokens[slot]

    async def discord_get(self, session: ClientSession, path: str) -> tuple[int, Any]:
        """GET ``{DISCORD_API}{path}`` with round-robin token selection.

        Rotates to the next token immediately on HTTP 429.  After all tokens
        have been tried once it waits up to 5 s then makes one final attempt.
        """
        if not self._tokens:
            return 503, {"message": "LOOKUP_DISCORD_TOKEN missing"}

        n = len(self._tokens)
        last_retry_after: float = 1.0

        for attempt in range(n + 1):
            async with self._lock:
                slot, token = self._pick()

            headers = {
                "Authorization": f"Bot {token}",
                "User-Agent": "CheterinLookup/1.0",
            }
            try:
                async with session.get(f"{DISCORD_API}{path}", headers=headers) as resp:
                    if resp.status == 429:
                        last_retry_after = float(resp.headers.get("Retry-After", "1"))
                        log.warning(
                            "discord_get: slot %d/%d 429 on %s (retry_after=%.1fs attempt %d/%d)",
                            slot + 1, n, path, last_retry_after, attempt + 1, n + 1,
                        )
                        if attempt < n - 1:
                            continue  # try next token immediately
                        await asyncio.sleep(min(last_retry_after, 5.0))
                        continue
                    try:
                        data = await resp.json(content_type=None)
                    except Exception:
                        data = {"message": await resp.text()}
                    return resp.status, data
            except Exception as exc:  # noqa: BLE001
                log.warning("discord_get attempt %d/%d error: %s", attempt + 1, n + 1, exc)

        return 429, {"message": "All Discord tokens are rate-limited; try again shortly."}

DISCORD_API = "https://discord.com/api/v10"
CDN = "https://cdn.discordapp.com"
SNOWFLAKE_RE = re.compile(r"^\d{17,20}$")
INVITE_RE = re.compile(r"^[A-Za-z0-9-]+$")
DISCORD_EPOCH_MS = 1_420_070_400_000

USER_CACHE_TTL = 15 * 60
INVITE_CACHE_TTL = 10 * 60
RATE_LIMIT_PER_MINUTE = 30
ABUSE_LOG_TTL = 48 * 3600

PERMISSION_NAMES: dict[int, str] = {
    1 << 0: "Create Instant Invite",
    1 << 1: "Kick Members",
    1 << 2: "Ban Members",
    1 << 3: "Administrator",
    1 << 4: "Manage Channels",
    1 << 5: "Manage Guild",
    1 << 6: "Add Reactions",
    1 << 7: "View Audit Log",
    1 << 8: "Priority Speaker",
    1 << 9: "Stream",
    1 << 10: "View Channel",
    1 << 11: "Send Messages",
    1 << 12: "Send TTS Messages",
    1 << 13: "Manage Messages",
    1 << 14: "Embed Links",
    1 << 15: "Attach Files",
    1 << 16: "Read Message History",
    1 << 17: "Mention Everyone",
    1 << 18: "Use External Emojis",
    1 << 19: "View Guild Insights",
    1 << 20: "Connect",
    1 << 21: "Speak",
    1 << 22: "Mute Members",
    1 << 23: "Deafen Members",
    1 << 24: "Move Members",
    1 << 25: "Use VAD",
    1 << 26: "Change Nickname",
    1 << 27: "Manage Nicknames",
    1 << 28: "Manage Roles",
    1 << 29: "Manage Webhooks",
    1 << 30: "Manage Expressions",
    1 << 31: "Use Application Commands",
    1 << 32: "Request to Speak",
    1 << 33: "Manage Events",
    1 << 34: "Manage Threads",
    1 << 35: "Create Public Threads",
    1 << 36: "Create Private Threads",
    1 << 37: "Use External Stickers",
    1 << 38: "Send Messages in Threads",
    1 << 39: "Use Embedded Activities",
    1 << 40: "Moderate Members",
    1 << 41: "View Creator Monetization Analytics",
    1 << 42: "Use Soundboard",
    1 << 43: "Create Expressions",
    1 << 44: "Create Events",
    1 << 45: "Use External Sounds",
    1 << 46: "Send Voice Messages",
    1 << 49: "Send Polls",
    1 << 50: "Use External Apps",
}

# Application flags → gateway intent labels (best-effort public mapping)
INTENT_FLAGS: list[tuple[int, str]] = [
    (1 << 12, "GATEWAY_PRESENCE"),
    (1 << 13, "GATEWAY_PRESENCE_LIMITED"),
    (1 << 14, "GATEWAY_GUILD_MEMBERS"),
    (1 << 15, "GATEWAY_GUILD_MEMBERS_LIMITED"),
    (1 << 16, "VERIFICATION_PENDING_GUILD_LIMIT"),
    (1 << 17, "EMBEDDED"),
    (1 << 18, "GATEWAY_MESSAGE_CONTENT"),
    (1 << 19, "GATEWAY_MESSAGE_CONTENT_LIMITED"),
    (1 << 23, "APPLICATION_COMMAND_BADGE"),
]


class TtlCache:
    def __init__(self) -> None:
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._data.get(key)
        if not item:
            return None
        expires, value = item
        if time.time() >= expires:
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: float) -> None:
        self._data[key] = (time.time() + ttl, value)


class RateLimiter:
    """Sliding window per IP. Returns (allowed, retry_after, captcha_required)."""

    def __init__(self, limit: int = RATE_LIMIT_PER_MINUTE) -> None:
        self.limit = limit
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._captcha: dict[str, float] = {}

    def check(self, ip: str) -> tuple[bool, int, bool]:
        now = time.time()
        captcha_until = self._captcha.get(ip, 0)
        if captcha_until > now:
            return False, int(captcha_until - now) + 1, True

        q = self._hits[ip]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.limit:
            # Soft CAPTCHA gate after threshold — operator must set LOOKUP_CAPTCHA_* env vars
            self._captcha[ip] = now + 60
            return False, 60, True
        q.append(now)
        return True, 0, False

    def clear_captcha(self, ip: str) -> None:
        """Called after successful CAPTCHA solve: clear gate and reset sliding window."""
        self._captcha.pop(ip, None)
        self._hits.pop(ip, None)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


def _client_ip(request: web.Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    peer = request.remote
    return peer or "unknown"


def snowflake_created_at(snowflake: str) -> str:
    ts = ((int(snowflake) >> 22) + DISCORD_EPOCH_MS) / 1000
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def permission_names(mask: int | str | None) -> list[str]:
    if mask is None or mask == "":
        return []
    value = int(mask)
    return [name for bit, name in PERMISSION_NAMES.items() if value & bit == bit]


def intents_from_flags(flags: int | None) -> list[str]:
    if not flags:
        return []
    return [name for bit, name in INTENT_FLAGS if flags & bit == bit]


def avatar_url(user_id: str, avatar: str | None) -> str:
    if not avatar:
        index = (int(user_id) >> 22) % 6
        return f"{CDN}/embed/avatars/{index}.png"
    ext = "gif" if avatar.startswith("a_") else "png"
    return f"{CDN}/avatars/{user_id}/{avatar}.{ext}?size=256"


def banner_url(user_id: str, banner: str | None) -> str | None:
    if not banner:
        return None
    ext = "gif" if banner.startswith("a_") else "png"
    return f"{CDN}/banners/{user_id}/{banner}.{ext}?size=512"


def guild_asset_url(kind: str, guild_id: str, hash_value: str | None) -> str | None:
    if not hash_value:
        return None
    ext = "gif" if hash_value.startswith("a_") else "png"
    return f"{CDN}/{kind}/{guild_id}/{hash_value}.{ext}?size=256"


def shape_user(raw: dict[str, Any]) -> dict[str, Any]:
    user_id = str(raw["id"])
    return {
        "id": user_id,
        "username": raw.get("username") or "",
        "global_name": raw.get("global_name"),
        "discriminator": str(raw.get("discriminator") or "0"),
        "avatar": raw.get("avatar"),
        "banner": raw.get("banner"),
        "accent_color": raw.get("accent_color"),
        "bot": bool(raw.get("bot")),
        "system": bool(raw.get("system")),
        "public_flags": int(raw.get("public_flags") or 0),
        "avatar_decoration_data": raw.get("avatar_decoration_data"),
        "collectibles": raw.get("collectibles"),
        "created_at": snowflake_created_at(user_id),
        "avatar_url": avatar_url(user_id, raw.get("avatar")),
        "banner_url": banner_url(user_id, raw.get("banner")),
    }


async def discord_get(app: web.Application, path: str) -> tuple[int, Any]:
    """Delegate to the app-level :class:`TokenPool`."""
    pool: TokenPool = app["token_pool"]
    session: ClientSession = app["http"]
    return await pool.discord_get(session, path)









async def fetch_application_rpc(app: web.Application, app_id: str) -> dict[str, Any] | None:
    """Public application RPC with retries. No user token."""
    session: ClientSession = app["http"]
    url = f"{DISCORD_API}/applications/{app_id}/rpc"
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            async with session.get(url, headers={"User-Agent": "CheterinLookup/1.0"}) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
                if resp.status in (404, 403):
                    return None
                if resp.status >= 500:
                    await asyncio.sleep(0.35 * (attempt + 1))
                    continue
                return None
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            await asyncio.sleep(0.35 * (attempt + 1))
    if last_error:
        log.warning("application rpc failed for %s: %s", app_id, last_error)
    return None


def normalize_invite(code: str) -> str | None:
    value = code.strip()
    if not value or SNOWFLAKE_RE.match(value):
        return None
    if "://" in value or value.startswith("discord.") or value.startswith("www."):
        # crude parse without urllib for path variants
        lowered = value.replace("https://", "").replace("http://", "")
        parts = lowered.split("/")
        if parts[0].startswith("discord.gg"):
            code_part = parts[1].split("?")[0] if len(parts) > 1 else ""
            return code_part if INVITE_RE.match(code_part) else None
        if "discord.com" in parts[0] or "discordapp.com" in parts[0]:
            if "invite" in parts:
                idx = parts.index("invite")
                if idx + 1 < len(parts):
                    code_part = parts[idx + 1].split("?")[0]
                    return code_part if INVITE_RE.match(code_part) else None
            return None
    bare = value.split("/")[0].split("?")[0]
    if SNOWFLAKE_RE.match(bare) or not INVITE_RE.match(bare):
        return None
    return bare


@web.middleware
async def rate_limit_middleware(request: web.Request, handler):
    # Health, config, plugins, and captcha/verify skip the rate-limit counter
    if request.path.endswith("/health") or request.path.endswith("/config") or request.path.endswith("/plugins"):
        return await handler(request)
    if request.path.endswith("/captcha/verify"):
        return await handler(request)
    if not request.path.startswith("/api/lookup/"):
        return await handler(request)
    # CDN proxy counts toward limit too
    limiter: RateLimiter = request.app["limiter"]
    ip = _client_ip(request)
    allowed, retry_after, captcha = limiter.check(ip)
    if not allowed:
        body = {
            "error": "rate_limited" if not captcha else "captcha_required",
            "code": "captcha_required" if captcha else "rate_limited",
            "retry_after": retry_after,
        }
        raise web.HTTPTooManyRequests(text=json.dumps(body), content_type="application/json", headers={"Retry-After": str(retry_after)})
    return await handler(request)


async def record_abuse(app: web.Application, ip: str, queried: str) -> None:
    logs: deque = app["abuse_logs"]
    logs.append((time.time(), _hash(ip), _hash(queried)))
    cutoff = time.time() - ABUSE_LOG_TTL
    while logs and logs[0][0] < cutoff:
        logs.popleft()


async def handle_health(request: web.Request) -> web.Response:
    pool: TokenPool = request.app["token_pool"]
    return web.json_response(
        {
            "ok": True,
            "service": "lookup-api",
            "token_configured": bool(pool),
            "token_count": len(pool),
            "rate_limit_per_minute": RATE_LIMIT_PER_MINUTE,
        }
    )

async def handle_config(request: web.Request) -> web.Response:
    captcha_enabled = os.getenv("LOOKUP_CAPTCHA_ENABLED", "false").lower() == "true"
    return web.json_response(
        {
            "lookup_client_id": os.getenv("LOOKUP_CLIENT_ID", ""),
            "cheterin_client_id": os.getenv("CHETERIN_CLIENT_ID", ""),
            "captcha_enabled": captcha_enabled,
            "captcha_provider": os.getenv("LOOKUP_CAPTCHA_PROVIDER", "turnstile") if captcha_enabled else None,
            "captcha_site_key": os.getenv("LOOKUP_CAPTCHA_SITE_KEY", "") if captcha_enabled else None,
            "rate_limit_per_minute": RATE_LIMIT_PER_MINUTE,
        }
    )


# CAPTCHA provider verify URLs (backend-to-provider call; secret never goes to frontend)
_CAPTCHA_VERIFY_URLS: dict[str, str] = {
    "turnstile": "https://challenges.cloudflare.com/turnstile/v0/siteverify",
    "hcaptcha": "https://api.hcaptcha.com/siteverify",
}


async def handle_captcha_verify(request: web.Request) -> web.Response:
    """POST /api/lookup/captcha/verify — verify a CAPTCHA token and clear the IP gate.

    Body: {"token": "<captcha-response-token>"}
    Returns: {"ok": true} or HTTP error.

    Requires LOOKUP_CAPTCHA_ENABLED=true, LOOKUP_CAPTCHA_PROVIDER, and LOOKUP_CAPTCHA_SECRET.
    Operator: set LOOKUP_CAPTCHA_SITE_KEY in environment; the frontend reads it from /api/lookup/config.
    """
    captcha_enabled = os.getenv("LOOKUP_CAPTCHA_ENABLED", "false").lower() == "true"
    if not captcha_enabled:
        raise web.HTTPServiceUnavailable(
            text='{"error":"captcha_not_enabled","message":"CAPTCHA is not configured on this instance"}',
            content_type="application/json",
        )

    secret = os.getenv("LOOKUP_CAPTCHA_SECRET", "").strip()
    if not secret:
        raise web.HTTPServiceUnavailable(
            text='{"error":"captcha_not_configured","message":"LOOKUP_CAPTCHA_SECRET not set"}',
            content_type="application/json",
        )

    provider = os.getenv("LOOKUP_CAPTCHA_PROVIDER", "turnstile").lower().strip()
    verify_url = _CAPTCHA_VERIFY_URLS.get(provider)
    if not verify_url:
        raise web.HTTPBadRequest(
            text=json.dumps({"error": "unknown_provider", "provider": provider}),
            content_type="application/json",
        )

    try:
        body = await request.json()
        token = (body.get("token") or "").strip()
    except Exception:
        raise web.HTTPBadRequest(
            text='{"error":"invalid_body","message":"Expected JSON {\"token\": \"...\"}"}',
            content_type="application/json",
        )

    if not token:
        raise web.HTTPBadRequest(
            text='{"error":"missing_token"}',
            content_type="application/json",
        )

    ip = _client_ip(request)
    session: ClientSession = request.app["http"]

    try:
        async with session.post(
            verify_url,
            data={"secret": secret, "response": token, "remoteip": ip},
            headers={"User-Agent": "CheterinLookup/1.0"},
        ) as resp:
            result: dict[str, Any] = await resp.json(content_type=None)
    except Exception as exc:
        log.warning("captcha verify request failed: %s", exc)
        raise web.HTTPBadGateway(
            text='{"error":"provider_error","message":"Could not reach CAPTCHA provider"}',
            content_type="application/json",
        )

    if not result.get("success"):
        codes = result.get("error-codes") or []
        raise web.HTTPForbidden(
            text=json.dumps({"error": "captcha_failed", "codes": codes}),
            content_type="application/json",
        )

    # Clear the captcha gate and rate-limit window so the IP can make fresh requests
    limiter: RateLimiter = request.app["limiter"]
    limiter.clear_captcha(ip)

    return web.json_response({"ok": True})


async def handle_plugins(request: web.Request) -> web.Response:
    # Reload from disk so catalog edits apply without restarting the process.
    manifest = load_plugins(quiet=True)
    request.app["plugins"] = manifest
    return web.json_response({"plugins": manifest})


async def handle_dsa_meta(request: web.Request) -> web.Response:
    """GET /api/lookup/dsa — source metadata (no upstream call)."""
    return web.json_response({"source": dsa_source_meta()})


async def handle_dsa(request: web.Request) -> web.Response:
    """GET /api/lookup/dsa/{id} — public Discord SoRs from EU DSA CSV export."""
    entity_id = request.match_info["id"].strip()
    if not SNOWFLAKE_RE.match(entity_id):
        raise web.HTTPBadRequest(text='{"error":"invalid_snowflake"}', content_type="application/json")

    cache: TtlCache = request.app["cache"]
    cached = cache.get(f"dsa:{entity_id}")
    if cached is not None:
        return web.json_response(cached)

    await record_abuse(request.app, _client_ip(request), entity_id)
    session: ClientSession = request.app["http"]
    try:
        statements = await fetch_discord_statements(session, entity_id)
    except Exception as exc:
        log.warning("DSA upstream failed for %s: %s", entity_id, exc)
        raise web.HTTPBadGateway(
            text=json.dumps({"error": "dsa_upstream_error", "message": "EU DSA Transparency Database unavailable"}),
            content_type="application/json",
        )

    payload = {
        "id": entity_id,
        "found": len(statements) > 0,
        "count": len(statements),
        "statements": statements,
        "source": dsa_source_meta(),
        "disclaimer": (
            "Empty results do not mean the account is clean or flagged — only that no matching "
            "public Statement of Reasons for Discord Netherlands B.V. was returned by the official export."
        ),
    }
    cache.set(f"dsa:{entity_id}", payload, DSA_CACHE_TTL)
    return web.json_response(payload)


async def handle_user(request: web.Request) -> web.Response:
    user_id = request.match_info["id"]
    if not SNOWFLAKE_RE.match(user_id):
        raise web.HTTPBadRequest(text='{"error":"invalid_snowflake"}', content_type="application/json")

    cache: TtlCache = request.app["cache"]
    cached = cache.get(f"user:{user_id}")
    if cached is not None:
        return web.json_response(cached)

    await record_abuse(request.app, _client_ip(request), user_id)
    status, data = await discord_get(request.app, f"/users/{user_id}")
    if status == 404:
        raise web.HTTPNotFound(text='{"error":"not_found"}', content_type="application/json")
    if status == 429:
        retry = int(data.get("retry_after", 5)) if isinstance(data, dict) else 5
        raise web.HTTPTooManyRequests(
            text='{"error":"discord_rate_limited","retry_after":%d}' % retry,
            content_type="application/json",
            headers={"Retry-After": str(retry)},
        )
    if status == 503:
        raise web.HTTPServiceUnavailable(text='{"error":"token_missing"}', content_type="application/json")
    if status >= 400 or not isinstance(data, dict):
        raise web.HTTPBadGateway(text='{"error":"upstream_error"}', content_type="application/json")

    shaped = shape_user(data)
    cache.set(f"user:{user_id}", shaped, USER_CACHE_TTL)
    return web.json_response(shaped)


async def handle_bot(request: web.Request) -> web.Response:
    bot_id = request.match_info["id"]
    if not SNOWFLAKE_RE.match(bot_id):
        raise web.HTTPBadRequest(text='{"error":"invalid_snowflake"}', content_type="application/json")

    cache: TtlCache = request.app["cache"]
    cached = cache.get(f"bot:{bot_id}")
    if cached is not None:
        return web.json_response(cached)

    await record_abuse(request.app, _client_ip(request), bot_id)
    status, user_raw = await discord_get(request.app, f"/users/{bot_id}")
    if status == 404:
        raise web.HTTPNotFound(text='{"error":"not_found"}', content_type="application/json")
    if status == 503:
        raise web.HTTPServiceUnavailable(text='{"error":"token_missing"}', content_type="application/json")
    if status == 429:
        retry = int(user_raw.get("retry_after", 5)) if isinstance(user_raw, dict) else 5
        raise web.HTTPTooManyRequests(
            text='{"error":"discord_rate_limited","retry_after":%d}' % retry,
            content_type="application/json",
            headers={"Retry-After": str(retry)},
        )
    if status >= 400 or not isinstance(user_raw, dict):
        raise web.HTTPBadGateway(text='{"error":"upstream_error"}', content_type="application/json")

    user = shape_user(user_raw)
    app_raw = await fetch_application_rpc(request.app, bot_id)
    degraded = app_raw is None

    install = (app_raw or {}).get("install_params") or {}
    scopes = list(install.get("scopes") or [])
    perms = install.get("permissions")
    if perms is not None:
        perms = str(perms)

    flags = (app_raw or {}).get("flags")
    payload = {
        "user": user,
        "application": None
        if degraded
        else {
            "id": str(app_raw.get("id") or bot_id),
            "name": app_raw.get("name") or user["username"],
            "description": app_raw.get("description"),
            "icon": app_raw.get("icon"),
            "bot_public": app_raw.get("bot_public"),
            "bot_require_code_grant": app_raw.get("bot_require_code_grant"),
            "verify_key": None,
            "flags": flags,
            "tags": list(app_raw.get("tags") or []),
            "install_params": {
                "scopes": scopes,
                "permissions": perms or "0",
            }
            if install
            else None,
            "approximate_guild_count": app_raw.get("approximate_guild_count"),
        },
        "scopes": scopes,
        "permissions": perms,
        "permissions_names": permission_names(perms),
        "intents": intents_from_flags(flags if isinstance(flags, int) else None),
        "degraded": degraded,
    }
    cache.set(f"bot:{bot_id}", payload, USER_CACHE_TTL)
    return web.json_response(payload)


async def handle_server(request: web.Request) -> web.Response:
    raw = request.match_info["code"]
    code = normalize_invite(raw)
    if not code:
        raise web.HTTPBadRequest(
            text='{"error":"invite_required","message":"Server lookup accepts invite codes only"}',
            content_type="application/json",
        )

    cache: TtlCache = request.app["cache"]
    cached = cache.get(f"invite:{code}")
    if cached is not None:
        return web.json_response(cached)

    await record_abuse(request.app, _client_ip(request), code)
    status, data = await discord_get(
        request.app,
        f"/invites/{code}?with_counts=true&with_expiration=true",
    )
    if status == 404:
        raise web.HTTPNotFound(text='{"error":"not_found"}', content_type="application/json")
    if status == 503:
        raise web.HTTPServiceUnavailable(text='{"error":"token_missing"}', content_type="application/json")
    if status == 429:
        retry = int(data.get("retry_after", 5)) if isinstance(data, dict) else 5
        raise web.HTTPTooManyRequests(
            text='{"error":"discord_rate_limited","retry_after":%d}' % retry,
            content_type="application/json",
            headers={"Retry-After": str(retry)},
        )
    if status >= 400 or not isinstance(data, dict) or not data.get("guild"):
        raise web.HTTPBadGateway(text='{"error":"upstream_error"}', content_type="application/json")

    guild = data["guild"]
    guild_id = str(guild["id"])
    inviter = data.get("inviter")
    channel = data.get("channel")
    payload = {
        "code": data.get("code") or code,
        "expires_at": data.get("expires_at"),
        "approximate_member_count": data.get("approximate_member_count"),
        "approximate_presence_count": data.get("approximate_presence_count"),
        "inviter": None
        if not inviter
        else {
            "id": str(inviter.get("id")),
            "username": inviter.get("username"),
            "global_name": inviter.get("global_name"),
            "avatar": inviter.get("avatar"),
        },
        "channel": None
        if not channel
        else {
            "id": str(channel.get("id")),
            "name": channel.get("name"),
            "type": channel.get("type"),
        },
        "guild": {
            "id": guild_id,
            "name": guild.get("name"),
            "description": guild.get("description"),
            "icon": guild.get("icon"),
            "splash": guild.get("splash"),
            "banner": guild.get("banner"),
            "features": list(guild.get("features") or []),
            "verification_level": guild.get("verification_level"),
            "nsfw_level": guild.get("nsfw_level"),
            "premium_subscription_count": guild.get("premium_subscription_count"),
            "icon_url": guild_asset_url("icons", guild_id, guild.get("icon")),
            "splash_url": guild_asset_url("splashes", guild_id, guild.get("splash")),
            "banner_url": guild_asset_url("banners", guild_id, guild.get("banner")),
        },
    }
    cache.set(f"invite:{code}", payload, INVITE_CACHE_TTL)
    return web.json_response(payload)


async def handle_cdn_proxy(request: web.Request) -> web.StreamResponse:
    kind = request.match_info["kind"]
    asset_id = request.match_info["id"]
    asset_hash = request.match_info["hash"]
    if kind not in {"avatar", "banner", "icon", "splash"}:
        raise web.HTTPBadRequest(text='{"error":"invalid_kind"}', content_type="application/json")
    if not SNOWFLAKE_RE.match(asset_id) or not re.match(r"^[A-Za-z0-9_]+$", asset_hash):
        raise web.HTTPBadRequest(text='{"error":"invalid_asset"}', content_type="application/json")

    size = request.rel_url.query.get("size", "512")
    fmt = request.rel_url.query.get("format")
    if not fmt:
        fmt = "gif" if asset_hash.startswith("a_") else "png"
    folder = {
        "avatar": "avatars",
        "banner": "banners",
        "icon": "icons",
        "splash": "splashes",
    }[kind]
    url = f"{CDN}/{folder}/{asset_id}/{asset_hash}.{fmt}?size={size}"
    session: ClientSession = request.app["http"]
    async with session.get(url, headers={"User-Agent": "CheterinLookup/1.0"}) as upstream:
        if upstream.status >= 400:
            raise web.HTTPBadGateway(text='{"error":"cdn_error"}', content_type="application/json")
        body = await upstream.read()
        content_type = upstream.headers.get("Content-Type", "application/octet-stream")
        filename = f"{kind}-{asset_id}.{fmt}"
        return web.Response(
            body=body,
            content_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "public, max-age=300",
            },
        )


def load_plugins(*, quiet: bool = False) -> list[dict[str, Any]]:
    path = _HERE / "plugins.json"
    if not path.exists():
        if not quiet:
            log.warning("plugins.json missing at %s", path)
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        plugins = list(data.get("plugins") or [])
        if not quiet:
            log.info("Loaded %d plugin catalog entries from %s", len(plugins), path)
        return plugins
    except Exception:  # noqa: BLE001
        log.exception("Failed to load plugins.json from %s", path)
        return []


async def on_startup(app: web.Application) -> None:
    app["http"] = ClientSession(timeout=ClientTimeout(total=20))


async def on_cleanup(app: web.Application) -> None:
    session: ClientSession = app["http"]
    await session.close()


def create_app() -> web.Application:
    # Prefer LOOKUP_DISCORD_TOKENS (comma-list); fall back to LOOKUP_DISCORD_TOKEN (single).
    raw_multi = os.getenv("LOOKUP_DISCORD_TOKENS", "").strip()
    raw_single = os.getenv("LOOKUP_DISCORD_TOKEN", "").strip()
    if raw_multi:
        tokens = [t.strip() for t in raw_multi.split(",") if t.strip()]
    elif raw_single:
        tokens = [raw_single]
    else:
        tokens = []
    # Guardrail: never silently fall back to BOT_TOKEN
    if not tokens and os.getenv("BOT_TOKEN"):
        log.warning("BOT_TOKEN is set but LOOKUP_DISCORD_TOKEN(S) is missing - Lookup will not use BOT_TOKEN")

    pool = TokenPool(tokens)
    app = web.Application(middlewares=[rate_limit_middleware])
    app["token_pool"] = pool
    app["token"] = tokens[0] if tokens else ""  # kept for legacy access
    app["cache"] = TtlCache()
    app["limiter"] = RateLimiter()
    app["abuse_logs"] = deque()
    app["plugins"] = load_plugins()

    app.router.add_get("/api/lookup/health", handle_health)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/api/lookup/config", handle_config)
    app.router.add_get("/api/lookup/plugins", handle_plugins)
    app.router.add_get("/api/lookup/dsa", handle_dsa_meta)
    app.router.add_get("/api/lookup/dsa/{id}", handle_dsa)
    app.router.add_post("/api/lookup/captcha/verify", handle_captcha_verify)
    app.router.add_get("/api/lookup/user/{id}", handle_user)
    app.router.add_get("/api/lookup/bot/{id}", handle_bot)
    app.router.add_get("/api/lookup/server/{code}", handle_server)
    app.router.add_get("/api/lookup/cdn/{kind}/{id}/{hash}", handle_cdn_proxy)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    host = os.getenv("LOOKUP_API_HOST", "127.0.0.1")
    port = int(os.getenv("LOOKUP_API_PORT", "8090"))
    app = create_app()
    pool: TokenPool = app["token_pool"]
    if not pool:
        log.warning("No LOOKUP_DISCORD_TOKEN(S) configured - Discord routes will return 503")
    else:
        log.info("Token pool loaded: %d token(s) configured", len(pool))
    web.run_app(app, host=host, port=port, print=lambda msg: log.info("%s", msg))


if __name__ == "__main__":
    main()
