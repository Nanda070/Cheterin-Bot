# Дашборд, Фаза 1 (Фундамент) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Embed an aiohttp web server + Discord OAuth2 login + a React dashboard shell into the existing bot process, so staff can authenticate and reach a protected (but still empty) dashboard.

**Architecture:** One process, one asyncio event loop — `main.py` starts an aiohttp `AppRunner` (non-blocking `TCPSite`) before `await bot.start(token)`, so both share the loop with no IPC. The web layer reads member/role data straight from the bot's live cache. React (Vite+TS+Tailwind) talks to it only through `/api/*` JSON routes.

**Tech Stack:** Python: `aiohttp`, `aiohttp-session` (`EncryptedCookieStorage`), `cryptography`, `pytest` + `pytest-aiohttp`. Frontend: Vite, React, TypeScript, Tailwind CSS v4 (`@tailwindcss/vite`), React Router, Vitest + Testing Library.

## Global Constraints

- All work happens in the working copy `C:\Users\adnan\Documents\coding\ChetMain_backup_20260701_211729`. Never touch `C:\Users\adnan\Documents\coding\ChetMain`.
- **Local-only git repo, commits expected.** A git repo was initialized inside this working copy specifically for implementing this plan (decision made after this plan was first written) — it has no remote and is never pushed anywhere; it does not touch the original `ChetMain` repo. Every task below should end with a normal `git add` + `git commit` for that task's changes, same as any other subagent-driven-development plan. Any "Verify (no commit)" step text still present below is stale — commit instead.
- Discord OAuth2 test credentials (test bot token, `DISCORD_CLIENT_ID=1521957442315878430`, `DISCORD_CLIENT_SECRET`) go into the working copy's `.env` only, during Task 8. Never print them to logs or commit them anywhere.
- Access is role-gated: `DASHBOARD_ACCESS_ROLE_IDS=1324239354209632357,1324239354209632358,1505359848433516734` (Kapo, Moderator, CTD) **or** Discord `guild_permissions.administrator == True`.
- Dashboard failing to start must never crash the bot (spec: "Раздел 4 — Обработка ошибок").
- Spec of record: `docs/superpowers/specs/2026-07-01-dashboard-phase1-foundation-design.md` in this same working copy.

---

### Task 1: Backend project scaffolding + config validation

**Files:**
- Create: `dashboard/__init__.py` (empty)
- Create: `dashboard/backend/__init__.py` (empty)
- Create: `dashboard/backend/config.py`
- Create: `dashboard/backend/tests/__init__.py` (empty)
- Create: `dashboard/backend/tests/test_config.py`
- Create: `requirements.txt`
- Create: `pytest.ini`

**Interfaces:**
- Produces: `class ConfigError(Exception)`, `@dataclass(frozen=True) class DashboardConfig(port: int, client_id: str, client_secret: str, redirect_uri: str, session_secret: str, access_role_ids: frozenset[str])`, `def load_dashboard_config(env: dict) -> DashboardConfig` (raises `ConfigError` on invalid input).

- [ ] **Step 1: Create `requirements.txt`**

```
discord.py>=2.7.1
python-dotenv>=1.0.1
aiohttp-session>=2.12
cryptography>=42.0
pytest>=8.0
pytest-aiohttp>=1.0
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: all packages install without errors (discord.py/python-dotenv may already be satisfied).

- [ ] **Step 3: Create `pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
testpaths = dashboard/backend/tests
```

- [ ] **Step 4: Create empty package files**

Create `dashboard/__init__.py`, `dashboard/backend/__init__.py`, `dashboard/backend/tests/__init__.py` — all empty files.

- [ ] **Step 5: Write the failing test**

`dashboard/backend/tests/test_config.py`:

```python
import pytest

from dashboard.backend.config import ConfigError, load_dashboard_config

VALID_ENV = {
    "DASHBOARD_PORT": "8080",
    "DISCORD_CLIENT_ID": "123",
    "DISCORD_CLIENT_SECRET": "secret",
    "DISCORD_OAUTH_REDIRECT_URI": "http://localhost:8080/api/auth/discord/callback",
    "SESSION_SECRET": "x" * 32,
    "DASHBOARD_ACCESS_ROLE_IDS": "1324239354209632357,1324239354209632358",
}


def test_loads_valid_config():
    config = load_dashboard_config(VALID_ENV)
    assert config.port == 8080
    assert config.client_id == "123"
    assert config.access_role_ids == frozenset({"1324239354209632357", "1324239354209632358"})


def test_missing_required_var_raises():
    env = dict(VALID_ENV)
    del env["DISCORD_CLIENT_ID"]
    with pytest.raises(ConfigError, match="DISCORD_CLIENT_ID"):
        load_dashboard_config(env)


def test_invalid_port_raises():
    env = dict(VALID_ENV, DASHBOARD_PORT="not-a-number")
    with pytest.raises(ConfigError, match="DASHBOARD_PORT"):
        load_dashboard_config(env)


def test_short_session_secret_raises():
    env = dict(VALID_ENV, SESSION_SECRET="short")
    with pytest.raises(ConfigError, match="SESSION_SECRET"):
        load_dashboard_config(env)


def test_empty_role_list_raises():
    env = dict(VALID_ENV, DASHBOARD_ACCESS_ROLE_IDS="")
    with pytest.raises(ConfigError, match="DASHBOARD_ACCESS_ROLE_IDS"):
        load_dashboard_config(env)
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.config'`

- [ ] **Step 7: Implement `dashboard/backend/config.py`**

