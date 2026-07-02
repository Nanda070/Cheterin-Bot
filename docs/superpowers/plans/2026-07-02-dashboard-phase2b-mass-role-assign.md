# Дашборд, Фаза 2b (Массовая выдача роли) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add mass role assignment (selected members / all / all-except-bots) as a background job with progress polling, reusing Phase 2a's access control, role-assignability checks, and design system.

**Architecture:** New module `dashboard/backend/mass_role_jobs.py` holds job state (in-memory dict) and the orchestration coroutine, kept independent of aiohttp so it can be awaited directly in tests. Two new routes appended to the existing `dashboard/backend/routes/moderation.py` route table (already registered in `create_app` — no `app.py` changes needed this phase). Frontend: one new self-contained `MassAssignModal.tsx` wired into `Members.tsx` via a single button, using real-timer polling (not fake timers — see Global Constraints).

**Tech Stack:** Python: aiohttp, discord.py, pytest + pytest-aiohttp (existing fakes). Frontend: React + TypeScript, existing `Modal`/`Button` primitives, Vitest + Testing Library.

## Global Constraints

- All work happens in `C:\Users\adnan\Documents\coding\ChetMain_backup_20260701_211729`. Never touch `C:\Users\adnan\Documents\coding\ChetMain`.
- Local-only git repo: commit each task with `git add <specific files>` + `git commit` — never bare `git add -A`/`git add .` (a Phase 2a task once swept in an unrelated 29k-line directory this way).
- Spec of record: `docs/superpowers/specs/2026-07-02-dashboard-phase2b-mass-role-assign-design.md`.
- Only mass **grant** is implemented — no mass revoke.
- Only one active job at a time: a second `POST .../mass-assign` while one is `"running"` → `409 {"error": "job_already_running"}`.
- `processed == succeeded + skipped + failed` must hold at every point; `total` counts every input (including invalid `selected` member ids, which are pre-counted as `failed`).
- Discord reason format reuses `dashboard_reason(reason, moderator)` from `moderation.py` exactly as Phase 2a uses it.
- **Frontend tests: no `vi.useFakeTimers()`/`vi.advanceTimersByTimeAsync`.** A Phase 2a task lost significant time to a `vi.useFakeTimers()`/React-19-effect-scheduling incompatibility. Use real timers with `waitFor` (Testing Library) throughout.
- No secrets in any committed file.
- Existing suites must stay green throughout: 74 pytest + 19 Vitest tests before this phase.

---

### Task 1: `mass_role_jobs.py` — job state + orchestration coroutine

**Files:**
- Create: `dashboard/backend/mass_role_jobs.py`
- Test: `dashboard/backend/tests/test_mass_role_jobs.py`

**Interfaces:**
- Consumes: `dashboard.backend.tests.fakes.FakeGuild/FakeMember/FakeRole` (existing).
- Produces: `@dataclass class MassAssignJob(status: str, total: int, processed: int = 0, succeeded: int = 0, skipped: int = 0, failed: int = 0, errors: list[str] = field(default_factory=list))`; module-level `JOBS: dict[str, MassAssignJob]`; `MAX_ERRORS = 20`; `async def run_mass_assign(job_id: str, guild, role, members: list, moderator, dashboard_reason: Callable) -> None` (mutates `JOBS[job_id]` in place, sets `status="completed"` when done). `dashboard_reason` is passed in as a callable (not imported) to avoid a circular import with `routes/moderation.py`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_mass_role_jobs.py`:

```python
import discord
import pytest

from dashboard.backend.mass_role_jobs import JOBS, MassAssignJob, run_mass_assign
from dashboard.backend.tests.fakes import FakeGuild, FakeMember, FakeRole


class _StubForbidden(discord.Forbidden):
    def __init__(self):
        pass


def _dashboard_reason(reason, moderator):
    return f"Dashboard: {reason} — by {moderator.name} ({moderator.id})"


