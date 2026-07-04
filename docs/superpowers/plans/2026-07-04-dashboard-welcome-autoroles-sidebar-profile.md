# Dashboard: Sidebar Profile Block, Welcome Toggles, Auto-Roles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the three pieces approved in `docs/superpowers/specs/2026-07-04-dashboard-welcome-autoroles-sidebar-profile-design.md` (commit `9f47af1`): a sidebar profile block, toggleable welcome channel/DM messages, and a new auto-role-on-join capability.

**Architecture:** Two new backend route files (`welcome.py`, `auto_roles.py`) reuse `bot_config.py`'s existing generic `load_config()`/`save_config()`/`get()` with three new keys that don't need to be added to `CONFIG_KEYS`/`LIST_KEYS` (those only govern the one-time env-var migration). The bot-side `welcome.py` (root) gets two new `if` guards around its existing sends, plus a new auto-role-granting block. Two new frontend pages and a sidebar addition to `DashboardShell.tsx` round it out.

**Tech Stack:** Python + aiohttp.web + discord.py (backend), React + TypeScript + Vite (frontend), pytest + pytest-asyncio (backend tests), Vitest + Testing Library (frontend tests).

## Global Constraints

- New `bot_config` keys: `WELCOME_CHANNEL_ENABLED` (bool, default `true`), `WELCOME_DM_ENABLED` (bool, default `true`), `AUTO_ROLE_IDS` (list of role-ID strings, default `[]`). None of these are added to `bot_config.py`'s `CONFIG_KEYS`/`LIST_KEYS` — those lists only govern env-var migration, and these three keys never existed as env vars.
- The welcome-channel toggle gates sending into the ALREADY-configured `WELCOME_CHANNEL_ID` (from the existing Конфигурация page) — it does not add a second channel picker.
- Auto-role assignability validation reuses the exact pattern already established in `dashboard/backend/routes/embed_builder.py`: not `@everyone` (`role.is_default()`), not `managed`, and `role.position < guild.me.top_role.position`.
- `welcome.py` (root, bot-side) changes get NO automated tests — event-listener cog code has zero pytest coverage anywhere in this project. Verification is a manual line-by-line diff review, per this project's standing convention.
- Every new backend route must be registered in `dashboard/backend/app.py`'s `create_app()` at the same time it's created — a prior feature in this project shipped a route file that was never registered, leaving it completely unreachable outside tests until a later review caught it. Do not defer registration to a later task.
- Both new routes are gated by the existing `require_dashboard_access` decorator, matching every other dashboard route.

---

## File Structure

- `dashboard/backend/routes/welcome.py` (new) — `GET`/`PUT /api/welcome-settings`.
- `dashboard/backend/routes/auto_roles.py` (new) — `GET`/`PUT /api/auto-roles`.
- `dashboard/backend/app.py` (modified) — registers both new route tables.
- `welcome.py` (modified, root) — bot-side toggle guards + auto-role granting.
- `dashboard/frontend/src/api/client.ts` (modified) — new types + functions.
- `dashboard/frontend/src/pages/Welcome.tsx` (new) — the toggle page.
- `dashboard/frontend/src/pages/AutoRoles.tsx` (new) — the role-checkbox page.
- `dashboard/frontend/src/pages/DashboardShell.tsx` (modified) — sidebar profile block + 2 nav entries.
- `dashboard/frontend/src/App.tsx` (modified) — 2 new routes.

---

### Task 1: `dashboard/backend/routes/welcome.py` — welcome-settings routes

**Files:**
- Create: `dashboard/backend/routes/welcome.py`
- Modify: `dashboard/backend/app.py` (import + `add_routes` call)
- Test: `dashboard/backend/tests/test_welcome_routes.py`

**Interfaces:**
- Consumes: `bot_config.load_config()`, `bot_config.save_config(data)`, `bot_config.get(key, default)` (existing, from `bot_config.py`).
- Produces: `GET /api/welcome-settings` → `{"channel_enabled": bool, "dm_enabled": bool}`; `PUT /api/welcome-settings` (body `{"channel_enabled": bool, "dm_enabled": bool}`) → same shape, persisted.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/backend/tests/test_welcome_routes.py`:

```python
import pytest

import bot_config
from dashboard.backend.routes.welcome import routes as welcome_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_config_file(tmp_path, monkeypatch):
    monkeypatch.setattr(bot_config, "CONFIG_FILE", str(tmp_path / "config.json"))


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    return guild, make_moderation_app(FakeBot(guild), [welcome_routes])


