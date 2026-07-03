# Phase 4c: Category Deletion Cleanup, Default Template, Panel Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the bug where deleting a feedback category leaves its pending cases permanently stuck, and add two dashboard convenience features: a one-click default-category-template button, and a button to publish the feedback panel to a Discord channel without using the `/feedback_panel send` slash command.

**Architecture:** The cascade-delete fix is a small addition to the existing `DELETE /api/feedback-categories/{category_key}` route. The panel-publishing logic currently inline in `feedback_menu.py`'s slash command gets extracted into `feedback_core.py` (the same `_core.py` extraction pattern already used for `decide_case`), then both the slash command and a new dashboard route call that shared function. The default-template button is a frontend-only prefill using a hardcoded constant — no backend changes.

**Tech Stack:** Python 3.12, discord.py, aiohttp (backend); React + TypeScript + Vite + Vitest (frontend). Same stack as every prior phase in this project.

## Global Constraints

- No caching in `feedback_categories.py` or its callers (already true, not touched by this plan).
- IDs (channel_id, role_ids) are stored/serialized as strings in JSON and API payloads; `int(...)`-conversion happens only at the exact Discord API call site.
- All new/touched routes remain gated by `require_dashboard_access`.
- Any acting-user identity used by a route must come from `request["moderator"]` (the session-derived moderator), never from the client-supplied JSON body.
- Validation order is binding everywhere: structural checks first, Discord-existence checks second, permission checks last (enforced by the `@require_dashboard_access` decorator running before the handler body).
- Never bare `git add -A`/`git add .` — stage only the specific files touched by each task.
- Never silently change a stated numeric/behavioral constant or weaken a test assertion to make it pass — if something in this plan looks wrong, flag it in the task report and fix the test's own data, not production code.
- `feedback_menu.py` is interaction-driven Discord bot code with zero pytest coverage anywhere in this project (no `FakeInteraction` pattern exists, and none should be invented). Verify any change to it by careful, minimal, line-by-line diffing against the current source — not by writing new interaction tests.
- Baseline before this plan: 235 backend (pytest) tests, 62 frontend (Vitest) tests, `tsc` clean, build clean, all at commit `392cc9c`.

---

### Task 1: Cascade-delete pending cases when their category is deleted

**Files:**
- Modify: `dashboard/backend/routes/feedback.py:228-238` (the `delete_feedback_category` route)
- Test: `dashboard/backend/tests/test_feedback_category_routes.py`

**Interfaces:**
- Consumes: `bot.feedback_cases` (a plain `dict[str, dict]` already on the `FakeBot`/real bot, keyed by `case_id`, each value having at least `category_key` and `status` keys — this is the exact same structure `feedback_core.decide_case` and the `list_feedback_cases`/`get_feedback_case` routes already read), `bot.update_file()` (async, no args, already used throughout the project to persist bot state).
- Produces: no new public interface — this task only changes the body of the existing `DELETE /api/feedback-categories/{category_key}` route, whose request/response shape is unchanged (still `{"ok": true}` on success, `{"error": "not_found"}` / 404 unchanged).

The current route body (read it first to confirm it still matches before editing):

```python
@routes.delete("/api/feedback-categories/{category_key}")
@require_dashboard_access
async def delete_feedback_category(request: web.Request) -> web.Response:
    category_key = request.match_info["category_key"]
    categories = feedback_categories.load_categories()
    if category_key not in categories:
        return web.json_response({"error": "not_found"}, status=404)

    del categories[category_key]
    feedback_categories.save_categories(categories)
    return web.json_response({"ok": True})
```

- [ ] **Step 1: Write the failing tests**

Add to `dashboard/backend/tests/test_feedback_category_routes.py` (append at the end of the file, after `test_delete_feedback_category_requires_auth`):

```python
@pytest.mark.asyncio
async def test_delete_feedback_category_removes_pending_cases(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    bot = app["bot"]
    bot.feedback_cases["PR-0001"] = {"case_id": "PR-0001", "category_key": "players", "status": "pending"}
    bot.feedback_cases["PR-0002"] = {"case_id": "PR-0002", "category_key": "players", "status": "approved"}
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    resp = await client.delete("/api/feedback-categories/players")

    assert resp.status == 200
    assert "PR-0001" not in bot.feedback_cases
    assert "PR-0002" in bot.feedback_cases
    assert bot.update_file_calls == 1


@pytest.mark.asyncio
async def test_delete_feedback_category_no_update_file_call_when_no_pending_cases(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    bot = app["bot"]
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    resp = await client.delete("/api/feedback-categories/players")

    assert resp.status == 200
    assert bot.update_file_calls == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_feedback_category_routes.py -v -k "removes_pending_cases or no_update_file_call"`