```python
from dataclasses import dataclass


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class DashboardConfig:
    port: int
    client_id: str
    client_secret: str
    redirect_uri: str
    session_secret: str
    access_role_ids: frozenset


REQUIRED_KEYS = (
    "DASHBOARD_PORT",
    "DISCORD_CLIENT_ID",
    "DISCORD_CLIENT_SECRET",
    "DISCORD_OAUTH_REDIRECT_URI",
    "SESSION_SECRET",
    "DASHBOARD_ACCESS_ROLE_IDS",
)


def load_dashboard_config(env: dict) -> DashboardConfig:
    missing = [key for key in REQUIRED_KEYS if not env.get(key)]
    if missing:
        raise ConfigError(f"Missing required env vars: {', '.join(missing)}")

    try:
        port = int(env["DASHBOARD_PORT"])
    except ValueError as exc:
        raise ConfigError(
            f"DASHBOARD_PORT must be an integer, got {env['DASHBOARD_PORT']!r}"
        ) from exc

    role_ids = frozenset(
        role_id.strip()
        for role_id in env["DASHBOARD_ACCESS_ROLE_IDS"].split(",")
        if role_id.strip()
    )
    if not role_ids:
        raise ConfigError("DASHBOARD_ACCESS_ROLE_IDS must contain at least one role id")

    session_secret = env["SESSION_SECRET"]
    if len(session_secret) < 32:
        raise ConfigError("SESSION_SECRET must be at least 32 characters long")

    return DashboardConfig(
        port=port,
        client_id=env["DISCORD_CLIENT_ID"],
        client_secret=env["DISCORD_CLIENT_SECRET"],
        redirect_uri=env["DISCORD_OAUTH_REDIRECT_URI"],
        session_secret=session_secret,
        access_role_ids=role_ids,
    )
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_config.py -v`
Expected: PASS (5 tests)

- [ ] **Step 9: Verify (no commit — see Global Constraints)**

Confirm all 5 tests pass. Do not run `git add`/`git commit`.

---

### Task 2: Access control (`has_dashboard_access`)

**Files:**
- Create: `dashboard/backend/access.py`
- Create: `dashboard/backend/tests/test_access.py`

**Interfaces:**
- Consumes: nothing from Task 1 directly (pure function, only needs `frozenset[str]`).
- Produces: `def has_dashboard_access(member, allowed_role_ids: frozenset) -> bool`. `member` is any object with `.roles` (iterable of objects with `.id`) and `.guild_permissions.administrator` (bool) — matches `discord.Member`'s shape.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_access.py`:

```python
from dashboard.backend.access import has_dashboard_access


class FakeRole:
    def __init__(self, role_id):
        self.id = role_id


class FakePermissions:
    def __init__(self, administrator):
        self.administrator = administrator


class FakeMember:
    def __init__(self, role_ids, administrator=False):
        self.roles = [FakeRole(r) for r in role_ids]
        self.guild_permissions = FakePermissions(administrator)


ALLOWED = frozenset({"1324239354209632357", "1324239354209632358"})


def test_member_with_allowed_role_has_access():
    member = FakeMember([1324239354209632358])
    assert has_dashboard_access(member, ALLOWED) is True


def test_member_without_allowed_role_denied():
    member = FakeMember([999])
    assert has_dashboard_access(member, ALLOWED) is False


def test_administrator_always_has_access():
    member = FakeMember([999], administrator=True)
    assert has_dashboard_access(member, ALLOWED) is True


def test_member_with_no_roles_denied():
    member = FakeMember([])
    assert has_dashboard_access(member, ALLOWED) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_access.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.access'`

- [ ] **Step 3: Implement `dashboard/backend/access.py`**

```python
def has_dashboard_access(member, allowed_role_ids: frozenset) -> bool:
    if member.guild_permissions.administrator:
        return True
    member_role_ids = {str(role.id) for role in member.roles}
    return not member_role_ids.isdisjoint(allowed_role_ids)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_access.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Verify (no commit)**

---

### Task 3: Guild member lookup with graceful degradation

**Files:**
- Create: `dashboard/backend/member_lookup.py`
- Create: `dashboard/backend/tests/test_member_lookup.py`

**Interfaces:**
- Produces: `class MemberLookupResult(member=None, not_found=False, service_error=False)`, `async def resolve_guild_member(bot, guild_id: int, user_id: int) -> MemberLookupResult`. Later tasks (auth routes) call this instead of touching `bot`/`guild` directly.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_member_lookup.py`:

