# Дашборд, Фаза 2a (Участники и модерация) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add member search/list, member card, ban/kick, single-role grant/revoke, and lockdown control to the existing dashboard (backend aiohttp routes + React pages), reusing the bot's live cache and the Phase 1 auth/design foundation.

**Architecture:** New route modules under `dashboard/backend/routes/` guarded by a shared `@require_dashboard_access` decorator (extracted from the Phase 1 inline pattern). Lockdown logic is refactored out of the `Interaction`-bound cog into pure functions (`lockdown_core.py`) shared by the slash command and the web API. Frontend converts `DashboardShell` into a layout with nested routes (`/`, `/members`, `/lockdown`) using the Phase 1 design tokens/components.

**Tech Stack:** Python: aiohttp, aiohttp-session, discord.py, pytest + pytest-aiohttp. Frontend: React + TypeScript + Vite, Tailwind v4 tokens, react-router-dom, Phosphor icons, Vitest + Testing Library.

## Global Constraints

- All work happens in `C:\Users\adnan\Documents\coding\ChetMain_backup_20260701_211729`. Never touch `C:\Users\adnan\Documents\coding\ChetMain`.
- Local-only git repo: commit each task with `git add` + `git commit` (no remote, no push).
- Spec of record: `docs/superpowers/specs/2026-07-01-dashboard-phase2a-members-moderation-design.md`.
- Phase 1 code that already passed review (`auth.py`, `app.py` internals, session, config) is NOT rewritten; the only Phase 1 file this plan modifies is `app.py` (route registration, Task 7) and frontend routing files.
- Discord action reasons use the format `f"Dashboard: {reason} — by {moderator.name} ({moderator.id})"` (same pattern as `spam.py`).
- All moderation actions log an embed to `LOG_CHANNEL_ID` via the existing `bot.send_log(embed)`.
- Error mapping (spec): no session → 401; no access/member gone → 403/404; bot cache down → 503; Discord `Forbidden` → 403; Discord `NotFound` → 404; other `discord.HTTPException` → 502.
- No secrets in any committed file.
- Existing suites must stay green: 36 pytest + 8 Vitest tests before this plan; every task ends with the relevant suite passing.

---

### Task 1: Test fakes + `require_dashboard_access` decorator

**Files:**
- Create: `dashboard/backend/routes/__init__.py` (empty)
- Create: `dashboard/backend/access_middleware.py`
- Create: `dashboard/backend/tests/fakes.py`
- Test: `dashboard/backend/tests/test_access_middleware.py`

**Interfaces:**
- Consumes: `has_dashboard_access` (access.py), `resolve_guild_member` (member_lookup.py), `setup_session` (session.py), `DashboardConfig` (config.py) — all Phase 1, unchanged.
- Produces: `def require_dashboard_access(handler)` — aiohttp handler decorator; on success sets `request["moderator"]` (discord.Member-shaped) and calls the handler; otherwise returns 401/403/503 JSON exactly like Phase 1's `me()`. Also produces reusable fakes: `FakeColor(value)`, `FakeRole(role_id, name, position, color_value=0, managed=False, default=False)` (with async `edit(**kwargs)` recording `edit_calls`), `FakePermissions(administrator=False, mention_everyone=False)`, `FakeAsset(url)`, `FakeMember(...)` (async `ban/kick/add_roles/remove_roles` recording calls, raising a configured exception if set), `FakeGuild(...)` (`members`, `roles`, `me`, `get_member`, `get_role`, async `fetch_member`), `FakeBot(guild)` (`get_guild`, `stats`, `feedback_cases`, async `send_log` recording embeds, `utcnow()`), and `make_moderation_app(bot, config)` + `force_login(client, user_id)` helpers for route tests.

- [ ] **Step 1: Create `dashboard/backend/routes/__init__.py`** (empty file).

- [ ] **Step 2: Create `dashboard/backend/tests/fakes.py`**

```python
from datetime import datetime, timezone

from aiohttp import web
from aiohttp_session import new_session

from dashboard.backend.config import DashboardConfig
from dashboard.backend.session import setup_session

TEST_CONFIG = DashboardConfig(
    port=8080,
    client_id="test-client-id",
    client_secret="test-client-secret",
    redirect_uri="http://localhost:8080/api/auth/discord/callback",
    session_secret="x" * 32,
    access_role_ids=frozenset({"111"}),
    frontend_url="",
)


class FakeColor:
    def __init__(self, value=0):
        self.value = value


class FakeRole:
    def __init__(self, role_id, name="role", position=1, color_value=0, managed=False, default=False):
        self.id = role_id
        self.name = name
        self.position = position
        self.color = FakeColor(color_value)
        self.managed = managed
        self._default = default
        self.mentionable = False
        self.permissions = FakePermissions()
        self.edit_calls = []
        self.edit_raises = None

    def is_default(self):
        return self._default

    async def edit(self, **kwargs):
        if self.edit_raises:
            raise self.edit_raises
        self.edit_calls.append(kwargs)


class FakePermissions:
    def __init__(self, administrator=False, mention_everyone=False):
        self.administrator = administrator
        self.mention_everyone = mention_everyone


class FakeAsset:
    def __init__(self, url="https://cdn.example/avatar.png"):
        self.url = url

    def __str__(self):
        return self.url


class FakeMember:
    def __init__(
        self,
        member_id,
        name="user",
        display_name=None,
        role_ids=(),
        roles=None,
        administrator=False,
        bot=False,
        top_role=None,
    ):
        self.id = member_id
        self.name = name
        self.display_name = display_name if display_name is not None else name
        self.bot = bot
        self.joined_at = datetime(2025, 1, 15, tzinfo=timezone.utc)
        self.created_at = datetime(2020, 6, 1, tzinfo=timezone.utc)
        default_role = FakeRole(0, name="@everyone", position=0, default=True)
        self.roles = [default_role] + (roles if roles is not None else [FakeRole(r) for r in role_ids])
        self.guild_permissions = FakePermissions(administrator)
        self.display_avatar = FakeAsset()
        self.top_role = top_role or (self.roles[-1] if len(self.roles) > 1 else default_role)
        self.action_calls = []
        self.action_raises = None

    async def _record(self, action, **kwargs):
        if self.action_raises:
            raise self.action_raises
        self.action_calls.append((action, kwargs))

    async def ban(self, **kwargs):
        await self._record("ban", **kwargs)

    async def kick(self, **kwargs):
        await self._record("kick", **kwargs)

    async def add_roles(self, role, **kwargs):
        await self._record("add_roles", role=role, **kwargs)

    async def remove_roles(self, role, **kwargs):
        await self._record("remove_roles", role=role, **kwargs)


class FakeGuild:
    def __init__(self, members=None, roles=None, me=None):
        self.members = members or []
        self.roles = roles or []
        self.me = me or FakeMember(1, name="bot", top_role=FakeRole(900, name="bot-role", position=50))

    def get_member(self, user_id):
        return next((m for m in self.members if m.id == user_id), None)

    def get_role(self, role_id):
        return next((r for r in self.roles if r.id == role_id), None)

    async def fetch_member(self, user_id):
        import discord

        member = self.get_member(user_id)
        if member is None:
            raise discord.NotFound.__new__(discord.NotFound)
        return member


class FakeBot:
    def __init__(self, guild):
        self._guild = guild
        self.stats = {}
        self.feedback_cases = {}
        self.sent_logs = []

    def get_guild(self, guild_id):
        return self._guild

    async def send_log(self, embed):
        self.sent_logs.append(embed)

    def utcnow(self):
        return datetime.now(timezone.utc)


def make_moderation_app(bot, routes_tables, config=TEST_CONFIG):
    app = web.Application()
    app["bot"] = bot
    app["dashboard_config"] = config
    app["guild_id"] = 1
    setup_session(app, config.session_secret)
    for table in routes_tables:
        app.add_routes(table)

    async def test_login(request):
        session = await new_session(request)
        session["discord_user_id"] = request.query["user_id"]
        return web.json_response({"ok": True})

    app.router.add_get("/test/login", test_login)
    return app


async def force_login(client, user_id):
    resp = await client.get(f"/test/login?user_id={user_id}")
    assert resp.status == 200
```

- [ ] **Step 3: Write the failing test**

`dashboard/backend/tests/test_access_middleware.py`:

```python
import pytest
from aiohttp import web

from dashboard.backend.access_middleware import require_dashboard_access
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)

routes = web.RouteTableDef()


@routes.get("/test/protected")
@require_dashboard_access
async def protected(request):
    return web.json_response({"moderator_id": request["moderator"].id})


def make_client_app(bot):
    return make_moderation_app(bot, [routes])


@pytest.mark.asyncio
async def test_no_session_returns_401(aiohttp_client):
    moderator = FakeMember(10, role_ids=[111])
    app = make_client_app(FakeBot(FakeGuild(members=[moderator])))
    client = await aiohttp_client(app)
    resp = await client.get("/test/protected")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_member_with_access_reaches_handler(aiohttp_client):
    moderator = FakeMember(10, role_ids=[111])
    app = make_client_app(FakeBot(FakeGuild(members=[moderator])))
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.get("/test/protected")
    assert resp.status == 200
    assert (await resp.json())["moderator_id"] == 10


@pytest.mark.asyncio
async def test_member_without_access_role_gets_403(aiohttp_client):
    intruder = FakeMember(20, role_ids=[999])
    app = make_client_app(FakeBot(FakeGuild(members=[intruder])))
    client = await aiohttp_client(app)
    await force_login(client, 20)
    resp = await client.get("/test/protected")
    assert resp.status == 403


@pytest.mark.asyncio
async def test_member_not_in_guild_gets_403(aiohttp_client):
    app = make_client_app(FakeBot(FakeGuild(members=[])))
    client = await aiohttp_client(app)
    await force_login(client, 30)
    resp = await client.get("/test/protected")
    assert resp.status == 403


@pytest.mark.asyncio
async def test_guild_unavailable_gets_503(aiohttp_client):
    class NoGuildBot(FakeBot):
        def get_guild(self, guild_id):
            return None

    app = make_client_app(NoGuildBot(FakeGuild()))
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.get("/test/protected")
    assert resp.status == 503
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_access_middleware.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.access_middleware'`

- [ ] **Step 5: Implement `dashboard/backend/access_middleware.py`**