@pytest.mark.asyncio
async def test_get_welcome_settings_defaults_to_enabled_when_file_missing(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/welcome-settings")
    assert resp.status == 200
    assert (await resp.json()) == {"channel_enabled": True, "dm_enabled": True}


@pytest.mark.asyncio
async def test_get_welcome_settings_returns_stored_values(aiohttp_client):
    bot_config.save_config({"WELCOME_CHANNEL_ENABLED": False, "WELCOME_DM_ENABLED": True})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/welcome-settings")
    assert (await resp.json()) == {"channel_enabled": False, "dm_enabled": True}


@pytest.mark.asyncio
async def test_get_welcome_settings_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/welcome-settings")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_update_welcome_settings_persists(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/welcome-settings", json={"channel_enabled": False, "dm_enabled": False}
    )
    assert resp.status == 200
    assert (await resp.json()) == {"channel_enabled": False, "dm_enabled": False}
    assert bot_config.load_config()["WELCOME_CHANNEL_ENABLED"] is False
    assert bot_config.load_config()["WELCOME_DM_ENABLED"] is False


@pytest.mark.asyncio
async def test_update_welcome_settings_rejects_non_boolean(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/welcome-settings", json={"channel_enabled": "yes", "dm_enabled": True}
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_update_welcome_settings_rejects_non_dict_body(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/welcome-settings", data="[]", headers={"Content-Type": "application/json"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_update_welcome_settings_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.put("/api/welcome-settings", json={"channel_enabled": True, "dm_enabled": True})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_welcome_settings_route_is_registered_in_the_real_app(aiohttp_client):
    from dashboard.backend.app import create_app
    from dashboard.backend.config import load_dashboard_config

    class _FakeBot:
        def get_guild(self, guild_id):
            return None

    config = load_dashboard_config(
        {
            "DASHBOARD_PORT": "0",
            "DISCORD_CLIENT_ID": "id",
            "DISCORD_CLIENT_SECRET": "secret",
            "DISCORD_OAUTH_REDIRECT_URI": "http://localhost:8080/api/auth/discord/callback",
            "SESSION_SECRET": "x" * 32,
            "DASHBOARD_ACCESS_ROLE_IDS": "111",
        }
    )
    app = create_app(_FakeBot(), config, guild_id=1)
    client = await aiohttp_client(app)
    # 401 (not 404) proves the route is registered and reachable in the real
    # app, and that the dashboard-access auth gate — not a missing route —
    # is what's rejecting the unauthenticated request.
    resp = await client.get("/api/welcome-settings")
    assert resp.status == 401
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_welcome_routes.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dashboard.backend.routes.welcome'`, and the registration test fails because `create_app` never imports it.

- [ ] **Step 3: Implement the routes**

Create `dashboard/backend/routes/welcome.py`:

```python
from aiohttp import web

import bot_config

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/welcome-settings")
@require_dashboard_access
async def get_welcome_settings(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "channel_enabled": bool(bot_config.get("WELCOME_CHANNEL_ENABLED", True)),
            "dm_enabled": bool(bot_config.get("WELCOME_DM_ENABLED", True)),
        }
    )


@routes.put("/api/welcome-settings")
@require_dashboard_access
async def update_welcome_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    channel_enabled = body.get("channel_enabled")
    dm_enabled = body.get("dm_enabled")
    if not isinstance(channel_enabled, bool) or not isinstance(dm_enabled, bool):
        return web.json_response({"error": "invalid_request"}, status=400)

    data = bot_config.load_config()
    data["WELCOME_CHANNEL_ENABLED"] = channel_enabled
    data["WELCOME_DM_ENABLED"] = dm_enabled
    bot_config.save_config(data)

    return web.json_response({"channel_enabled": channel_enabled, "dm_enabled": dm_enabled})
```

- [ ] **Step 4: Register the route table in `app.py`**

In `dashboard/backend/app.py`, change the import block:

```python
from .routes.config import routes as config_routes
```

to:

```python
from .routes.config import routes as config_routes
from .routes.welcome import routes as welcome_routes
```

Then add `app.add_routes(welcome_routes)` to `create_app`, alongside the other `app.add_routes(...)` calls (e.g. right after `app.add_routes(config_routes)`).

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_welcome_routes.py -v`
Expected: all 8 tests PASS.

- [ ] **Step 6: Run the full backend suite to check for regressions**

Run: `pytest`
Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add dashboard/backend/routes/welcome.py dashboard/backend/app.py dashboard/backend/tests/test_welcome_routes.py
git commit -m "feat: add welcome-settings routes for channel/DM toggle"
```

---

### Task 2: `dashboard/backend/routes/auto_roles.py` — auto-roles routes

**Files:**
- Create: `dashboard/backend/routes/auto_roles.py`
- Modify: `dashboard/backend/app.py` (import + `add_routes` call)
- Test: `dashboard/backend/tests/test_auto_roles_routes.py`

**Interfaces:**
- Consumes: `bot_config.load_config()`, `bot_config.save_config(data)`, `bot_config.get(key, default)` (existing).
- Produces: `GET /api/auto-roles` → `{"role_ids": [str, ...]}`; `PUT /api/auto-roles` (body `{"role_ids": [str, ...]}`) → same shape, persisted, with role-assignability validation.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/backend/tests/test_auto_roles_routes.py`:

```python
import pytest

import bot_config
from dashboard.backend.routes.auto_roles import routes as auto_roles_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, FakeRole, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_config_file(tmp_path, monkeypatch):
    monkeypatch.setattr(bot_config, "CONFIG_FILE", str(tmp_path / "config.json"))


def build(roles=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot_top = FakeRole(900, name="bot-role", position=50)
    me = FakeMember(1, name="bot", top_role=bot_top)
    guild = FakeGuild(members=[moderator], roles=roles or [], me=me)
    return guild, make_moderation_app(FakeBot(guild), [auto_roles_routes])


@pytest.mark.asyncio
async def test_get_auto_roles_defaults_to_empty_when_file_missing(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/auto-roles")
    assert resp.status == 200
    assert (await resp.json()) == {"role_ids": []}


@pytest.mark.asyncio
async def test_get_auto_roles_returns_stored_values(aiohttp_client):
    bot_config.save_config({"AUTO_ROLE_IDS": ["7", "8"]})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/auto-roles")
    assert (await resp.json()) == {"role_ids": ["7", "8"]}


@pytest.mark.asyncio
async def test_get_auto_roles_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/auto-roles")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_update_auto_roles_persists_valid_roles(aiohttp_client):
    role = FakeRole(7, name="Member", position=5)
    _, app = build(roles=[role])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-roles", json={"role_ids": ["7"]})
    assert resp.status == 200
    assert (await resp.json()) == {"role_ids": ["7"]}
    assert bot_config.load_config()["AUTO_ROLE_IDS"] == ["7"]


@pytest.mark.asyncio
async def test_update_auto_roles_rejects_role_above_bot(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    _, app = build(roles=[role])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-roles", json={"role_ids": ["9"]})
    assert resp.status == 403
    assert (await resp.json())["error"] == "role_not_assignable"


@pytest.mark.asyncio
async def test_update_auto_roles_rejects_managed_role(aiohttp_client):
    role = FakeRole(8, name="BotRole", position=5, managed=True)
    _, app = build(roles=[role])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-roles", json={"role_ids": ["8"]})
    assert resp.status == 403
    assert (await resp.json())["error"] == "role_not_assignable"


@pytest.mark.asyncio
async def test_update_auto_roles_rejects_unknown_role(aiohttp_client):
    _, app = build(roles=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-roles", json={"role_ids": ["999"]})
    assert resp.status == 403
    assert (await resp.json())["error"] == "role_not_assignable"


@pytest.mark.asyncio
async def test_update_auto_roles_rejects_non_list_body(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/auto-roles", json={"role_ids": "7"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_update_auto_roles_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.put("/api/auto-roles", json={"role_ids": []})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_auto_roles_route_is_registered_in_the_real_app(aiohttp_client):
    from dashboard.backend.app import create_app
    from dashboard.backend.config import load_dashboard_config

    class _FakeBot:
        def get_guild(self, guild_id):
            return None

    config = load_dashboard_config(
        {
            "DASHBOARD_PORT": "0",
            "DISCORD_CLIENT_ID": "id",
            "DISCORD_CLIENT_SECRET": "secret",
            "DISCORD_OAUTH_REDIRECT_URI": "http://localhost:8080/api/auth/discord/callback",
            "SESSION_SECRET": "x" * 32,
            "DASHBOARD_ACCESS_ROLE_IDS": "111",
        }
    )
    app = create_app(_FakeBot(), config, guild_id=1)
    client = await aiohttp_client(app)
    # 401 (not 404) proves the route is registered and reachable in the real
    # app, and that the dashboard-access auth gate — not a missing route —
    # is what's rejecting the unauthenticated request.
    resp = await client.get("/api/auto-roles")
    assert resp.status == 401
```

**Note on `FakeRole`'s `managed` parameter:** already exists (`dashboard/backend/tests/fakes.py:26`, `managed=False` default) — no change needed to `fakes.py`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_auto_roles_routes.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dashboard.backend.routes.auto_roles'`.

- [ ] **Step 3: Implement the routes**

Create `dashboard/backend/routes/auto_roles.py`:

```python
from aiohttp import web

import bot_config

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


def _is_role_assignable(role, guild) -> bool:
    return not role.is_default() and not role.managed and role.position < guild.me.top_role.position


@routes.get("/api/auto-roles")
@require_dashboard_access
async def get_auto_roles(request: web.Request) -> web.Response:
    role_ids = bot_config.get("AUTO_ROLE_IDS", [])
    return web.json_response({"role_ids": [str(r) for r in role_ids]})


@routes.put("/api/auto-roles")
@require_dashboard_access
async def update_auto_roles(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    role_ids_raw = body.get("role_ids")
    if not isinstance(role_ids_raw, list):
        return web.json_response({"error": "invalid_request"}, status=400)

    try:
        role_ids = [int(r) for r in role_ids_raw]
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)

    for role_id in role_ids:
        role = guild.get_role(role_id)
        if role is None or not _is_role_assignable(role, guild):
            return web.json_response({"error": "role_not_assignable"}, status=403)

    data = bot_config.load_config()
    data["AUTO_ROLE_IDS"] = [str(r) for r in role_ids]
    bot_config.save_config(data)

    return web.json_response({"role_ids": [str(r) for r in role_ids]})
```

- [ ] **Step 4: Register the route table in `app.py`**

In `dashboard/backend/app.py`, change the import block:

```python
from .routes.welcome import routes as welcome_routes
```

to:

```python
from .routes.welcome import routes as welcome_routes
from .routes.auto_roles import routes as auto_roles_routes
```

Then add `app.add_routes(auto_roles_routes)` to `create_app`, alongside the other `app.add_routes(...)` calls.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_auto_roles_routes.py -v`
Expected: all 10 tests PASS.

- [ ] **Step 6: Run the full backend suite to check for regressions**

Run: `pytest`
Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add dashboard/backend/routes/auto_roles.py dashboard/backend/app.py dashboard/backend/tests/test_auto_roles_routes.py
git commit -m "feat: add auto-roles routes with role-assignability validation"
```

---

### Task 3: `welcome.py` (root, bot-side) — toggle guards and auto-role granting

**Files:**
- Modify: `welcome.py:50-110` (`on_member_join`)

**Interfaces:**
- Consumes: `bot_config.get(key, default)` (existing, no other task's code).

**Note:** No automated tests for this task — event-listener cog code has zero pytest coverage anywhere in this project. Verification is a manual line-by-line diff review against the pre-change source.

- [ ] **Step 1: Wrap the channel-send block in the new toggle**

In `welcome.py`, replace lines 50-54:

```python
        welcome_ch_id = bot_config.get("WELCOME_CHANNEL_ID")
        if welcome_ch_id:
            welcome_ch = self.bot.get_channel(int(welcome_ch_id))
            if welcome_ch:
                await welcome_ch.send(f"Приветствую тебя {member.mention} на сервере **{guild.name}**! Теперь нас {guild.member_count}!")
```

with:

```python
        if bot_config.get("WELCOME_CHANNEL_ENABLED", True):
            welcome_ch_id = bot_config.get("WELCOME_CHANNEL_ID")
            if welcome_ch_id:
                welcome_ch = self.bot.get_channel(int(welcome_ch_id))
                if welcome_ch:
                    await welcome_ch.send(f"Приветствую тебя {member.mention} на сервере **{guild.name}**! Теперь нас {guild.member_count}!")
```

- [ ] **Step 2: Add auto-role granting right after the channel-send block**

Immediately after the block from Step 1 (still inside `on_member_join`, before the invite-tracking `if used and used.inviter:` block), add:

```python

        auto_role_ids = bot_config.get("AUTO_ROLE_IDS", [])
        if auto_role_ids:
            roles_to_add = [guild.get_role(int(rid)) for rid in auto_role_ids]
            roles_to_add = [r for r in roles_to_add if r is not None]
            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add, reason="Авто-роль при входе")
                except discord.Forbidden:
                    pass
```

- [ ] **Step 3: Wrap the DM-send block in the new toggle**

Replace lines 95-100 (the original line numbers — re-locate by content since Steps 1-2 shifted line numbers):

```python
        dm_sent = False
        try:
            await member.send(embed=dm_embed)
            dm_sent = True
        except discord.Forbidden:
            dm_sent = False
```

with:

```python
        dm_sent = False
        if bot_config.get("WELCOME_DM_ENABLED", True):
            try:
                await member.send(embed=dm_embed)
                dm_sent = True
            except discord.Forbidden:
                dm_sent = False
```

- [ ] **Step 4: Manually verify with a line-by-line diff**

Run: `git diff welcome.py`
Confirm: only the three edits above changed — the channel-send block gained one `if` wrapper (with all inner lines correctly re-indented one level), a new 9-line auto-role block was inserted between the channel-send block and the invite-tracking block, and the DM-send block gained one `if` wrapper (with its `try`/`except` re-indented one level). Confirm the `dm_embed` construction (lines building `dm_embed.add_field(...)`, unaffected by Step 3 since it happens before the wrapped `try` block) and the DM-log embed construction after Step 3's block are both completely untouched — `dm_sent` must still be defined (as `False`) even when the DM toggle is off, since the DM-log embed always reads `dm_sent` afterward.

- [ ] **Step 5: Commit**

```bash
git add welcome.py
git commit -m "feat: add welcome channel/DM toggles and auto-role granting on join"
```

---

### Task 4: Frontend API client

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts`
- Test: `dashboard/frontend/src/api/welcomeAutoRoles.test.ts` (new)

**Interfaces:**
- Consumes: `/api/welcome-settings` (Task 1), `/api/auto-roles` (Task 2).
- Produces: `WelcomeSettings`, `fetchWelcomeSettings`, `updateWelcomeSettings`, `AutoRolesSettings`, `fetchAutoRoles`, `updateAutoRoles`. Tasks 5-6 consume these.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/frontend/src/api/welcomeAutoRoles.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  fetchAutoRoles,
  fetchWelcomeSettings,
  updateAutoRoles,
  updateWelcomeSettings,
} from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('welcome and auto-roles api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchWelcomeSettings calls the welcome-settings endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ channel_enabled: true, dm_enabled: false }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchWelcomeSettings()
    expect(result).toEqual({ channel_enabled: true, dm_enabled: false })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/welcome-settings')
  })

  it('updateWelcomeSettings PUTs the toggle values', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ channel_enabled: false, dm_enabled: true }))
    vi.stubGlobal('fetch', fetchMock)

    await updateWelcomeSettings({ channel_enabled: false, dm_enabled: true })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/welcome-settings',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ channel_enabled: false, dm_enabled: true }),
      }),
    )
  })

  it('fetchAutoRoles calls the auto-roles endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ role_ids: ['7', '8'] }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchAutoRoles()
    expect(result).toEqual({ role_ids: ['7', '8'] })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/auto-roles')
  })

  it('updateAutoRoles PUTs the selected role ids', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ role_ids: ['7'] }))
    vi.stubGlobal('fetch', fetchMock)

    await updateAutoRoles(['7'])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/auto-roles',
      expect.objectContaining({ method: 'PUT', body: JSON.stringify({ role_ids: ['7'] }) }),
    )
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `dashboard/frontend`): `npx vitest run src/api/welcomeAutoRoles.test.ts`
Expected: FAIL — none of these functions are exported from `./client` yet.

- [ ] **Step 3: Add the types and functions to `client.ts`**

Add to the end of `dashboard/frontend/src/api/client.ts`:

```typescript
export interface WelcomeSettings {
  channel_enabled: boolean
  dm_enabled: boolean
}

export function fetchWelcomeSettings(): Promise<WelcomeSettings> {
  return apiFetch('/api/welcome-settings')
}

export function updateWelcomeSettings(settings: WelcomeSettings): Promise<WelcomeSettings> {
  return apiFetch('/api/welcome-settings', jsonInit('PUT', settings))
}

export interface AutoRolesSettings {
  role_ids: string[]
}

export function fetchAutoRoles(): Promise<AutoRolesSettings> {
  return apiFetch('/api/auto-roles')
}

export function updateAutoRoles(roleIds: string[]): Promise<AutoRolesSettings> {
  return apiFetch('/api/auto-roles', jsonInit('PUT', { role_ids: roleIds }))
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run (from `dashboard/frontend`): `npx vitest run src/api/welcomeAutoRoles.test.ts`
Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/welcomeAutoRoles.test.ts
git commit -m "feat: add welcome-settings and auto-roles API client functions"
```

---

### Task 5: `Welcome.tsx` page

**Files:**
- Create: `dashboard/frontend/src/pages/Welcome.tsx`
- Test: `dashboard/frontend/src/pages/Welcome.test.tsx`

**Interfaces:**
- Consumes: `fetchWelcomeSettings`, `updateWelcomeSettings`, `type WelcomeSettings` from `client.ts` (Task 4).
- Produces: `WelcomePage` component. Task 7 wires this into `App.tsx` at `/welcome`.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/frontend/src/pages/Welcome.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { WelcomePage } from './Welcome'

describe('WelcomePage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the current toggle state', async () => {
    vi.spyOn(client, 'fetchWelcomeSettings').mockResolvedValue({ channel_enabled: true, dm_enabled: false })
    render(<WelcomePage />)

    const channelToggle = (await screen.findByLabelText(
      'Отправлять приветствие в канал',
    )) as HTMLInputElement
    const dmToggle = screen.getByLabelText('Отправлять приветствие в личные сообщения') as HTMLInputElement
    expect(channelToggle.checked).toBe(true)
    expect(dmToggle.checked).toBe(false)
  })

  it('toggles and saves the settings', async () => {
    vi.spyOn(client, 'fetchWelcomeSettings').mockResolvedValue({ channel_enabled: true, dm_enabled: true })
    const updateSpy = vi
      .spyOn(client, 'updateWelcomeSettings')
      .mockResolvedValue({ channel_enabled: false, dm_enabled: true })

    render(<WelcomePage />)
    fireEvent.click(await screen.findByLabelText('Отправлять приветствие в канал'))
    fireEvent.click(screen.getByText('Сохранить'))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith({ channel_enabled: false, dm_enabled: true }),
    )
    expect(await screen.findByText('Сохранено.')).toBeInTheDocument()
  })

  it('shows an error when saving fails', async () => {
    vi.spyOn(client, 'fetchWelcomeSettings').mockResolvedValue({ channel_enabled: true, dm_enabled: true })
    vi.spyOn(client, 'updateWelcomeSettings').mockRejectedValue(new Error('fail'))

    render(<WelcomePage />)
    fireEvent.click(await screen.findByText('Сохранить'))

    expect(await screen.findByText('Не удалось сохранить настройки')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `dashboard/frontend`): `npx vitest run src/pages/Welcome.test.tsx`
Expected: FAIL — the module `./Welcome` doesn't exist yet.

- [ ] **Step 3: Implement `Welcome.tsx`**

Create `dashboard/frontend/src/pages/Welcome.tsx`:

```tsx
import { useEffect, useState } from 'react'
import { fetchWelcomeSettings, updateWelcomeSettings, type WelcomeSettings } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

export function WelcomePage() {
  const [settings, setSettings] = useState<WelcomeSettings | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')

  useEffect(() => {
    fetchWelcomeSettings()
      .then(setSettings)
      .catch(() => setError('Не удалось загрузить настройки'))
  }, [])

  const toggle = (key: keyof WelcomeSettings) => {
    setSettings((prev) => (prev ? { ...prev, [key]: !prev[key] } : prev))
  }

  const save = async () => {
    if (!settings) return
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const updated = await updateWelcomeSettings(settings)
      setSettings(updated)
      setSavedMessage('Сохранено.')
    } catch {
      setError('Не удалось сохранить настройки')
    } finally {
      setBusy(false)
    }
  }

  if (!settings) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  return (
    <div className="flex max-w-xl flex-col gap-4">
      <h1 className="text-lg font-semibold text-foreground">Приветствие и прощание</h1>

      <Card className="flex flex-col gap-3">
        <label className="flex items-center gap-2 text-sm text-foreground">
          <input
            type="checkbox"
            checked={settings.channel_enabled}
            onChange={() => toggle('channel_enabled')}
          />
          Отправлять приветствие в канал
        </label>
        <label className="flex items-center gap-2 text-sm text-foreground">
          <input type="checkbox" checked={settings.dm_enabled} onChange={() => toggle('dm_enabled')} />
          Отправлять приветствие в личные сообщения
        </label>
        <p className="text-xs text-muted">Канал для приветствий выбирается на странице «Конфигурация».</p>
      </Card>

      {error && <p className="text-sm text-danger">{error}</p>}
      {savedMessage && <p className="text-sm text-primary">{savedMessage}</p>}

      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </Button>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run (from `dashboard/frontend`): `npx vitest run src/pages/Welcome.test.tsx`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/pages/Welcome.tsx dashboard/frontend/src/pages/Welcome.test.tsx
git commit -m "feat: add Welcome page with channel/DM toggles"
```

---

### Task 6: `AutoRoles.tsx` page

**Files:**
- Create: `dashboard/frontend/src/pages/AutoRoles.tsx`
- Test: `dashboard/frontend/src/pages/AutoRoles.test.tsx`

**Interfaces:**
- Consumes: `fetchAutoRoles`, `updateAutoRoles`, `type AutoRolesSettings` from `client.ts` (Task 4); `fetchRoles`, `type RoleInfo` (existing, from `client.ts`).
- Produces: `AutoRolesPage` component. Task 7 wires this into `App.tsx` at `/auto-roles`.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/frontend/src/pages/AutoRoles.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { AutoRolesPage } from './AutoRoles'

describe('AutoRolesPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders roles with the currently selected ones checked', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([
      { id: '7', name: 'Member', color: '#5865f2', position: 5 },
      { id: '8', name: 'VIP', color: '#5865f2', position: 6 },
    ])
    vi.spyOn(client, 'fetchAutoRoles').mockResolvedValue({ role_ids: ['7'] })

    render(<AutoRolesPage />)

    const memberCheckbox = (await screen.findByLabelText('Member')) as HTMLInputElement
    const vipCheckbox = screen.getByLabelText('VIP') as HTMLInputElement
    expect(memberCheckbox.checked).toBe(true)
    expect(vipCheckbox.checked).toBe(false)
  })

  it('toggles a role and saves the selection', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([
      { id: '7', name: 'Member', color: '#5865f2', position: 5 },
    ])
    vi.spyOn(client, 'fetchAutoRoles').mockResolvedValue({ role_ids: [] })
    const updateSpy = vi.spyOn(client, 'updateAutoRoles').mockResolvedValue({ role_ids: ['7'] })

    render(<AutoRolesPage />)
    fireEvent.click(await screen.findByLabelText('Member'))
    fireEvent.click(screen.getByText('Сохранить'))

    await waitFor(() => expect(updateSpy).toHaveBeenCalledWith(['7']))
    expect(await screen.findByText('Сохранено.')).toBeInTheDocument()
  })

  it('shows an error when saving fails', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchAutoRoles').mockResolvedValue({ role_ids: [] })
    vi.spyOn(client, 'updateAutoRoles').mockRejectedValue(new Error('fail'))

    render(<AutoRolesPage />)
    fireEvent.click(await screen.findByText('Сохранить'))

    expect(await screen.findByText('Не удалось сохранить — проверьте, что роли ниже роли бота')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `dashboard/frontend`): `npx vitest run src/pages/AutoRoles.test.tsx`
Expected: FAIL — the module `./AutoRoles` doesn't exist yet.

- [ ] **Step 3: Implement `AutoRoles.tsx`**

Create `dashboard/frontend/src/pages/AutoRoles.tsx`:

```tsx
import { useEffect, useState } from 'react'
import { fetchAutoRoles, fetchRoles, updateAutoRoles, type RoleInfo } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

export function AutoRolesPage() {
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetchRoles(), fetchAutoRoles()])
      .then(([roleList, settings]) => {
        setRoles(roleList)
        setSelectedRoleIds(settings.role_ids)
      })
      .catch(() => setError('Не удалось загрузить роли'))
      .finally(() => setLoading(false))
  }, [])

  const toggleRole = (roleId: string) => {
    setSelectedRoleIds((prev) =>
      prev.includes(roleId) ? prev.filter((id) => id !== roleId) : [...prev, roleId],
    )
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const updated = await updateAutoRoles(selectedRoleIds)
      setSelectedRoleIds(updated.role_ids)
      setSavedMessage('Сохранено.')
    } catch {
      setError('Не удалось сохранить — проверьте, что роли ниже роли бота')
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return <p className="text-sm text-muted">Загрузка…</p>
  }

  return (
    <div className="flex max-w-xl flex-col gap-4">
      <h1 className="text-lg font-semibold text-foreground">Авто-роли</h1>

      <Card className="flex flex-col gap-3">
        <p className="text-sm text-muted">Роли, которые автоматически выдаются при входе на сервер</p>
        <div className="flex flex-wrap gap-2">
          {roles.map((r) => (
            <label key={r.id} className="flex items-center gap-1 text-xs text-foreground">
              <input
                type="checkbox"
                checked={selectedRoleIds.includes(r.id)}
                onChange={() => toggleRole(r.id)}
              />
              {r.name}
            </label>
          ))}
        </div>
      </Card>

      {error && <p className="text-sm text-danger">{error}</p>}
      {savedMessage && <p className="text-sm text-primary">{savedMessage}</p>}

      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </Button>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run (from `dashboard/frontend`): `npx vitest run src/pages/AutoRoles.test.tsx`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/pages/AutoRoles.tsx dashboard/frontend/src/pages/AutoRoles.test.tsx
git commit -m "feat: add AutoRoles page with role checkbox list"
```

---

### Task 7: Sidebar profile block, nav entries, and routing

**Files:**
- Modify: `dashboard/frontend/src/pages/DashboardShell.tsx`
- Test: `dashboard/frontend/src/pages/DashboardShell.test.tsx` (already exists, from an earlier mini-feature — you are ADDING to it)
- Modify: `dashboard/frontend/src/App.tsx`

**Interfaces:**
- Consumes: `WelcomePage` from `Welcome.tsx` (Task 5), `AutoRolesPage` from `AutoRoles.tsx` (Task 6).

- [ ] **Step 1: Write the failing tests**

Add to the end of the `describe('DashboardShell', ...)` block in `dashboard/frontend/src/pages/DashboardShell.test.tsx` (before the closing `})`):

```tsx
  it('renders the user avatar and username at the top of the sidebar', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
    })

    render(
      <MemoryRouter initialEntries={['/members']}>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<div>Home Page Marker</div>} />
            <Route path="/members" element={<DashboardShell />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    )

    expect(await screen.findByText('tester')).toBeInTheDocument()
  })

  it('lists nav entries for Welcome and Auto Roles', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
    })

    render(
      <MemoryRouter initialEntries={['/members']}>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<div>Home Page Marker</div>} />
            <Route path="/members" element={<DashboardShell />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    )

    expect(await screen.findByText('Приветствие и прощание')).toBeInTheDocument()
    expect(screen.getByText('Авто-роли')).toBeInTheDocument()
  })