```python
import discord
import pytest

from dashboard.backend.member_lookup import resolve_guild_member


class _StubNotFound(discord.NotFound):
    def __init__(self):
        pass  # bypass real HTTPException.__init__, we don't need a real HTTP response


class _StubHTTPException(discord.HTTPException):
    def __init__(self):
        pass


class FakeGuild:
    def __init__(self, cached_member=None, fetch_result=None, fetch_raises=None):
        self._cached_member = cached_member
        self._fetch_result = fetch_result
        self._fetch_raises = fetch_raises

    def get_member(self, user_id):
        return self._cached_member

    async def fetch_member(self, user_id):
        if self._fetch_raises:
            raise self._fetch_raises
        return self._fetch_result


class FakeBot:
    def __init__(self, guild):
        self._guild = guild

    def get_guild(self, guild_id):
        return self._guild


@pytest.mark.asyncio
async def test_returns_cached_member_without_fetching():
    guild = FakeGuild(cached_member="member-from-cache")
    bot = FakeBot(guild)
    result = await resolve_guild_member(bot, 1, 42)
    assert result.member == "member-from-cache"
    assert result.not_found is False
    assert result.service_error is False


@pytest.mark.asyncio
async def test_falls_back_to_fetch_when_not_cached():
    guild = FakeGuild(cached_member=None, fetch_result="member-from-fetch")
    bot = FakeBot(guild)
    result = await resolve_guild_member(bot, 1, 42)
    assert result.member == "member-from-fetch"


@pytest.mark.asyncio
async def test_not_found_when_fetch_raises_notfound():
    guild = FakeGuild(cached_member=None, fetch_raises=_StubNotFound())
    bot = FakeBot(guild)
    result = await resolve_guild_member(bot, 1, 42)
    assert result.member is None
    assert result.not_found is True
    assert result.service_error is False


@pytest.mark.asyncio
async def test_service_error_when_fetch_raises_http_exception():
    guild = FakeGuild(cached_member=None, fetch_raises=_StubHTTPException())
    bot = FakeBot(guild)
    result = await resolve_guild_member(bot, 1, 42)
    assert result.member is None
    assert result.service_error is True


@pytest.mark.asyncio
async def test_service_error_when_guild_missing():
    bot = FakeBot(guild=None)
    result = await resolve_guild_member(bot, 1, 42)
    assert result.service_error is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_member_lookup.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.member_lookup'`

- [ ] **Step 3: Implement `dashboard/backend/member_lookup.py`**

```python
import discord


class MemberLookupResult:
    def __init__(self, member=None, not_found=False, service_error=False):
        self.member = member
        self.not_found = not_found
        self.service_error = service_error


async def resolve_guild_member(bot, guild_id: int, user_id: int) -> MemberLookupResult:
    guild = bot.get_guild(guild_id)
    if guild is None:
        return MemberLookupResult(service_error=True)

    member = guild.get_member(user_id)
    if member is not None:
        return MemberLookupResult(member=member)

    try:
        member = await guild.fetch_member(user_id)
        return MemberLookupResult(member=member)
    except discord.NotFound:
        return MemberLookupResult(not_found=True)
    except discord.HTTPException:
        return MemberLookupResult(service_error=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_member_lookup.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Verify (no commit)**

---

### Task 4: Discord OAuth2 HTTP calls (token exchange + identity)

**Files:**
- Create: `dashboard/backend/discord_oauth.py`
- Create: `dashboard/backend/tests/test_discord_oauth.py`

**Interfaces:**
- Produces: `DISCORD_API_BASE` constant, `class DiscordOAuthError(Exception)`, `async def exchange_code_for_token(session, code, client_id, client_secret, redirect_uri, api_base=DISCORD_API_BASE) -> dict`, `async def fetch_discord_identity(session, access_token, api_base=DISCORD_API_BASE) -> dict`. Both accept `api_base` so tests point at a local stub server instead of real Discord.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_discord_oauth.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_discord_oauth.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.discord_oauth'`

- [ ] **Step 3: Implement `dashboard/backend/discord_oauth.py`**

```python
import aiohttp

DISCORD_API_BASE = "https://discord.com/api/v10"


class DiscordOAuthError(Exception):
    pass


async def exchange_code_for_token(
    session: aiohttp.ClientSession,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    api_base: str = DISCORD_API_BASE,
) -> dict:
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    async with session.post(f"{api_base}/oauth2/token", data=data) as resp:
        if resp.status != 200:
            raise DiscordOAuthError(f"Token exchange failed with status {resp.status}")
        return await resp.json()


async def fetch_discord_identity(
    session: aiohttp.ClientSession,
    access_token: str,
    api_base: str = DISCORD_API_BASE,
) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with session.get(f"{api_base}/users/@me", headers=headers) as resp:
        if resp.status != 200:
            raise DiscordOAuthError(f"Fetching identity failed with status {resp.status}")
        return await resp.json()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_discord_oauth.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Verify (no commit)**

---

### Task 5: Session cookie setup (`EncryptedCookieStorage`)

**Files:**
- Create: `dashboard/backend/session.py`
- Create: `dashboard/backend/tests/test_session.py`

**Interfaces:**
- Produces: `def derive_fernet_key(secret: str) -> bytes`, `def setup_session(app, session_secret: str) -> None`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_session.py`:

```python
from cryptography.fernet import Fernet

from dashboard.backend.session import derive_fernet_key


def test_derive_fernet_key_is_valid_fernet_key():
    key = derive_fernet_key("any-length-secret-works-fine")
    Fernet(key)  # raises ValueError if not a valid 32-byte urlsafe-base64 key


def test_derive_fernet_key_is_deterministic():
    assert derive_fernet_key("same-secret") == derive_fernet_key("same-secret")


def test_derive_fernet_key_differs_per_secret():
    assert derive_fernet_key("secret-one") != derive_fernet_key("secret-two")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_session.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.session'`

- [ ] **Step 3: Implement `dashboard/backend/session.py`**

```python
import base64
import hashlib

from aiohttp import web
from aiohttp_session import setup as setup_aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage


def derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def setup_session(app: web.Application, session_secret: str) -> None:
    storage = EncryptedCookieStorage(derive_fernet_key(session_secret), cookie_name="chetbot_dashboard_session")
    setup_aiohttp_session(app, storage)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_session.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Verify (no commit)**

---

### Task 6: Auth routes (`login`, `callback`, `logout`, `me`)

**Files:**
- Create: `dashboard/backend/auth.py`
- Create: `dashboard/backend/tests/test_auth.py`

**Interfaces:**
- Consumes: `DashboardConfig` (Task 1), `has_dashboard_access` (Task 2), `resolve_guild_member`/`MemberLookupResult` (Task 3), `exchange_code_for_token`/`fetch_discord_identity`/`DiscordOAuthError` (Task 4), `setup_session` (Task 5).
- Produces: `routes = web.RouteTableDef()` with `GET /api/auth/login`, `GET /api/auth/discord/callback`, `POST /api/auth/logout`, `GET /api/auth/me`. Expects `request.app["bot"]`, `request.app["dashboard_config"]`, `request.app["guild_id"]`, `request.app["http_session"]` to be set (Task 7 wires these).

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_auth.py`:

