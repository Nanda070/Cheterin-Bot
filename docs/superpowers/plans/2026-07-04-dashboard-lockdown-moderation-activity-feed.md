# Dashboard: Lockdown Page — Moderation Activity Feed — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the "recent moderation activity" feed on the Lockdown page approved in `docs/superpowers/specs/2026-07-04-dashboard-lockdown-moderation-activity-feed-design.md` (commit `2e41763`): a new append-only JSON log, fed from four action sources, exposed as a read-only dashboard endpoint and rendered as a card on the Lockdown page.

**Architecture:** A new root module `moderation_log.py` provides `append_event`/`load_events` against a capped, no-cache JSON file (same pattern as `reaction_roles.py`/`feedback_categories.py`). Four call sites append to it: automatic anti-spam punishment (`spam.py`), automatic tempban (`tempban.py`), and manual ban/kick from the dashboard (`dashboard/backend/routes/moderation.py`, routed through the existing shared `_send_action_log` helper via a new optional `event_type` parameter). A new read-only `GET /api/moderation-log` route serves the log to a new card on `Lockdown.tsx`.

**Tech Stack:** Python + discord.py + aiohttp.web (backend), React + TypeScript + Vite (frontend), pytest + pytest-asyncio (backend tests), Vitest + Testing Library (frontend tests).

## Global Constraints