```

This reuses the exact `AuthProvider`/`fetchCurrentUser` mocking pattern already present at the top of this same test file (from the earlier header-rename task) — do not duplicate the imports, just add these two `it` blocks using the same already-imported `render`, `screen`, `MemoryRouter`, `Route`, `Routes`, `client`, `AuthProvider`, `vi`.

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `dashboard/frontend`): `npx vitest run src/pages/DashboardShell.test.tsx`
Expected: FAIL — the sidebar has no profile block yet, and `SECTIONS` has no "Приветствие и прощание"/"Авто-роли" entries yet.

- [ ] **Step 3: Add the sidebar profile block and nav entries**

In `dashboard/frontend/src/pages/DashboardShell.tsx`, change the icon import:

```tsx
import {
  CalendarCheck,
  ChatCircleText,
  GearSix,
  ShieldWarning,
  SignOut,
  Sparkle,
  Stack,
  Trophy,
  UsersThree,
  type Icon,
} from '@phosphor-icons/react'
```

to:

```tsx
import {
  CalendarCheck,
  ChatCircleText,
  GearSix,
  HandWaving,
  ShieldWarning,
  SignOut,
  Sparkle,
  Stack,
  Trophy,
  UserCirclePlus,
  UsersThree,
  type Icon,
} from '@phosphor-icons/react'
```

Change the `SECTIONS` array:

```tsx
const SECTIONS: Section[] = [
  { label: 'Feedback и тикеты', icon: ChatCircleText, to: '/feedback' },
  { label: 'Конструктор кнопок и эмбедов', icon: Stack, to: '/reaction-roles' },
  { label: 'События и голосования', icon: CalendarCheck, to: '/events' },
  { label: 'Сетки', icon: Trophy, to: '/brackets' },
  { label: 'Lockdown и модерация', icon: ShieldWarning, to: '/lockdown' },
  { label: 'Участники и роли', icon: UsersThree, to: '/members' },
  { label: 'Конфигурация', icon: GearSix, to: '/config' },
]
```

to:

```tsx
const SECTIONS: Section[] = [
  { label: 'Feedback и тикеты', icon: ChatCircleText, to: '/feedback' },
  { label: 'Конструктор кнопок и эмбедов', icon: Stack, to: '/reaction-roles' },
  { label: 'События и голосования', icon: CalendarCheck, to: '/events' },
  { label: 'Сетки', icon: Trophy, to: '/brackets' },
  { label: 'Приветствие и прощание', icon: HandWaving, to: '/welcome' },
  { label: 'Авто-роли', icon: UserCirclePlus, to: '/auto-roles' },
  { label: 'Lockdown и модерация', icon: ShieldWarning, to: '/lockdown' },
  { label: 'Участники и роли', icon: UsersThree, to: '/members' },
  { label: 'Конфигурация', icon: GearSix, to: '/config' },
]
```

Then replace the `<aside>` opening (the line right before `<nav className="flex flex-col gap-2">`):

```tsx
        <aside className="w-72 shrink-0 border-r border-border p-4">
          <nav className="flex flex-col gap-2">