```python
import pytest
from aiohttp import web
from aiohttp_session import get_session

from dashboard.backend.auth import routes
from dashboard.backend.config import DashboardConfig
from dashboard.backend.session import setup_session

CONFIG = DashboardConfig(
    port=8080,
    client_id="test-client-id",
    client_secret="test-client-secret",
    redirect_uri="http://localhost:8080/api/auth/discord/callback",
    session_secret="x" * 32,
    access_role_ids=frozenset({"111"}),
)


class FakeRole:
    def __init__(self, role_id):
        self.id = role_id


class FakePermissions:
    def __init__(self, administrator=False):
        self.administrator = administrator


class FakeMember:
    def __init__(self, member_id, role_ids, administrator=False):
        self.id = member_id
        self.name = "tester"
        self.display_avatar = None
        self.roles = [FakeRole(r) for r in role_ids]
        self.guild_permissions = FakePermissions(administrator)


class FakeGuild:
    def __init__(self, member=None):
        self._member = member

    def get_member(self, user_id):
        return self._member

    async def fetch_member(self, user_id):
        return self._member


class FakeBot:
    def __init__(self, guild):
        self._guild = guild

    def get_guild(self, guild_id):
        return self._guild


def make_app(bot, http_session_stub):
    app = web.Application()
    app["bot"] = bot
    app["dashboard_config"] = CONFIG
    app["guild_id"] = 1
    app["http_session"] = http_session_stub
    setup_session(app, CONFIG.session_secret)
    app.add_routes(routes)
    return app


class _NullHttpSession:
    """Placeholder; overridden per-test via monkeypatch on discord_oauth functions."""


@pytest.mark.asyncio
async def test_login_redirects_to_discord_and_sets_state_cookie(aiohttp_client):
    app = make_app(FakeBot(FakeGuild()), _NullHttpSession())
    client = await aiohttp_client(app)
    resp = await client.get("/api/auth/login", allow_redirects=False)
    assert resp.status == 302
    assert "discord.com/api/oauth2/authorize" in resp.headers["Location"]
    assert "oauth_state" in resp.cookies


@pytest.mark.asyncio
async def test_me_without_session_returns_401(aiohttp_client):
    app = make_app(FakeBot(FakeGuild()), _NullHttpSession())
    client = await aiohttp_client(app)
    resp = await client.get("/api/auth/me")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_callback_denies_when_role_missing(aiohttp_client, monkeypatch):
    import dashboard.backend.auth as auth_module

    async def fake_exchange(*args, **kwargs):
        return {"access_token": "tok"}

    async def fake_identity(*args, **kwargs):
        return {"id": "999"}

    monkeypatch.setattr(auth_module, "exchange_code_for_token", fake_exchange)
    monkeypatch.setattr(auth_module, "fetch_discord_identity", fake_identity)

    member_without_role = FakeMember(999, role_ids=[])
    app = make_app(FakeBot(FakeGuild(member_without_role)), _NullHttpSession())
    client = await aiohttp_client(app)

    login_resp = await client.get("/api/auth/login", allow_redirects=False)
    state_cookie = login_resp.cookies["oauth_state"].value

    resp = await client.get(
        f"/api/auth/discord/callback?code=abc&state={state_cookie}",
        allow_redirects=False,
    )
    assert resp.status == 302
    assert "/access-denied" in resp.headers["Location"]


@pytest.mark.asyncio
async def test_callback_succeeds_and_me_returns_user(aiohttp_client, monkeypatch):
    import dashboard.backend.auth as auth_module

    async def fake_exchange(*args, **kwargs):
        return {"access_token": "tok"}

    async def fake_identity(*args, **kwargs):
        return {"id": "111"}

    monkeypatch.setattr(auth_module, "exchange_code_for_token", fake_exchange)
    monkeypatch.setattr(auth_module, "fetch_discord_identity", fake_identity)

    member_with_role = FakeMember(111, role_ids=[111])
    app = make_app(FakeBot(FakeGuild(member_with_role)), _NullHttpSession())
    client = await aiohttp_client(app)

    login_resp = await client.get("/api/auth/login", allow_redirects=False)
    state_cookie = login_resp.cookies["oauth_state"].value

    callback_resp = await client.get(
        f"/api/auth/discord/callback?code=abc&state={state_cookie}",
        allow_redirects=False,
    )
    assert callback_resp.status == 302
    assert callback_resp.headers["Location"] == "/"

    me_resp = await client.get("/api/auth/me")
    assert me_resp.status == 200
    body = await me_resp.json()
    assert body["id"] == "111"


@pytest.mark.asyncio
async def test_logout_clears_session(aiohttp_client, monkeypatch):
    import dashboard.backend.auth as auth_module

    async def fake_exchange(*args, **kwargs):
        return {"access_token": "tok"}

    async def fake_identity(*args, **kwargs):
        return {"id": "111"}

    monkeypatch.setattr(auth_module, "exchange_code_for_token", fake_exchange)
    monkeypatch.setattr(auth_module, "fetch_discord_identity", fake_identity)

    member_with_role = FakeMember(111, role_ids=[111])
    app = make_app(FakeBot(FakeGuild(member_with_role)), _NullHttpSession())
    client = await aiohttp_client(app)

    login_resp = await client.get("/api/auth/login", allow_redirects=False)
    state_cookie = login_resp.cookies["oauth_state"].value
    await client.get(
        f"/api/auth/discord/callback?code=abc&state={state_cookie}",
        allow_redirects=False,
    )

    logout_resp = await client.post("/api/auth/logout")
    assert logout_resp.status == 200

    me_resp = await client.get("/api/auth/me")
    assert me_resp.status == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_auth.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.auth'`