Expected: `test_delete_feedback_category_removes_pending_cases` FAILS with `assert "PR-0001" not in bot.feedback_cases` (case still present, since the route doesn't clean it up yet). `test_delete_feedback_category_no_update_file_call_when_no_pending_cases` PASSES already (nothing to fix there yet, `update_file_calls` starts at 0 and nothing currently calls it) — that's expected and fine, it becomes a real regression guard once Step 3 lands.

- [ ] **Step 3: Implement the cascade-delete**

Replace the route body in `dashboard/backend/routes/feedback.py` with:

```python
@routes.delete("/api/feedback-categories/{category_key}")
@require_dashboard_access
async def delete_feedback_category(request: web.Request) -> web.Response:
    category_key = request.match_info["category_key"]
    categories = feedback_categories.load_categories()
    if category_key not in categories:
        return web.json_response({"error": "not_found"}, status=404)

    del categories[category_key]
    feedback_categories.save_categories(categories)

    bot = request.app["bot"]
    removed_case_ids = [
        case_id
        for case_id, case_data in bot.feedback_cases.items()
        if case_data.get("category_key") == category_key and case_data.get("status") == "pending"
    ]
    if removed_case_ids:
        for case_id in removed_case_ids:
            del bot.feedback_cases[case_id]
        await bot.update_file()

    return web.json_response({"ok": True})
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_feedback_category_routes.py -v`
Expected: all pass (14 existing + 2 new = 16 in this file).

- [ ] **Step 5: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `237 passed` (235 baseline + 2 new).

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/feedback.py dashboard/backend/tests/test_feedback_category_routes.py
git commit -m "fix: cascade-delete pending feedback cases when their category is deleted"
```

---

### Task 2: Extract panel-publishing logic into `feedback_core.py`

**Files:**
- Modify: `feedback_core.py` (add `publish_feedback_panel`)
- Modify: `feedback_menu.py:51-89` (refactor `feedback_panel_send` to call it)
- Modify: `dashboard/backend/tests/fakes.py` (add a `mention` property to `FakeChannel`)
- Test: `dashboard/backend/tests/test_feedback_core.py`

**Interfaces:**
- Consumes: `feedback_menu.FeedbackView` (existing class, `FeedbackView(bot)` — builds one button per category from `get_feedback_categories()`), `feedback_menu.PANEL_BANNER_URL` (existing module-level string constant), `bot.utcnow()`, `bot.send_log(embed)` (existing, already used by `decide_case`), `channel.send(**kwargs)` (existing on both real `discord.TextChannel` and this project's `FakeChannel`), `channel.mention` (added by Step 1 of this task).
- Produces: `async def publish_feedback_panel(bot, channel, published_by_id: int, published_by_mention: str) -> discord.Message` in `feedback_core.py`. Task 3's dashboard route and this task's refactored slash command both call this exact signature. `publish_feedback_panel` does **not** validate that `channel` is a text channel — that is the caller's responsibility (the slash command already does an `isinstance(target_channel, discord.TextChannel)` check before calling it; Task 3's route does a plain existence check via `guild.get_channel(...)`, consistent with this project's existing `_validate_category_relations` pattern which also does not do an `isinstance` check, since this project's test fakes are not real discord.py subclasses).

- [ ] **Step 1: Add a `mention` property to `FakeChannel`**

In `dashboard/backend/tests/fakes.py`, inside the `FakeChannel` class (right after `self.send_raises = None` in `__init__`, before the `fetch_message` method), add:

```python
    @property
    def mention(self):
        return f"<#{self.id}>"
```

- [ ] **Step 2: Write the failing test**

Add to `dashboard/backend/tests/test_feedback_core.py` (append at the end of the file):

```python
@pytest.mark.asyncio
async def test_publish_feedback_panel_sends_embed_and_logs():
    channel = FakeChannel(500, name="reports")
    guild = FakeGuild(channels=[channel])
    bot = FakeBot(guild)

    message = await feedback_core.publish_feedback_panel(
        bot, channel, published_by_id=10, published_by_mention="<@10>"
    )

    assert len(channel.send_calls) == 1
    assert channel.send_calls[0]["embed"].color.value == discord.Color.from_rgb(44, 47, 51).value
    assert channel.send_calls[0]["view"] is not None
    assert message.id in channel._messages
    assert len(bot.sent_logs) == 1
    assert "<@10>" in bot.sent_logs[0].description
    assert "(`10`)" in bot.sent_logs[0].description
    assert "<#500>" in bot.sent_logs[0].description
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python -m pytest dashboard/backend/tests/test_feedback_core.py -v -k publish_feedback_panel`
Expected: FAIL with `AttributeError: module 'feedback_core' has no attribute 'publish_feedback_panel'`.

- [ ] **Step 4: Add `publish_feedback_panel` to `feedback_core.py`**

Append to `feedback_core.py` (after `decide_case`, at the end of the file):

```python
async def publish_feedback_panel(bot, channel, published_by_id: int, published_by_mention: str) -> discord.Message:
    from feedback_menu import FeedbackView, PANEL_BANNER_URL

    embed = discord.Embed(
        description=(
            "### <:IconModeration:1356540597770518538>・Выберите тип связи со стаффом.\n\n"
            "```\n"
            "В создавшемся обращении, как можно точнее опишите его суть "
            "и по возможности прикрепите фото и/или видео для дальнейшего ознакомления.\n"
            "```"
        ),
        color=discord.Color.from_rgb(44, 47, 51),
    )
    embed.set_image(url=PANEL_BANNER_URL)

    message = await channel.send(embed=embed, view=FeedbackView(bot))

    log_embed = discord.Embed(
        title="🧩 Панель feedback опубликована",
        description=(
            f"**Кто:** {published_by_mention} (`{published_by_id}`)\n"
            f"**Канал:** {channel.mention}\n"
            f"**Сообщение:** [Открыть]({message.jump_url})"
        ),
        color=discord.Color.blurple(),
        timestamp=bot.utcnow(),
    )
    await bot.send_log(log_embed)

    return message
```

This is a byte-for-byte copy of the embed text, color, and log fields currently inline in `feedback_menu.py`'s `feedback_panel_send` (see Step 6) — only the parameter names change (`published_by_id`/`published_by_mention` instead of reading `interaction.user` directly, `channel` instead of `target_channel`).

- [ ] **Step 5: Run the test to verify it passes**

Run: `python -m pytest dashboard/backend/tests/test_feedback_core.py -v -k publish_feedback_panel`
Expected: PASS.

- [ ] **Step 6: Refactor `feedback_menu.py`'s `feedback_panel_send` to call it**

Read `feedback_menu.py` in full first to confirm the method still matches. Replace the entire method body (currently lines 51-89, from `@feedback_panel_group.command(...)` through the final `await self.bot.send_log(log_embed)`) with:

```python
    @feedback_panel_group.command(name="send", description="Опубликовать панель обратной связи")
    @app_commands.describe(channel="Канал для публикации панели")
    async def feedback_panel_send(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
    ):
        target_channel = channel or interaction.channel
        if not isinstance(target_channel, discord.TextChannel):
            await interaction.response.send_message("Нужен обычный текстовый канал.", ephemeral=True)
            return

        # Сначала отвечаем на interaction, потом отправляем панель
        await interaction.response.send_message("Панель опубликована.", ephemeral=True)
        await feedback_core.publish_feedback_panel(
            self.bot,
            target_channel,
            published_by_id=interaction.user.id,
            published_by_mention=interaction.user.mention,
        )
```

This preserves the exact existing behavior: same `isinstance` guard, same ephemeral response ordering (respond to the interaction before sending the panel — unchanged), same embed/log content (now built by `publish_feedback_panel`). `feedback_menu.py` already has `import feedback_core` at the top of the file (from Phase 4a) — no new import needed. `PANEL_BANNER_URL` stays defined in `feedback_menu.py` exactly where it is; `feedback_core.py`'s local import in Step 4 reads it from there.

- [ ] **Step 7: Verify `feedback_menu.py` still imports cleanly**

Run: `python -c "import feedback_menu"`
Expected: exits cleanly, no output, no traceback.

- [ ] **Step 8: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `238 passed` (237 from Task 1 + 1 new).

- [ ] **Step 9: Commit**

```bash
git add feedback_core.py feedback_menu.py dashboard/backend/tests/fakes.py dashboard/backend/tests/test_feedback_core.py
git commit -m "refactor: extract panel-publishing into feedback_core.publish_feedback_panel"
```

---

### Task 3: `POST /api/feedback-panel/publish` route

**Files:**
- Modify: `dashboard/backend/routes/feedback.py` (append the new route; no `app.py` changes needed — this route table is already registered)
- Test: Create `dashboard/backend/tests/test_feedback_panel_routes.py`

**Interfaces:**
- Consumes: `feedback_core.publish_feedback_panel(bot, channel, published_by_id, published_by_mention)` (Task 2), `_get_guild_or_none(request)` (existing helper already at the top of `dashboard/backend/routes/feedback.py`), `require_dashboard_access` (existing decorator).
- Produces: `POST /api/feedback-panel/publish` — request body `{"channel_id": "<string>"}`, response `{"ok": true, "message_id": "<string>"}` on success (201... no, 200, since no new resource is created at a new URL — matches this project's convention of 200 for actions and 201 only for the category-create route). Errors: `{"error": "invalid_request"}` 400 (missing/non-string/non-numeric `channel_id`), `{"error": "channel_not_found"}` 404, `{"error": "service_unavailable"}` 503 (no guild), 401 (unauthenticated, via the decorator).

- [ ] **Step 1: Write the failing tests**

Create `dashboard/backend/tests/test_feedback_panel_routes.py`:

```python
import pytest

from dashboard.backend.routes.feedback import routes as feedback_routes
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, force_login, make_moderation_app


def build(channels=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator], channels=channels or [])
    return guild, make_moderation_app(FakeBot(guild), [feedback_routes])


