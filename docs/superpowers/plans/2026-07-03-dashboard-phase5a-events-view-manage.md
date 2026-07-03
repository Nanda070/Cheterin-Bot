# Phase 5a: Events/Voting — Dashboard View & Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let dashboard moderators view active/closed events and polls, inspect participants/vote results, close, delete, and notify participants — without touching the Discord test server directly — while removing `events.py`'s stale module-level cache so dashboard and bot always see the same live state.

**Architecture:** `events.py`'s `load_events()`/`save_events()` lose their module-level cache (matching `feedback_categories.py`'s established no-cache pattern). The three mutating actions currently inlined as closures in `EventManageSelect` (`close`, `delete`, `notify`) get extracted into a new `events_core.py`, following the `_core.py` pattern already used by `feedback_core.py` — both the Discord `/event manage` panel and new dashboard routes call the same functions. A new `dashboard/backend/routes/events.py` exposes list/detail/close/delete/notify over HTTP, and a matching `Events.tsx` + `EventDetailPanel.tsx` pair on the frontend follows the exact list+detail-panel convention already used by `FeedbackCases.tsx`/`FeedbackCaseDetailPanel.tsx`.

**Tech Stack:** Python 3.12, discord.py, aiohttp (backend); React + TypeScript + Vite + Vitest (frontend). Same stack as every prior phase.

## Global Constraints

- No caching in `events.py`'s data-access layer after this plan (this phase's core fix).
- IDs (`channel_id`, `role_reward`, `user_id`) are serialized as strings in every dashboard API response; the underlying `events_data.json` storage format is UNCHANGED (still native ints) — do not migrate stored data, only the API boundary.
- `int(...)`-conversion happens only where a real Discord API call needs it, exactly at that call site.
- All new/touched routes are gated by `require_dashboard_access`.
- Validation order everywhere: structural checks first, Discord-existence checks second, permission last (enforced by the decorator running before the handler body).
- Never bare `git add -A`/`git add .` — stage only the specific files each task touches.
- Never silently change a stated numeric/behavioral constant or weaken a test assertion to make it pass — if something in this plan looks wrong, flag it in the task report and fix the test's own data, not production code.
- `events.py`'s interaction-driven code (`EventBuilderView`, registration modals, vote buttons, `EventManageSelect`, `/event setup`/`/event manage`) gets zero new pytest coverage — no `FakeInteraction` pattern exists in this project and none should be invented. Verify any change to it by careful, minimal, line-by-line diffing against the current source.
- **One deliberate, explicitly-flagged deviation from the original code**: `close_event` (Task 2) rebuilds the participation view via `create_participation_view(message_id, ev, disabled=True)` instead of the original code's `discord.ui.View.from_message(msg)`. The original approach re-parses whatever components are actually attached to the live Discord message; the new approach rebuilds the view fresh from stored event data. Both produce the same observable result (all buttons disabled) for every event this code ever runs against, since `create_participation_view` is the only code path that ever attaches a view to an event message in the first place — but `discord.ui.View.from_message` cannot be exercised against this project's plain-Python test fakes (it expects real discord.py API-shaped component payloads, not the View objects our fakes store), so this task's tests would otherwise be unable to verify the disable behavior at all. Flagged here for the reviewer to independently judge, same as this project's other documented deviations (e.g. `isinstance` → `is not None` in `feedback_core.decide_case`).
- Baseline before this plan: 243 backend (pytest) tests, 65 frontend (Vitest) tests, `tsc` clean, build clean, at commit `a046a83`.

---

### Task 1: Remove `events.py`'s module-level cache

**Files:**
- Modify: `events.py:1-50` (imports, `_EVENTS_CACHE`/`_EVENTS_LOCK`, `load_events`, `save_events`)
- Test: Create `dashboard/backend/tests/test_events_data.py`