- [ ] **Step 3: Implement `dashboard/backend/auth.py`**

```python
import secrets

from aiohttp import web
from aiohttp_session import get_session

from .discord_oauth import DiscordOAuthError, exchange_code_for_token, fetch_discord_identity
from .access import has_dashboard_access
from .member_lookup import resolve_guild_member

routes = web.RouteTableDef()

STATE_COOKIE_NAME = "oauth_state"
DISCORD_AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"


@routes.get("/api/auth/login")
async def login(request: web.Request) -> web.Response:
    config = request.app["dashboard_config"]
    state = secrets.token_urlsafe(32)
    authorize_url = (
        f"{DISCORD_AUTHORIZE_URL}?client_id={config.client_id}"
        f"&redirect_uri={config.redirect_uri}"
        f"&response_type=code&scope=identify&state={state}"
    )
    response = web.HTTPFound(authorize_url)
    response.set_cookie(STATE_COOKIE_NAME, state, httponly=True, max_age=600)
    return response


@routes.get("/api/auth/discord/callback")
async def callback(request: web.Request) -> web.Response:
    config = request.app["dashboard_config"]
    bot = request.app["bot"]
    guild_id = request.app["guild_id"]

    if request.query.get("error"):
        return web.HTTPFound("/login?auth_error=denied")

    code = request.query.get("code")
    returned_state = request.query.get("state")
    cookie_state = request.cookies.get(STATE_COOKIE_NAME)
    if (
        not code
        or not returned_state
        or not cookie_state
        or not secrets.compare_digest(returned_state, cookie_state)
    ):
        return web.HTTPFound("/login?auth_error=state_mismatch")

    http_session = request.app["http_session"]
    try:
        token_data = await exchange_code_for_token(
            http_session, code, config.client_id, config.client_secret, config.redirect_uri
        )
        identity = await fetch_discord_identity(http_session, token_data["access_token"])
    except DiscordOAuthError:
        return web.HTTPFound("/login?auth_error=oauth_failed")

    user_id = int(identity["id"])
    lookup = await resolve_guild_member(bot, guild_id, user_id)

    if lookup.service_error:
        return web.HTTPFound("/login?auth_error=service_unavailable")
    if lookup.not_found or lookup.member is None:
        return web.HTTPFound("/access-denied?reason=not_a_member")
    if not has_dashboard_access(lookup.member, config.access_role_ids):
        return web.HTTPFound("/access-denied?reason=insufficient_role")

    session = await get_session(request)
    session["discord_user_id"] = str(user_id)

    response = web.HTTPFound("/")
    response.del_cookie(STATE_COOKIE_NAME)
    return response


@routes.post("/api/auth/logout")
async def logout(request: web.Request) -> web.Response:
    session = await get_session(request)
    session.invalidate()
    return web.json_response({"ok": True})


@routes.get("/api/auth/me")
async def me(request: web.Request) -> web.Response:
    session = await get_session(request)
    user_id = session.get("discord_user_id")
    if not user_id:
        return web.json_response({"error": "unauthorized"}, status=401)

    config = request.app["dashboard_config"]
    bot = request.app["bot"]
    guild_id = request.app["guild_id"]

    lookup = await resolve_guild_member(bot, guild_id, int(user_id))
    if lookup.service_error:
        return web.json_response({"error": "service_unavailable"}, status=503)
    if lookup.not_found or lookup.member is None:
        return web.json_response({"error": "forbidden"}, status=403)
    if not has_dashboard_access(lookup.member, config.access_role_ids):
        return web.json_response({"error": "forbidden"}, status=403)

    member = lookup.member
    return web.json_response(
        {
            "id": str(member.id),
            "username": member.name,
            "avatar": str(member.display_avatar.url) if member.display_avatar else None,
            "is_admin": member.guild_permissions.administrator,
        }
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_auth.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Verify (no commit)**

---

### Task 7: `app.py` — wire routes, sessions, health check, graceful startup

**Files:**
- Create: `dashboard/backend/app.py`
- Create: `dashboard/backend/tests/test_app.py`

**Interfaces:**
- Consumes: `load_dashboard_config`/`ConfigError` (Task 1), `setup_session` (Task 5), `routes` (Task 6).
- Produces: `def create_app(bot, config, guild_id: int) -> web.Application`, `async def start_dashboard(bot, guild_id: int, env: dict | None = None) -> web.AppRunner | None`. `main.py` (Task 8) calls `start_dashboard`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_app.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_app.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.app'`

- [ ] **Step 3: Implement `dashboard/backend/app.py`**