@pytest.fixture(autouse=True)
def clear_jobs():
    JOBS.clear()
    yield
    JOBS.clear()


@pytest.mark.asyncio
async def test_assigns_role_to_all_members_without_it():
    role = FakeRole(7, name="VIP", position=5)
    members = [FakeMember(100 + i, name=f"m{i}") for i in range(3)]
    guild = FakeGuild(members=members, roles=[role])
    moderator = FakeMember(10, name="mod")

    JOBS["job-1"] = MassAssignJob(status="running", total=len(members))
    await run_mass_assign("job-1", guild, role, members, moderator, _dashboard_reason)

    job = JOBS["job-1"]
    assert job.status == "completed"
    assert job.succeeded == 3
    assert job.skipped == 0
    assert job.failed == 0
    assert job.processed == 3
    for member in members:
        action, kwargs = member.action_calls[0]
        assert action == "add_roles"
        assert kwargs["role"].id == 7
        assert "Dashboard: массовая выдача роли VIP" in kwargs["reason"]
        assert "(10)" in kwargs["reason"]


@pytest.mark.asyncio
async def test_skips_members_who_already_have_the_role():
    role = FakeRole(7, name="VIP", position=5)
    already_has = FakeMember(100, name="has-it", roles=[FakeRole(7, name="VIP", position=5)])
    needs_it = FakeMember(101, name="needs-it")
    members = [already_has, needs_it]
    guild = FakeGuild(members=members, roles=[role])
    moderator = FakeMember(10, name="mod")

    JOBS["job-1"] = MassAssignJob(status="running", total=len(members))
    await run_mass_assign("job-1", guild, role, members, moderator, _dashboard_reason)

    job = JOBS["job-1"]
    assert job.skipped == 1
    assert job.succeeded == 1
    assert already_has.action_calls == []
    assert needs_it.action_calls[0][0] == "add_roles"


@pytest.mark.asyncio
async def test_continues_after_one_member_fails():
    role = FakeRole(7, name="VIP", position=5)
    broken = FakeMember(100, name="broken")
    broken.action_raises = _StubForbidden()
    fine = FakeMember(101, name="fine")
    members = [broken, fine]
    guild = FakeGuild(members=members, roles=[role])
    moderator = FakeMember(10, name="mod")

    JOBS["job-1"] = MassAssignJob(status="running", total=len(members))
    await run_mass_assign("job-1", guild, role, members, moderator, _dashboard_reason)

    job = JOBS["job-1"]
    assert job.status == "completed"
    assert job.failed == 1
    assert job.succeeded == 1
    assert job.processed == 2
    assert len(job.errors) == 1
    assert "broken" in job.errors[0]


@pytest.mark.asyncio
async def test_processed_equals_sum_of_outcomes():
    role = FakeRole(7, name="VIP", position=5)
    members = [FakeMember(100 + i, name=f"m{i}") for i in range(5)]
    guild = FakeGuild(members=members, roles=[role])
    moderator = FakeMember(10, name="mod")

    JOBS["job-1"] = MassAssignJob(status="running", total=len(members))
    await run_mass_assign("job-1", guild, role, members, moderator, _dashboard_reason)

    job = JOBS["job-1"]
    assert job.processed == job.succeeded + job.skipped + job.failed
    assert job.processed == job.total
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_mass_role_jobs.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.mass_role_jobs'`

- [ ] **Step 3: Implement `dashboard/backend/mass_role_jobs.py`**