```

with:

```tsx
        <aside className="w-72 shrink-0 border-r border-border p-4">
          <div className="mb-4 flex items-center gap-3 rounded-control border border-border bg-surface p-3">
            {user?.avatar ? (
              <img src={user.avatar} alt="" className="h-9 w-9 rounded-full" />
            ) : (
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-muted text-sm font-semibold text-primary">
                {user?.username?.slice(0, 1).toUpperCase()}
              </span>
            )}
            <span className="truncate text-sm font-medium text-foreground">{user?.username}</span>
          </div>
          <nav className="flex flex-col gap-2">
```

This reuses the `user` variable already destructured at the top of the component (`const { user, refresh } = useAuth()`) — no new hook needed.

- [ ] **Step 4: Run the tests to verify they pass**

Run (from `dashboard/frontend`): `npx vitest run src/pages/DashboardShell.test.tsx`
Expected: all tests PASS (the 1 pre-existing test from the header-rename task, plus these 2 new ones).

- [ ] **Step 5: Wire the two new routes into `App.tsx`**

In `dashboard/frontend/src/App.tsx`, change the imports (add two new lines after the existing `ConfigPage` import):

```tsx
import { ConfigPage } from './pages/Config'
```

to:

```tsx
import { ConfigPage } from './pages/Config'
import { WelcomePage } from './pages/Welcome'
import { AutoRolesPage } from './pages/AutoRoles'
```

Then add two new nested routes inside the existing `ProtectedRoute`/`DashboardShell` block, alongside the other dashboard pages (e.g. right after the `brackets/:id` route and before `config`):

```tsx
            <Route path="brackets" element={<BracketsPage />} />
            <Route path="brackets/:id" element={<BracketDetailPage />} />
            <Route path="config" element={<ConfigPage />} />