```python
import logging
import os

import aiohttp
from aiohttp import web

from .auth import routes as auth_routes
from .config import ConfigError, DashboardConfig, load_dashboard_config
from .session import setup_session

logger = logging.getLogger("dashboard")


@web.middleware
async def json_error_middleware(request, handler):
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled dashboard error on %s", request.path)
        return web.json_response({"error": "internal_error"}, status=500)


def create_app(bot, config: DashboardConfig, guild_id: int) -> web.Application:
    app = web.Application(middlewares=[json_error_middleware])
    app["bot"] = bot
    app["dashboard_config"] = config
    app["guild_id"] = guild_id
    app["http_session"] = aiohttp.ClientSession()
    setup_session(app, config.session_secret)
    app.add_routes(auth_routes)

    async def health(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    app.router.add_get("/api/health", health)

    async def cleanup_http_session(cleanup_app: web.Application) -> None:
        await cleanup_app["http_session"].close()

    app.on_cleanup.append(cleanup_http_session)
    return app


async def start_dashboard(bot, guild_id: int, env: dict | None = None) -> web.AppRunner | None:
    env = env if env is not None else os.environ
    try:
        config = load_dashboard_config(env)
    except ConfigError as exc:
        logger.error("Dashboard disabled: %s", exc)
        return None

    app = create_app(bot, config, guild_id)
    runner = web.AppRunner(app)
    await runner.setup()
    try:
        site = web.TCPSite(runner, "0.0.0.0", config.port)
        await site.start()
    except OSError as exc:
        logger.error("Dashboard disabled: failed to bind port %s (%s)", config.port, exc)
        await runner.cleanup()
        return None

    logger.info("Dashboard listening on port %s", config.port)
    return runner
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_app.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Run the full backend test suite**

Run: `pytest dashboard/backend/tests/ -v`
Expected: all tests from Tasks 1–7 pass (20 tests total)

- [ ] **Step 6: Verify (no commit)**

---

### Task 8: Wire into `main.py` + add real `.env` values

**Files:**
- Modify: `main.py:80-91` (the `bot = ChetBot()` block through end of file)
- Modify: `.env` (append new keys)

**Interfaces:**
- Consumes: `start_dashboard` (Task 7).

- [ ] **Step 1: Append new keys to `.env`**

Add to the end of `.env` (`BOT_TOKEN`/`GUILD_ID` at the top of `.env` should be swapped to the test bot's token/guild for local dev — do this manually, it's already covered by "Согласен... Работай с бэкапом" from the conversation). **`DISCORD_CLIENT_SECRET` is a real secret — never write its literal value into this plan file or any other file under `docs/`; put it only in `.env`, which is gitignored in this working copy.**

```
# ==========================================
# ДАШБОРД (Фаза 1)
# ==========================================
DASHBOARD_PORT=8080
DISCORD_CLIENT_ID=1521957442315878430
DISCORD_CLIENT_SECRET=<взять из переписки с пользователем — тестовый Client Secret, не коммитить нигде>
DISCORD_OAUTH_REDIRECT_URI=http://localhost:8080/api/auth/discord/callback
SESSION_SECRET=<сгенерировать: python -c "import secrets; print(secrets.token_urlsafe(32))">
DASHBOARD_ACCESS_ROLE_IDS=1324239354209632357,1324239354209632358,1505359848433516734
```

Generate `SESSION_SECRET` by running: `python -c "import secrets; print(secrets.token_urlsafe(32))"` and paste the output in place of the placeholder.

- [ ] **Step 2: Replace the bottom of `main.py`**

Replace lines 80-91 (from `bot = ChetBot()` to the end of the file) with:

```python
bot = ChetBot()

@bot.event
async def on_ready():
    logging.getLogger("chetbot").info(f"{bot.user} запущен и готов к работе!")


async def main():
    guild_id_raw = os.getenv("GUILD_ID")
    if not guild_id_raw:
        raise RuntimeError("Переменная окружения GUILD_ID не задана.")
    guild_id = int(guild_id_raw)

    from dashboard.backend.app import start_dashboard

    dashboard_runner = await start_dashboard(bot, guild_id)

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана.")

    try:
        await bot.start(token)
    finally:
        if dashboard_runner is not None:
            await dashboard_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Add `import asyncio` if not already present**

`main.py` already has `import asyncio` at line 5 — confirm it's there, no change needed.

- [ ] **Step 4: Manual verification — bot still starts normally**

Run: `python main.py`
Expected: log line `<bot_name> запущен и готов к работе!` appears, and a log line `Dashboard listening on port 8080` appears. Stop with Ctrl+C.

- [ ] **Step 5: Manual verification — dashboard survives a port conflict**

In one terminal, run: `python -c "import socket; s = socket.socket(); s.bind(('0.0.0.0', 8080)); input('holding port, press enter to release...')"`
In another terminal, run: `python main.py`
Expected: log line `Dashboard disabled: failed to bind port 8080 (...)`, but the bot still logs `запущен и готов к работе!` and keeps running. Stop both processes.

- [ ] **Step 6: Verify (no commit)**

---

### Task 9: Frontend scaffolding (Vite + React + TS + Tailwind v4)

**Files:**
- Create: `dashboard/frontend/` (via `npm create vite@latest`)
- Modify: `dashboard/frontend/vite.config.ts`
- Modify: `dashboard/frontend/src/index.css` (or equivalent global stylesheet)

**Interfaces:**
- Produces: a running Vite dev server proxying `/api/*` to the backend port from Task 8.

- [ ] **Step 1: Scaffold the Vite project**

Run (from the working copy root):
```bash
npm create vite@latest dashboard/frontend -- --template react-ts
cd dashboard/frontend
npm install
```

- [ ] **Step 2: Add Tailwind CSS v4 via its Vite plugin**

Run: `npm install tailwindcss @tailwindcss/vite`