```python
import asyncio
from dataclasses import dataclass, field
from typing import Callable

import discord

MAX_ERRORS = 20


@dataclass
class MassAssignJob:
    status: str  # "running" | "completed" | "failed"
    total: int
    processed: int = 0
    succeeded: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list = field(default_factory=list)


JOBS: dict[str, MassAssignJob] = {}


async def run_mass_assign(
    job_id: str,
    guild,
    role,
    members: list,
    moderator,
    dashboard_reason: Callable[[str, object], str],
) -> None:
    job = JOBS[job_id]
    semaphore = asyncio.Semaphore(3)

    async def process(member) -> None:
        if any(r.id == role.id for r in member.roles):
            job.skipped += 1
        else:
            async with semaphore:
                try:
                    await member.add_roles(
                        role,
                        reason=dashboard_reason(f"массовая выдача роли {role.name}", moderator),
                    )
                    job.succeeded += 1
                except discord.HTTPException as exc:
                    job.failed += 1
                    if len(job.errors) < MAX_ERRORS:
                        job.errors.append(f"{member.name}: {exc}")
        job.processed += 1

    await asyncio.gather(*(process(member) for member in members))
    job.status = "completed"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_mass_role_jobs.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/mass_role_jobs.py dashboard/backend/tests/test_mass_role_jobs.py
git commit -m "feat(dashboard): add mass role assignment job orchestration"
```

---

### Task 2: `POST /api/roles/{role_id}/mass-assign` + `GET /api/roles/mass-assign/{job_id}`

**Files:**
- Modify: `dashboard/backend/routes/moderation.py` (append; add `import asyncio`, `import uuid`, `from .. import mass_role_jobs` to the top)
- Test: `dashboard/backend/tests/test_mass_assign_routes.py`

**Interfaces:**
- Consumes: `mass_role_jobs.JOBS`/`MassAssignJob`/`run_mass_assign` (Task 1); existing `_get_guild_or_none`, `_resolve_assignable_role`, `dashboard_reason`, `require_dashboard_access` (all already in `moderation.py`/`access_middleware.py` from Phase 2a — read the current file before appending, do not redefine).
- Produces: `POST /api/roles/{role_id}/mass-assign` → `202 {"job_id": str}` / `400`/`403`/`404`/`409`/`503`; `GET /api/roles/mass-assign/{job_id}` → `200 {status, total, processed, succeeded, skipped, failed, errors}` / `404`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_mass_assign_routes.py`:

```python
import asyncio

import pytest

from dashboard.backend import mass_role_jobs
from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def clear_jobs():
    mass_role_jobs.JOBS.clear()
    yield
    mass_role_jobs.JOBS.clear()