```python
import functools

from aiohttp import web
from aiohttp_session import get_session

from .access import has_dashboard_access
from .member_lookup import resolve_guild_member


def require_dashboard_access(handler):
    """Guard an aiohttp handler with the Phase 1 session -> member -> role check.

    On success the resolved discord.Member is available as request["moderator"].
    """

    @functools.wraps(handler)
    async def wrapper(request: web.Request) -> web.StreamResponse:
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

        request["moderator"] = lookup.member
        return await handler(request)

    return wrapper
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_access_middleware.py -v`
Expected: PASS (5 tests)

- [ ] **Step 7: Run the full backend suite** — `pytest dashboard/backend/tests/ -q` — all pass (36 + 5).

- [ ] **Step 8: Commit**

```bash
git add dashboard/backend/routes/__init__.py dashboard/backend/access_middleware.py dashboard/backend/tests/fakes.py dashboard/backend/tests/test_access_middleware.py
git commit -m "feat(dashboard): add require_dashboard_access decorator and shared test fakes"
```

---

### Task 2: Member serializers + `GET /api/members` (search + pagination)

**Files:**
- Create: `dashboard/backend/routes/moderation.py`
- Test: `dashboard/backend/tests/test_members_list.py`

**Interfaces:**
- Consumes: `require_dashboard_access` (Task 1), fakes (Task 1).
- Produces: `routes = web.RouteTableDef()` in `moderation.py` (later tasks append handlers to this same table); `def serialize_member_summary(member) -> dict`; `def serialize_member_detail(member, bot) -> dict` (added in Task 3); `GET /api/members` returning `{total, page, page_size, members: [...]}`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_members_list.py`:

```python
import pytest

from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)


def build_client_app(members):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator] + members)
    return make_moderation_app(FakeBot(guild), [moderation_routes])


@pytest.mark.asyncio
async def test_lists_members_with_pagination_fields(aiohttp_client):
    members = [FakeMember(100 + i, name=f"user{i}") for i in range(3)]
    client = await aiohttp_client(build_client_app(members))
    await force_login(client, 10)

    resp = await client.get("/api/members")
    assert resp.status == 200
    body = await resp.json()
    assert body["total"] == 4  # moderator + 3
    assert body["page"] == 1
    assert body["page_size"] == 20
    first = body["members"][0]
    assert set(first) == {"id", "username", "display_name", "avatar", "role_count", "joined_at", "is_bot"}


@pytest.mark.asyncio
async def test_search_matches_name_and_display_name_case_insensitive(aiohttp_client):
    named = FakeMember(101, name="SharpShooter")
    nicked = FakeMember(102, name="boring", display_name="ShArP_nick")
    other = FakeMember(103, name="unrelated")
    client = await aiohttp_client(build_client_app([named, nicked, other]))
    await force_login(client, 10)

    resp = await client.get("/api/members?search=sharp")
    body = await resp.json()
    assert body["total"] == 2
    assert {m["id"] for m in body["members"]} == {"101", "102"}


@pytest.mark.asyncio
async def test_pagination_slices_and_caps_page_size(aiohttp_client):
    members = [FakeMember(200 + i, name=f"m{i:03d}") for i in range(30)]
    client = await aiohttp_client(build_client_app(members))
    await force_login(client, 10)

    resp = await client.get("/api/members?page=2&page_size=10")
    body = await resp.json()
    assert body["page"] == 2
    assert len(body["members"]) == 10

    resp = await client.get("/api/members?page_size=5000")
    body = await resp.json()
    assert body["page_size"] == 100


@pytest.mark.asyncio
async def test_invalid_pagination_returns_400(aiohttp_client):
    client = await aiohttp_client(build_client_app([]))
    await force_login(client, 10)
    resp = await client.get("/api/members?page=abc")
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    client = await aiohttp_client(build_client_app([]))
    resp = await client.get("/api/members")
    assert resp.status == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_members_list.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.routes.moderation'`

- [ ] **Step 3: Implement `dashboard/backend/routes/moderation.py`**

```python
from aiohttp import web

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def serialize_member_summary(member) -> dict:
    return {
        "id": str(member.id),
        "username": member.name,
        "display_name": member.display_name,
        "avatar": str(member.display_avatar.url) if member.display_avatar else None,
        "role_count": max(0, len(member.roles) - 1),  # exclude @everyone
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "is_bot": member.bot,
    }


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


@routes.get("/api/members")
@require_dashboard_access
async def list_members(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    search = request.query.get("search", "").strip().lower()
    try:
        page = max(1, int(request.query.get("page", "1")))
        page_size = min(100, max(1, int(request.query.get("page_size", "20"))))
    except ValueError:
        return web.json_response({"error": "invalid_pagination"}, status=400)

    members = list(guild.members)
    if search:
        members = [
            m
            for m in members
            if search in m.name.lower() or search in m.display_name.lower()
        ]

    total = len(members)
    start = (page - 1) * page_size
    page_items = members[start : start + page_size]

    return web.json_response(
        {
            "total": total,
            "page": page,
            "page_size": page_size,
            "members": [serialize_member_summary(m) for m in page_items],
        }
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_members_list.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routes/moderation.py dashboard/backend/tests/test_members_list.py
git commit -m "feat(dashboard): add GET /api/members with search and pagination"
```

---

### Task 3: `GET /api/members/{id}` (member card)

**Files:**
- Modify: `dashboard/backend/routes/moderation.py` (append)
- Test: `dashboard/backend/tests/test_member_detail.py`

**Interfaces:**
- Consumes: `routes`, `serialize_member_summary` (Task 2), fakes (Task 1). `bot.stats` is keyed by string user id with `{joins, leaves, invites}`; `bot.feedback_cases` values contain `submitter_id` (int) — mirrors `welcome.py`'s `/userinfo`.
- Produces: `serialize_member_detail(member, bot) -> dict`; `GET /api/members/{member_id}`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_member_detail.py`:

```python
import pytest

from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)


def build(members, stats=None, cases=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator] + members))
    bot.stats = stats or {}
    bot.feedback_cases = cases or {}
    return make_moderation_app(bot, [moderation_routes])


@pytest.mark.asyncio
async def test_detail_shape_matches_userinfo(aiohttp_client):
    target = FakeMember(
        50,
        name="target",
        roles=[FakeRole(7, name="VIP", position=3, color_value=0x5865F2)],
    )
    stats = {"50": {"joins": 2, "leaves": 1, "invites": 4}}
    cases = {"c1": {"submitter_id": 50}, "c2": {"submitter_id": 999}}
    client = await aiohttp_client(build([target], stats, cases))
    await force_login(client, 10)

    resp = await client.get("/api/members/50")
    assert resp.status == 200
    body = await resp.json()
    assert body["id"] == "50"
    assert body["created_at"].startswith("2020-06-01")
    assert body["roles"] == [{"id": "7", "name": "VIP", "color": "#5865f2"}]
    assert body["invite_stats"] == {"joins": 2, "leaves": 1, "invites": 4}
    assert body["feedback_case_count"] == 1
    assert body["is_bot"] is False


@pytest.mark.asyncio
async def test_detail_defaults_when_no_stats(aiohttp_client):
    target = FakeMember(51, name="fresh")
    client = await aiohttp_client(build([target]))
    await force_login(client, 10)

    resp = await client.get("/api/members/51")
    body = await resp.json()
    assert body["invite_stats"] == {"joins": 0, "leaves": 0, "invites": 0}
    assert body["feedback_case_count"] == 0


@pytest.mark.asyncio
async def test_detail_404_when_member_absent(aiohttp_client):
    client = await aiohttp_client(build([]))
    await force_login(client, 10)
    resp = await client.get("/api/members/404404")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_detail_400_on_non_numeric_id(aiohttp_client):
    client = await aiohttp_client(build([]))
    await force_login(client, 10)
    resp = await client.get("/api/members/abc")
    assert resp.status == 400
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_member_detail.py -v`
Expected: FAIL — 404 from aiohttp (route not registered yet), assertions on shape fail.

- [ ] **Step 3: Append to `dashboard/backend/routes/moderation.py`**

```python
def serialize_member_detail(member, bot) -> dict:
    stats = bot.stats.get(str(member.id), {"joins": 0, "leaves": 0, "invites": 0})
    case_count = sum(
        1 for c in bot.feedback_cases.values() if c.get("submitter_id") == member.id
    )
    roles = [
        {"id": str(r.id), "name": r.name, "color": f"#{r.color.value:06x}"}
        for r in member.roles
        if not r.is_default()
    ]
    return {
        "id": str(member.id),
        "username": member.name,
        "display_name": member.display_name,
        "avatar": str(member.display_avatar.url) if member.display_avatar else None,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "created_at": member.created_at.isoformat(),
        "roles": roles,
        "invite_stats": {
            "joins": stats.get("joins", 0),
            "leaves": stats.get("leaves", 0),
            "invites": stats.get("invites", 0),
        },
        "feedback_case_count": case_count,
        "is_bot": member.bot,
    }


def _parse_member_id(request):
    try:
        return int(request.match_info["member_id"])
    except ValueError:
        return None