- [ ] **Step 3: Update `dashboard/frontend/vite.config.ts`**

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 4: Replace the contents of `dashboard/frontend/src/index.css`**

```css
@import "tailwindcss";

body {
  background-color: #020617;
}
```

- [ ] **Step 5: Manual verification**

Run (with the backend from Task 8 already running in another terminal): `cd dashboard/frontend && npm run dev`
Expected: Vite prints a local URL (e.g. `http://localhost:5173`); opening it in a browser shows the default Vite+React starter page with a dark background (confirms Tailwind is active).

- [ ] **Step 6: Verify (no commit)**

---

### Task 10: `api/client.ts` — typed fetch wrapper

**Files:**
- Create: `dashboard/frontend/src/api/client.ts`
- Create: `dashboard/frontend/src/api/client.test.ts`
- Modify: `dashboard/frontend/package.json` (add test dependencies + script)
- Create: `dashboard/frontend/src/setupTests.ts`

**Interfaces:**
- Produces: `interface DashboardUser { id, username, avatar, is_admin }`, `async function fetchCurrentUser(): Promise<DashboardUser | null>`, `async function logout(): Promise<void>`, `function loginUrl(): string`.

- [ ] **Step 1: Install Vitest and testing libraries**

Run (from `dashboard/frontend/`): `npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom`

- [ ] **Step 2: Add a `test` script to `package.json`**

Add to the `"scripts"` section of `dashboard/frontend/package.json`:
```json
"test": "vitest run"
```

- [ ] **Step 3: Extend `vite.config.ts` with Vitest config**

```ts
/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts',
  },
})
```

- [ ] **Step 4: Create `dashboard/frontend/src/setupTests.ts`**

```ts
import '@testing-library/jest-dom'
```

- [ ] **Step 5: Write the failing test**

`dashboard/frontend/src/api/client.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchCurrentUser, logout, loginUrl } from './client'

describe('client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns null when the API responds 401', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
    const user = await fetchCurrentUser()
    expect(user).toBeNull()
  })

  it('returns the user object when the API responds 200', async () => {
    const payload = { id: '1', username: 'tester', avatar: null, is_admin: false }
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => payload }),
    )
    const user = await fetchCurrentUser()
    expect(user).toEqual(payload)
  })

  it('throws on unexpected error statuses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }))
    await expect(fetchCurrentUser()).rejects.toThrow()
  })

  it('logout posts to the logout endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true })
    vi.stubGlobal('fetch', fetchMock)
    await logout()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auth/logout',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('loginUrl points at the login route', () => {
    expect(loginUrl()).toBe('/api/auth/login')
  })
})
```

- [ ] **Step 6: Run test to verify it fails**

Run: `npm run test`
Expected: FAIL — `Cannot find module './client'`

- [ ] **Step 7: Implement `dashboard/frontend/src/api/client.ts`**

```ts
export interface DashboardUser {
  id: string
  username: string
  avatar: string | null
  is_admin: boolean
}

export async function fetchCurrentUser(): Promise<DashboardUser | null> {
  const response = await fetch('/api/auth/me', { credentials: 'include' })
  if (response.status === 401 || response.status === 403) {
    return null
  }
  if (!response.ok) {
    throw new Error(`Failed to fetch current user: ${response.status}`)
  }
  return response.json()
}

export async function logout(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
}

export function loginUrl(): string {
  return '/api/auth/login'
}
```

- [ ] **Step 8: Run test to verify it passes**

Run: `npm run test`
Expected: PASS (5 tests)

- [ ] **Step 9: Verify (no commit)**

---

### Task 11: `AuthContext` + `ProtectedRoute`

**Files:**
- Create: `dashboard/frontend/src/context/AuthContext.tsx`
- Create: `dashboard/frontend/src/components/ProtectedRoute.tsx`
- Create: `dashboard/frontend/src/components/ProtectedRoute.test.tsx`
- Modify: `dashboard/frontend/package.json` (add `react-router-dom`)

**Interfaces:**
- Consumes: `fetchCurrentUser`, `DashboardUser` (Task 10).
- Produces: `function AuthProvider({ children }): JSX.Element`, `function useAuth(): { user: DashboardUser | null, isLoading: boolean, refresh: () => Promise<void> }`, `function ProtectedRoute({ children }): JSX.Element`.

- [ ] **Step 1: Install `react-router-dom`**

Run: `npm install react-router-dom`

- [ ] **Step 2: Implement `dashboard/frontend/src/context/AuthContext.tsx`**

```tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { fetchCurrentUser, type DashboardUser } from '../api/client'

interface AuthContextValue {
  user: DashboardUser | null
  isLoading: boolean
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<DashboardUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refresh = async () => {
    setIsLoading(true)
    try {
      setUser(await fetchCurrentUser())
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  return <AuthContext.Provider value={{ user, isLoading, refresh }}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
```

- [ ] **Step 3: Write the failing test for `ProtectedRoute`**

`dashboard/frontend/src/components/ProtectedRoute.test.tsx`:

```tsx
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../context/AuthContext'
import { ProtectedRoute } from './ProtectedRoute'

describe('ProtectedRoute', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('redirects to /login when there is no authenticated user', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<div>Login page</div>} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <div>Secret dashboard</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('Login page')).toBeInTheDocument())
  })

  it('renders children when a user is authenticated', async () => {
    const payload = { id: '1', username: 'tester', avatar: null, is_admin: false }
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => payload }),
    )

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<div>Login page</div>} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <div>Secret dashboard</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('Secret dashboard')).toBeInTheDocument())
  })
})
```