def build(members=None, roles=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot_top = FakeRole(900, name="bot-role", position=50)
    me = FakeMember(1, name="bot", top_role=bot_top)
    guild = FakeGuild(members=[moderator] + (members or []), roles=roles or [], me=me)
    return make_moderation_app(FakeBot(guild), [moderation_routes])


async def _wait_for_completion(client, job_id, attempts=50):
    for _ in range(attempts):
        resp = await client.get(f"/api/roles/mass-assign/{job_id}")
        body = await resp.json()
        if body["status"] != "running":
            return body
        await asyncio.sleep(0.01)
    raise AssertionError("job did not complete in time")


@pytest.mark.asyncio
async def test_mass_assign_all_except_bots_completes(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    human = FakeMember(50, name="human", bot=False)
    a_bot = FakeMember(51, name="a-bot", bot=True)
    client = await aiohttp_client(build(members=[human, a_bot], roles=[role]))
    await force_login(client, 10)

    resp = await client.post("/api/roles/7/mass-assign", json={"target": "all_except_bots"})
    assert resp.status == 202
    job_id = (await resp.json())["job_id"]

    body = await _wait_for_completion(client, job_id)
    assert body["status"] == "completed"
    # build()'s own moderator (FakeMember(10), bot=False) is also a guild member
    # and is non-bot, so "all_except_bots" legitimately includes it too: 2 total.
    assert body["total"] == 2
    assert body["succeeded"] == 2
    assert human.action_calls[0][0] == "add_roles"
    assert a_bot.action_calls == []


@pytest.mark.asyncio
async def test_mass_assign_selected_records_missing_member(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    present = FakeMember(60, name="present")
    client = await aiohttp_client(build(members=[present], roles=[role]))
    await force_login(client, 10)

    resp = await client.post(
        "/api/roles/7/mass-assign",
        json={"target": "selected", "member_ids": ["60", "9999"]},
    )
    assert resp.status == 202
    job_id = (await resp.json())["job_id"]

    body = await _wait_for_completion(client, job_id)
    assert body["total"] == 2
    assert body["succeeded"] == 1
    assert body["failed"] == 1
    assert any("9999" in line for line in body["errors"])


@pytest.mark.asyncio
async def test_mass_assign_selected_requires_member_ids(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    client = await aiohttp_client(build(roles=[role]))
    await force_login(client, 10)

    resp = await client.post("/api/roles/7/mass-assign", json={"target": "selected", "member_ids": []})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_mass_assign_rejects_role_above_bot(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    client = await aiohttp_client(build(roles=[role]))
    await force_login(client, 10)

    resp = await client.post("/api/roles/9/mass-assign", json={"target": "all"})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_mass_assign_rejects_second_job_while_running(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    client = await aiohttp_client(build(roles=[role]))
    await force_login(client, 10)
    mass_role_jobs.JOBS["already-running"] = mass_role_jobs.MassAssignJob(status="running", total=5)

    resp = await client.post("/api/roles/7/mass-assign", json={"target": "all"})
    assert resp.status == 409


@pytest.mark.asyncio
async def test_mass_assign_status_404_for_unknown_job(aiohttp_client):
    client = await aiohttp_client(build())
    await force_login(client, 10)
    resp = await client.get("/api/roles/mass-assign/does-not-exist")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_mass_assign_requires_auth(aiohttp_client):
    client = await aiohttp_client(build())
    resp = await client.post("/api/roles/7/mass-assign", json={"target": "all"})
    assert resp.status == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_mass_assign_routes.py -v`
Expected: FAIL — routes not registered (404s / AttributeError on missing module).

- [ ] **Step 3: Append to `dashboard/backend/routes/moderation.py`**

Add to the imports at the top of the file:

```python
import asyncio
import uuid

from .. import mass_role_jobs
```

Append at the end of the file:

```python
@routes.post("/api/roles/{role_id}/mass-assign")
@require_dashboard_access
async def mass_assign_role(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    role, error = _resolve_assignable_role(request, request.match_info["role_id"])
    if error:
        return error

    if any(job.status == "running" for job in mass_role_jobs.JOBS.values()):
        return web.json_response({"error": "job_already_running"}, status=409)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    target = body.get("target")
    missing_ids: list[str] = []

    if target == "all":
        members = list(guild.members)
    elif target == "all_except_bots":
        members = [m for m in guild.members if not m.bot]
    elif target == "selected":
        member_ids = body.get("member_ids") or []
        if not member_ids:
            return web.json_response({"error": "invalid_request"}, status=400)
        members = []
        for raw_id in member_ids:
            try:
                member = guild.get_member(int(raw_id))
            except (TypeError, ValueError):
                member = None
            if member is None:
                missing_ids.append(str(raw_id))
            else:
                members.append(member)
    else:
        return web.json_response({"error": "invalid_request"}, status=400)

    job_id = str(uuid.uuid4())
    job = mass_role_jobs.MassAssignJob(
        status="running",
        total=len(members) + len(missing_ids),
        failed=len(missing_ids),
        processed=len(missing_ids),
        errors=[f"Участник {mid}: не найден на сервере" for mid in missing_ids],
    )
    mass_role_jobs.JOBS[job_id] = job

    moderator = request["moderator"]
    asyncio.create_task(
        mass_role_jobs.run_mass_assign(job_id, guild, role, members, moderator, dashboard_reason)
    )

    return web.json_response({"job_id": job_id}, status=202)


@routes.get("/api/roles/mass-assign/{job_id}")
@require_dashboard_access
async def mass_assign_status(request: web.Request) -> web.Response:
    job = mass_role_jobs.JOBS.get(request.match_info["job_id"])
    if job is None:
        return web.json_response({"error": "job_not_found"}, status=404)
    return web.json_response(
        {
            "status": job.status,
            "total": job.total,
            "processed": job.processed,
            "succeeded": job.succeeded,
            "skipped": job.skipped,
            "failed": job.failed,
            "errors": job.errors,
        }
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_mass_assign_routes.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (74 + 4 + 7 = 85)

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/moderation.py dashboard/backend/tests/test_mass_assign_routes.py
git commit -m "feat(dashboard): add mass role assignment routes"
```

---

### Task 3: Frontend API client — mass-assign functions

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts` (append; do NOT change any existing export)
- Test: `dashboard/frontend/src/api/massAssign.test.ts`

**Interfaces:**
- Consumes: existing `apiFetch`, `jsonInit`, `ApiError` (already in `client.ts`, private/exported respectively — read the current file before appending).
- Produces: `type MassAssignTarget = 'all' | 'all_except_bots' | 'selected'`; `interface MassAssignStatus { status: 'running' | 'completed' | 'failed'; total: number; processed: number; succeeded: number; skipped: number; failed: number; errors: string[] }`; `function startMassAssign(roleId: string, target: MassAssignTarget, memberIds?: string[]): Promise<string>`; `function fetchMassAssignStatus(jobId: string): Promise<MassAssignStatus>`.

- [ ] **Step 1: Write the failing test**

`dashboard/frontend/src/api/massAssign.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchMassAssignStatus, startMassAssign } from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('mass assign api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('startMassAssign posts target and omits member_ids when not selected', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ job_id: 'job-1' }))
    vi.stubGlobal('fetch', fetchMock)

    const jobId = await startMassAssign('7', 'all_except_bots')
    expect(jobId).toBe('job-1')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/roles/7/mass-assign',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ target: 'all_except_bots' }),
      }),
    )
  })

  it('startMassAssign includes member_ids for selected target', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ job_id: 'job-2' }))
    vi.stubGlobal('fetch', fetchMock)

    await startMassAssign('7', 'selected', ['1', '2'])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/roles/7/mass-assign',
      expect.objectContaining({
        body: JSON.stringify({ target: 'selected', member_ids: ['1', '2'] }),
      }),
    )
  })

  it('fetchMassAssignStatus GETs the status endpoint', async () => {
    const payload = {
      status: 'running',
      total: 10,
      processed: 3,
      succeeded: 3,
      skipped: 0,
      failed: 0,
      errors: [],
    }
    const fetchMock = vi.fn().mockResolvedValue(okJson(payload))
    vi.stubGlobal('fetch', fetchMock)

    const status = await fetchMassAssignStatus('job-1')
    expect(status).toEqual(payload)
    expect(fetchMock).toHaveBeenCalledWith('/api/roles/mass-assign/job-1', expect.objectContaining({ credentials: 'include' }))
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd dashboard/frontend && npm run test`
Expected: FAIL — `startMassAssign`/`fetchMassAssignStatus` not exported.

- [ ] **Step 3: Append to `dashboard/frontend/src/api/client.ts`**

```ts
export type MassAssignTarget = 'all' | 'all_except_bots' | 'selected'

export interface MassAssignStatus {
  status: 'running' | 'completed' | 'failed'
  total: number
  processed: number
  succeeded: number
  skipped: number
  failed: number
  errors: string[]
}

export async function startMassAssign(
  roleId: string,
  target: MassAssignTarget,
  memberIds?: string[],
): Promise<string> {
  const body: Record<string, unknown> = { target }
  if (memberIds) body.member_ids = memberIds
  const result = await apiFetch<{ job_id: string }>(`/api/roles/${roleId}/mass-assign`, jsonInit('POST', body))
  return result.job_id
}

export function fetchMassAssignStatus(jobId: string): Promise<MassAssignStatus> {
  return apiFetch(`/api/roles/mass-assign/${jobId}`)
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test`
Expected: PASS — 3 new + all existing (22 total)

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/massAssign.test.ts
git commit -m "feat(dashboard): add mass role assignment API client functions"
```

---

### Task 4: `MassAssignModal.tsx` + wire into `Members.tsx`

**Files:**
- Create: `dashboard/frontend/src/components/MassAssignModal.tsx`
- Test: `dashboard/frontend/src/components/MassAssignModal.test.tsx`
- Modify: `dashboard/frontend/src/pages/Members.tsx` (add one button + modal mount; read the current file first — do not alter existing search/list/detail-panel logic)

**Interfaces:**
- Consumes: `fetchRoles`, `fetchMembers`, `startMassAssign`, `fetchMassAssignStatus`, types `RoleInfo`/`MemberSummary`/`MassAssignTarget`/`MassAssignStatus` (Task 3); `Modal`, `Button` (existing, from Phase 2a Task 9 / earlier).
- Produces: `MassAssignModal({ open, onClose }: { open: boolean; onClose: () => void })`.

- [ ] **Step 1: Write the failing test**

`dashboard/frontend/src/components/MassAssignModal.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { MassAssignModal } from './MassAssignModal'

describe('MassAssignModal', () => {
  afterEach(() => vi.restoreAllMocks())

  it('shows an error when starting without selecting a role', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    render(<MassAssignModal open onClose={() => {}} />)

    await waitFor(() => screen.getByText('VIP'))
    fireEvent.click(screen.getByText('Начать'))
    expect(await screen.findByText('Выберите роль')).toBeInTheDocument()
  })

  it('starts a job and shows progress once status resolves', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    vi.spyOn(client, 'startMassAssign').mockResolvedValue('job-1')
    vi.spyOn(client, 'fetchMassAssignStatus').mockResolvedValue({
      status: 'completed',
      total: 5,
      processed: 5,
      succeeded: 5,
      skipped: 0,
      failed: 0,
      errors: [],
    })

    render(<MassAssignModal open onClose={() => {}} />)
    await waitFor(() => screen.getByText('VIP'))

    fireEvent.change(screen.getByLabelText('Роль'), { target: { value: '7' } })
    fireEvent.click(screen.getByLabelText('Все кроме ботов'))
    fireEvent.click(screen.getByText('Начать'))

    await waitFor(() => expect(screen.getByText('Обработано: 5 / 5')).toBeInTheDocument())
    expect(screen.getByText('Готово')).toBeInTheDocument()
  })

  it('requires at least one selected member for target=selected', async () => {
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    render(<MassAssignModal open onClose={() => {}} />)

    await waitFor(() => screen.getByText('VIP'))
    fireEvent.change(screen.getByLabelText('Роль'), { target: { value: '7' } })
    fireEvent.click(screen.getByLabelText('Выбранные участники'))
    fireEvent.click(screen.getByText('Начать'))

    expect(await screen.findByText('Выберите хотя бы одного участника')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test`
Expected: FAIL — `Cannot find module './MassAssignModal'`.

- [ ] **Step 3: Implement `dashboard/frontend/src/components/MassAssignModal.tsx`**

```tsx
import { useEffect, useState } from 'react'
import {
  fetchMassAssignStatus,
  fetchMembers,
  fetchRoles,
  startMassAssign,
  type MassAssignStatus,
  type MassAssignTarget,
  type MemberSummary,
  type RoleInfo,
} from '../api/client'
import { Button } from './ui/Button'
import { Modal } from './ui/Modal'

interface Props {
  open: boolean
  onClose: () => void
}

export function MassAssignModal({ open, onClose }: Props) {
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [roleId, setRoleId] = useState('')
  const [target, setTarget] = useState<MassAssignTarget>('all_except_bots')
  const [search, setSearch] = useState('')
  const [searchResults, setSearchResults] = useState<MemberSummary[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<MassAssignStatus | null>(null)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)

  useEffect(() => {
    if (open) fetchRoles().then(setRoles).catch(() => {})
  }, [open])

  useEffect(() => {
    if (!open || target !== 'selected' || !search) {
      setSearchResults([])
      return
    }
    const timer = setTimeout(() => {
      fetchMembers(search, 1)
        .then((page) => setSearchResults(page.members))
        .catch(() => {})
    }, 300)
    return () => clearTimeout(timer)
  }, [open, target, search])

  useEffect(() => {
    if (!jobId) return
    let cancelled = false
    let interval: ReturnType<typeof setInterval>
    const poll = () => {
      fetchMassAssignStatus(jobId)
        .then((result) => {
          if (cancelled) return
          setStatus(result)
          if (result.status !== 'running') clearInterval(interval)
        })
        .catch(() => {
          if (!cancelled) clearInterval(interval)
        })
    }
    poll()
    interval = setInterval(poll, 2000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [jobId])

  const toggleSelected = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleStart = async () => {
    if (!roleId) {
      setError('Выберите роль')
      return
    }
    if (target === 'selected' && selectedIds.size === 0) {
      setError('Выберите хотя бы одного участника')
      return
    }
    setStarting(true)
    setError('')
    try {
      const id = await startMassAssign(roleId, target, target === 'selected' ? Array.from(selectedIds) : undefined)
      setJobId(id)
    } catch {
      setError('Не удалось запустить операцию (возможно, уже выполняется другая)')
    } finally {
      setStarting(false)
    }
  }

  const handleClose = () => {
    setJobId(null)
    setStatus(null)
    setSelectedIds(new Set())
    setSearch('')
    setError('')
    onClose()
  }

  return (
    <Modal open={open} title="Массовая выдача роли" onClose={handleClose}>
      {!jobId ? (
        <div className="flex flex-col gap-3">
          <label className="text-sm text-muted" htmlFor="mass-role">
            Роль
          </label>
          <select
            id="mass-role"
            value={roleId}
            onChange={(e) => setRoleId(e.target.value)}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="">Выберите роль…</option>
            {roles.map((role) => (
              <option key={role.id} value={role.id}>
                {role.name}
              </option>
            ))}
          </select>

          <div className="flex flex-col gap-1.5">
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input
                type="radio"
                name="target"
                checked={target === 'selected'}
                onChange={() => setTarget('selected')}
              />
              Выбранные участники
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input type="radio" name="target" checked={target === 'all'} onChange={() => setTarget('all')} />
              Все участники
            </label>
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input
                type="radio"
                name="target"
                checked={target === 'all_except_bots'}
                onChange={() => setTarget('all_except_bots')}
              />
              Все кроме ботов
            </label>
          </div>

          {target === 'selected' && (
            <div className="flex flex-col gap-2">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Поиск участника…"
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />
              <p className="text-xs text-muted">Выбрано: {selectedIds.size}</p>
              <div className="flex max-h-40 flex-col gap-1 overflow-y-auto">
                {searchResults.map((member) => (
                  <label key={member.id} className="flex items-center gap-2 text-sm text-foreground">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(member.id)}
                      onChange={() => toggleSelected(member.id)}
                    />
                    {member.display_name}
                  </label>
                ))}
              </div>
            </div>
          )}

          {error && <p className="text-sm text-danger">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={handleClose} disabled={starting}>
              Отмена
            </Button>
            <Button variant="primary" onClick={handleStart} disabled={starting}>
              {starting ? 'Запускаем…' : 'Начать'}
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-foreground">
            Обработано: {status?.processed ?? 0} / {status?.total ?? '…'}
          </p>
          <p className="text-xs text-muted">
            Успешно: {status?.succeeded ?? 0} · Пропущено (уже была роль): {status?.skipped ?? 0} · Ошибок:{' '}
            {status?.failed ?? 0}
          </p>
          {status?.errors && status.errors.length > 0 && (
            <div className="max-h-32 overflow-y-auto rounded-control border border-border bg-background p-2 text-xs text-danger">
              {status.errors.map((line, index) => (
                <p key={index}>{line}</p>
              ))}
            </div>
          )}
          {status?.status !== 'running' && (
            <div className="flex justify-end pt-2">
              <Button variant="primary" onClick={handleClose}>
                Готово
              </Button>
            </div>
          )}
        </div>
      )}
    </Modal>
  )
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test`
Expected: PASS — 3 new tests (26 total including all prior).

- [ ] **Step 5: Wire into `Members.tsx`**

Read the current `dashboard/frontend/src/pages/Members.tsx` first. Add the import:

```tsx
import { MassAssignModal } from '../components/MassAssignModal'
```

Add one piece of state near the other `useState` calls:

```tsx
const [massAssignOpen, setMassAssignOpen] = useState(false)
```

Change the search-bar wrapper `<div className="relative mb-4 max-w-md">...</div>` block to sit inside a flex row with a new button next to it — replace:

```tsx
        <div className="relative mb-4 max-w-md">
          <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск по имени или нику…"
            className="w-full rounded-control border border-border bg-surface py-2 pl-9 pr-3 text-sm text-foreground outline-none focus:border-primary"
          />
        </div>
```

with:

```tsx
        <div className="mb-4 flex items-center gap-3">
          <div className="relative max-w-md flex-1">
            <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по имени или нику…"
              className="w-full rounded-control border border-border bg-surface py-2 pl-9 pr-3 text-sm text-foreground outline-none focus:border-primary"
            />
          </div>
          <Button variant="secondary" onClick={() => setMassAssignOpen(true)}>
            Массовая выдача роли
          </Button>
        </div>

        <MassAssignModal
          open={massAssignOpen}
          onClose={() => {
            setMassAssignOpen(false)
            fetchMembers(debounced, page).then(setData).catch(() => {})
          }}
        />
```

`Button` is already imported in this file (used for pagination). No other changes to `Members.tsx`.

- [ ] **Step 6: Run tests + typecheck + build**

Run: `npm run test`, `npx tsc --noEmit`, `npm run build`
Expected: all green, no debug artifacts, no stray files (check `git status --short` before committing).

- [ ] **Step 7: Commit**

```bash
git add dashboard/frontend/src/components/MassAssignModal.tsx dashboard/frontend/src/components/MassAssignModal.test.tsx dashboard/frontend/src/pages/Members.tsx
git commit -m "feat(dashboard): add mass role assignment modal wired into Members page"
```

---

### Task 5: Full end-to-end manual verification

**Files:** none (verification only).

- [ ] **Step 1:** Start backend (`python main.py`) and frontend (`npm run dev`), log in.
- [ ] **Step 2:** `/members` → click "Массовая выдача роли" → pick a harmless test role, target "Все кроме ботов" → "Начать". Progress appears immediately (not after a 2s delay), updates, ends with "Готово" and correct succeeded/skipped counts. Confirm in Discord the role was actually applied to human members, not bots.
- [ ] **Step 3:** Open the modal again while a job is technically still finishing (or immediately after) is not required — just confirm starting a second job normally after the first completes works (no stuck 409).
- [ ] **Step 4:** Target "Выбранные участники" — search, check 1-2 members, start, confirm only those got the role.
- [ ] **Step 5:** Record results in the progress ledger. No commit (nothing changed).

---

## Self-Review Notes

- **Spec coverage:** API shape (Task 2) matches the spec's endpoint table exactly, including the `processed == succeeded+skipped+failed` invariant and `total` counting missing `selected` ids. Job model, semaphore-limited concurrency, and per-member error isolation (Task 1) match "Выполнение джобы". Frontend (Task 4) covers all three target modes, polling, and the completion summary. "Вне рамок" (mass revoke, job persistence, multiple concurrent jobs) are correctly absent.
- **Type consistency:** `MassAssignJob` fields (Task 1) match the JSON keys the route returns (Task 2) match the TS `MassAssignStatus` interface (Task 3) match what `MassAssignModal` reads (Task 4) — `status/total/processed/succeeded/skipped/failed/errors` used identically throughout.
- **Placeholder scan:** none found — every step has complete code.