**Interfaces:**
- Produces: `events.load_events() -> dict` and `events.save_events(data: dict) -> None` keep their exact existing names/signatures (zero call-site changes anywhere else in `events.py` — every existing caller already does `data = await load_events()` / `await save_events(data)` fresh on every interaction, so removing the cache changes nothing about how they're called).

The current top of `events.py` (read it first to confirm it still matches):

```python
# pyrefly: ignore [missing-import]
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
import uuid
import logging
from typing import Optional
import random
import string

logger = logging.getLogger("chetbot.events")
EVENTS_FILE = "events_data.json"


_EVENTS_CACHE = None
_EVENTS_LOCK = asyncio.Lock()

async def load_events() -> dict:
    global _EVENTS_CACHE
    if _EVENTS_CACHE is not None:
        return _EVENTS_CACHE
        
    async with _EVENTS_LOCK:
        if _EVENTS_CACHE is not None:
            return _EVENTS_CACHE
        def _read():
            if os.path.exists(EVENTS_FILE):
                with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                    try:
                        return json.load(f)
                    except json.JSONDecodeError:
                        return {}
            return {}
        _EVENTS_CACHE = await asyncio.to_thread(_read)
        if "events" not in _EVENTS_CACHE:
            _EVENTS_CACHE["events"] = {}
        return _EVENTS_CACHE


async def save_events(data: dict):
    global _EVENTS_CACHE
    _EVENTS_CACHE = data
    async with _EVENTS_LOCK:
        def _write():
            with open(EVENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        await asyncio.to_thread(_write)
```

- [ ] **Step 1: Write the failing tests**

Create `dashboard/backend/tests/test_events_data.py`:

```python
import json
import os

import pytest

import events


@pytest.fixture(autouse=True)
def isolated_events_file(tmp_path, monkeypatch):
    monkeypatch.setattr(events, "EVENTS_FILE", str(tmp_path / "events_data.json"))


@pytest.mark.asyncio
async def test_load_events_returns_empty_events_dict_when_file_missing():
    data = await events.load_events()
    assert data == {"events": {}}


@pytest.mark.asyncio
async def test_save_then_load_roundtrips():
    await events.save_events({"events": {"123": {"title": "Test"}}})
    data = await events.load_events()
    assert data == {"events": {"123": {"title": "Test"}}}


@pytest.mark.asyncio
async def test_load_events_reads_fresh_after_external_write():
    await events.load_events()  # first read, populates any cache that might exist
    with open(events.EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"events": {"999": {"title": "Written externally"}}}, f)
    data = await events.load_events()
    assert data == {"events": {"999": {"title": "Written externally"}}}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_events_data.py -v`
Expected: `test_load_events_reads_fresh_after_external_write` FAILS (the cache returns the stale first-read value, `{"events": {}}`, instead of the externally-written data). The other two tests PASS already (they don't exercise the cache's staleness).

- [ ] **Step 3: Remove the cache**

Replace the block in `events.py` shown above with:

```python
# pyrefly: ignore [missing-import]
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
import uuid
import logging
from typing import Optional
import random
import string

logger = logging.getLogger("chetbot.events")
EVENTS_FILE = "events_data.json"


async def load_events() -> dict:
    def _read():
        if os.path.exists(EVENTS_FILE):
            with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}
    data = await asyncio.to_thread(_read)
    if "events" not in data:
        data["events"] = {}
    return data


async def save_events(data: dict):
    def _write():
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    await asyncio.to_thread(_write)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_events_data.py -v`
Expected: all 3 pass.

- [ ] **Step 5: Verify `events.py` still imports cleanly**

Run: `python -c "import events"`
Expected: exits cleanly, no output.

- [ ] **Step 6: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `246 passed` (243 baseline + 3 new).

- [ ] **Step 7: Commit**

```bash
git add events.py dashboard/backend/tests/test_events_data.py
git commit -m "fix: remove stale module-level cache from events.py, always read fresh"
```

---

### Task 2: Extract `events_core.py` and refactor `events.py`'s management panel to use it

**Files:**
- Create: `events_core.py`
- Modify: `events.py:556-723` (`create_participation_view` — add `disabled` parameter)
- Modify: `events.py:730-864` (`EventNotifyModal.on_submit`, `EventManageSelect`'s `cb_close`/`cb_delete` closures)
- Modify: `dashboard/backend/tests/fakes.py` (add `delete()` to `FakeMessage`)
- Test: Create `dashboard/backend/tests/test_events_core.py`

**Interfaces:**
- Consumes: `events.load_events`/`events.save_events` (Task 1), `events.create_participation_view(message_id, event_data, disabled=False)` (extended by this task).
- Produces:
  - `async def close_event(bot, message_id: str) -> dict` — returns `{"ok": True}` or `{"ok": False, "error": "not_found"}`.
  - `async def delete_event(bot, guild, message_id: str) -> dict` — same shape.
  - `async def notify_participants(bot, guild, message_id: str, text: str) -> dict` — returns `{"ok": True, "success": int, "failed": int}` or `{"ok": False, "error": "not_found"}` / `{"ok": False, "error": "no_participants"}`.
  These three functions are what Task 4's dashboard routes call directly, and what this task's own refactored `events.py` closures call.

Read `events.py` in full first — you need its exact current content to make precise, minimal diffs. This is unusually high-risk: `events.py` is interaction-driven Discord bot code with zero pytest coverage anywhere in this project. Verify correctness by reading carefully and diffing minimally, not by inventing new interaction tests.

- [ ] **Step 1: Add a `delete()` method to `FakeMessage`**

In `dashboard/backend/tests/fakes.py`, inside the `FakeMessage` class, add (near the other async methods like `edit`):

```python
    async def delete(self):
        pass
```

- [ ] **Step 2: Extend `create_participation_view` with a `disabled` parameter**

In `events.py`, the function signature at line 556 currently reads:

```python
def create_participation_view(message_id: str, event_data: dict) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
```

Change to:

```python
def create_participation_view(message_id: str, event_data: dict, disabled: bool = False) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
```

And change the function's final line (currently `return view` at the end of the function, line ~723) to:

```python
    if disabled:
        for item in view.children:
            item.disabled = True
    return view
```

This is a backward-compatible addition — every existing call site (`EventBuilderView.publish`, the `Events.on_ready` listener) omits the new parameter and keeps its current behavior unchanged.

- [ ] **Step 3: Write the failing tests**

Create `dashboard/backend/tests/test_events_core.py`:

```python
import discord
import pytest

import events_core
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, FakeMessage, FakeRole


@pytest.fixture(autouse=True)
def isolated_events_file(tmp_path, monkeypatch):
    import events

    monkeypatch.setattr(events, "EVENTS_FILE", str(tmp_path / "events_data.json"))


def _tournament_event(channel_id=500, role_reward=None, participants=None):
    return {
        "type": "tournament",
        "channel_id": channel_id,
        "author_id": 1,
        "title": "Test Tournament",
        "description": "desc",
        "banner_url": "",
        "mode": "solo",
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": role_reward,
        "ping": "none",
        "status": "open",
        "participants": participants or [],
        "options": [],
        "multi_select": False,
        "votes": {},
    }


@pytest.mark.asyncio
async def test_close_event_not_found_returns_error():
    import events

    bot = FakeBot(FakeGuild())
    result = await events_core.close_event(bot, "MISSING")
    assert result == {"ok": False, "error": "not_found"}


@pytest.mark.asyncio
async def test_close_event_sets_status_and_persists():
    import events

    await events.save_events({"events": {"900": _tournament_event()}})
    bot = FakeBot(FakeGuild())

    result = await events_core.close_event(bot, "900")

    assert result == {"ok": True}
    data = await events.load_events()
    assert data["events"]["900"]["status"] == "closed"


@pytest.mark.asyncio
async def test_close_event_disables_participation_buttons_on_live_message():
    import events

    ev = _tournament_event()
    await events.save_events({"events": {"900": ev}})
    base_embed = discord.Embed(title="Test Tournament")
    message = FakeMessage(900, embeds=[base_embed])
    channel = FakeChannel(500, messages={900: message})
    guild = FakeGuild(channels=[channel])
    bot = FakeBot(guild)

    await events_core.close_event(bot, "900")

    assert len(message.edit_calls) == 1
    edited_view = message.edit_calls[0]["view"]
    assert all(item.disabled for item in edited_view.children)
    assert message.edit_calls[0]["embed"].footer.text == "🔴 Статус: Закрыто"


@pytest.mark.asyncio
async def test_close_event_survives_missing_channel():
    import events

    await events.save_events({"events": {"900": _tournament_event()}})
    guild = FakeGuild(channels=[])  # channel 500 won't resolve
    bot = FakeBot(guild)

    result = await events_core.close_event(bot, "900")

    assert result == {"ok": True}
    data = await events.load_events()
    assert data["events"]["900"]["status"] == "closed"


@pytest.mark.asyncio
async def test_delete_event_not_found_returns_error():
    guild = FakeGuild()
    bot = FakeBot(guild)
    result = await events_core.delete_event(bot, guild, "MISSING")
    assert result == {"ok": False, "error": "not_found"}


@pytest.mark.asyncio
async def test_delete_event_removes_from_storage():
    import events

    await events.save_events({"events": {"900": _tournament_event()}})
    guild = FakeGuild()
    bot = FakeBot(guild)

    result = await events_core.delete_event(bot, guild, "900")

    assert result == {"ok": True}
    data = await events.load_events()
    assert "900" not in data["events"]


@pytest.mark.asyncio
async def test_delete_event_removes_role_from_all_participants():
    import events

    role = FakeRole(200, name="Tournament Role")
    member1 = FakeMember(10, name="p1")
    member2 = FakeMember(20, name="p2")
    ev = _tournament_event(role_reward=200, participants=[{"user_id": 10, "ign": "a"}, {"user_id": 20, "ign": "b"}])
    await events.save_events({"events": {"900": ev}})
    guild = FakeGuild(members=[member1, member2], roles=[role])
    bot = FakeBot(guild)

    await events_core.delete_event(bot, guild, "900")

    assert member1.action_calls == [("remove_roles", {"role": role})]
    assert member2.action_calls == [("remove_roles", {"role": role})]


@pytest.mark.asyncio
async def test_delete_event_deletes_live_message():
    import events

    ev = _tournament_event()
    await events.save_events({"events": {"900": ev}})
    message = FakeMessage(900)
    channel = FakeChannel(500, messages={900: message})
    guild = FakeGuild(channels=[channel])
    bot = FakeBot(guild)

    await events_core.delete_event(bot, guild, "900")

    # FakeMessage.delete() is a no-op recorder-free stub; absence of an
    # exception is the assertion here (fetch_message succeeded and delete
    # didn't raise). Combined with test_delete_event_removes_from_storage,
    # this proves the full deletion path runs without error.


@pytest.mark.asyncio
async def test_notify_participants_not_found_returns_error():
    guild = FakeGuild()
    bot = FakeBot(guild)
    result = await events_core.notify_participants(bot, guild, "MISSING", "hello")
    assert result == {"ok": False, "error": "not_found"}


@pytest.mark.asyncio
async def test_notify_participants_empty_participants_returns_error():
    import events

    await events.save_events({"events": {"900": _tournament_event(participants=[])}})
    guild = FakeGuild()
    bot = FakeBot(guild)

    result = await events_core.notify_participants(bot, guild, "900", "hello")

    assert result == {"ok": False, "error": "no_participants"}


@pytest.mark.asyncio
async def test_notify_participants_sends_dm_and_counts_results():
    import events

    reachable = FakeMember(10, name="reachable")
    unreachable = FakeMember(20, name="unreachable")
    unreachable.send_raises = discord.Forbidden.__new__(discord.Forbidden)
    ev = _tournament_event(participants=[{"user_id": 10, "ign": "a"}, {"user_id": 20, "ign": "b"}])
    await events.save_events({"events": {"900": ev}})
    guild = FakeGuild(members=[reachable, unreachable])
    bot = FakeBot(guild)

    result = await events_core.notify_participants(bot, guild, "900", "Hello everyone")

    assert result == {"ok": True, "success": 1, "failed": 1}
    assert len(reachable.send_calls) == 1
    assert "Hello everyone" in reachable.send_calls[0]["content"]
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_events_core.py -v`
Expected: all FAIL with `ModuleNotFoundError: No module named 'events_core'`.

- [ ] **Step 5: Create `events_core.py`**

```python
import asyncio
import logging

import discord

import events

logger = logging.getLogger("chetbot.events_core")


async def close_event(bot, message_id: str) -> dict:
    data = await events.load_events()
    ev = data["events"].get(message_id)
    if not ev:
        return {"ok": False, "error": "not_found"}

    ev["status"] = "closed"
    await events.save_events(data)

    try:
        ch = bot.get_channel(ev["channel_id"])
        if not ch:
            try:
                ch = await bot.fetch_channel(ev["channel_id"])
            except Exception:
                ch = None
        if ch:
            msg = await ch.fetch_message(int(message_id))
            if msg.embeds:
                emb = msg.embeds[0].copy()
                emb.set_footer(text="🔴 Статус: Закрыто")
                view = events.create_participation_view(message_id, ev, disabled=True)
                await msg.edit(embed=emb, view=view)
    except Exception as e:
        logger.warning("Не удалось закрыть сообщение события %s: %s", message_id, e)

    return {"ok": True}


async def delete_event(bot, guild, message_id: str) -> dict:
    data = await events.load_events()
    ev = data["events"].pop(message_id, None)
    if not ev:
        return {"ok": False, "error": "not_found"}
    await events.save_events(data)

    role_id = ev.get("role_reward")
    if role_id and guild:
        role = guild.get_role(role_id)
        if role:
            for p in ev.get("participants", []):
                try:
                    mem = guild.get_member(p["user_id"])
                    if mem:
                        await mem.remove_roles(role)
                except Exception as e:
                    logger.debug("Не удалось снять роль с участника %s: %s", p.get("user_id"), e)

    try:
        ch = bot.get_channel(ev["channel_id"])
        if not ch:
            try:
                ch = await bot.fetch_channel(ev["channel_id"])
            except Exception:
                ch = None
        if ch:
            msg = await ch.fetch_message(int(message_id))
            await msg.delete()
    except Exception as e:
        logger.warning("Не удалось удалить сообщение события %s: %s", message_id, e)

    return {"ok": True}


async def notify_participants(bot, guild, message_id: str, text: str) -> dict:
    data = await events.load_events()
    ev = data.get("events", {}).get(message_id)
    if not ev:
        return {"ok": False, "error": "not_found"}

    participants = ev.get("participants", [])
    if not participants:
        return {"ok": False, "error": "no_participants"}

    user_ids = list(set(p.get("user_id") for p in participants if p.get("user_id")))

    success = 0
    failed = 0
    for uid in user_ids:
        try:
            user = (guild.get_member(uid) if guild else None) or await bot.fetch_user(uid)
            if user:
                await user.send(content=f"**📢 Уведомление о событии «{ev.get('title')}»:**\n\n{text}")
                success += 1
            else:
                failed += 1
        except Exception as e:
            logger.debug("Не удалось отправить уведомление участнику %s: %s", uid, e)
            failed += 1
        await asyncio.sleep(0.1)

    return {"ok": True, "success": success, "failed": failed}
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_events_core.py -v`
Expected: all 11 pass.

- [ ] **Step 7: Refactor `events.py`'s management panel to call `events_core`**

Add `import events_core` to `events.py`'s top-level imports (after `import string`):

```python
import random
import string

import events_core
```

Replace `EventNotifyModal.on_submit` (currently lines 742-775) with:

```python
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        text = self.inp_text.value.strip()

        data = await events.load_events()
        ev = data.get("events", {}).get(self.message_id)
        if not ev:
            await interaction.followup.send("❌ Событие не найдено.", ephemeral=True)
            return
        if not ev.get("participants"):
            await interaction.followup.send("❌ Список участников пуст. Рассылать некому.", ephemeral=True)
            return

        user_ids = list(set(p.get("user_id") for p in ev.get("participants", []) if p.get("user_id")))
        await interaction.followup.send(
            f"Начинаю рассылку для {len(user_ids)} участников... Пожалуйста, подождите.", ephemeral=True
        )

        result = await events_core.notify_participants(self.bot, interaction.guild, self.message_id, text)

        await interaction.followup.send(
            f"✅ Рассылка завершена!\nУспешно: {result['success']}\nНе удалось (ЛС закрыты): {result['failed']}",
            ephemeral=True,
        )
```

This module (`events.py`) is itself the module `import events` refers to in `events_core.py` — inside `events.py` itself, call `load_events`/`create_participation_view` directly (unqualified), not via an `events.` prefix, since they're defined in the same file. Only `events_core.py` needs the `import events` qualifier.

Replace the `cb_close` closure body (currently lines 805-826) with:

```python
        async def cb_close(i: discord.Interaction):
            await events_core.close_event(self.bot, msg_id)
            await i.response.send_message("✅ Событие закрыто.", ephemeral=True)
```

Replace the `cb_delete` closure body (currently lines 828-854) with:

```python
        async def cb_delete(i: discord.Interaction):
            await events_core.delete_event(self.bot, i.guild, msg_id)
            await i.response.send_message("🗑️ Событие удалено.", ephemeral=True)
```

Both preserve the original's exact observable behavior: the same ephemeral success message is always shown regardless of whether the event was found (matching the original code's `if ev_to_close:` guard, which also silently skipped the body but still sent the same success message on a miss — this is a pre-existing quirk, not something to "fix" here, since `msg_id` always comes from a dropdown populated from currently-existing events and a miss can only happen from an extremely narrow concurrent-deletion race).

- [ ] **Step 8: Verify `events.py` still imports cleanly**

Run: `python -c "import events"`
Expected: exits cleanly, no output. (This also transitively proves `events_core.py` imports cleanly, since `events.py` now imports it.)

- [ ] **Step 9: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `257 passed` (246 from Task 1 + 11 new).

- [ ] **Step 10: Commit**

```bash
git add events_core.py events.py dashboard/backend/tests/fakes.py dashboard/backend/tests/test_events_core.py
git commit -m "refactor: extract close/delete/notify event actions into events_core.py"
```

---

### Task 3: `GET /api/events` and `GET /api/events/{message_id}` routes

**Files:**
- Create: `dashboard/backend/routes/events.py`
- Modify: `dashboard/backend/app.py` (register the new route table)
- Test: Create `dashboard/backend/tests/test_events_routes.py`

**Interfaces:**
- Consumes: `events.load_events` (Task 1).
- Produces: `serialize_event_summary(message_id: str, ev: dict) -> dict` and `serialize_event_detail(message_id: str, ev: dict) -> dict`, both defined in this task's route file and reused unmodified by Task 4 (Task 4 does not need to serialize anything new — its routes only return `{"ok": True, ...}` shapes).

- [ ] **Step 1: Write the failing tests**

Create `dashboard/backend/tests/test_events_routes.py`:

```python
import pytest

from dashboard.backend.routes.events import routes as events_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app

import events


@pytest.fixture(autouse=True)
def isolated_events_file(tmp_path, monkeypatch):
    monkeypatch.setattr(events, "EVENTS_FILE", str(tmp_path / "events_data.json"))


def _tournament_event(status="open", mode="solo", participants=None, **overrides):
    ev = {
        "type": "tournament",
        "channel_id": 500,
        "author_id": 1,
        "title": "Test Tournament",
        "description": "desc",
        "banner_url": "",
        "mode": mode,
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "ping": "none",
        "status": status,
        "participants": participants or [],
        "options": [],
        "multi_select": False,
        "votes": {},
    }
    ev.update(overrides)
    return ev


def _poll_event(status="open", options=None, votes=None, multi_select=False):
    return {
        "type": "poll",
        "channel_id": 500,
        "author_id": 1,
        "title": "Test Poll",
        "description": "desc",
        "banner_url": "",
        "mode": "solo",
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "ping": "none",
        "status": status,
        "participants": [],
        "options": options or ["A", "B"],
        "multi_select": multi_select,
        "votes": votes or {},
    }


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    return guild, make_moderation_app(FakeBot(guild), [events_routes])


@pytest.mark.asyncio
async def test_list_events_defaults_to_open(aiohttp_client):
    await events.save_events(
        {"events": {"900": _tournament_event(status="open"), "901": _tournament_event(status="closed")}}
    )
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events")
    assert resp.status == 200
    body = await resp.json()
    assert [e["message_id"] for e in body["events"]] == ["900"]


@pytest.mark.asyncio
async def test_list_events_filters_by_closed(aiohttp_client):
    await events.save_events(
        {"events": {"900": _tournament_event(status="open"), "901": _tournament_event(status="closed")}}
    )
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events?status=closed")
    assert resp.status == 200
    body = await resp.json()
    assert [e["message_id"] for e in body["events"]] == ["901"]


@pytest.mark.asyncio
async def test_list_events_rejects_invalid_status(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events?status=bogus")
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_status"


@pytest.mark.asyncio
async def test_list_events_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/events")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_get_event_detail_tournament_solo_shape(aiohttp_client):
    ev = _tournament_event(mode="solo", participants=[{"user_id": 20, "ign": "PlayerOne"}])
    await events.save_events({"events": {"900": ev}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events/900")
    assert resp.status == 200
    body = await resp.json()
    assert body["mode"] == "solo"
    assert body["participants"] == [{"user_id": "20", "ign": "PlayerOne"}]


@pytest.mark.asyncio
async def test_get_event_detail_tournament_team_code_groups_by_team(aiohttp_client):
    participants = [
        {"user_id": 1, "team_code": "ABC123", "team_name": "Alpha", "ign": "cap", "is_captain": True},
        {"user_id": 2, "team_code": "ABC123", "team_name": "Alpha", "ign": "mate", "is_captain": False},
    ]
    ev = _tournament_event(mode="team_code", participants=participants)
    await events.save_events({"events": {"900": ev}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events/900")
    body = await resp.json()
    assert len(body["participants"]) == 1
    team = body["participants"][0]
    assert team["team_code"] == "ABC123"
    assert team["team_name"] == "Alpha"
    assert len(team["members"]) == 2


@pytest.mark.asyncio
async def test_get_event_detail_poll_shape_with_percentages(aiohttp_client):
    ev = _poll_event(options=["Yes", "No"], votes={"1": [0], "2": [0], "3": [1]})
    await events.save_events({"events": {"900": ev}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events/900")
    body = await resp.json()
    assert body["options"] == [
        {"label": "Yes", "votes": 2, "percent": 66},
        {"label": "No", "votes": 1, "percent": 33},
    ]


@pytest.mark.asyncio
async def test_get_event_detail_404_when_unknown(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events/missing")
    assert resp.status == 404
    assert (await resp.json())["error"] == "not_found"


@pytest.mark.asyncio
async def test_get_event_detail_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/events/900")
    assert resp.status == 401
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_events_routes.py -v`
Expected: all FAIL — `dashboard/backend/routes/events.py` doesn't exist yet, so the import at the top of the test file raises `ModuleNotFoundError`.

- [ ] **Step 3: Create `dashboard/backend/routes/events.py`**

```python
from aiohttp import web

import events

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

VALID_STATUSES = {"open", "closed"}


def _tournament_count(ev: dict) -> int:
    participants = ev.get("participants", [])
    if ev.get("mode") == "team_code":
        teams = set(p.get("team_code") for p in participants if p.get("team_code"))
        return len(teams)
    return len(participants)


def serialize_event_summary(message_id: str, ev: dict) -> dict:
    if ev.get("type") == "tournament":
        count = _tournament_count(ev)
    else:
        count = sum(len(v) for v in ev.get("votes", {}).values())
    return {
        "message_id": message_id,
        "type": ev.get("type"),
        "title": ev.get("title", ""),
        "status": ev.get("status", "open"),
        "channel_id": str(ev.get("channel_id", "")),
        "count": count,
    }


def _serialize_participants(ev: dict) -> list:
    parts = ev.get("participants", [])
    mode = ev.get("mode", "solo")
    if mode == "solo":
        return [{"user_id": str(p["user_id"]), "ign": p.get("ign") or "—"} for p in parts]
    if mode == "team_captain":
        return [
            {"user_id": str(p["user_id"]), "team_name": p.get("team_name", ""), "members": p.get("members", "")}
            for p in parts
        ]
    teams: dict = {}
    for p in parts:
        teams.setdefault(p.get("team_code"), []).append(p)
    result = []
    for code, members in teams.items():
        captain = next((m for m in members if m.get("is_captain")), members[0] if members else None)
        result.append(
            {
                "team_code": code,
                "team_name": captain.get("team_name", "") if captain else "",
                "members": [
                    {
                        "user_id": str(m["user_id"]),
                        "ign": m.get("ign") or "—",
                        "is_captain": bool(m.get("is_captain")),
                    }
                    for m in members
                ],
            }
        )
    return result


def _serialize_poll_options(ev: dict) -> list:
    votes = ev.get("votes", {})
    opts = ev.get("options", [])
    counts = [0] * len(opts)
    total = 0
    for user_votes in votes.values():
        for v in user_votes:
            if v < len(counts):
                counts[v] += 1
                total += 1
    result = []
    for idx, opt in enumerate(opts):
        c = counts[idx]
        pct = int((c / total * 100) if total > 0 else 0)
        result.append({"label": opt, "votes": c, "percent": pct})
    return result


def serialize_event_detail(message_id: str, ev: dict) -> dict:
    base = {
        "message_id": message_id,
        "type": ev.get("type"),
        "title": ev.get("title", ""),
        "description": ev.get("description", ""),
        "status": ev.get("status", "open"),
        "channel_id": str(ev.get("channel_id", "")),
        "role_reward": str(ev["role_reward"]) if ev.get("role_reward") else None,
    }
    if ev.get("type") == "tournament":
        base["mode"] = ev.get("mode", "solo")
        base["max_limit"] = ev.get("max_limit", 0)
        base["team_size"] = ev.get("team_size", 5)
        base["participants"] = _serialize_participants(ev)
    else:
        base["multi_select"] = ev.get("multi_select", False)
        base["options"] = _serialize_poll_options(ev)
    return base


@routes.get("/api/events")
@require_dashboard_access
async def list_events(request: web.Request) -> web.Response:
    status = request.query.get("status", "open")
    if status not in VALID_STATUSES:
        return web.json_response({"error": "invalid_status"}, status=400)

    data = await events.load_events()
    events_list = [
        serialize_event_summary(message_id, ev)
        for message_id, ev in data.get("events", {}).items()
        if ev.get("status", "open") == status
    ]
    return web.json_response({"events": events_list})


@routes.get("/api/events/{message_id}")
@require_dashboard_access
async def get_event(request: web.Request) -> web.Response:
    message_id = request.match_info["message_id"]
    data = await events.load_events()
    ev = data.get("events", {}).get(message_id)
    if ev is None:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response(serialize_event_detail(message_id, ev))
```

- [ ] **Step 4: Register the route table in `app.py`**

In `dashboard/backend/app.py`, add the import (after the existing `from .routes.feedback import routes as feedback_routes` line):

```python
from .routes.events import routes as events_routes
```

And add the registration call (after the existing `app.add_routes(feedback_routes)` line):

```python
    app.add_routes(events_routes)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_events_routes.py -v`
Expected: all 9 pass.

- [ ] **Step 6: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `266 passed` (257 from Task 2 + 9 new).

- [ ] **Step 7: Commit**

```bash
git add dashboard/backend/routes/events.py dashboard/backend/app.py dashboard/backend/tests/test_events_routes.py
git commit -m "feat(dashboard): add GET /api/events list and detail routes"
```

---

### Task 4: `POST .../close`, `DELETE`, `POST .../notify` routes

**Files:**
- Modify: `dashboard/backend/routes/events.py` (append; no `app.py` changes needed — this route table is already registered from Task 3)
- Test: Modify `dashboard/backend/tests/test_events_routes.py` (append)

**Interfaces:**
- Consumes: `events_core.close_event`, `events_core.delete_event`, `events_core.notify_participants` (Task 2).
- Produces: `POST /api/events/{message_id}/close` → `{"ok": true}` / 404; `DELETE /api/events/{message_id}` → `{"ok": true}` / 404; `POST /api/events/{message_id}/notify` (body `{"message": string}`) → `{"ok": true, "success": int, "failed": int}` / 400 (`invalid_request` or `no_participants`) / 404 (`not_found`).

- [ ] **Step 1: Write the failing tests**

Append to `dashboard/backend/tests/test_events_routes.py` (add `import events_core` isn't needed — these tests only exercise the HTTP layer):

```python
@pytest.mark.asyncio
async def test_close_event_route_success(aiohttp_client):
    await events.save_events({"events": {"900": _tournament_event()}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events/900/close")
    assert resp.status == 200
    assert (await resp.json()) == {"ok": True}
    data = await events.load_events()
    assert data["events"]["900"]["status"] == "closed"


@pytest.mark.asyncio
async def test_close_event_route_404(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events/missing/close")
    assert resp.status == 404
    assert (await resp.json())["error"] == "not_found"


@pytest.mark.asyncio
async def test_close_event_route_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/events/900/close")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_delete_event_route_success(aiohttp_client):
    await events.save_events({"events": {"900": _tournament_event()}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete("/api/events/900")
    assert resp.status == 200
    data = await events.load_events()
    assert "900" not in data["events"]


@pytest.mark.asyncio
async def test_delete_event_route_404(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete("/api/events/missing")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_delete_event_route_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.delete("/api/events/900")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_notify_event_route_success(aiohttp_client):
    ev = _tournament_event(participants=[{"user_id": 20, "ign": "a"}])
    await events.save_events({"events": {"900": ev}})
    member = FakeMember(20, name="p1")
    guild = FakeGuild(members=[FakeMember(10, name="mod", role_ids=[111]), member])
    app = make_moderation_app(FakeBot(guild), [events_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events/900/notify", json={"message": "Hello"})
    assert resp.status == 200
    body = await resp.json()
    assert body == {"ok": True, "success": 1, "failed": 0}


@pytest.mark.asyncio
async def test_notify_event_route_rejects_missing_message(aiohttp_client):
    await events.save_events({"events": {"900": _tournament_event(participants=[{"user_id": 20}])}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events/900/notify", json={})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_notify_event_route_400_when_no_participants(aiohttp_client):
    await events.save_events({"events": {"900": _tournament_event(participants=[])}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events/900/notify", json={"message": "Hello"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "no_participants"


@pytest.mark.asyncio
async def test_notify_event_route_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/events/900/notify", json={"message": "hi"})
    assert resp.status == 401
```

Note: `_, app = build()` only creates a guild with the moderator member — tests that need `notify` to actually reach a real participant member build their own guild directly (see `test_notify_event_route_success`), since `build()`'s guild has no other members.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_events_routes.py -v -k "close_event_route or delete_event_route or notify_event_route"`
Expected: all FAIL with 404 (routes don't exist yet — aiohttp returns 404 for unmatched routes).

- [ ] **Step 3: Add the three routes**

Append to `dashboard/backend/routes/events.py` (at the end of the file), and add `import events_core` to the top of the file (alongside the existing `import events`):

```python
import events_core
```

```python
@routes.post("/api/events/{message_id}/close")
@require_dashboard_access
async def close_event_route(request: web.Request) -> web.Response:
    message_id = request.match_info["message_id"]
    bot = request.app["bot"]
    result = await events_core.close_event(bot, message_id)
    if not result["ok"]:
        return web.json_response({"error": result["error"]}, status=404)
    return web.json_response({"ok": True})


@routes.delete("/api/events/{message_id}")
@require_dashboard_access
async def delete_event_route(request: web.Request) -> web.Response:
    message_id = request.match_info["message_id"]
    bot = request.app["bot"]
    guild = bot.get_guild(request.app["guild_id"])
    result = await events_core.delete_event(bot, guild, message_id)
    if not result["ok"]:
        return web.json_response({"error": result["error"]}, status=404)
    return web.json_response({"ok": True})


@routes.post("/api/events/{message_id}/notify")
@require_dashboard_access
async def notify_event_route(request: web.Request) -> web.Response:
    message_id = request.match_info["message_id"]

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    message = body.get("message")
    if not isinstance(message, str) or not message.strip():
        return web.json_response({"error": "invalid_request"}, status=400)

    bot = request.app["bot"]
    guild = bot.get_guild(request.app["guild_id"])
    result = await events_core.notify_participants(bot, guild, message_id, message.strip())
    if not result["ok"]:
        status_code = {"not_found": 404, "no_participants": 400}.get(result["error"], 400)
        return web.json_response({"error": result["error"]}, status=status_code)
    return web.json_response({"ok": True, "success": result["success"], "failed": result["failed"]})
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_events_routes.py -v`
Expected: all 19 pass (9 from Task 3 + 10 new).

- [ ] **Step 5: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `276 passed` (266 from Task 3 + 10 new).

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/events.py dashboard/backend/tests/test_events_routes.py
git commit -m "feat(dashboard): add close/delete/notify event routes"
```

---

### Task 5: Frontend API client

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts` (append)
- Test: Create `dashboard/frontend/src/api/events.test.ts`

**Interfaces:**
- Consumes: `apiFetch<T>` and `jsonInit` (existing helpers already at the top of `client.ts`).
- Produces:
  - `export interface EventParticipantSolo { user_id: string; ign: string }`
  - `export interface EventParticipantTeamCaptain { user_id: string; team_name: string; members: string }`
  - `export interface EventParticipantTeamCodeMember { user_id: string; ign: string; is_captain: boolean }`
  - `export interface EventParticipantTeamCode { team_code: string; team_name: string; members: EventParticipantTeamCodeMember[] }`
  - `export interface EventPollOption { label: string; votes: number; percent: number }`
  - `export interface EventSummary { message_id: string; type: 'tournament' | 'poll'; title: string; status: 'open' | 'closed'; channel_id: string; count: number }`
  - `export interface EventDetail extends EventSummary { description: string; role_reward: string | null; mode?: 'solo' | 'team_captain' | 'team_code'; max_limit?: number; team_size?: number; participants?: (EventParticipantSolo | EventParticipantTeamCaptain | EventParticipantTeamCode)[]; multi_select?: boolean; options?: EventPollOption[] }`
  - `export function fetchEvents(status?: string): Promise<EventSummary[]>`
  - `export function fetchEventDetail(messageId: string): Promise<EventDetail>`
  - `export function closeEvent(messageId: string): Promise<void>`
  - `export function deleteEvent(messageId: string): Promise<void>`
  - `export function notifyEventParticipants(messageId: string, message: string): Promise<{ success: number; failed: number }>`

- [ ] **Step 1: Write the failing test**

Create `dashboard/frontend/src/api/events.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest'
import { closeEvent, deleteEvent, fetchEventDetail, fetchEvents, notifyEventParticipants } from './client'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status })
}

describe('events API client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchEvents defaults to no query string', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ events: [] }))
    await fetchEvents()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/events')
  })

  it('fetchEvents appends the status filter', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ events: [] }))
    await fetchEvents('closed')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/events?status=closed')
  })

  it('fetchEventDetail GETs the event by id', async () => {
    const detail = { message_id: '900', type: 'tournament', title: 'T', status: 'open', channel_id: '500', count: 0, description: '', role_reward: null }
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(detail))
    const result = await fetchEventDetail('900')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/events/900')
    expect(result).toEqual(detail)
  })

  it('closeEvent POSTs to the close endpoint', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ ok: true }))
    await closeEvent('900')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/events/900/close')
    expect(init?.method).toBe('POST')
  })

  it('deleteEvent DELETEs the event', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ ok: true }))
    await deleteEvent('900')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/events/900')
    expect(init?.method).toBe('DELETE')
  })

  it('notifyEventParticipants POSTs the message and returns counts', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse({ ok: true, success: 3, failed: 1 }))
    const result = await notifyEventParticipants('900', 'Hello')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/events/900/notify')
    expect(JSON.parse(init?.body as string)).toEqual({ message: 'Hello' })
    expect(result).toEqual({ success: 3, failed: 1 })
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `dashboard/frontend/`): `npm run test -- events.test`
Expected: FAIL — none of `fetchEvents`/`fetchEventDetail`/`closeEvent`/`deleteEvent`/`notifyEventParticipants` are exported from `./client` yet.

- [ ] **Step 3: Add the types and functions**

Append to `dashboard/frontend/src/api/client.ts` (at the end of the file):

```typescript
export interface EventParticipantSolo {
  user_id: string
  ign: string
}

export interface EventParticipantTeamCaptain {
  user_id: string
  team_name: string
  members: string
}

export interface EventParticipantTeamCodeMember {
  user_id: string
  ign: string
  is_captain: boolean
}

export interface EventParticipantTeamCode {
  team_code: string
  team_name: string
  members: EventParticipantTeamCodeMember[]
}

export interface EventPollOption {
  label: string
  votes: number
  percent: number
}

export interface EventSummary {
  message_id: string
  type: 'tournament' | 'poll'
  title: string
  status: 'open' | 'closed'
  channel_id: string
  count: number
}

export interface EventDetail extends EventSummary {
  description: string
  role_reward: string | null
  mode?: 'solo' | 'team_captain' | 'team_code'
  max_limit?: number
  team_size?: number
  participants?: (EventParticipantSolo | EventParticipantTeamCaptain | EventParticipantTeamCode)[]
  multi_select?: boolean
  options?: EventPollOption[]
}

export async function fetchEvents(status?: string): Promise<EventSummary[]> {
  const path = status ? `/api/events?status=${status}` : '/api/events'
  const body = await apiFetch<{ events: EventSummary[] }>(path)
  return body.events
}

export function fetchEventDetail(messageId: string): Promise<EventDetail> {
  return apiFetch(`/api/events/${messageId}`)
}

export async function closeEvent(messageId: string): Promise<void> {
  await apiFetch(`/api/events/${messageId}/close`, jsonInit('POST'))
}

export async function deleteEvent(messageId: string): Promise<void> {
  await apiFetch(`/api/events/${messageId}`, jsonInit('DELETE'))
}

export async function notifyEventParticipants(
  messageId: string,
  message: string,
): Promise<{ success: number; failed: number }> {
  return apiFetch(`/api/events/${messageId}/notify`, jsonInit('POST', { message }))
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm run test -- events.test`
Expected: PASS.

- [ ] **Step 5: Run the full frontend suite and typecheck**

Run: `npm run test` then `npx tsc --noEmit`
Expected: `71 passed` (65 baseline + 6 new), `tsc` clean.

- [ ] **Step 6: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/events.test.ts
git commit -m "feat(dashboard): add events API client functions"
```

---

### Task 6: Frontend UI — events list and detail panel

**Files:**
- Create: `dashboard/frontend/src/pages/Events.tsx`
- Create: `dashboard/frontend/src/pages/EventDetailPanel.tsx`
- Modify: `dashboard/frontend/src/pages/DashboardShell.tsx:24-31` (wire the existing "События и голосования" sidebar entry to `/events`)
- Modify: `dashboard/frontend/src/App.tsx` (add the `/events` route)
- Test: Create `dashboard/frontend/src/pages/Events.test.tsx`
- Test: Create `dashboard/frontend/src/pages/EventDetailPanel.test.tsx`

**Interfaces:**
- Consumes: `fetchEvents`, `fetchEventDetail`, `closeEvent`, `deleteEvent`, `notifyEventParticipants`, and all the `Event*` types (Task 5); existing `Card`, `Button`, `Modal` components (same imports/usage as `FeedbackCases.tsx`/`FeedbackCaseDetailPanel.tsx`/`FeedbackCategories.tsx`).
- Produces: `export function EventsPage()`, `export function EventDetailPanel(props: { messageId: string; onClose: () => void; onChanged: () => void })` — no other file consumes these beyond `App.tsx`'s route wiring in this task.

`DashboardShell.tsx`'s `SECTIONS` array (lines 24-31) currently has:

```typescript
const SECTIONS: Section[] = [
  { label: 'Feedback и тикеты', icon: ChatCircleText, to: '/feedback' },
  { label: 'Конструктор кнопок и эмбедов', icon: Stack, to: '/reaction-roles' },
  { label: 'События и голосования', icon: CalendarCheck },
  { label: 'Lockdown и модерация', icon: ShieldWarning, to: '/lockdown' },
  { label: 'Участники и роли', icon: UsersThree, to: '/members' },
  { label: 'Конфигурация', icon: GearSix },
]
```

The `CalendarCheck` icon is already imported at the top of the file. The "События и голосования" entry currently has no `to`, which makes `DashboardShell` render it as a disabled "скоро" placeholder (see the ternary at line 85: entries without `to` render the placeholder branch).

`App.tsx`'s current routes (read the file first to confirm it still matches):

```tsx
            <Route index element={<HomePage />} />
            <Route path="members" element={<MembersPage />} />
            <Route path="lockdown" element={<LockdownPage />} />
            <Route path="reaction-roles" element={<MessageBuilderPage />} />
            <Route path="feedback" element={<FeedbackPage />} />
```

- [ ] **Step 1: Write the failing tests**

Create `dashboard/frontend/src/pages/EventDetailPanel.test.tsx`:

```typescript
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { EventDetailPanel } from './EventDetailPanel'

const tournamentDetail: client.EventDetail = {
  message_id: '900',
  type: 'tournament',
  title: 'Летний турнир',
  status: 'open',
  channel_id: '500',
  count: 1,
  description: 'desc',
  role_reward: null,
  mode: 'solo',
  max_limit: 0,
  team_size: 5,
  participants: [{ user_id: '20', ign: 'PlayerOne' }],
}

const pollDetail: client.EventDetail = {
  message_id: '901',
  type: 'poll',
  title: 'Опрос дня',
  status: 'open',
  channel_id: '500',
  count: 2,
  description: 'desc',
  role_reward: null,
  multi_select: false,
  options: [
    { label: 'Да', votes: 2, percent: 100 },
    { label: 'Нет', votes: 0, percent: 0 },
  ],
}

describe('EventDetailPanel', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders tournament participants', async () => {
    vi.spyOn(client, 'fetchEventDetail').mockResolvedValue(tournamentDetail)

    render(<EventDetailPanel messageId="900" onClose={() => {}} onChanged={() => {}} />)

    expect(await screen.findByText('Летний турнир')).toBeInTheDocument()
    expect(screen.getByText('PlayerOne')).toBeInTheDocument()
  })

  it('renders poll vote percentages', async () => {
    vi.spyOn(client, 'fetchEventDetail').mockResolvedValue(pollDetail)

    render(<EventDetailPanel messageId="901" onClose={() => {}} onChanged={() => {}} />)

    expect(await screen.findByText('Опрос дня')).toBeInTheDocument()
    expect(screen.getByText('Да')).toBeInTheDocument()
    expect(screen.getByText('100%')).toBeInTheDocument()
  })

  it('closes an event', async () => {
    vi.spyOn(client, 'fetchEventDetail').mockResolvedValue(tournamentDetail)
    const closeSpy = vi.spyOn(client, 'closeEvent').mockResolvedValue(undefined)
    const onChanged = vi.fn()

    render(<EventDetailPanel messageId="900" onClose={() => {}} onChanged={onChanged} />)

    await waitFor(() => screen.getByText('Закрыть'))
    fireEvent.click(screen.getByText('Закрыть'))

    await waitFor(() => expect(closeSpy).toHaveBeenCalledWith('900'))
    await waitFor(() => expect(onChanged).toHaveBeenCalled())
  })

  it('deletes an event after confirmation', async () => {
    vi.spyOn(client, 'fetchEventDetail').mockResolvedValue(tournamentDetail)
    const deleteSpy = vi.spyOn(client, 'deleteEvent').mockResolvedValue(undefined)
    const onChanged = vi.fn()

    render(<EventDetailPanel messageId="900" onClose={() => {}} onChanged={onChanged} />)

    await waitFor(() => screen.getByText('Удалить'))
    fireEvent.click(screen.getByText('Удалить'))
    const dialog = screen.getByRole('dialog')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Удалить событие' }))

    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith('900'))
    await waitFor(() => expect(onChanged).toHaveBeenCalled())
  })

  it('sends a notification to participants', async () => {
    vi.spyOn(client, 'fetchEventDetail').mockResolvedValue(tournamentDetail)
    const notifySpy = vi.spyOn(client, 'notifyEventParticipants').mockResolvedValue({ success: 1, failed: 0 })

    render(<EventDetailPanel messageId="900" onClose={() => {}} onChanged={() => {}} />)

    await waitFor(() => screen.getByText('Рассылка'))
    fireEvent.click(screen.getByText('Рассылка'))

    const dialog = screen.getByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText('Текст сообщения'), { target: { value: 'Привет!' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Отправить' }))

    await waitFor(() => expect(notifySpy).toHaveBeenCalledWith('900', 'Привет!'))
  })
})
```

Create `dashboard/frontend/src/pages/Events.test.tsx`:

```typescript
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { EventsPage } from './Events'

const summary: client.EventSummary = {
  message_id: '900',
  type: 'tournament',
  title: 'Летний турнир',
  status: 'open',
  channel_id: '500',
  count: 5,
}

describe('EventsPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('lists events for the default open filter', async () => {
    const fetchSpy = vi.spyOn(client, 'fetchEvents').mockResolvedValue([summary])

    render(<EventsPage />)

    expect(await screen.findByText('Летний турнир')).toBeInTheDocument()
    expect(fetchSpy).toHaveBeenCalledWith('open')
  })

  it('reloads with the closed filter when changed', async () => {
    const fetchSpy = vi.spyOn(client, 'fetchEvents').mockResolvedValue([])

    render(<EventsPage />)
    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith('open'))

    fireEvent.change(screen.getByLabelText('Статус'), { target: { value: 'closed' } })

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith('closed'))
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm run test -- Events`
Expected: FAIL — neither `Events.tsx` nor `EventDetailPanel.tsx` exists yet.

- [ ] **Step 3: Create `dashboard/frontend/src/pages/EventDetailPanel.tsx`**

```tsx
import { useEffect, useState } from 'react'
import {
  closeEvent,
  deleteEvent,
  fetchEventDetail,
  notifyEventParticipants,
  type EventDetail,
  type EventParticipantTeamCode,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'

interface Props {
  messageId: string
  onClose: () => void
  onChanged: () => void
}

export function EventDetailPanel({ messageId, onClose, onChanged }: Props) {
  const [detail, setDetail] = useState<EventDetail | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [pendingDelete, setPendingDelete] = useState(false)
  const [notifyOpen, setNotifyOpen] = useState(false)
  const [notifyText, setNotifyText] = useState('')
  const [notifyError, setNotifyError] = useState('')

  useEffect(() => {
    fetchEventDetail(messageId)
      .then(setDetail)
      .catch(() => setError('Не удалось загрузить событие'))
  }, [messageId])

  const close = async () => {
    setBusy(true)
    setError('')
    try {
      await closeEvent(messageId)
      onChanged()
    } catch {
      setError('Не удалось закрыть событие')
    } finally {
      setBusy(false)
    }
  }

  const confirmDelete = async () => {
    setBusy(true)
    setError('')
    try {
      await deleteEvent(messageId)
      setPendingDelete(false)
      onChanged()
    } catch {
      setError('Не удалось удалить событие')
      setPendingDelete(false)
    } finally {
      setBusy(false)
    }
  }

  const sendNotify = async () => {
    if (!notifyText.trim()) {
      setNotifyError('Введите текст сообщения')
      return
    }
    setBusy(true)
    setNotifyError('')
    try {
      await notifyEventParticipants(messageId, notifyText.trim())
      setNotifyOpen(false)
      setNotifyText('')
    } catch {
      setNotifyError('Не удалось отправить рассылку')
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

  return (
    <Card className="animate-fade-in-up flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-semibold text-foreground">{detail.title}</h2>
          <p className="text-xs text-muted">
            {detail.type === 'tournament' ? 'Турнир' : 'Опрос'} · {detail.status}
          </p>
        </div>
        <button onClick={onClose} className="cursor-pointer text-muted hover:text-foreground">
          ×
        </button>
      </div>

      {detail.type === 'tournament' && detail.mode === 'solo' && (
        <ul className="flex flex-col gap-1 text-sm">
          {(detail.participants ?? []).map((p) => {
            const solo = p as { user_id: string; ign: string }
            return (
              <li key={solo.user_id} className="text-foreground">
                {solo.ign}
              </li>
            )
          })}
        </ul>
      )}

      {detail.type === 'tournament' && detail.mode === 'team_captain' && (
        <ul className="flex flex-col gap-1 text-sm">
          {(detail.participants ?? []).map((p) => {
            const team = p as { user_id: string; team_name: string; members: string }
            return (
              <li key={team.user_id} className="text-foreground">
                {team.team_name} — {team.members}
              </li>
            )
          })}
        </ul>
      )}

      {detail.type === 'tournament' && detail.mode === 'team_code' && (
        <div className="flex flex-col gap-2 text-sm">
          {(detail.participants as EventParticipantTeamCode[] | undefined)?.map((team) => (
            <div key={team.team_code}>
              <p className="text-foreground">{team.team_name}</p>
              <ul className="ml-3">
                {team.members.map((m) => (
                  <li key={m.user_id} className="text-muted">
                    {m.ign}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {detail.type === 'poll' && (
        <div className="flex flex-col gap-2 text-sm">
          {(detail.options ?? []).map((opt) => (
            <div key={opt.label} className="flex justify-between text-foreground">
              <span>{opt.label}</span>
              <span>{opt.percent}%</span>
            </div>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="flex gap-2 border-t border-border pt-4">
        <Button variant="secondary" onClick={close} disabled={busy}>
          Закрыть
        </Button>
        {detail.type === 'tournament' && (
          <Button variant="secondary" onClick={() => setNotifyOpen(true)} disabled={busy}>
            Рассылка
          </Button>
        )}
        <Button variant="danger" onClick={() => setPendingDelete(true)} disabled={busy}>
          Удалить
        </Button>
      </div>

      <Modal open={pendingDelete} title="Удалить событие?" onClose={() => setPendingDelete(false)}>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={() => setPendingDelete(false)}>
            Отмена
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Удалить событие
          </Button>
        </div>
      </Modal>

      <Modal open={notifyOpen} title="Рассылка участникам" onClose={() => setNotifyOpen(false)}>
        <div className="flex flex-col gap-3">
          <label className="text-sm text-muted" htmlFor="event-notify-text">
            Текст сообщения
          </label>
          <textarea
            id="event-notify-text"
            value={notifyText}
            onChange={(e) => setNotifyText(e.target.value)}
            rows={4}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />
          {notifyError && <p className="text-sm text-danger">{notifyError}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setNotifyOpen(false)} disabled={busy}>
              Отмена
            </Button>
            <Button variant="primary" onClick={sendNotify} disabled={busy}>
              Отправить
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  )
}
```

- [ ] **Step 4: Create `dashboard/frontend/src/pages/Events.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { fetchEvents, type EventSummary } from '../api/client'
import { Card } from '../components/ui/Card'
import { EventDetailPanel } from './EventDetailPanel'

type StatusFilter = 'open' | 'closed'

export function EventsPage() {
  const [status, setStatus] = useState<StatusFilter>('open')
  const [events, setEvents] = useState<EventSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState('')

  const reload = () => {
    fetchEvents(status)
      .then(setEvents)
      .catch(() => setError('Не удалось загрузить события'))
  }

  useEffect(reload, [status])

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <div className="mb-4 flex items-center gap-3">
          <h1 className="text-lg font-semibold text-foreground">События и голосования</h1>
          <label className="ml-auto text-sm text-muted" htmlFor="event-status">
            Статус
          </label>
          <select
            id="event-status"
            value={status}
            onChange={(e) => setStatus(e.target.value as StatusFilter)}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="open">Активные</option>
            <option value="closed">Закрытые</option>
          </select>
        </div>

        {error && <p className="mb-4 text-sm text-danger">{error}</p>}

        <div className="flex flex-col gap-2">
          {events.map((ev) => (
            <Card key={ev.message_id} interactive className="!p-3" onClick={() => setSelectedId(ev.message_id)}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-foreground">{ev.title}</p>
                  <p className="text-xs text-muted">
                    {ev.type === 'tournament' ? 'Турнир' : 'Опрос'} · {ev.count}
                  </p>
                </div>
              </div>
            </Card>
          ))}
          {events.length === 0 && <p className="text-sm text-muted">Событий нет.</p>}
        </div>
      </div>

      {selectedId && (
        <div className="w-96 shrink-0">
          <EventDetailPanel
            messageId={selectedId}
            onClose={() => setSelectedId(null)}
            onChanged={() => {
              setSelectedId(null)
              reload()
            }}
          />
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Wire the sidebar and route**

In `dashboard/frontend/src/pages/DashboardShell.tsx`, change the `SECTIONS` array's events entry from:

```typescript
  { label: 'События и голосования', icon: CalendarCheck },
```

to:

```typescript
  { label: 'События и голосования', icon: CalendarCheck, to: '/events' },
```

In `dashboard/frontend/src/App.tsx`, add the import (alongside the existing page imports):

```typescript
import { EventsPage } from './pages/Events'
```

And add the route (alongside the existing routes inside the `DashboardShell` route's children):

```tsx
            <Route path="events" element={<EventsPage />} />
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `npm run test -- Events`
Expected: all pass (2 in `Events.test.tsx` + 5 in `EventDetailPanel.test.tsx`).

- [ ] **Step 7: Run the full frontend suite, typecheck, and build**

Run: `npm run test` then `npx tsc --noEmit` then `npm run build`
Expected: `78 passed` (71 from Task 5 + 7 new), `tsc` clean, build clean.

- [ ] **Step 8: Commit**

```bash
git add dashboard/frontend/src/pages/Events.tsx dashboard/frontend/src/pages/EventDetailPanel.tsx dashboard/frontend/src/pages/Events.test.tsx dashboard/frontend/src/pages/EventDetailPanel.test.tsx dashboard/frontend/src/pages/DashboardShell.tsx dashboard/frontend/src/App.tsx
git commit -m "feat(dashboard): add events list and detail panel UI, wire into sidebar"
```

---

### Task 7: Manual E2E verification (user-performed, not a subagent task)

Not automatable — requires a live Discord test server. Steps for the user:

1. Restart the backend and frontend dev servers (done by the assistant before handoff, per standing project convention).
2. On the "События и голосования" sidebar entry, confirm it's now a live link (no more "скоро" badge) and opens the events list.
3. Create a tournament and a poll via the existing `/event setup` Discord command; register a couple of participants / cast a few votes.
4. On the dashboard, confirm both appear under the "Активные" filter with correct participant/vote counts, and that the detail panel shows the right participant/vote breakdown for each mode you tested (solo/team_captain/team_code for tournaments, single/multi-select for polls).
5. Click "Рассылка" on a tournament, send a test message, confirm participants receive the DM (matching what the bot's own `/event manage` → "📢 Рассылка" already does).
6. Click "Закрыть" on an event; confirm its Discord message shows the closed footer and disabled buttons, and that it now appears under "Закрытые" instead of "Активные".
7. Click "Удалить" on an event with a `role_reward` set; confirm the role is removed from all participants and the Discord message is deleted.
8. Confirm `/event manage`'s own close/delete/notify still work unchanged, for parity — and confirm an event closed/deleted from the dashboard is immediately reflected if you then open `/event manage` in Discord (proving the cache removal from Task 1 actually works end-to-end, not just in tests).

---

## Self-Review Notes

- **Spec coverage:** all spec sections map to tasks — cache removal (Task 1), `events_core.py` extraction (Task 2), list/detail routes (Task 3), close/delete/notify routes (Task 4), frontend client (Task 5), frontend UI + sidebar/route wiring (Task 6). The spec's testing section's "dedicated regression test proving `load_events()` reads fresh" is `test_load_events_reads_fresh_after_external_write` in Task 1.
- **Placeholder scan:** none found — every step has complete code.
- **Type/name consistency:** `events_core.close_event(bot, message_id)` / `delete_event(bot, guild, message_id)` / `notify_participants(bot, guild, message_id, text)` are defined once in Task 2 and consumed with identical signatures in Task 2's own refactored `events.py` closures and Task 4's routes. `serialize_event_summary`/`serialize_event_detail` are defined once in Task 3 and not redefined elsewhere. Frontend `EventSummary`/`EventDetail` types (Task 5) are consumed identically by `Events.tsx`/`EventDetailPanel.tsx` (Task 6). Test count progression double-checked by direct arithmetic: 243 → 246 (Task 1, +3) → 257 (Task 2, +11) → 266 (Task 3, +9) → 276 (Task 4, +10) backend; 65 → 71 (Task 5, +6) → 78 (Task 6, +7) frontend.
- **Cross-task risk caught during planning:** `discord.ui.View.from_message()` (used by the original `cb_close` closure) cannot be exercised against this project's plain-Python fakes. Task 2 documents the deliberate switch to rebuilding the view via `create_participation_view(..., disabled=True)` instead, in the plan's Global Constraints section, so a reviewer can independently judge it rather than discover it as an unexplained diff — the same discipline this project applied to the `isinstance` → `is not None` deviation in `feedback_core.decide_case` back in Phase 4a.
- **Cross-task risk caught during planning (test-query collision):** Task 6's delete/notify tests each open a `Modal` containing a button whose name could collide with page-level text in a larger integration (though `EventDetailPanel` has no page-level "Удалить событие"/"Отправить" duplicate today) — the tests still use `within(dialog)` scoping defensively and consistently with this project's established convention, so a future change that adds a colliding label elsewhere won't silently break query specificity assumptions.