- [ ] **Step 4: Run test to verify it fails**

Run: `npm run test`
Expected: FAIL — `Cannot find module './ProtectedRoute'`

- [ ] **Step 5: Implement `dashboard/frontend/src/components/ProtectedRoute.tsx`**

```tsx
import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center text-slate-400">Загрузка...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `npm run test`
Expected: PASS (2 tests, plus the 5 from Task 10 — 7 total)

- [ ] **Step 7: Verify (no commit)**

---

### Task 12: Pages + routing (Login, AccessDenied, DashboardShell)

**Files:**
- Create: `dashboard/frontend/src/pages/Login.tsx`
- Create: `dashboard/frontend/src/pages/AccessDenied.tsx`
- Create: `dashboard/frontend/src/pages/DashboardShell.tsx`
- Modify: `dashboard/frontend/src/App.tsx`

**Interfaces:**
- Consumes: `AuthProvider`, `useAuth` (Task 11), `ProtectedRoute` (Task 11), `loginUrl`, `logout` (Task 10).

- [ ] **Step 1: Create `dashboard/frontend/src/pages/Login.tsx`**

```tsx
import { loginUrl } from '../api/client'

export function LoginPage() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-6 bg-slate-950 text-slate-100">
      <h1 className="text-2xl font-semibold">Панель управления ботом</h1>
      <a
        href={loginUrl()}
        className="rounded-lg bg-indigo-600 px-6 py-3 font-medium transition hover:bg-indigo-500"
      >
        Войти через Discord
      </a>
    </div>
  )
}
```

- [ ] **Step 2: Create `dashboard/frontend/src/pages/AccessDenied.tsx`**

```tsx
export function AccessDeniedPage() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-4 bg-slate-950 text-slate-100">
      <h1 className="text-2xl font-semibold">Доступ запрещён</h1>
      <p className="text-slate-400">У вас нет прав для просмотра этой панели.</p>
    </div>
  )
}
```

- [ ] **Step 3: Create `dashboard/frontend/src/pages/DashboardShell.tsx`**

```tsx
import { useAuth } from '../context/AuthContext'
import { logout } from '../api/client'

const SECTIONS = [
  'Feedback и тикеты',
  'Конструктор кнопок и эмбедов',
  'События и голосования',
  'Lockdown и модерация',
  'Участники и роли',
  'Конфигурация',
]

export function DashboardShell() {
  const { user, refresh } = useAuth()

  const handleLogout = async () => {
    await logout()
    await refresh()
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      <aside className="w-64 border-r border-slate-800 p-4">
        <nav className="flex flex-col gap-2">
          {SECTIONS.map((section) => (
            <div key={section} className="rounded-md px-3 py-2 text-slate-400">
              {section} <span className="text-xs">(скоро)</span>
            </div>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-6">
        <div className="flex items-center justify-between">
          <span>Вы вошли как {user?.username}</span>
          <button onClick={handleLogout} className="rounded-md bg-slate-800 px-4 py-2">
            Выйти
          </button>
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 4: Replace `dashboard/frontend/src/App.tsx`**

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/Login'
import { AccessDeniedPage } from './pages/AccessDenied'
import { DashboardShell } from './pages/DashboardShell'

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/access-denied" element={<AccessDeniedPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardShell />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
```

- [ ] **Step 5: Run the full frontend test suite**

Run: `npm run test`
Expected: all 7 tests from Tasks 10–11 still pass (this task adds no new automated tests — pages are verified manually in Task 13).

- [ ] **Step 6: Verify (no commit)**

---

### Task 13: Full end-to-end manual verification

**Files:** none (verification only, matches the spec's "Проверка (manual verification)" section).

- [ ] **Step 1: Start the backend**

Run: `python main.py` (from the working copy root, with the test bot's `.env` values from Task 8)
Expected: log shows the bot connected and `Dashboard listening on port 8080`.

- [ ] **Step 2: Start the frontend**

Run: `cd dashboard/frontend && npm run dev`
Expected: Vite dev server starts, prints its local URL.

- [ ] **Step 3: Confirm the login page renders**

Open the Vite URL in a browser.
Expected: "Панель управления ботом" with a "Войти через Discord" button.

- [ ] **Step 4: Log in with a Discord account that has an allowed role**

Click "Войти через Discord", authorize with a test-server account that has the Kapo, Moderator, or CTD role (or Administrator permission).
Expected: redirected back to the dashboard shell, showing the sidebar with the 6 placeholder sections and "Вы вошли как <username>".

- [ ] **Step 5: Confirm `/api/auth/me` returns the right shape**

Open browser dev tools → Network tab → find the `/api/auth/me` request.
Expected: 200 response with `{ id, username, avatar, is_admin }`.

- [ ] **Step 6: Log in with an account that has none of the allowed roles**

Log out, then log in again with a different test-server account without Kapo/Moderator/CTD/Administrator.
Expected: redirected to `/access-denied` showing "Доступ запрещён".

- [ ] **Step 7: Confirm logout clears the session**

While logged in with an authorized account, click "Выйти".
Expected: redirected/refreshed to the login page; reloading the dashboard URL directly also redirects to `/login` (no stale session).

- [ ] **Step 8: Confirm the bot survives a dashboard port conflict**

Re-run the check from Task 8 Step 5 (hold port 8080 with the throwaway `socket` script, then start `python main.py`).
Expected: bot logs "запущен и готов к работе!" even though the dashboard failed to bind.

- [ ] **Step 9: Record results**

No commit. If any step fails, note which one — this is the acceptance gate for Phase 1 before starting Phase 2.