```

to:

```tsx
            <Route path="brackets" element={<BracketsPage />} />
            <Route path="brackets/:id" element={<BracketDetailPage />} />
            <Route path="welcome" element={<WelcomePage />} />
            <Route path="auto-roles" element={<AutoRolesPage />} />
            <Route path="config" element={<ConfigPage />} />
```

- [ ] **Step 6: Run the full frontend suite to check for regressions**

Run (from `dashboard/frontend`): `npx vitest run`
Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add dashboard/frontend/src/pages/DashboardShell.tsx dashboard/frontend/src/pages/DashboardShell.test.tsx dashboard/frontend/src/App.tsx
git commit -m "feat: add sidebar profile block and wire up Welcome/AutoRoles nav and routes"
```

---

## Final Verification

After all seven tasks are complete:

- [ ] Run the full backend suite: `pytest` (from the repo root) — all tests pass.
- [ ] Run the full frontend suite: `npx vitest run` (from `dashboard/frontend`) — all tests pass.
- [ ] Manually verify in the browser (dev servers restarted): the sidebar shows your avatar+username at the top; "Приветствие и прощание" and "Авто-роли" appear in the nav and are reachable; toggling the welcome channel/DM switches and saving persists across a page reload; selecting auto-roles and saving persists, and picking a role positioned above the bot's own role is rejected with a clear error.
- [ ] Manually verify on the real Discord test server (since `welcome.py`'s bot-side changes have no automated coverage): join with a test account (or have someone else join) and confirm — with both toggles on, the channel message and DM both arrive as before; with the channel toggle off, only the DM arrives; with the DM toggle off, only the channel message arrives; with one or more auto-roles configured, the new member receives them.