@pytest.mark.asyncio
async def test_publish_feedback_panel_success(aiohttp_client):
    channel = FakeChannel(500, name="reports")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-panel/publish", json={"channel_id": "500"})

    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert len(channel.send_calls) == 1


@pytest.mark.asyncio
async def test_publish_feedback_panel_404_when_channel_missing(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-panel/publish", json={"channel_id": "500"})

    assert resp.status == 404
    assert (await resp.json())["error"] == "channel_not_found"


@pytest.mark.asyncio
async def test_publish_feedback_panel_rejects_missing_channel_id(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-panel/publish", json={})

    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_publish_feedback_panel_requires_auth(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)

    resp = await client.post("/api/feedback-panel/publish", json={"channel_id": "500"})

    assert resp.status == 401


@pytest.mark.asyncio
async def test_publish_feedback_panel_attributes_to_session_moderator_not_body(aiohttp_client):
    channel = FakeChannel(500, name="reports")
    _, app = build(channels=[channel])
    bot = app["bot"]
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-panel/publish", json={"channel_id": "500"})

    assert resp.status == 200
    assert "<@10>" in bot.sent_logs[0].description
```

The last test proves the acting-user identity comes from the login session (`force_login(client, 10)`), not from the request body — the POST body has no user-identifying field at all, yet the published-panel log embed correctly attributes moderator id `10`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_feedback_panel_routes.py -v`
Expected: all 5 FAIL with 404 (route doesn't exist yet, aiohttp returns 404 for unmatched routes).

- [ ] **Step 3: Add the route**

Append to `dashboard/backend/routes/feedback.py` (at the end of the file, after `delete_feedback_category`):

```python
@routes.post("/api/feedback-panel/publish")
@require_dashboard_access
async def publish_feedback_panel_route(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    channel_id_raw = body.get("channel_id")
    if not isinstance(channel_id_raw, str) or not channel_id_raw:
        return web.json_response({"error": "invalid_request"}, status=400)
    try:
        channel_id = int(channel_id_raw)
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)

    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    bot = request.app["bot"]
    moderator = request["moderator"]
    message = await feedback_core.publish_feedback_panel(
        bot, channel, published_by_id=moderator.id, published_by_mention=f"<@{moderator.id}>"
    )
    return web.json_response({"ok": True, "message_id": str(message.id)})
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_feedback_panel_routes.py -v`
Expected: all 5 pass.

- [ ] **Step 5: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `243 passed` (238 from Task 2 + 5 new).

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/feedback.py dashboard/backend/tests/test_feedback_panel_routes.py
git commit -m "feat(dashboard): add POST /api/feedback-panel/publish route"
```

---

### Task 4: Frontend API client function

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts` (append)
- Test: Create `dashboard/frontend/src/api/feedbackPanel.test.ts`

**Interfaces:**
- Consumes: `apiFetch<T>` and `jsonInit` (existing helpers already at the top of `client.ts`).
- Produces: `export async function publishFeedbackPanel(channelId: string): Promise<{ message_id: string }>` — matches Task 3's route exactly (`POST /api/feedback-panel/publish`, body `{ channel_id: channelId }`, response includes `message_id`).

- [ ] **Step 1: Write the failing test**

Create `dashboard/frontend/src/api/feedbackPanel.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest'
import { publishFeedbackPanel } from './client'

describe('publishFeedbackPanel', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('POSTs the selected channel id and returns the message id', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true, message_id: '999' }), { status: 200 }),
    )

    const result = await publishFeedbackPanel('500')

    expect(result).toEqual({ ok: true, message_id: '999' })
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/feedback-panel/publish')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual({ channel_id: '500' })
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `dashboard/frontend/`): `npm run test -- feedbackPanel`
Expected: FAIL — `publishFeedbackPanel` is not exported from `./client`.

- [ ] **Step 3: Add the function**

Append to `dashboard/frontend/src/api/client.ts` (at the end of the file, after `deleteFeedbackCategory`):

```typescript
export function publishFeedbackPanel(channelId: string): Promise<{ ok: boolean; message_id: string }> {
  return apiFetch('/api/feedback-panel/publish', jsonInit('POST', { channel_id: channelId }))
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm run test -- feedbackPanel`
Expected: PASS. (Note the test asserts `result` equals `{ ok: true, message_id: '999' }` — the function's declared return type includes `ok`, matching the actual JSON shape returned by Task 3's route.)

- [ ] **Step 5: Run the full frontend suite and typecheck**

Run: `npm run test` then `npx tsc --noEmit`
Expected: `63 passed` (62 baseline + 1 new), `tsc` clean.

- [ ] **Step 6: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/feedbackPanel.test.ts
git commit -m "feat(dashboard): add publishFeedbackPanel API client function"
```

---

### Task 5: Frontend UI — default template button and publish button

**Files:**
- Modify: `dashboard/frontend/src/pages/FeedbackCategories.tsx`
- Modify: `dashboard/frontend/src/pages/FeedbackCategories.test.tsx`

**Interfaces:**
- Consumes: `publishFeedbackPanel(channelId: string)` (Task 4), existing `channels` state (already fetched via `fetchChannels()` in this file's `reload()`), existing `Modal`/`Button` components, existing `spec`/`setSpec`/`setEditingKey`/`setFormOpen`/`setError` state already in this file.
- Produces: no new exports — purely additive UI inside `FeedbackCategoriesPage`.

- [ ] **Step 1: Write the failing tests**

Read `dashboard/frontend/src/pages/FeedbackCategories.test.tsx` in full first to see its existing imports and helper patterns. Add these two tests at the end of the `describe('FeedbackCategoriesPage', ...)` block, and change the import line at the top of the file from:

```typescript
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
```

to:

```typescript
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
```

Then append:

```typescript
  it('opens the create form pre-filled with the default category template', async () => {
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'reports' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<FeedbackCategoriesPage />)

    await waitFor(() => screen.getByText('Дефолтный шаблон'))
    fireEvent.click(screen.getByText('Дефолтный шаблон'))

    await waitFor(() => screen.getByLabelText('Ключ'))
    expect((screen.getByLabelText('Ключ') as HTMLInputElement).value).toBe('players')
    expect((screen.getByLabelText('Префикс дела') as HTMLInputElement).value).toBe('PR')
    expect((screen.getByLabelText('Имя треда') as HTMLInputElement).value).toBe('player-report')
  })

  it('publishes the panel to the selected channel', async () => {
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'reports' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const publishSpy = vi.spyOn(client, 'publishFeedbackPanel').mockResolvedValue({ ok: true, message_id: '999' })

    render(<FeedbackCategoriesPage />)

    await waitFor(() => screen.getByRole('button', { name: 'Опубликовать' }))
    fireEvent.click(screen.getByRole('button', { name: 'Опубликовать' }))

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })

    const dialog = screen.getByRole('dialog')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Опубликовать' }))

    await waitFor(() => expect(publishSpy).toHaveBeenCalledWith('500'))
  })
```

**Note on the second test's button-name collision:** once the publish modal is open, there are TWO buttons both named "Опубликовать" — the page-level button (now covered by the modal overlay) and the modal's own submit button. `within(dialog).getByRole('button', { name: 'Опубликовать' })` scopes the query to only the modal's button. Do NOT rename either button to dodge this — scope the query instead (this project's established convention; see the "Дефолтный Шаблон" and "Категории" tab-label incidents in earlier phases of this project's history for why).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm run test -- FeedbackCategories`
Expected: both new tests FAIL (`getByText('Дефолтный шаблон')` / `getByRole('button', { name: 'Опубликовать' })` find nothing yet).

- [ ] **Step 3: Add the default template constant and button**

In `dashboard/frontend/src/pages/FeedbackCategories.tsx`, after the existing `EMPTY_FIELD` constant (currently line 18) and before `emptySpec()` (currently line 20), add:

```typescript
const DEFAULT_TEMPLATE: FeedbackCategorySpec = {
  key: 'players',
  title: 'Жалоба на участника',
  button_label: '            Жалоба на участника            ',
  channel_id: '',
  case_prefix: 'PR',
  case_title: 'Жалоба на участника',
  thread_name: 'player-report',
  review_role_ids: [],
  approved_text: 'Участник наказан.',
  denied_text: 'Жалоба отклонена.',
  modal_title: 'Жалоба на участника',
  fields: [
    { key: 'offender', label: 'Ник / ID участника', style: 'short', required: true, max_length: 120 },
    { key: 'complaint', label: 'Суть жалобы', style: 'paragraph', required: true, max_length: 1000 },
    { key: 'datetime', label: 'Дата и время ситуации', style: 'short', required: false, max_length: 120 },
    { key: 'proof', label: 'Доказательства', style: 'paragraph', required: false, max_length: 1000 },
  ],
  mini_summary_key: 'offender',
}
```

This is byte-for-byte the same content as `feedback_categories.py`'s `migrate_from_env_if_needed()` "players" template, minus `channel_id`/`review_role_ids` (left empty for the user to pick).

Add the import for `publishFeedbackPanel` — change the import block at the top of the file from:

```typescript
import {
  createFeedbackCategory,
  deleteFeedbackCategory,
  fetchChannels,
  fetchFeedbackCategories,
  fetchRoles,
  updateFeedbackCategory,
  type ChannelInfo,
  type FeedbackCategoryFieldSpec,
  type FeedbackCategorySpec,
  type RoleInfo,
} from '../api/client'
```

to:

```typescript
import {
  createFeedbackCategory,
  deleteFeedbackCategory,
  fetchChannels,
  fetchFeedbackCategories,
  fetchRoles,
  publishFeedbackPanel,
  updateFeedbackCategory,
  type ChannelInfo,
  type FeedbackCategoryFieldSpec,
  type FeedbackCategorySpec,
  type RoleInfo,
} from '../api/client'
```

Inside `FeedbackCategoriesPage`, after the existing `openCreate` function, add:

```typescript
  const openDefaultTemplate = () => {
    setEditingKey(null)
    setSpec({ ...DEFAULT_TEMPLATE, fields: DEFAULT_TEMPLATE.fields.map((f) => ({ ...f })) })
    setError('')
    setFormOpen(true)
  }
```

Change the page header's button row from:

```tsx
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-foreground">Категории обращений</h1>
        <Button variant="primary" onClick={openCreate}>
          Создать категорию
        </Button>
      </div>
```

to:

```tsx
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-foreground">Категории обращений</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={openDefaultTemplate}>
            Дефолтный шаблон
          </Button>
          <Button variant="secondary" onClick={openPublish}>
            Опубликовать
          </Button>
          <Button variant="primary" onClick={openCreate}>
            Создать категорию
          </Button>
        </div>
      </div>
```

- [ ] **Step 4: Run the default-template test to verify it passes**

Run: `npm run test -- FeedbackCategories -t "default category template"`
Expected: PASS. (The publish test still fails — `openPublish` doesn't exist yet.)

- [ ] **Step 5: Add the publish button state, handler, and modal**

Inside `FeedbackCategoriesPage`, after the existing `pendingDelete`/`error`/`busy` state declarations, add:

```typescript
  const [publishOpen, setPublishOpen] = useState(false)
  const [publishChannelId, setPublishChannelId] = useState('')
  const [publishBusy, setPublishBusy] = useState(false)
  const [publishError, setPublishError] = useState('')
```

After the existing `openDefaultTemplate` function (added in Step 3), add:

```typescript
  const openPublish = () => {
    setPublishChannelId('')
    setPublishError('')
    setPublishOpen(true)
  }

  const publish = async () => {
    if (!publishChannelId) {
      setPublishError('Выберите канал')
      return
    }
    setPublishBusy(true)
    setPublishError('')
    try {
      await publishFeedbackPanel(publishChannelId)
      setPublishOpen(false)
    } catch {
      setPublishError('Не удалось опубликовать панель')
    } finally {
      setPublishBusy(false)
    }
  }
```

After the existing "Удалить категорию?" `Modal` block (the last element before the closing `</div>` at the end of the component's return), add:

```tsx
      <Modal open={publishOpen} title="Опубликовать панель обращений" onClose={() => setPublishOpen(false)}>
        <div className="flex flex-col gap-3">
          <label className="text-sm text-muted" htmlFor="fc-publish-channel">
            Канал
          </label>
          <select
            id="fc-publish-channel"
            value={publishChannelId}
            onChange={(e) => setPublishChannelId(e.target.value)}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="">Выберите канал…</option>
            {channels.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          {publishError && <p className="text-sm text-danger">{publishError}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setPublishOpen(false)} disabled={publishBusy}>
              Отмена
            </Button>
            <Button variant="primary" onClick={publish} disabled={publishBusy}>
              {publishBusy ? 'Публикуем…' : 'Опубликовать'}
            </Button>
          </div>
        </div>
      </Modal>
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `npm run test -- FeedbackCategories`
Expected: all pass, including both new tests.

- [ ] **Step 7: Run the full frontend suite, typecheck, and build**

Run: `npm run test` then `npx tsc --noEmit` then `npm run build`
Expected: `65 passed` (63 from Task 4 + 2 new), `tsc` clean, build clean.

- [ ] **Step 8: Commit**

```bash
git add dashboard/frontend/src/pages/FeedbackCategories.tsx dashboard/frontend/src/pages/FeedbackCategories.test.tsx
git commit -m "feat(dashboard): add default-template and publish-panel buttons to Категории page"
```

---

### Task 6: Manual E2E verification (user-performed, not a subagent task)

Not automatable — requires a live Discord test server. Steps for the user:

1. Restart the backend and frontend dev servers (done by the assistant before handoff, per standing project convention).
2. On the Категории page, create a category, add a pending case for it in Discord (submit the feedback form), then delete the category from the dashboard. Confirm the pending case disappears from the Обращения tab's list. Confirm an already-decided (approved/denied) case for a *different, still-existing* category is unaffected.
3. Click "Дефолтный шаблон", confirm the create form opens pre-filled with the "players" template fields, pick a channel and role, save, confirm the category is created correctly.
4. Click "Опубликовать", pick a channel, confirm the panel embed with category buttons appears in that Discord channel (matching what `/feedback_panel send` produces), and confirm a log entry appears in the bot's log channel.
5. Confirm `/feedback_panel send` (the original slash command) still works unchanged, for parity.

---

## Self-Review Notes

- **Spec coverage:** all three spec sections (cascade-delete, default template, publish button) map to Tasks 1, 5 (template half), and 2+3+5 (publish half) respectively. Every "Testing" bullet in the spec has a corresponding task-level test.
- **Placeholder scan:** none found — every step has complete code.
- **Type/name consistency:** `publish_feedback_panel(bot, channel, published_by_id, published_by_mention)` is defined once in Task 2 and consumed identically (same parameter names, same call shape) in Task 2's own refactored slash command and Task 3's route. `publishFeedbackPanel(channelId: string)` in Task 4 is consumed identically in Task 5. Test count progression double-checked by direct arithmetic: 235 → 237 (Task 1, +2) → 238 (Task 2, +1) → 243 (Task 3, +5) backend; 62 → 63 (Task 4, +1) → 65 (Task 5, +2) frontend.
- **Cross-task risk caught during planning:** Task 5's second test opens a modal containing a button with the exact same accessible name ("Опубликовать") as the page-level button that opened it — this is the same class of test-query collision this project hit twice before (Phase 3b's "Reaction Roles" tab, Phase 4b's "Обращения" tab). The plan pre-empts it by specifying `within(dialog)` scoping directly in Task 5's Step 1, rather than leaving it for a reviewer to catch after the fact.