- Scope is exactly four event types: `spam_punish`, `tempban`, `manual_ban`, `manual_kick`. Manual role grant/revoke (`grant_role`/`revoke_role` in `moderation.py`, which also call `_send_action_log`) are explicitly OUT of scope — they must not pass the new `event_type` parameter and must not appear in the log.
- `moderation_log.json` is capped at `MAX_ENTRIES = 200` (oldest trimmed on overflow) and follows the project's no-cache convention: every `load_events()`/`append_event()` call reads/writes the file fresh from disk.
- IDs (`user_id`, `moderator_id`) are stored as strings, matching the project-wide convention for Discord snowflakes (they can exceed JavaScript's safe-integer range).
- `moderator_id`/`moderator_display` are `null` for automatic events (`spam_punish`, `tempban`) — this is how the frontend distinguishes "Автоматически" from a named moderator.
- `GET /api/moderation-log` is read-only — no `POST`/`PUT`/`DELETE` for this resource.
- `tempban.py`'s three early-return error paths (`discord.Forbidden`, `discord.HTTPException`, generic `Exception`, all before the ban succeeds) must NOT log an event — only the success path logs.
- `spam.py`'s event must be logged unconditionally, even when `SPAM_LOG_CHANNEL_ID` is unset (the existing Discord-embed log is a separate, gated concern from this persistence).
- `moderation_log.json` must be added to `.gitignore` (same class of runtime-generated file as `events_data.json`/`config.json`/`feedback_categories.json`).

---

### Task 1: `moderation_log.py` core module

**Files:**
- Create: `moderation_log.py`
- Test: `dashboard/backend/tests/test_moderation_log.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `moderation_log.LOG_FILE: str` (module-level constant, `"moderation_log.json"`) and `moderation_log.MAX_ENTRIES: int` (`200`) — both must be plain module attributes (not wrapped in a class) so tests can `monkeypatch.setattr` them, matching the pattern in `dashboard/backend/tests/test_reaction_roles_core.py`.
- Produces: `moderation_log.load_events() -> list[dict]` — returns stored events newest-first. Tasks 2, 3, 4, 5 all call this or `append_event`.
- Produces: `moderation_log.append_event(event_type: str, user_id: int, user_display: str, reason: str, moderator_id: int | None = None, moderator_display: str | None = None, extra: str = "") -> None`. Tasks 2, 3, 4 call this.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/backend/tests/test_moderation_log.py`:

```python
import pytest

import moderation_log


@pytest.fixture(autouse=True)
def isolated_log(tmp_path, monkeypatch):
    monkeypatch.setattr(moderation_log, "LOG_FILE", str(tmp_path / "moderation_log.json"))


def test_load_events_returns_empty_list_when_file_missing():
    assert moderation_log.load_events() == []


def test_load_events_returns_empty_list_on_corrupt_json():
    with open(moderation_log.LOG_FILE, "w", encoding="utf-8") as f:
        f.write("{not valid json")
    assert moderation_log.load_events() == []


def test_append_then_load_returns_newest_first():
    moderation_log.append_event("spam_punish", 1, "userA", "reason1")
    moderation_log.append_event("tempban", 2, "userB", "reason2")
    events = moderation_log.load_events()
    assert len(events) == 2
    assert events[0]["type"] == "tempban"
    assert events[1]["type"] == "spam_punish"


def test_append_event_stores_all_fields():
    moderation_log.append_event(
        "manual_ban", 100, "target", "spam", moderator_id=10, moderator_display="mod", extra="7 дн."
    )
    event = moderation_log.load_events()[0]
    assert event["type"] == "manual_ban"
    assert event["user_id"] == "100"
    assert event["user_display"] == "target"
    assert event["moderator_id"] == "10"
    assert event["moderator_display"] == "mod"
    assert event["reason"] == "spam"
    assert event["extra"] == "7 дн."
    assert "timestamp" in event


def test_append_event_defaults_moderator_to_none_for_automatic_events():
    moderation_log.append_event("tempban", 5, "userC", "auto reason")
    event = moderation_log.load_events()[0]
    assert event["moderator_id"] is None
    assert event["moderator_display"] is None


def test_append_event_trims_to_max_entries(monkeypatch):
    monkeypatch.setattr(moderation_log, "MAX_ENTRIES", 3)
    for i in range(5):
        moderation_log.append_event("spam_punish", i, f"user{i}", "reason")
    events = moderation_log.load_events()
    assert len(events) == 3
    assert events[0]["user_id"] == "4"
    assert events[-1]["user_id"] == "2"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_moderation_log.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'moderation_log'` (the module doesn't exist yet).

- [ ] **Step 3: Implement `moderation_log.py`**

Create `moderation_log.py`:

```python
import json
import os
from datetime import datetime, timezone

LOG_FILE = "moderation_log.json"
MAX_ENTRIES = 200


def load_events() -> list[dict]:
    """Returns stored events newest-first."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            events = json.load(f)
        except json.JSONDecodeError:
            return []
    return list(reversed(events))


def append_event(
    event_type: str,
    user_id: int,
    user_display: str,
    reason: str,
    moderator_id: int | None = None,
    moderator_display: str | None = None,
    extra: str = "",
) -> None:
    events = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                events = json.load(f)
            except json.JSONDecodeError:
                events = []

    events.append(
        {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": str(user_id),
            "user_display": user_display,
            "moderator_id": str(moderator_id) if moderator_id is not None else None,
            "moderator_display": moderator_display,
            "reason": reason,
            "extra": extra,
        }
    )

    if len(events) > MAX_ENTRIES:
        events = events[-MAX_ENTRIES:]

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_moderation_log.py -v`
Expected: all 6 tests PASS.

- [ ] **Step 5: Add `moderation_log.json` to `.gitignore`**

In `.gitignore`, add a new line after the existing `reaction_roles.json` entry (the file currently ends with `feedback_categories.json` / `reaction_roles.json` on the last two lines):

```
moderation_log.json
```

- [ ] **Step 6: Commit**

```bash
git add moderation_log.py dashboard/backend/tests/test_moderation_log.py .gitignore
git commit -m "feat: add moderation_log module for the recent-activity feed"
```

---

### Task 2: Instrument `spam.py`'s automatic punishment

**Files:**
- Modify: `spam.py:1-9` (imports), `spam.py:214-231` (`_punish`)

**Interfaces:**
- Consumes: `moderation_log.append_event(...)` from Task 1.

**Note:** There is zero pytest coverage for discord.py cog/event-listener code anywhere in this project (no `FakeInteraction`/event-simulation class exists) — this task has no automated test. Verification is a careful manual line-by-line diff review against the pre-change source, consistent with how this project has always handled this class of change.

- [ ] **Step 1: Add the import**

In `spam.py`, change line 7:

```python
import bot_config
```

to:

```python
import bot_config
import moderation_log
```

- [ ] **Step 2: Add the unconditional log call in `_punish`**

In `spam.py`, replace lines 230-238:

```python
        # Purge сообщений за последние 20 минут в фоне (текстовые каналы + треды)
        asyncio.create_task(self.purge_recent_messages(guild, member))

        # Лог
        if not log_channel_id:
            return
        log_channel = guild.get_channel(int(log_channel_id))
        if not log_channel:
            return
```

with:

```python
        # Purge сообщений за последние 20 минут в фоне (текстовые каналы + треды)
        asyncio.create_task(self.purge_recent_messages(guild, member))

        channels_spammed_for_log = list(set(f"<#{e['channel_id']}>" for e in matches))
        moderation_log.append_event(
            "spam_punish",
            member.id,
            member.name,
            f"Спам массовыми тегами ({limit} одинаковых сообщений за 60 сек.)",
            extra=", ".join(channels_spammed_for_log),
        )

        # Лог
        if not log_channel_id:
            return
        log_channel = guild.get_channel(int(log_channel_id))
        if not log_channel:
            return
```

This call is placed BEFORE the `if not log_channel_id: return` early-return, so the moderation-log entry is written unconditionally — independent of whether the Discord embed log channel is configured. The existing `channels_spammed` variable further down (inside the embed-building code, unchanged) is a separate, pre-existing computation — do not remove or rename it; `channels_spammed_for_log` here is a deliberately separate local variable for the log call, since the log call now runs before that later computation exists.

- [ ] **Step 3: Manually verify with a line-by-line diff**

Run: `git diff spam.py`
Confirm: only the import line and the 8-line insertion inside `_punish` changed. No other line in `_punish` or the rest of the file was touched — in particular, the embed-building code below (lines that were 240+ before this change) must be byte-for-byte identical to before.

- [ ] **Step 4: Commit**

```bash
git add spam.py
git commit -m "feat: record automatic anti-spam punishment in the moderation log"
```

---

### Task 3: Instrument `tempban.py`'s automatic tempban

**Files:**
- Modify: `tempban.py:1-8` (imports), `tempban.py:155-159` (end of `_do_tempban`)

**Interfaces:**
- Consumes: `moderation_log.append_event(...)` from Task 1.

**Note:** Same as Task 2 — no automated test exists or is expected for this cog code; verification is a manual line-by-line diff review.

- [ ] **Step 1: Add the import**

In `tempban.py`, change line 6:

```python
import bot_config
```

to:

```python
import bot_config
import moderation_log
```

- [ ] **Step 2: Add the log call on the success path only**

In `tempban.py`, replace lines 155-159:

```python
        embed.set_footer(text="Пользователь кикнут (сообщения за 20 минут удалены).")
        embed.timestamp = now

        await self.bot.send_log(embed)
```

with:

```python
        embed.set_footer(text="Пользователь кикнут (сообщения за 20 минут удалены).")
        embed.timestamp = now

        moderation_log.append_event(
            "tempban",
            member.id,
            member.name,
            TEMPBAN_REASON,
            extra=f"Канал: <#{message.channel.id}>; unban: {'ok' if not unban_error else unban_error}",
        )

        await self.bot.send_log(embed)
```

This is placed after the member has actually been banned (the function returns early at three points above this — `discord.Forbidden`, `discord.HTTPException`, and generic `Exception` — all before reaching this line), so the log call only ever runs on the success path, matching the plan's constraint.

- [ ] **Step 3: Manually verify with a line-by-line diff**

Run: `git diff tempban.py`
Confirm: only the import line and the 7-line insertion at the end of `_do_tempban` changed. Confirm the three early-return branches above (`except discord.Forbidden`, `except discord.HTTPException as e`, `except Exception as e`, each ending in `return`) are unchanged and still return before reaching the new code.

- [ ] **Step 4: Commit**

```bash
git add tempban.py
git commit -m "feat: record automatic tempban in the moderation log"
```

---

### Task 4: Manual ban/kick logging and the read-only API endpoint

**Files:**
- Modify: `dashboard/backend/routes/moderation.py:1-11` (imports), `:125-133` (`_send_action_log`), `:181-184` (`ban_member`'s call), `:209-211` (`kick_member`'s call)
- Modify: `dashboard/backend/tests/test_ban_kick.py` (add isolation fixture + 2 new tests)
- Create: `dashboard/backend/tests/test_moderation_log_routes.py`

**Interfaces:**
- Consumes: `moderation_log.append_event(...)` and `moderation_log.load_events()`/`moderation_log.MAX_ENTRIES` from Task 1.
- Produces: `GET /api/moderation-log?limit=N` — JSON `{"events": [...]}`, gated by `require_dashboard_access`. Task 5 (frontend) calls this.

- [ ] **Step 1: Write the failing tests for ban/kick logging**

In `dashboard/backend/tests/test_ban_kick.py`, add this import and autouse fixture right after the existing imports (after the `from dashboard.backend.tests.fakes import (...)` block, before `class _StubForbidden`):

```python
import moderation_log


@pytest.fixture(autouse=True)
def isolated_moderation_log(tmp_path, monkeypatch):
    monkeypatch.setattr(moderation_log, "LOG_FILE", str(tmp_path / "moderation_log.json"))
```

This isolates ALL tests in this file (existing and new) from the real `moderation_log.json`, since `ban_member`/`kick_member` will now write to it on every call.

Then add these two tests to the end of the file:

```python
@pytest.mark.asyncio
async def test_ban_records_moderation_log_entry(aiohttp_client):
    target = FakeMember(70, name="rulebreaker")
    _, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/members/70/ban", json={"reason": "спам", "delete_message_days": 0})

    events = moderation_log.load_events()
    assert len(events) == 1
    assert events[0]["type"] == "manual_ban"
    assert events[0]["user_id"] == "70"
    assert events[0]["moderator_id"] == "10"


@pytest.mark.asyncio
async def test_kick_records_moderation_log_entry(aiohttp_client):
    target = FakeMember(71, name="mild")
    _, app = build([target])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/members/71/kick", json={"reason": "флуд"})

    events = moderation_log.load_events()
    assert len(events) == 1
    assert events[0]["type"] == "manual_kick"
    assert events[0]["moderator_id"] == "10"
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_ban_kick.py -v -k "records_moderation_log_entry"`
Expected: FAIL — both tests fail with `AssertionError: assert 0 == 1` (or similar), since `_send_action_log` doesn't write to `moderation_log` yet.

- [ ] **Step 3: Write the failing tests for the new endpoint**

Create `dashboard/backend/tests/test_moderation_log_routes.py`:

```python
import pytest

import moderation_log
from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_moderation_log(tmp_path, monkeypatch):
    monkeypatch.setattr(moderation_log, "LOG_FILE", str(tmp_path / "moderation_log.json"))


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator]))
    return make_moderation_app(bot, [moderation_routes])


@pytest.mark.asyncio
async def test_get_moderation_log_returns_events_newest_first(aiohttp_client):
    moderation_log.append_event("spam_punish", 1, "userA", "reason1")
    moderation_log.append_event("tempban", 2, "userB", "reason2")
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/moderation-log")
    assert resp.status == 200
    body = await resp.json()
    assert [e["type"] for e in body["events"]] == ["tempban", "spam_punish"]


@pytest.mark.asyncio
async def test_get_moderation_log_respects_limit(aiohttp_client):
    for i in range(5):
        moderation_log.append_event("spam_punish", i, f"user{i}", "reason")
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/moderation-log?limit=2")
    body = await resp.json()
    assert len(body["events"]) == 2


@pytest.mark.asyncio
async def test_get_moderation_log_requires_auth(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/moderation-log")
    assert resp.status == 401
```

- [ ] **Step 4: Run the new endpoint tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_moderation_log_routes.py -v`
Expected: FAIL — `404 Not Found` or `AttributeError`, since the route doesn't exist yet.

- [ ] **Step 5: Add the `moderation_log` import**

In `dashboard/backend/routes/moderation.py`, change the import block (lines 1-8):

```python
import asyncio
import uuid

import discord
from aiohttp import web

from ..access_middleware import require_dashboard_access
from .. import mass_role_jobs
```

to:

```python
import asyncio
import uuid

import discord
from aiohttp import web

import moderation_log
from ..access_middleware import require_dashboard_access
from .. import mass_role_jobs
```

- [ ] **Step 6: Add `event_type` to `_send_action_log`**

In `dashboard/backend/routes/moderation.py`, replace `_send_action_log` (lines 125-133):

```python
async def _send_action_log(bot, title: str, target, moderator, reason: str, extra: str = ""):
    embed = discord.Embed(title=title, color=discord.Color.red(), timestamp=bot.utcnow())
    embed.add_field(name="Кто", value=f"{moderator.name} (`{moderator.id}`)", inline=False)
    embed.add_field(name="Кого", value=f"{target.name} (`{target.id}`)", inline=False)
    embed.add_field(name="Причина", value=reason, inline=False)
    if extra:
        embed.add_field(name="Дополнительно", value=extra, inline=False)
    embed.set_footer(text="Dashboard · Moderation")
    await bot.send_log(embed)
```

with:

```python
async def _send_action_log(
    bot, title: str, target, moderator, reason: str, extra: str = "", event_type: str | None = None
):
    embed = discord.Embed(title=title, color=discord.Color.red(), timestamp=bot.utcnow())
    embed.add_field(name="Кто", value=f"{moderator.name} (`{moderator.id}`)", inline=False)
    embed.add_field(name="Кого", value=f"{target.name} (`{target.id}`)", inline=False)
    embed.add_field(name="Причина", value=reason, inline=False)
    if extra:
        embed.add_field(name="Дополнительно", value=extra, inline=False)
    embed.set_footer(text="Dashboard · Moderation")
    await bot.send_log(embed)
    if event_type:
        moderation_log.append_event(
            event_type,
            target.id,
            target.name,
            reason,
            moderator_id=moderator.id,
            moderator_display=moderator.name,
            extra=extra,
        )
```

`event_type` defaults to `None`, so the two existing call sites in `grant_role` (around line 281) and `revoke_role` (around line 303) — which do not pass `event_type` — are unaffected and will NOT write to the moderation log, matching this task's out-of-scope requirement. Do not modify `grant_role` or `revoke_role`.

- [ ] **Step 7: Pass `event_type` from `ban_member` and `kick_member`**

In `dashboard/backend/routes/moderation.py`, change `ban_member`'s call to `_send_action_log` (lines 181-184):

```python
    await _send_action_log(
        request.app["bot"], "🔨 Бан через дашборд", target, moderator, reason,
        extra=f"Удаление сообщений: {days} дн.",
    )
```

to:

```python
    await _send_action_log(
        request.app["bot"], "🔨 Бан через дашборд", target, moderator, reason,
        extra=f"Удаление сообщений: {days} дн.", event_type="manual_ban",
    )
```

And change `kick_member`'s call (lines 209-211):

```python
    await _send_action_log(
        request.app["bot"], "👢 Кик через дашборд", target, moderator, reason
    )
```

to:

```python
    await _send_action_log(
        request.app["bot"], "👢 Кик через дашборд", target, moderator, reason, event_type="manual_kick"
    )
```

- [ ] **Step 8: Add the `GET /api/moderation-log` route**

In `dashboard/backend/routes/moderation.py`, add this new route directly after the `_send_action_log` function (right before `def _get_target_or_response(request):`):

```python
@routes.get("/api/moderation-log")
@require_dashboard_access
async def get_moderation_log(request: web.Request) -> web.Response:
    try:
        limit = int(request.query.get("limit", 50))
    except ValueError:
        limit = 50
    limit = max(0, min(limit, moderation_log.MAX_ENTRIES))
    events = moderation_log.load_events()[:limit]
    return web.json_response({"events": events})
```

- [ ] **Step 9: Run all affected backend tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_ban_kick.py dashboard/backend/tests/test_moderation_log_routes.py dashboard/backend/tests/test_roles.py -v`
Expected: all tests PASS — including every pre-existing test in `test_ban_kick.py` and `test_roles.py` (the latter covers `grant_role`/`revoke_role` and must show zero behavior change, since `event_type` was not added to those call sites).

- [ ] **Step 10: Run the full backend suite to check for regressions**

Run: `pytest`
Expected: all tests PASS (no regressions anywhere else in the backend).

- [ ] **Step 11: Commit**

```bash
git add dashboard/backend/routes/moderation.py dashboard/backend/tests/test_ban_kick.py dashboard/backend/tests/test_moderation_log_routes.py
git commit -m "feat: log manual ban/kick to the moderation log and expose GET /api/moderation-log"
```

---

### Task 5: Frontend — activity feed card on the Lockdown page

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts:135-137` (after `deactivateLockdown`)
- Test: `dashboard/frontend/src/api/moderation.test.ts`
- Modify: `dashboard/frontend/src/pages/Lockdown.tsx`
- Test: `dashboard/frontend/src/pages/Lockdown.test.tsx`

**Interfaces:**
- Consumes: `GET /api/moderation-log` from Task 4, returning `{"events": [...]}` where each event has the exact shape defined in `ModerationLogEntry` below.
- Produces: `ModerationLogEntry` interface and `fetchModerationLog(): Promise<ModerationLogEntry[]>` in `client.ts`, consumed by `Lockdown.tsx`.

- [ ] **Step 1: Write the failing test for the API client function**

In `dashboard/frontend/src/api/moderation.test.ts`, add this test to the end of the `describe('moderation api client', ...)` block (before the closing `})`):

```typescript
  it('fetchModerationLog unwraps the events array', async () => {
    const events = [
      {
        type: 'manual_ban',
        timestamp: '2026-07-04T12:00:00+00:00',
        user_id: '70',
        user_display: 'rulebreaker',
        moderator_id: '10',
        moderator_display: 'mod',
        reason: 'спам',
        extra: '',
      },
    ]
    const fetchMock = vi.fn().mockResolvedValue(okJson({ events }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchModerationLog()
    expect(result).toEqual(events)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/moderation-log')
  })
```

Add `fetchModerationLog` to the existing import block at the top of the file:

```typescript
import {
  ApiError,
  banMember,
  fetchLockdownStatus,
  fetchMembers,
  fetchModerationLog,
  grantRole,
} from './client'
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `dashboard/frontend`): `npx vitest run src/api/moderation.test.ts -t "fetchModerationLog"`
Expected: FAIL — `fetchModerationLog` is not exported from `./client` yet.

- [ ] **Step 3: Add `ModerationLogEntry` and `fetchModerationLog` to `client.ts`**

In `dashboard/frontend/src/api/client.ts`, add this immediately after `deactivateLockdown` (after line 137, before `export type MassAssignTarget = ...`):

```typescript
export interface ModerationLogEntry {
  type: 'spam_punish' | 'tempban' | 'manual_ban' | 'manual_kick'
  timestamp: string
  user_id: string
  user_display: string
  moderator_id: string | null
  moderator_display: string | null
  reason: string
  extra: string
}

export async function fetchModerationLog(): Promise<ModerationLogEntry[]> {
  const body = await apiFetch<{ events: ModerationLogEntry[] }>('/api/moderation-log')
  return body.events
}
```

- [ ] **Step 4: Run the client test to verify it passes**

Run (from `dashboard/frontend`): `npx vitest run src/api/moderation.test.ts`
Expected: all tests PASS, including the new one and every pre-existing test in the file.

- [ ] **Step 5: Write the failing tests for the Lockdown page card**

Create `dashboard/frontend/src/pages/Lockdown.test.tsx` if it does not already exist — it already exists, so instead add these two tests to the end of the `describe('LockdownPage', ...)` block in the existing file (before the closing `})`):

```tsx
  it('renders moderation activity entries', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([
      {
        type: 'manual_ban',
        timestamp: '2026-07-04T12:00:00+00:00',
        user_id: '70',
        user_display: 'rulebreaker',
        moderator_id: '10',
        moderator_display: 'mod',
        reason: 'спам',
        extra: '',
      },
      {
        type: 'tempban',
        timestamp: '2026-07-04T11:00:00+00:00',
        user_id: '5',
        user_display: 'userC',
        moderator_id: null,
        moderator_display: null,
        reason: 'Автоматический Tempban (Сброс сообщений за 20 мин.)',
        extra: '',
      },
    ])

    render(<LockdownPage />)

    expect(await screen.findByText('rulebreaker')).toBeInTheDocument()
    expect(screen.getByText('mod')).toBeInTheDocument()
    expect(screen.getByText('userC')).toBeInTheDocument()
    expect(screen.getByText('Автоматически')).toBeInTheDocument()
  })

  it('shows an empty state when there is no activity', async () => {
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])

    render(<LockdownPage />)

    expect(await screen.findByText('Активности пока нет.')).toBeInTheDocument()
  })
```

- [ ] **Step 6: Run the new tests to verify they fail**

Run (from `dashboard/frontend`): `npx vitest run src/pages/Lockdown.test.tsx -t "moderation activity|empty state"`
Expected: FAIL — `client.fetchModerationLog` is not called by the component yet, so `vi.spyOn(client, 'fetchModerationLog')` either throws (if unused) or the expected text never appears.

- [ ] **Step 7: Add the activity feed card to `Lockdown.tsx`**

Replace the full contents of `dashboard/frontend/src/pages/Lockdown.tsx`:

```tsx
import { Clock, Prohibit, ShieldCheck, ShieldWarning, SignOut, Warning } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  activateLockdown,
  deactivateLockdown,
  fetchLockdownStatus,
  fetchModerationLog,
  type LockdownStatus,
  type ModerationLogEntry,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'

const TYPE_ICON: Record<ModerationLogEntry['type'], typeof Warning> = {
  spam_punish: Warning,
  tempban: Clock,
  manual_ban: Prohibit,
  manual_kick: SignOut,
}

const TYPE_LABEL: Record<ModerationLogEntry['type'], string> = {
  spam_punish: 'Анти-спам',
  tempban: 'Tempban',
  manual_ban: 'Бан (дашборд)',
  manual_kick: 'Кик (дашборд)',
}

export function LockdownPage() {
  const [status, setStatus] = useState<LockdownStatus | null>(null)
  const [confirming, setConfirming] = useState<'activate' | 'deactivate' | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [activity, setActivity] = useState<ModerationLogEntry[] | null>(null)

  const reload = () => {
    fetchLockdownStatus()
      .then((s) => {
        setStatus(s)
        setError('')
      })
      .catch(() => setError('Не удалось получить статус'))
  }

  useEffect(reload, [])
  useEffect(() => {
    fetchModerationLog()
      .then(setActivity)
      .catch(() => setActivity([]))
  }, [])

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
    <div className="flex max-w-xl flex-col gap-4">
      <Card className="animate-fade-in-up">
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

      <Card className="animate-fade-in-up">
        <h2 className="font-semibold text-foreground">Последняя активность</h2>
        {activity === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
        {activity !== null && activity.length === 0 && (
          <p className="mt-2 text-sm text-muted">Активности пока нет.</p>
        )}
        {activity !== null && activity.length > 0 && (
          <ul className="mt-3 flex flex-col gap-3">
            {activity.map((entry, index) => {
              const Icon = TYPE_ICON[entry.type]
              return (
                <li key={index} className="flex items-start gap-3 border-t border-border pt-3 first:border-t-0 first:pt-0">
                  <Icon size={18} className="mt-0.5 shrink-0 text-muted" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-foreground">
                      <span className="font-medium">{TYPE_LABEL[entry.type]}</span> — {entry.user_display}
                    </p>
                    <p className="text-xs text-muted">{entry.reason}</p>
                    <p className="text-xs text-muted">
                      {entry.moderator_display ?? 'Автоматически'} · {new Date(entry.timestamp).toLocaleString()}
                    </p>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </Card>
    </div>
  )
}
```

- [ ] **Step 8: Run all Lockdown frontend tests to verify they pass**

Run (from `dashboard/frontend`): `npx vitest run src/pages/Lockdown.test.tsx`
Expected: all tests PASS, including the two pre-existing tests (`shows inactive status`, `activates after confirmation and refreshes status`) — both must now also mock `fetchModerationLog` implicitly resolving to `undefined` via the default Vitest auto-mock behavior; if the pre-existing tests fail because `fetchModerationLog` is called but not mocked, add `vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])` to those two pre-existing tests as well.

- [ ] **Step 9: Run the full frontend suite to check for regressions**

Run (from `dashboard/frontend`): `npx vitest run`
Expected: all tests PASS (no regressions anywhere else in the frontend).

- [ ] **Step 10: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/moderation.test.ts dashboard/frontend/src/pages/Lockdown.tsx dashboard/frontend/src/pages/Lockdown.test.tsx
git commit -m "feat: show recent moderation activity feed on the Lockdown page"
```

---

## Final Verification

After all five tasks are complete:

- [ ] Run the full backend suite: `pytest` (from the repo root) — all tests pass.
- [ ] Run the full frontend suite: `npx vitest run` (from `dashboard/frontend`) — all tests pass.
- [ ] Manually verify in the browser (dev servers restarted): the Lockdown page shows the new "Последняя активность" card; ban/kick a test member from the Members page and confirm the entry appears with the moderator's name; if possible, trigger the real anti-spam/tempban flows on the test server and confirm those entries show "Автоматически".