@routes.get("/api/members/{member_id}")
@require_dashboard_access
async def member_detail(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    member_id = _parse_member_id(request)
    if member_id is None:
        return web.json_response({"error": "invalid_member_id"}, status=400)

    member = guild.get_member(member_id)
    if member is None:
        return web.json_response({"error": "member_not_found"}, status=404)

    return web.json_response(serialize_member_detail(member, request.app["bot"]))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_member_detail.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routes/moderation.py dashboard/backend/tests/test_member_detail.py
git commit -m "feat(dashboard): add GET /api/members/{id} member card endpoint"
```

---

### Task 4: Ban and kick endpoints

**Files:**
- Modify: `dashboard/backend/routes/moderation.py` (append)
- Test: `dashboard/backend/tests/test_ban_kick.py`

**Interfaces:**
- Consumes: `routes`, `_get_guild_or_none`, `_parse_member_id` (Tasks 2-3); fakes (Task 1). Real `discord.Embed` is used for logs (pure data object, safe in tests).
- Produces: `POST /api/members/{member_id}/ban` (body `{reason: str, delete_message_days: 0|1|7}`), `POST /api/members/{member_id}/kick` (body `{reason: str}`); helper `def dashboard_reason(reason, moderator) -> str`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_ban_kick.py`:

```python
import discord
import pytest

from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)


class _StubForbidden(discord.Forbidden):
    def __init__(self):
        pass


def build(members):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator] + members))
    return bot, make_moderation_app(bot, [moderation_routes])


@pytest.mark.asyncio
async def test_ban_calls_discord_and_logs(aiohttp_client):
    target = FakeMember(60, name="rulebreaker")
    bot, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/members/60/ban", json={"reason": "спам", "delete_message_days": 7}
    )
    assert resp.status == 200
    action, kwargs = target.action_calls[0]
    assert action == "ban"
    assert kwargs["delete_message_seconds"] == 7 * 86400
    assert "Dashboard: спам" in kwargs["reason"]
    assert "(10)" in kwargs["reason"]
    assert len(bot.sent_logs) == 1


@pytest.mark.asyncio
async def test_kick_calls_discord_and_logs(aiohttp_client):
    target = FakeMember(61, name="mild")
    bot, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/61/kick", json={"reason": "флуд"})
    assert resp.status == 200
    action, kwargs = target.action_calls[0]
    assert action == "kick"
    assert "Dashboard: флуд" in kwargs["reason"]
    assert len(bot.sent_logs) == 1


@pytest.mark.asyncio
async def test_ban_requires_reason_and_valid_days(aiohttp_client):
    target = FakeMember(62)
    _, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/62/ban", json={"reason": "  ", "delete_message_days": 0})
    assert resp.status == 400
    resp = await client.post("/api/members/62/ban", json={"reason": "ok", "delete_message_days": 3})
    assert resp.status == 400
    assert target.action_calls == []


@pytest.mark.asyncio
async def test_ban_forbidden_maps_to_403(aiohttp_client):
    target = FakeMember(63)
    target.action_raises = _StubForbidden()
    _, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/members/63/ban", json={"reason": "x", "delete_message_days": 0})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_ban_missing_member_maps_to_404(aiohttp_client):
    _, app = build([])
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.post("/api/members/9999/ban", json={"reason": "x", "delete_message_days": 0})
    assert resp.status == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_ban_kick.py -v`
Expected: FAIL — routes not registered (404s).

- [ ] **Step 3: Append to `dashboard/backend/routes/moderation.py`**

Add imports at the top of the file: `import discord`.

```python
ALLOWED_DELETE_DAYS = {0, 1, 7}


def dashboard_reason(reason: str, moderator) -> str:
    return f"Dashboard: {reason} — by {moderator.name} ({moderator.id})"


async def _send_action_log(bot, title: str, target, moderator, reason: str, extra: str = ""):
    embed = discord.Embed(title=title, color=discord.Color.red(), timestamp=bot.utcnow())
    embed.add_field(name="Кто", value=f"{moderator.name} (`{moderator.id}`)", inline=False)
    embed.add_field(name="Кого", value=f"{target.name} (`{target.id}`)", inline=False)
    embed.add_field(name="Причина", value=reason, inline=False)
    if extra:
        embed.add_field(name="Дополнительно", value=extra, inline=False)
    embed.set_footer(text="Dashboard · Moderation")
    await bot.send_log(embed)


def _get_target_or_response(request):
    """Returns (member, None) or (None, error Response)."""
    guild = _get_guild_or_none(request)
    if guild is None:
        return None, web.json_response({"error": "service_unavailable"}, status=503)
    member_id = _parse_member_id(request)
    if member_id is None:
        return None, web.json_response({"error": "invalid_member_id"}, status=400)
    member = guild.get_member(member_id)
    if member is None:
        return None, web.json_response({"error": "member_not_found"}, status=404)
    return member, None


def _map_discord_error(exc):
    if isinstance(exc, discord.Forbidden):
        return web.json_response({"error": "forbidden_by_discord"}, status=403)
    if isinstance(exc, discord.NotFound):
        return web.json_response({"error": "member_not_found"}, status=404)
    return web.json_response({"error": "discord_error"}, status=502)


@routes.post("/api/members/{member_id}/ban")
@require_dashboard_access
async def ban_member(request: web.Request) -> web.Response:
    target, error = _get_target_or_response(request)
    if error:
        return error

    body = await request.json()
    reason = (body.get("reason") or "").strip()
    days = body.get("delete_message_days", 0)
    if not reason or days not in ALLOWED_DELETE_DAYS:
        return web.json_response({"error": "invalid_request"}, status=400)

    moderator = request["moderator"]
    full_reason = dashboard_reason(reason, moderator)
    try:
        await target.ban(reason=full_reason, delete_message_seconds=days * 86400)
    except discord.HTTPException as exc:
        return _map_discord_error(exc)

    await _send_action_log(
        request.app["bot"], "🔨 Бан через дашборд", target, moderator, reason,
        extra=f"Удаление сообщений: {days} дн.",
    )
    return web.json_response({"ok": True})


@routes.post("/api/members/{member_id}/kick")
@require_dashboard_access
async def kick_member(request: web.Request) -> web.Response:
    target, error = _get_target_or_response(request)
    if error:
        return error

    body = await request.json()
    reason = (body.get("reason") or "").strip()
    if not reason:
        return web.json_response({"error": "invalid_request"}, status=400)

    moderator = request["moderator"]
    try:
        await target.kick(reason=dashboard_reason(reason, moderator))
    except discord.HTTPException as exc:
        return _map_discord_error(exc)

    await _send_action_log(
        request.app["bot"], "👢 Кик через дашборд", target, moderator, reason
    )
    return web.json_response({"ok": True})
```

Note: `discord.Forbidden`/`discord.NotFound` are subclasses of `discord.HTTPException`, so the single `except discord.HTTPException` plus `_map_discord_error`'s isinstance checks handles all three spec cases (403/404/502) — same subclass-ordering discipline as Task 3 of Phase 1.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_ban_kick.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routes/moderation.py dashboard/backend/tests/test_ban_kick.py
git commit -m "feat(dashboard): add ban and kick endpoints with Discord error mapping"
```

---

### Task 5: Roles endpoints (list assignable, grant, revoke)

**Files:**
- Modify: `dashboard/backend/routes/moderation.py` (append)
- Test: `dashboard/backend/tests/test_roles.py`

**Interfaces:**
- Consumes: everything from Tasks 2-4.
- Produces: `GET /api/roles` → `{roles: [{id, name, color, position}]}` (assignable only: not default, not managed, `position < guild.me.top_role.position`, sorted by position descending); `POST /api/members/{member_id}/roles` (body `{role_id: str}`); `DELETE /api/members/{member_id}/roles/{role_id}`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_roles.py`:

```python
import discord
import pytest

from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)


class _StubForbidden(discord.Forbidden):
    def __init__(self):
        pass


def build(members=None, roles=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot_top = FakeRole(900, name="bot-role", position=50)
    me = FakeMember(1, name="bot", top_role=bot_top)
    guild = FakeGuild(members=[moderator] + (members or []), roles=roles or [], me=me)
    return make_moderation_app(FakeBot(guild), [moderation_routes])


@pytest.mark.asyncio
async def test_roles_lists_only_assignable_sorted(aiohttp_client):
    roles = [
        FakeRole(0, name="@everyone", position=0, default=True),
        FakeRole(2, name="Low", position=5),
        FakeRole(3, name="High", position=40),
        FakeRole(4, name="AboveBot", position=60),
        FakeRole(5, name="Integration", position=10, managed=True),
    ]
    client = await aiohttp_client(build(roles=roles))
    await force_login(client, 10)

    resp = await client.get("/api/roles")
    assert resp.status == 200
    body = await resp.json()
    assert [r["name"] for r in body["roles"]] == ["High", "Low"]


@pytest.mark.asyncio
async def test_grant_role_calls_add_roles(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    target = FakeMember(70, name="lucky")
    client = await aiohttp_client(build(members=[target], roles=[role]))
    await force_login(client, 10)

    resp = await client.post("/api/members/70/roles", json={"role_id": "7"})
    assert resp.status == 200
    action, kwargs = target.action_calls[0]
    assert action == "add_roles"
    assert kwargs["role"].id == 7


@pytest.mark.asyncio
async def test_revoke_role_calls_remove_roles(aiohttp_client):
    role = FakeRole(8, name="Temp", position=5)
    target = FakeMember(71, name="temp")
    client = await aiohttp_client(build(members=[target], roles=[role]))
    await force_login(client, 10)

    resp = await client.delete("/api/members/71/roles/8")
    assert resp.status == 200
    action, kwargs = target.action_calls[0]
    assert action == "remove_roles"
    assert kwargs["role"].id == 8


@pytest.mark.asyncio
async def test_grant_unknown_or_unassignable_role_404(aiohttp_client):
    above_bot = FakeRole(9, name="AboveBot", position=60)
    target = FakeMember(72)
    client = await aiohttp_client(build(members=[target], roles=[above_bot]))
    await force_login(client, 10)

    resp = await client.post("/api/members/72/roles", json={"role_id": "12345"})
    assert resp.status == 404
    resp = await client.post("/api/members/72/roles", json={"role_id": "9"})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_grant_forbidden_maps_to_403(aiohttp_client):
    role = FakeRole(11, name="Race", position=5)
    target = FakeMember(73)
    target.action_raises = _StubForbidden()
    client = await aiohttp_client(build(members=[target], roles=[role]))
    await force_login(client, 10)

    resp = await client.post("/api/members/73/roles", json={"role_id": "11"})
    assert resp.status == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_roles.py -v`
Expected: FAIL — routes not registered (404s).

- [ ] **Step 3: Append to `dashboard/backend/routes/moderation.py`**

```python
def _assignable_roles(guild):
    top = guild.me.top_role.position
    return sorted(
        (r for r in guild.roles if not r.is_default() and not r.managed and r.position < top),
        key=lambda r: r.position,
        reverse=True,
    )


@routes.get("/api/roles")
@require_dashboard_access
async def list_roles(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)
    return web.json_response(
        {
            "roles": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "color": f"#{r.color.value:06x}",
                    "position": r.position,
                }
                for r in _assignable_roles(guild)
            ]
        }
    )


def _resolve_assignable_role(request, role_id_raw):
    """Returns (role, None) or (None, error Response)."""
    guild = _get_guild_or_none(request)
    try:
        role_id = int(role_id_raw)
    except (TypeError, ValueError):
        return None, web.json_response({"error": "invalid_role_id"}, status=400)
    role = guild.get_role(role_id)
    if role is None:
        return None, web.json_response({"error": "role_not_found"}, status=404)
    if role.is_default() or role.managed or role.position >= guild.me.top_role.position:
        return None, web.json_response({"error": "role_not_assignable"}, status=403)
    return role, None


@routes.post("/api/members/{member_id}/roles")
@require_dashboard_access
async def grant_role(request: web.Request) -> web.Response:
    target, error = _get_target_or_response(request)
    if error:
        return error
    body = await request.json()
    role, error = _resolve_assignable_role(request, body.get("role_id"))
    if error:
        return error

    moderator = request["moderator"]
    try:
        await target.add_roles(role, reason=dashboard_reason(f"выдана роль {role.name}", moderator))
    except discord.HTTPException as exc:
        return _map_discord_error(exc)

    await _send_action_log(
        request.app["bot"], "🎖️ Роль выдана через дашборд", target, moderator, role.name
    )
    return web.json_response({"ok": True})


@routes.delete("/api/members/{member_id}/roles/{role_id}")
@require_dashboard_access
async def revoke_role(request: web.Request) -> web.Response:
    target, error = _get_target_or_response(request)
    if error:
        return error
    role, error = _resolve_assignable_role(request, request.match_info["role_id"])
    if error:
        return error

    moderator = request["moderator"]
    try:
        await target.remove_roles(role, reason=dashboard_reason(f"снята роль {role.name}", moderator))
    except discord.HTTPException as exc:
        return _map_discord_error(exc)

    await _send_action_log(
        request.app["bot"], "🎖️ Роль снята через дашборд", target, moderator, role.name
    )
    return web.json_response({"ok": True})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_roles.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Run the full backend suite** — `pytest dashboard/backend/tests/ -q` — all green.

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/moderation.py dashboard/backend/tests/test_roles.py
git commit -m "feat(dashboard): add assignable-roles listing and grant/revoke endpoints"
```

---

### Task 6: Extract `lockdown_core.py` from the Lockdown cog

**Files:**
- Create: `lockdown_core.py` (repo root, next to `lockdown.py`)
- Modify: `lockdown.py` (delegate to core, keep slash-command UX identical)
- Test: `dashboard/backend/tests/test_lockdown_core.py`

**Interfaces:**
- Consumes: nothing from dashboard code — this is bot-side refactoring.
- Produces (all in `lockdown_core.py`): `BACKUP_FILE`, `load_backup() -> dict`, `save_backup(data)`, `get_mention_exempt_ids() -> set[int]`, `get_mentionable_exempt_ids() -> set[int]`, `antispam_status() -> tuple[bool, int]`, `async activate_antispam(guild, mention_exempt, mentionable_exempt) -> tuple[int, list[str]]`, `async deactivate_antispam(guild) -> tuple[int, list[str]] | None` (**None = нет сохранённого бэкапа**, refinement of the spec signature so the "нечего восстанавливать" case stays distinguishable).

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_lockdown_core.py`:

```python
import json

import pytest

import lockdown_core
from dashboard.backend.tests.fakes import FakeGuild, FakeRole


@pytest.fixture(autouse=True)
def isolated_backup(tmp_path, monkeypatch):
    monkeypatch.setattr(lockdown_core, "BACKUP_FILE", str(tmp_path / "antispam_backup.json"))


def _role(role_id, *, mention_everyone=False, mentionable=False, position=5, **kw):
    role = FakeRole(role_id, position=position, **kw)
    role.permissions.mention_everyone = mention_everyone
    role.mentionable = mentionable
    return role


@pytest.mark.asyncio
async def test_activate_strips_permissions_and_saves_backup():
    noisy = _role(2, mention_everyone=True, mentionable=True)
    quiet = _role(3)
    guild = FakeGuild(roles=[_role(0, default=True), noisy, quiet])

    modified, errors = await lockdown_core.activate_antispam(guild, set(), set())

    assert modified == 1
    assert errors == []
    assert noisy.edit_calls  # got edited
    assert quiet.edit_calls == []
    active, count = lockdown_core.antispam_status()
    assert active is True
    assert count == 1


@pytest.mark.asyncio
async def test_activate_respects_exempts():
    exempt = _role(5, mention_everyone=True)
    guild = FakeGuild(roles=[exempt])

    modified, _ = await lockdown_core.activate_antispam(guild, {5}, set())
    assert modified == 0
    assert exempt.edit_calls == []


@pytest.mark.asyncio
async def test_deactivate_restores_from_backup():
    noisy = _role(2, mention_everyone=True, mentionable=True)
    guild = FakeGuild(roles=[noisy])
    await lockdown_core.activate_antispam(guild, set(), set())
    noisy.permissions.mention_everyone = False
    noisy.mentionable = False

    result = await lockdown_core.deactivate_antispam(guild)
    assert result is not None
    restored, errors = result
    assert restored == 1
    assert errors == []
    active, _ = lockdown_core.antispam_status()
    assert active is False


@pytest.mark.asyncio
async def test_deactivate_without_backup_returns_none():
    guild = FakeGuild(roles=[])
    assert await lockdown_core.deactivate_antispam(guild) is None


@pytest.mark.asyncio
async def test_activate_collects_errors_and_continues():
    import discord

    class _StubForbidden(discord.Forbidden):
        def __init__(self):
            pass

    broken = _role(6, mention_everyone=True)
    broken.edit_raises = _StubForbidden()
    fine = _role(7, mention_everyone=True)
    guild = FakeGuild(roles=[broken, fine])

    modified, errors = await lockdown_core.activate_antispam(guild, set(), set())
    assert modified == 1
    assert len(errors) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_lockdown_core.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'lockdown_core'`

- [ ] **Step 3: Create `lockdown_core.py`**

Logic is moved verbatim from `lockdown.py`'s `_load_backup`/`_save_backup`/`_get_*_exempt_ids`/`_activate`/`_deactivate` bodies, minus everything touching `interaction`/embeds:

```python
import json
import os

import discord

BACKUP_FILE = "antispam_backup.json"


def load_backup() -> dict:
    if os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_backup(data: dict):
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_mention_exempt_ids() -> set[int]:
    raw = os.getenv("ANTISPAM_MENTION_EXEMPT_ROLES", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def get_mentionable_exempt_ids() -> set[int]:
    raw = os.getenv("ANTISPAM_MENTIONABLE_EXEMPT_ROLES", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def antispam_status() -> tuple[bool, int]:
    backup = load_backup()
    return bool(backup.get("active", False)), len(backup.get("roles", {}))


async def activate_antispam(
    guild, mention_exempt: set[int], mentionable_exempt: set[int]
) -> tuple[int, list[str]]:
    backup = load_backup()
    backup_roles: dict[str, dict] = {}
    modified_count = 0
    errors: list[str] = []

    for role in guild.roles:
        if role.is_default() or role.managed:
            continue

        is_mention_exempt = role.id in mention_exempt or role.permissions.administrator
        is_mentionable_exempt = role.id in mentionable_exempt

        need_mention_change = (not is_mention_exempt) and role.permissions.mention_everyone
        need_mentionable_change = (not is_mentionable_exempt) and role.mentionable

        if not need_mention_change and not need_mentionable_change:
            continue

        backup_roles[str(role.id)] = {
            "mention_everyone": role.permissions.mention_everyone,
            "mentionable": role.mentionable,
        }

        try:
            kwargs = {}
            if need_mention_change:
                new_perms = discord.Permissions(getattr(role.permissions, "value", 0))
                new_perms.update(mention_everyone=False)
                kwargs["permissions"] = new_perms
            if need_mentionable_change:
                kwargs["mentionable"] = False
            await role.edit(**kwargs, reason="Antispam ON")
            modified_count += 1
        except discord.Forbidden:
            errors.append(f"{role.name} (нет прав)")
        except Exception as exc:
            errors.append(f"{role.name} ({exc})")

    backup["roles"] = backup_roles
    backup["active"] = True
    save_backup(backup)
    return modified_count, errors


async def deactivate_antispam(guild) -> tuple[int, list[str]] | None:
    backup = load_backup()
    backup_roles: dict[str, dict] = backup.get("roles", {})
    if not backup_roles:
        return None

    restored_count = 0
    errors: list[str] = []

    for role_id_str, saved in backup_roles.items():
        role = guild.get_role(int(role_id_str))
        if not role:
            continue
        try:
            kwargs = {}
            if saved.get("mention_everyone") and not role.permissions.mention_everyone:
                new_perms = discord.Permissions(getattr(role.permissions, "value", 0))
                new_perms.update(mention_everyone=True)
                kwargs["permissions"] = new_perms
            if saved.get("mentionable") and not role.mentionable:
                kwargs["mentionable"] = True
            if kwargs:
                await role.edit(**kwargs, reason="Antispam OFF")
                restored_count += 1
        except discord.Forbidden:
            errors.append(f"{role.name} (нет прав)")
        except Exception as exc:
            errors.append(f"{role.name} ({exc})")

    backup["roles"] = {}
    backup["active"] = False
    save_backup(backup)
    return restored_count, errors
```

(Note the one deliberate difference from the original: `discord.Permissions(getattr(role.permissions, "value", 0))` instead of `discord.Permissions(role.permissions.value)` so `FakePermissions` without `.value` works; real `discord.Permissions` has `.value`, so production behavior is identical.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_lockdown_core.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Rewrite `lockdown.py` to delegate**

Replace the entire file with:

```python
import discord
from discord.ext import commands
from discord import app_commands

import lockdown_core


class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="antispam", description="Включить / выключить антиспам-режим для ролей")
    @app_commands.describe(mode="on — включить, off — выключить")
    @app_commands.choices(mode=[
        app_commands.Choice(name="on", value="on"),
        app_commands.Choice(name="off", value="off"),
        app_commands.Choice(name="status", value="status"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def antispam(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            await interaction.followup.send("Команда доступна только на сервере.", ephemeral=True)
            return

        if mode.value == "on":
            await self._activate(interaction, guild)
        elif mode.value == "off":
            await self._deactivate(interaction, guild)
        else:
            await self._status(interaction)

    async def _activate(self, interaction: discord.Interaction, guild: discord.Guild):
        modified_count, errors = await lockdown_core.activate_antispam(
            guild,
            lockdown_core.get_mention_exempt_ids(),
            lockdown_core.get_mentionable_exempt_ids(),
        )

        embed = discord.Embed(
            title="🛡️ Антиспам-режим ВКЛЮЧЁН",
            color=discord.Color.red(),
            timestamp=self.bot.utcnow(),
        )
        embed.add_field(name="Кто включил", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
        embed.add_field(name="Изменено ролей", value=str(modified_count), inline=True)
        if errors:
            embed.add_field(name="Ошибки", value="\n".join(errors[:10]), inline=False)
        embed.set_footer(text="Lockdown · Antispam")
        await self.bot.send_log(embed)

        status = f"✅ Антиспам включён. Изменено ролей: **{modified_count}**."
        if errors:
            status += f"\n⚠️ Ошибки ({len(errors)}): " + ", ".join(errors[:5])
        await interaction.followup.send(status, ephemeral=True)

    async def _deactivate(self, interaction: discord.Interaction, guild: discord.Guild):
        result = await lockdown_core.deactivate_antispam(guild)
        if result is None:
            await interaction.followup.send("Нет сохранённого бэкапа — антиспам не был включён или уже выключен.", ephemeral=True)
            return
        restored_count, errors = result

        embed = discord.Embed(
            title="🟢 Антиспам-режим ВЫКЛЮЧЕН",
            color=discord.Color.green(),
            timestamp=self.bot.utcnow(),
        )
        embed.add_field(name="Кто выключил", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
        embed.add_field(name="Восстановлено ролей", value=str(restored_count), inline=True)
        if errors:
            embed.add_field(name="Ошибки", value="\n".join(errors[:10]), inline=False)
        embed.set_footer(text="Lockdown · Antispam")
        await self.bot.send_log(embed)

        status = f"✅ Антиспам выключен. Восстановлено ролей: **{restored_count}**."
        if errors:
            status += f"\n⚠️ Ошибки ({len(errors)}): " + ", ".join(errors[:5])
        await interaction.followup.send(status, ephemeral=True)

    async def _status(self, interaction: discord.Interaction):
        is_active, role_count = lockdown_core.antispam_status()

        if is_active:
            embed = discord.Embed(
                title="🛡️ Антиспам-режим: ВКЛЮЧЁН",
                description=f"Изменённых ролей в бэкапе: **{role_count}**",
                color=discord.Color.red(),
                timestamp=self.bot.utcnow(),
            )
        else:
            embed = discord.Embed(
                title="🟢 Антиспам-режим: ВЫКЛЮЧЕН",
                description="Все роли работают в обычном режиме.",
                color=discord.Color.green(),
                timestamp=self.bot.utcnow(),
            )
        embed.set_footer(text="Lockdown · Antispam Status")
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Lockdown(bot))
```

- [ ] **Step 6: Verify the cog still imports and full suite passes**

Run: `python -c "import lockdown"` (expect no output) and `pytest dashboard/backend/tests/ -q` (all green).

- [ ] **Step 7: Commit**

```bash
git add lockdown_core.py lockdown.py dashboard/backend/tests/test_lockdown_core.py
git commit -m "refactor: extract lockdown antispam logic into lockdown_core for reuse"
```

---

### Task 7: Lockdown API routes + register all Phase 2a routes in `create_app`

**Files:**
- Create: `dashboard/backend/routes/lockdown.py`
- Modify: `dashboard/backend/app.py` (add two imports + two `add_routes` lines inside `create_app`)
- Test: `dashboard/backend/tests/test_lockdown_routes.py`

**Interfaces:**
- Consumes: `lockdown_core` (Task 6), `require_dashboard_access` (Task 1).
- Produces: `routes` table with `GET /api/lockdown/status` → `{active: bool, role_count: int}`, `POST /api/lockdown/activate` → `{ok, modified_count, errors}`, `POST /api/lockdown/deactivate` → `{ok, restored_count, errors}` or 409 `{"error": "not_active"}` when there is no backup. After this task the real `create_app` serves every Phase 2a endpoint.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_lockdown_routes.py`:

```python
import pytest

import lockdown_core
from dashboard.backend.routes.lockdown import routes as lockdown_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def isolated_backup(tmp_path, monkeypatch):
    monkeypatch.setattr(lockdown_core, "BACKUP_FILE", str(tmp_path / "antispam_backup.json"))


def build(roles=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator], roles=roles or []))
    return bot, make_moderation_app(bot, [lockdown_routes])


@pytest.mark.asyncio
async def test_status_inactive_by_default(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.get("/api/lockdown/status")
    assert resp.status == 200
    assert await resp.json() == {"active": False, "role_count": 0}


@pytest.mark.asyncio
async def test_activate_then_status_then_deactivate(aiohttp_client):
    noisy = FakeRole(2, position=5)
    noisy.permissions.mention_everyone = True
    bot, app = build(roles=[noisy])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/lockdown/activate")
    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert body["modified_count"] == 1
    assert len(bot.sent_logs) == 1

    resp = await client.get("/api/lockdown/status")
    assert (await resp.json())["active"] is True

    resp = await client.post("/api/lockdown/deactivate")
    assert resp.status == 200
    assert (await resp.json())["ok"] is True
    assert len(bot.sent_logs) == 2


@pytest.mark.asyncio
async def test_deactivate_without_backup_409(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.post("/api/lockdown/deactivate")
    assert resp.status == 409


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/lockdown/status")
    assert resp.status == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_lockdown_routes.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.routes.lockdown'`

- [ ] **Step 3: Implement `dashboard/backend/routes/lockdown.py`**

```python
import discord
from aiohttp import web

import lockdown_core
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


async def _log(bot, title: str, color, moderator, lines: dict):
    embed = discord.Embed(title=title, color=color, timestamp=bot.utcnow())
    embed.add_field(name="Кто", value=f"{moderator.name} (`{moderator.id}`)", inline=False)
    for name, value in lines.items():
        embed.add_field(name=name, value=value, inline=True)
    embed.set_footer(text="Dashboard · Lockdown")
    await bot.send_log(embed)


@routes.get("/api/lockdown/status")
@require_dashboard_access
async def lockdown_status(request: web.Request) -> web.Response:
    active, role_count = lockdown_core.antispam_status()
    return web.json_response({"active": active, "role_count": role_count})


@routes.post("/api/lockdown/activate")
@require_dashboard_access
async def lockdown_activate(request: web.Request) -> web.Response:
    guild = request.app["bot"].get_guild(request.app["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    modified_count, errors = await lockdown_core.activate_antispam(
        guild,
        lockdown_core.get_mention_exempt_ids(),
        lockdown_core.get_mentionable_exempt_ids(),
    )
    await _log(
        request.app["bot"], "🛡️ Антиспам ВКЛЮЧЁН (дашборд)", discord.Color.red(),
        request["moderator"], {"Изменено ролей": str(modified_count)},
    )
    return web.json_response({"ok": True, "modified_count": modified_count, "errors": errors})


@routes.post("/api/lockdown/deactivate")
@require_dashboard_access
async def lockdown_deactivate(request: web.Request) -> web.Response:
    guild = request.app["bot"].get_guild(request.app["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    result = await lockdown_core.deactivate_antispam(guild)
    if result is None:
        return web.json_response({"error": "not_active"}, status=409)

    restored_count, errors = result
    await _log(
        request.app["bot"], "🟢 Антиспам ВЫКЛЮЧЕН (дашборд)", discord.Color.green(),
        request["moderator"], {"Восстановлено ролей": str(restored_count)},
    )
    return web.json_response({"ok": True, "restored_count": restored_count, "errors": errors})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_lockdown_routes.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Register both route tables in `create_app`**

In `dashboard/backend/app.py`, after `from .auth import routes as auth_routes` add:

```python
from .routes.lockdown import routes as lockdown_routes
from .routes.moderation import routes as moderation_routes
```

and after `app.add_routes(auth_routes)` add:

```python
    app.add_routes(moderation_routes)
    app.add_routes(lockdown_routes)
```

- [ ] **Step 6: Run the full backend suite** — `pytest dashboard/backend/tests/ -q` — all green (the Phase 1 `test_app.py` health/startup tests confirm `create_app` still builds).

- [ ] **Step 7: Commit**

```bash
git add dashboard/backend/routes/lockdown.py dashboard/backend/app.py dashboard/backend/tests/test_lockdown_routes.py
git commit -m "feat(dashboard): add lockdown API routes and register phase 2a routes"
```

---

### Task 8: Frontend API client extensions

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts` (append; do NOT change existing exports)
- Test: `dashboard/frontend/src/api/moderation.test.ts`

**Interfaces:**
- Consumes: nothing new; lives beside Phase 1's `fetchCurrentUser`/`logout`/`loginUrl` (untouched — their 5 tests must stay green).
- Produces (all exported from `client.ts`): `class ApiError extends Error { status: number }`; interfaces `MemberSummary`, `MembersPage`, `RoleChip { id, name, color }`, `MemberDetail`, `RoleInfo { id, name, color, position }`, `LockdownStatus { active, role_count }`; functions `fetchMembers(search: string, page: number, pageSize?: number): Promise<MembersPage>`, `fetchMemberDetail(id: string): Promise<MemberDetail>`, `banMember(id: string, reason: string, deleteMessageDays: 0 | 1 | 7): Promise<void>`, `kickMember(id: string, reason: string): Promise<void>`, `fetchRoles(): Promise<RoleInfo[]>`, `grantRole(memberId: string, roleId: string): Promise<void>`, `revokeRole(memberId: string, roleId: string): Promise<void>`, `fetchLockdownStatus(): Promise<LockdownStatus>`, `activateLockdown(): Promise<void>`, `deactivateLockdown(): Promise<void>`.

- [ ] **Step 1: Write the failing test**

`dashboard/frontend/src/api/moderation.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ApiError,
  banMember,
  fetchLockdownStatus,
  fetchMembers,
  grantRole,
} from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('moderation api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchMembers builds query string and returns page', async () => {
    const page = { total: 1, page: 2, page_size: 20, members: [] }
    const fetchMock = vi.fn().mockResolvedValue(okJson(page))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchMembers('sharp', 2)
    expect(result).toEqual(page)
    const url = fetchMock.mock.calls[0][0] as string
    expect(url).toContain('/api/members?')
    expect(url).toContain('search=sharp')
    expect(url).toContain('page=2')
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ credentials: 'include' })
  })

  it('banMember POSTs reason and delete days', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await banMember('42', 'спам', 7)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/members/42/ban',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify({ reason: 'спам', delete_message_days: 7 }),
      }),
    )
  })

  it('grantRole POSTs role id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await grantRole('42', '7')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/members/42/roles',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ role_id: '7' }) }),
    )
  })

  it('throws ApiError with status on failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, status: 403, json: async () => ({ error: 'forbidden_by_discord' }) }),
    )
    await expect(fetchLockdownStatus()).rejects.toMatchObject({ status: 403 })
    await expect(fetchLockdownStatus()).rejects.toBeInstanceOf(ApiError)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd dashboard/frontend && npm run test`
Expected: FAIL — new exports don't exist.

- [ ] **Step 3: Append to `dashboard/frontend/src/api/client.ts`** (leave everything already there untouched)

```ts
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { credentials: 'include', ...init })
  if (!response.ok) {
    let detail = ''
    try {
      detail = ((await response.json()) as { error?: string }).error ?? ''
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(response.status, detail || `HTTP ${response.status}`)
  }
  return response.json() as Promise<T>
}

const jsonInit = (method: string, body?: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
})

export interface MemberSummary {
  id: string
  username: string
  display_name: string
  avatar: string | null
  role_count: number
  joined_at: string | null
  is_bot: boolean
}

export interface MembersPage {
  total: number
  page: number
  page_size: number
  members: MemberSummary[]
}

export interface RoleChip {
  id: string
  name: string
  color: string
}

export interface MemberDetail extends Omit<MemberSummary, 'role_count'> {
  created_at: string
  roles: RoleChip[]
  invite_stats: { joins: number; leaves: number; invites: number }
  feedback_case_count: number
}

export interface RoleInfo extends RoleChip {
  position: number
}

export interface LockdownStatus {
  active: boolean
  role_count: number
}

export function fetchMembers(search: string, page: number, pageSize = 20): Promise<MembersPage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (search) params.set('search', search)
  return apiFetch(`/api/members?${params}`)
}

export function fetchMemberDetail(id: string): Promise<MemberDetail> {
  return apiFetch(`/api/members/${id}`)
}

export async function banMember(id: string, reason: string, deleteMessageDays: 0 | 1 | 7): Promise<void> {
  await apiFetch(`/api/members/${id}/ban`, jsonInit('POST', { reason, delete_message_days: deleteMessageDays }))
}

export async function kickMember(id: string, reason: string): Promise<void> {
  await apiFetch(`/api/members/${id}/kick`, jsonInit('POST', { reason }))
}

export async function fetchRoles(): Promise<RoleInfo[]> {
  const body = await apiFetch<{ roles: RoleInfo[] }>('/api/roles')
  return body.roles
}

export async function grantRole(memberId: string, roleId: string): Promise<void> {
  await apiFetch(`/api/members/${memberId}/roles`, jsonInit('POST', { role_id: roleId }))
}

export async function revokeRole(memberId: string, roleId: string): Promise<void> {
  await apiFetch(`/api/members/${memberId}/roles/${roleId}`, jsonInit('DELETE'))
}

export function fetchLockdownStatus(): Promise<LockdownStatus> {
  return apiFetch('/api/lockdown/status')
}

export async function activateLockdown(): Promise<void> {
  await apiFetch('/api/lockdown/activate', jsonInit('POST'))
}

export async function deactivateLockdown(): Promise<void> {
  await apiFetch('/api/lockdown/deactivate', jsonInit('POST'))
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test`
Expected: PASS — 4 new + all 8 existing (12 total).

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/moderation.test.ts
git commit -m "feat(dashboard): add moderation/lockdown API client functions"
```

---

### Task 9: Modal component + shell layout with nested routes

**Files:**
- Create: `dashboard/frontend/src/components/ui/Modal.tsx`
- Create: `dashboard/frontend/src/pages/Home.tsx`
- Modify: `dashboard/frontend/src/pages/DashboardShell.tsx` (sidebar links + `<Outlet/>`)
- Modify: `dashboard/frontend/src/App.tsx` (nested routes)
- Test: `dashboard/frontend/src/components/Modal.test.tsx`

**Interfaces:**
- Consumes: design tokens + `Card` (Phase 1), `useAuth`, `logout`.
- Produces: `Modal({ open, title, children, onClose })` — overlay dialog used by Task 10's confirm flows; `DashboardShell` becomes a layout rendering `<Outlet/>`; routes `/` (index → `Home`), `/members`, `/lockdown` (pages arrive in Tasks 10-11; until then temporary placeholders defined here keep the app compiling).

- [ ] **Step 1: Write the failing test**

`dashboard/frontend/src/components/Modal.test.tsx`:

```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Modal } from './ui/Modal'

describe('Modal', () => {
  it('renders nothing when closed', () => {
    render(
      <Modal open={false} title="Заголовок" onClose={() => {}}>
        <p>Контент</p>
      </Modal>,
    )
    expect(screen.queryByText('Заголовок')).not.toBeInTheDocument()
  })

  it('renders title and children when open, closes on overlay click and Escape', () => {
    const onClose = vi.fn()
    render(
      <Modal open title="Подтверждение" onClose={onClose}>
        <p>Точно?</p>
      </Modal>,
    )
    expect(screen.getByText('Подтверждение')).toBeInTheDocument()
    expect(screen.getByText('Точно?')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('modal-overlay'))
    expect(onClose).toHaveBeenCalledTimes(1)

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(2)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test`
Expected: FAIL — `Cannot find module './ui/Modal'`.

- [ ] **Step 3: Implement `dashboard/frontend/src/components/ui/Modal.tsx`**

```tsx
import { useEffect, type ReactNode } from 'react'

interface ModalProps {
  open: boolean
  title: string
  children: ReactNode
  onClose: () => void
}

export function Modal({ open, title, children, onClose }: ModalProps) {
  useEffect(() => {
    if (!open) return
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      data-testid="modal-overlay"
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        className="animate-dropdown-in w-full max-w-md rounded-card border border-border bg-surface p-5 shadow-[0_12px_28px_-8px_rgba(0,0,0,0.6)]"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="mb-4 text-lg font-semibold text-foreground">{title}</h2>
        {children}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create `dashboard/frontend/src/pages/Home.tsx`** (welcome card moved out of the shell)

```tsx
import { Card } from '../components/ui/Card'
import { useAuth } from '../context/AuthContext'

export function HomePage() {
  const { user } = useAuth()
  return (
    <Card className="animate-fade-in-up max-w-2xl">
      <h1 className="text-lg font-semibold text-foreground">Добро пожаловать, {user?.username}</h1>
      <p className="mt-2 text-sm text-muted">
        Выберите раздел слева. «Участники и роли» и «Lockdown и модерация» уже работают —
        остальные разделы появятся в следующих фазах.
      </p>
    </Card>
  )
}
```

- [ ] **Step 5: Rewrite `dashboard/frontend/src/pages/DashboardShell.tsx`**

Keep the existing header (logo, user `Dropdown` with logout — unchanged), replace the sidebar/main body:

```tsx
import {
  CalendarCheck,
  ChatCircleText,
  GearSix,
  ShieldWarning,
  SignOut,
  Sparkle,
  Stack,
  UsersThree,
  type Icon,
} from '@phosphor-icons/react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { logout } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Dropdown, DropdownItem } from '../components/ui/Dropdown'

interface Section {
  label: string
  icon: Icon
  to?: string
}

const SECTIONS: Section[] = [
  { label: 'Feedback и тикеты', icon: ChatCircleText },
  { label: 'Конструктор кнопок и эмбедов', icon: Stack },
  { label: 'События и голосования', icon: CalendarCheck },
  { label: 'Lockdown и модерация', icon: ShieldWarning, to: '/lockdown' },
  { label: 'Участники и роли', icon: UsersThree, to: '/members' },
  { label: 'Конфигурация', icon: GearSix },
]

export function DashboardShell() {
  const { user, refresh } = useAuth()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      await logout()
      await refresh()
    } catch (error) {
      console.error('Failed to log out:', error)
    } finally {
      setIsLoggingOut(false)
    }
  }

  const itemBase =
    'flex items-center justify-between gap-3 rounded-control border border-border bg-surface p-3 text-sm transition-colors duration-200 ease-out'

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-2 text-foreground">
          <Sparkle size={20} weight="fill" className="text-primary" />
          <span className="font-semibold">Панель управления ботом</span>
        </div>

        <Dropdown
          trigger={
            <span className="flex items-center gap-2 rounded-control px-2 py-1.5 hover:bg-surface-hover">
              {user?.avatar ? (
                <img src={user.avatar} alt="" className="h-7 w-7 rounded-full" />
              ) : (
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-muted text-xs font-semibold text-primary">
                  {user?.username?.slice(0, 1).toUpperCase()}
                </span>
              )}
              <span className="text-sm text-foreground">{user?.username}</span>
            </span>
          }
        >
          <DropdownItem onClick={handleLogout} danger>
            <SignOut size={16} />
            {isLoggingOut ? 'Выходим…' : 'Выйти'}
          </DropdownItem>
        </Dropdown>
      </header>

      <div className="flex flex-1">
        <aside className="w-72 shrink-0 border-r border-border p-4">
          <nav className="flex flex-col gap-2">
            {SECTIONS.map(({ label, icon: SectionIcon, to }, index) =>
              to ? (
                <NavLink
                  key={label}
                  to={to}
                  style={{ animationDelay: `${index * 40}ms` }}
                  className={({ isActive }) =>
                    `animate-fade-in-up ${itemBase} cursor-pointer hover:bg-surface-hover ${
                      isActive ? 'border-primary/60 bg-primary-muted text-foreground' : 'text-foreground'
                    }`
                  }
                >
                  <span className="flex items-center gap-3">
                    <SectionIcon size={18} className="text-muted" />
                    {label}
                  </span>
                </NavLink>
              ) : (
                <div
                  key={label}
                  style={{ animationDelay: `${index * 40}ms` }}
                  className={`animate-fade-in-up ${itemBase} text-muted`}
                >
                  <span className="flex items-center gap-3">
                    <SectionIcon size={18} className="text-muted" />
                    {label}
                  </span>
                  <span className="rounded-full bg-surface-hover px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted">
                    скоро
                  </span>
                </div>
              ),
            )}
          </nav>
        </aside>

        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Rewrite `dashboard/frontend/src/App.tsx` with nested routes**

Until Tasks 10-11 land, `/members` and `/lockdown` point at inline placeholders so the app compiles:

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/Login'
import { AccessDeniedPage } from './pages/AccessDenied'
import { DashboardShell } from './pages/DashboardShell'
import { HomePage } from './pages/Home'

function App() {
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
          >
            <Route index element={<HomePage />} />
            <Route path="members" element={<div>Участники — скоро (Task 10)</div>} />
            <Route path="lockdown" element={<div>Lockdown — скоро (Task 11)</div>} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
```

- [ ] **Step 7: Run tests + typecheck**

Run: `npm run test` (Modal tests + all previous pass; the existing ProtectedRoute tests render `DashboardShell` children — if the "renders children when a user is authenticated" test asserts on text now moved to `HomePage`, update that assertion to match the shell's header text `Панель управления ботом` instead) and `npx tsc --noEmit`.
Expected: all green, no type errors.

- [ ] **Step 8: Commit**

```bash
git add dashboard/frontend/src
git commit -m "feat(dashboard): add Modal, nested routing, sidebar nav links"
```

---

### Task 10: Members page (search + list + detail panel with ban/kick/roles)

**Files:**
- Create: `dashboard/frontend/src/pages/Members.tsx`
- Create: `dashboard/frontend/src/pages/MemberDetailPanel.tsx`
- Modify: `dashboard/frontend/src/App.tsx` (replace `/members` placeholder)
- Test: `dashboard/frontend/src/pages/Members.test.tsx`

**Interfaces:**
- Consumes: `fetchMembers`, `fetchMemberDetail`, `banMember`, `kickMember`, `fetchRoles`, `grantRole`, `revokeRole`, types (Task 8); `Card`, `Button`, `Dropdown`/`DropdownItem`, `Modal` (Phase 1 + Task 9).
- Produces: `MembersPage` component (default view: search input, paginated card list, click → detail panel); `MemberDetailPanel({ memberId, onClose, onActionDone })`.

- [ ] **Step 1: Write the failing test**

`dashboard/frontend/src/pages/Members.test.tsx`:

```tsx
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { MembersPage } from './Members'

const page = (members: Partial<client.MemberSummary>[], total = members.length): client.MembersPage => ({
  total,
  page: 1,
  page_size: 20,
  members: members.map((m, i) => ({
    id: String(i + 1),
    username: `user${i}`,
    display_name: `user${i}`,
    avatar: null,
    role_count: 0,
    joined_at: null,
    is_bot: false,
    ...m,
  })),
})

describe('MembersPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('loads and renders the first page of members', async () => {
    vi.spyOn(client, 'fetchMembers').mockResolvedValue(page([{ username: 'Alpha' }, { username: 'Beta' }]))
    render(
      <MemoryRouter>
        <MembersPage />
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByText('Alpha')).toBeInTheDocument())
    expect(screen.getByText('Beta')).toBeInTheDocument()
    expect(client.fetchMembers).toHaveBeenCalledWith('', 1)
  })

  it('debounces search input and refetches with the query', async () => {
    vi.useFakeTimers()
    const spy = vi.spyOn(client, 'fetchMembers').mockResolvedValue(page([]))
    render(
      <MemoryRouter>
        <MembersPage />
      </MemoryRouter>,
    )
    fireEvent.change(screen.getByPlaceholderText('Поиск по имени или нику…'), {
      target: { value: 'sharp' },
    })
    expect(spy).not.toHaveBeenCalledWith('sharp', 1)
    await vi.advanceTimersByTimeAsync(350)
    expect(spy).toHaveBeenCalledWith('sharp', 1)
    vi.useRealTimers()
  })

  it('opens the detail panel when a member is clicked', async () => {
    vi.spyOn(client, 'fetchMembers').mockResolvedValue(page([{ id: '42', username: 'Clicky' }]))
    vi.spyOn(client, 'fetchMemberDetail').mockResolvedValue({
      id: '42',
      username: 'Clicky',
      display_name: 'Clicky',
      avatar: null,
      joined_at: null,
      created_at: '2020-06-01T00:00:00+00:00',
      is_bot: false,
      roles: [],
      invite_stats: { joins: 0, leaves: 0, invites: 0 },
      feedback_case_count: 0,
    })
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(
      <MemoryRouter>
        <MembersPage />
      </MemoryRouter>,
    )
    await waitFor(() => screen.getByText('Clicky'))
    fireEvent.click(screen.getByText('Clicky'))
    await waitFor(() => expect(screen.getByText('Забанить')).toBeInTheDocument())
    expect(screen.getByText('Кикнуть')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test`
Expected: FAIL — `Cannot find module './Members'`.

- [ ] **Step 3: Implement `dashboard/frontend/src/pages/MemberDetailPanel.tsx`**

```tsx
import { X } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  banMember,
  fetchMemberDetail,
  fetchRoles,
  grantRole,
  kickMember,
  revokeRole,
  type MemberDetail,
  type RoleInfo,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Dropdown, DropdownItem } from '../components/ui/Dropdown'
import { Modal } from '../components/ui/Modal'

type PendingAction = 'ban' | 'kick' | null

interface Props {
  memberId: string
  onClose: () => void
  onActionDone: () => void
}

export function MemberDetailPanel({ memberId, onClose, onActionDone }: Props) {
  const [detail, setDetail] = useState<MemberDetail | null>(null)
  const [assignable, setAssignable] = useState<RoleInfo[]>([])
  const [pending, setPending] = useState<PendingAction>(null)
  const [reason, setReason] = useState('')
  const [deleteDays, setDeleteDays] = useState<0 | 1 | 7>(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const reload = () => {
    fetchMemberDetail(memberId).then(setDetail).catch(() => setError('Не удалось загрузить участника'))
    fetchRoles().then(setAssignable).catch(() => {})
  }

  useEffect(reload, [memberId])

  const confirmAction = async () => {
    if (!reason.trim()) {
      setError('Укажите причину')
      return
    }
    setBusy(true)
    setError('')
    try {
      if (pending === 'ban') await banMember(memberId, reason.trim(), deleteDays)
      if (pending === 'kick') await kickMember(memberId, reason.trim())
      setPending(null)
      setReason('')
      onActionDone()
      onClose()
    } catch {
      setError('Discord отклонил действие (не хватает прав?)')
    } finally {
      setBusy(false)
    }
  }

  const toggleRole = async (roleId: string, has: boolean) => {
    setBusy(true)
    setError('')
    try {
      if (has) await revokeRole(memberId, roleId)
      else await grantRole(memberId, roleId)
      reload()
    } catch {
      setError('Discord отклонил изменение роли')
    } finally {
      setBusy(false)
    }
  }

  if (!detail) {
    return (
      <Card className="animate-fade-in-up">
        <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
      </Card>
    )
  }

  const memberRoleIds = new Set(detail.roles.map((r) => r.id))

  return (
    <Card className="animate-fade-in-up flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {detail.avatar && <img src={detail.avatar} alt="" className="h-12 w-12 rounded-full" />}
          <div>
            <h2 className="font-semibold text-foreground">{detail.display_name}</h2>
            <p className="text-xs text-muted">@{detail.username} · {detail.id}</p>
          </div>
        </div>
        <button onClick={onClose} className="cursor-pointer text-muted hover:text-foreground">
          <X size={18} />
        </button>
      </div>

      <dl className="grid grid-cols-2 gap-2 text-sm">
        <dt className="text-muted">Вошёл на сервер</dt>
        <dd>{detail.joined_at ? new Date(detail.joined_at).toLocaleDateString('ru-RU') : '—'}</dd>
        <dt className="text-muted">Аккаунт создан</dt>
        <dd>{new Date(detail.created_at).toLocaleDateString('ru-RU')}</dd>
        <dt className="text-muted">Приглашения</dt>
        <dd>
          {detail.invite_stats.invites} (зашло {detail.invite_stats.joins}, ушло {detail.invite_stats.leaves})
        </dd>
        <dt className="text-muted">Обращений/жалоб</dt>
        <dd>{detail.feedback_case_count}</dd>
      </dl>

      <div>
        <h3 className="mb-2 text-sm font-medium text-muted">Роли</h3>
        <div className="flex flex-wrap gap-1.5">
          {detail.roles.map((role) => (
            <button
              key={role.id}
              onClick={() => toggleRole(role.id, true)}
              disabled={busy}
              title="Нажмите, чтобы снять роль"
              className="cursor-pointer rounded-full border border-border px-2.5 py-0.5 text-xs transition-colors hover:border-danger hover:text-danger"
              style={{ color: role.color !== '#000000' ? role.color : undefined }}
            >
              {role.name} ×
            </button>
          ))}
          <Dropdown
            align="left"
            trigger={
              <span className="rounded-full border border-dashed border-border px-2.5 py-0.5 text-xs text-muted hover:text-foreground">
                + добавить роль
              </span>
            }
          >
            {assignable
              .filter((r) => !memberRoleIds.has(r.id))
              .map((role) => (
                <DropdownItem key={role.id} onClick={() => toggleRole(role.id, false)}>
                  {role.name}
                </DropdownItem>
              ))}
          </Dropdown>
        </div>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      {!detail.is_bot && (
        <div className="flex gap-2 border-t border-border pt-4">
          <Button variant="danger" onClick={() => setPending('ban')} disabled={busy}>
            Забанить
          </Button>
          <Button variant="secondary" onClick={() => setPending('kick')} disabled={busy}>
            Кикнуть
          </Button>
        </div>
      )}

      <Modal
        open={pending !== null}
        title={pending === 'ban' ? `Забанить ${detail.display_name}?` : `Кикнуть ${detail.display_name}?`}
        onClose={() => setPending(null)}
      >
        <div className="flex flex-col gap-3">
          <label className="text-sm text-muted" htmlFor="mod-reason">
            Причина (обязательно)
          </label>
          <input
            id="mod-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            placeholder="Например: спам в общем чате"
          />
          {pending === 'ban' && (
            <>
              <label className="text-sm text-muted" htmlFor="mod-days">
                Удалить сообщения за
              </label>
              <select
                id="mod-days"
                value={deleteDays}
                onChange={(e) => setDeleteDays(Number(e.target.value) as 0 | 1 | 7)}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
              >
                <option value={0}>Не удалять</option>
                <option value={1}>1 день</option>
                <option value={7}>7 дней</option>
              </select>
            </>
          )}
          {error && <p className="text-sm text-danger">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setPending(null)} disabled={busy}>
              Отмена
            </Button>
            <Button variant="danger" onClick={confirmAction} disabled={busy}>
              {busy ? 'Выполняем…' : 'Подтвердить'}
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  )
}
```

- [ ] **Step 4: Implement `dashboard/frontend/src/pages/Members.tsx`**

```tsx
import { MagnifyingGlass } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchMembers, type MembersPage as MembersPageData } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { MemberDetailPanel } from './MemberDetailPanel'

export function MembersPage() {
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<MembersPageData | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebounced(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    fetchMembers(debounced, page)
      .then((result) => {
        setData(result)
        setError('')
      })
      .catch(() => setError('Не удалось загрузить участников'))
  }, [debounced, page])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <div className="relative mb-4 max-w-md">
          <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск по имени или нику…"
            className="w-full rounded-control border border-border bg-surface py-2 pl-9 pr-3 text-sm text-foreground outline-none focus:border-primary"
          />
        </div>

        {error && <p className="mb-4 text-sm text-danger">{error}</p>}

        <div className="flex flex-col gap-2">
          {data?.members.map((member) => (
            <Card
              key={member.id}
              interactive
              className="!p-3"
              onClick={() => setSelectedId(member.id)}
            >
              <div className="flex items-center gap-3">
                {member.avatar ? (
                  <img src={member.avatar} alt="" className="h-9 w-9 rounded-full" />
                ) : (
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-muted text-xs font-semibold text-primary">
                    {member.username.slice(0, 1).toUpperCase()}
                  </span>
                )}
                <div className="flex-1">
                  <p className="text-sm text-foreground">{member.display_name}</p>
                  <p className="text-xs text-muted">
                    @{member.username}
                    {member.is_bot && ' · бот'} · ролей: {member.role_count}
                  </p>
                </div>
              </div>
            </Card>
          ))}
          {data && data.members.length === 0 && (
            <p className="text-sm text-muted">Никого не найдено.</p>
          )}
        </div>

        {data && totalPages > 1 && (
          <div className="mt-4 flex items-center gap-3">
            <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Назад
            </Button>
            <span className="text-sm text-muted">
              {page} / {totalPages}
            </span>
            <Button
              variant="secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Вперёд
            </Button>
          </div>
        )}
      </div>

      {selectedId && (
        <div className="w-96 shrink-0">
          <MemberDetailPanel
            memberId={selectedId}
            onClose={() => setSelectedId(null)}
            onActionDone={() => fetchMembers(debounced, page).then(setData).catch(() => {})}
          />
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Replace the `/members` placeholder in `App.tsx`**

```tsx
import { MembersPage } from './pages/Members'
// ...
<Route path="members" element={<MembersPage />} />
```

- [ ] **Step 6: Run tests + typecheck**

Run: `npm run test` and `npx tsc --noEmit`
Expected: all green (3 new Members tests + everything prior).

- [ ] **Step 7: Commit**

```bash
git add dashboard/frontend/src
git commit -m "feat(dashboard): add members page with search, detail panel, ban/kick/roles"
```

---

### Task 11: Lockdown page

**Files:**
- Create: `dashboard/frontend/src/pages/Lockdown.tsx`
- Modify: `dashboard/frontend/src/App.tsx` (replace `/lockdown` placeholder)
- Test: `dashboard/frontend/src/pages/Lockdown.test.tsx`

**Interfaces:**
- Consumes: `fetchLockdownStatus`, `activateLockdown`, `deactivateLockdown` (Task 8); `Card`, `Button`, `Modal` (Task 9).

- [ ] **Step 1: Write the failing test**

`dashboard/frontend/src/pages/Lockdown.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { LockdownPage } from './Lockdown'

describe('LockdownPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows inactive status', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    render(<LockdownPage />)
    await waitFor(() => expect(screen.getByText(/выключен/i)).toBeInTheDocument())
    expect(screen.getByText('Включить антиспам')).toBeInTheDocument()
  })

  it('activates after confirmation and refreshes status', async () => {
    const statusSpy = vi
      .spyOn(client, 'fetchLockdownStatus')
      .mockResolvedValueOnce({ active: false, role_count: 0 })
      .mockResolvedValueOnce({ active: true, role_count: 3 })
    const activateSpy = vi.spyOn(client, 'activateLockdown').mockResolvedValue()

    render(<LockdownPage />)
    await waitFor(() => screen.getByText('Включить антиспам'))
    fireEvent.click(screen.getByText('Включить антиспам'))
    fireEvent.click(screen.getByText('Подтвердить'))

    await waitFor(() => expect(activateSpy).toHaveBeenCalled())
    await waitFor(() => expect(statusSpy).toHaveBeenCalledTimes(2))
    expect(screen.getByText(/включён/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test`
Expected: FAIL — `Cannot find module './Lockdown'`.

- [ ] **Step 3: Implement `dashboard/frontend/src/pages/Lockdown.tsx`**

```tsx
import { ShieldCheck, ShieldWarning } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  activateLockdown,
  deactivateLockdown,
  fetchLockdownStatus,
  type LockdownStatus,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'

export function LockdownPage() {
  const [status, setStatus] = useState<LockdownStatus | null>(null)
  const [confirming, setConfirming] = useState<'activate' | 'deactivate' | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const reload = () => {
    fetchLockdownStatus()
      .then((s) => {
        setStatus(s)
        setError('')
      })
      .catch(() => setError('Не удалось получить статус'))
  }

  useEffect(reload, [])

  const confirm = async () => {
    setBusy(true)
    setError('')
    try {
      if (confirming === 'activate') await activateLockdown()
      if (confirming === 'deactivate') await deactivateLockdown()
      setConfirming(null)
      reload()
    } catch {
      setError('Операция не удалась — подробности в логах бота')
    } finally {
      setBusy(false)
    }
  }

  if (!status) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  return (
    <Card className="animate-fade-in-up max-w-xl">
      <div className="flex items-center gap-3">
        {status.active ? (
          <ShieldWarning size={28} weight="fill" className="text-danger" />
        ) : (
          <ShieldCheck size={28} weight="fill" className="text-success" />
        )}
        <div>
          <h1 className="font-semibold text-foreground">
            Антиспам-режим: {status.active ? 'ВКЛЮЧЁН' : 'ВЫКЛЮЧЕН'}
          </h1>
          <p className="text-sm text-muted">
            {status.active
              ? `Изменённых ролей в бэкапе: ${status.role_count}`
              : 'Все роли работают в обычном режиме.'}
          </p>
        </div>
      </div>

      {error && <p className="mt-3 text-sm text-danger">{error}</p>}

      <div className="mt-5 flex gap-2">
        {status.active ? (
          <Button variant="secondary" onClick={() => setConfirming('deactivate')} disabled={busy}>
            Выключить антиспам
          </Button>
        ) : (
          <Button variant="danger" onClick={() => setConfirming('activate')} disabled={busy}>
            Включить антиспам
          </Button>
        )}
      </div>

      <Modal
        open={confirming !== null}
        title={confirming === 'activate' ? 'Включить антиспам-режим?' : 'Выключить антиспам-режим?'}
        onClose={() => setConfirming(null)}
      >
        <p className="mb-4 text-sm text-muted">
          {confirming === 'activate'
            ? 'У всех не-исключённых ролей будут сняты права massive mention, текущее состояние сохранится в бэкап.'
            : 'Права ролей будут восстановлены из бэкапа.'}
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setConfirming(null)} disabled={busy}>
            Отмена
          </Button>
          <Button variant="danger" onClick={confirm} disabled={busy}>
            {busy ? 'Выполняем…' : 'Подтвердить'}
          </Button>
        </div>
      </Modal>
    </Card>
  )
}
```

- [ ] **Step 4: Replace the `/lockdown` placeholder in `App.tsx`**

```tsx
import { LockdownPage } from './pages/Lockdown'
// ...
<Route path="lockdown" element={<LockdownPage />} />
```

- [ ] **Step 5: Run tests + typecheck + build**

Run: `npm run test`, `npx tsc --noEmit`, `npm run build`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add dashboard/frontend/src
git commit -m "feat(dashboard): add lockdown control page"
```

---

### Task 12: Full end-to-end manual verification

**Files:** none (verification only).

- [ ] **Step 1:** Start backend (`python main.py`) and frontend (`cd dashboard/frontend && npm run dev`), log in at `http://localhost:5173` with an authorized account.
- [ ] **Step 2:** Sidebar: «Участники и роли» and «Lockdown и модерация» are highlighted links; the other four still show «скоро».
- [ ] **Step 3:** `/members`: list loads; search finds a member by both username and server nickname; pagination works on >20 members.
- [ ] **Step 4:** Click a member: card shows join/created dates, invite stats, roles. Add a harmless test role via «+ добавить роль», confirm it appears in Discord; remove it by clicking the role chip.
- [ ] **Step 5:** On a **disposable test account**: kick with a reason → confirm the account is kicked and the log embed appears in `LOG_CHANNEL_ID`. Re-invite, then ban with «1 день» message deletion → confirm ban + log embed; unban manually in Discord afterwards.
- [ ] **Step 6:** `/lockdown`: status shows ВЫКЛЮЧЕН; activate → Discord roles change, log embed sent, status flips to ВКЛЮЧЁН with role count; `/antispam status` slash command agrees; deactivate → roles restored, both UIs agree.
- [ ] **Step 7:** Negative check: try to ban a member whose top role is above the bot's → dashboard shows the «Discord отклонил действие» error, no crash.
- [ ] **Step 8:** Record results in the progress ledger. No commit (nothing changed).

---

## Self-Review Notes

- **Spec coverage:** every endpoint in the spec's API table maps to Tasks 2-5/7; `@require_dashboard_access` → Task 1; lockdown refactor with unchanged slash-command UX → Task 6; frontend pages + sidebar links → Tasks 9-11; manual verification → Task 12. `deactivate_antispam -> ... | None` is a documented refinement of the spec signature (None = нет бэкапа), consumed consistently in Tasks 6, 7 and the cog.
- **Type consistency:** `request["moderator"]` (Tasks 1→4/5/7); `routes` table shared across Tasks 2-5 (one `moderation.py`); frontend types in Task 8 match the JSON shapes produced in Tasks 2-5/7 field-for-field; `FakeRole.color.value`/`FakePermissions` match how serializers and `lockdown_core` read them.
- **Known deviation to respect:** existing Phase 1 tests may reference text moved from `DashboardShell` to `HomePage` (Task 9 Step 7 addresses this explicitly).
