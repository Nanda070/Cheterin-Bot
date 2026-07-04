# Dashboard: Scrollbar Styling, Title Rename, Plain-Text Embeds — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship three independent, small dashboard UX fixes approved in `docs/superpowers/specs/2026-07-04-dashboard-scrollbar-title-plain-text-embeds-design.md` (commit `0f636a3`): a themed scrollbar sitewide, a renamed site title, and support for sending plain-text-only messages from the embed builder.

**Architecture:** Fix 1 is a pure CSS addition to the existing global stylesheet. Fix 2 is a three-file text replacement. Fix 3 threads a `content` parameter through the existing `validate_embed_spec`/`validateEmbedSpec` validators (frontend and backend) so the "must have an embed field" check is skipped when message text is present, and both `create_embed_message`/`update_embed_message` send `embed=None` instead of an empty `discord.Embed` when the spec truly has no content.

**Tech Stack:** React + TypeScript + Vite (frontend), aiohttp.web + discord.py (backend), Vitest + Testing Library (frontend tests), pytest + pytest-asyncio (backend tests).

## Global Constraints

- Only these files change: `dashboard/frontend/src/index.css`, `dashboard/frontend/src/pages/DashboardShell.tsx`, `dashboard/frontend/index.html`, `dashboard/frontend/src/pages/EmbedBuilder.tsx`, `embed_builder.py`, `dashboard/backend/routes/embed_builder.py` — plus `dashboard/frontend/src/pages/Login.tsx`, found during planning to contain the same title string as `DashboardShell.tsx` (see Task 2 note). No new files, no new routes.
- The existing `empty_embed` error must still fire when BOTH `content` and every embed field are blank — this is a regression risk, not a new behavior.
- Validation order stays: structural checks (spec/content validation, role-id structure) → Discord-existence checks (channel/message lookup) → role/permission checks. Do not reorder the existing checks in `create_embed_message`/`update_embed_message`.
- `EmbedPreview.tsx` needs no changes — it already renders `content` separately from the embed card.

---

### Task 1: Themed scrollbar

**Files:**
- Modify: `dashboard/frontend/src/index.css:34-44` (existing `@layer base` block)

**Interfaces:** None — pure CSS, no exports or function signatures involved.

- [ ] **Step 1: Add the scrollbar rules to the existing `@layer base` block**

Open `dashboard/frontend/src/index.css` and replace the current `@layer base` block (lines 34-44):

```css
@layer base {
  body {
    background-color: var(--color-background);
    color: var(--color-foreground);
    font-family: var(--font-sans);
  }

  * {
    border-color: var(--color-border);
  }
}
```

with:

```css
@layer base {
  body {
    background-color: var(--color-background);
    color: var(--color-foreground);
    font-family: var(--font-sans);
  }

  * {
    border-color: var(--color-border);
    scrollbar-width: thin;
    scrollbar-color: var(--color-border) transparent;
  }

  *::-webkit-scrollbar {
    width: 10px;
    height: 10px;
  }

  *::-webkit-scrollbar-track {
    background: transparent;
  }

  *::-webkit-scrollbar-thumb {
    background-color: var(--color-border);
    border-radius: var(--radius-control);
  }

  *::-webkit-scrollbar-thumb:hover {
    background-color: var(--color-surface-hover);
  }
}
```

- [ ] **Step 2: Verify visually in the browser**

Start the frontend dev server (`npm run dev` in `dashboard/frontend`) and open a page with a scrollable area (e.g. a long list page, or a modal with `overflow-y-auto`). Confirm: the scrollbar thumb is dark and matches `--color-border` (`#232838`), the track is transparent (shows the page background through it), the thumb turns lighter (`--color-surface-hover`, `#181d2c`) on hover, and the corners are rounded rather than square. This is a visual-only change — there is no automated test for it, consistent with the approved spec's Testing section.

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/index.css
git commit -m "style: themed scrollbar matching dark design system"
```

---

### Task 2: Site title rename

**Files:**
- Modify: `dashboard/frontend/index.html:7`
- Modify: `dashboard/frontend/src/pages/DashboardShell.tsx:57`
- Modify: `dashboard/frontend/src/pages/Login.tsx:14`

**Interfaces:** None — plain text replacement, no logic changes.

**Note:** The approved spec named only `DashboardShell.tsx` and `index.html` for this fix. While preparing this plan, `dashboard/frontend/src/pages/Login.tsx:14` was found to render the exact same string (`Панель управления ботом`) as the login page's heading — leaving it unchanged would produce a half-renamed site (new title in the header, old title on the login screen the user sees first). This file is added to the scope of this task as the same one-line text change, not a new feature.

- [ ] **Step 1: Rename the browser tab title**

In `dashboard/frontend/index.html`, change line 7:

```html
    <title>frontend</title>
```

to:

```html
    <title>404 Bot Dashboard</title>
```

- [ ] **Step 2: Rename the dashboard header title**

In `dashboard/frontend/src/pages/DashboardShell.tsx`, change line 57:

```tsx
          <span className="font-semibold">Панель управления ботом</span>
```

to:

```tsx
          <span className="font-semibold">404 Bot Dashboard</span>
```

- [ ] **Step 3: Rename the login page title**

In `dashboard/frontend/src/pages/Login.tsx`, change line 14:

```tsx
          <h1 className="text-xl font-semibold text-foreground">Панель управления ботом</h1>
```

to:

```tsx
          <h1 className="text-xl font-semibold text-foreground">404 Bot Dashboard</h1>
```

- [ ] **Step 4: Verify no old title text remains**

Run: `grep -rn "Панель управления ботом" dashboard/frontend/src dashboard/frontend/index.html`
Expected: no output (no matches). Neither `DashboardShell.test.tsx`, `Login.test.tsx`, nor any other test file asserts on this string (there is no `DashboardShell.test.tsx` or `Login.test.tsx` in the repo at all), so no test files need updating.

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/index.html dashboard/frontend/src/pages/DashboardShell.tsx dashboard/frontend/src/pages/Login.tsx
git commit -m "chore: rename dashboard title to 404 Bot Dashboard"
```

---

### Task 3: Backend embed-spec validation accepts content-only messages

**Files:**
- Modify: `embed_builder.py:75-110` (`validate_embed_spec`)
- Test: `dashboard/backend/tests/test_embed_builder_core.py`

**Interfaces:**
- Produces: `embed_builder.is_embed_spec_empty(spec: dict) -> bool` — new function, `True` when the spec has no title/description/fields/image/thumbnail. Task 4 imports and calls this.
- Produces: `embed_builder.validate_embed_spec(spec: dict, content: str = "") -> str | None` — signature changed, `content` is new and defaults to `""` so all six existing call sites in `test_embed_builder_core.py` that call it with one argument keep passing unchanged. Task 4 calls this with the request's `content` string.

- [ ] **Step 1: Write the failing tests**

Add to the end of `dashboard/backend/tests/test_embed_builder_core.py`:

```python
def test_is_embed_spec_empty_true_for_blank_spec():
    assert embed_builder.is_embed_spec_empty({}) is True


def test_is_embed_spec_empty_false_when_title_present():
    assert embed_builder.is_embed_spec_empty({"title": "Hi"}) is False


def test_validate_embed_spec_accepts_empty_embed_with_content():
    assert embed_builder.validate_embed_spec({}, content="Just text") is None


def test_validate_embed_spec_rejects_empty_embed_and_blank_content():
    assert embed_builder.validate_embed_spec({}, content="   ") == "empty_embed"
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_embed_builder_core.py -v -k "is_embed_spec_empty or accepts_empty_embed_with_content or rejects_empty_embed_and_blank_content"`
Expected: FAIL — `AttributeError: module 'embed_builder' has no attribute 'is_embed_spec_empty'` for the first two, and `TypeError: validate_embed_spec() got an unexpected keyword argument 'content'` for the other two.

- [ ] **Step 3: Implement `is_embed_spec_empty` and update `validate_embed_spec`**

In `embed_builder.py`, replace the existing `validate_embed_spec` function (lines 75-110):

```python
def validate_embed_spec(spec: dict) -> str | None:
    title = spec.get("title") or ""
    description = spec.get("description") or ""
    author_name = (spec.get("author") or {}).get("name") or ""
    footer_text = (spec.get("footer") or {}).get("text") or ""
    image_url = (spec.get("image") or {}).get("url") or ""
    thumbnail_url = (spec.get("thumbnail") or {}).get("url") or ""
    fields = spec.get("fields") or []

    if not (title or description or fields or image_url or thumbnail_url):
        return "empty_embed"
    if len(title) > 256:
        return "title_too_long"
    if len(description) > 4096:
        return "description_too_long"
    if len(footer_text) > 2048:
        return "footer_too_long"
    if len(author_name) > 256:
        return "author_name_too_long"
    if len(fields) > 25:
        return "too_many_fields"

    total_length = len(title) + len(description) + len(footer_text) + len(author_name)
    for field in fields:
        name = field.get("name") or ""
        value = field.get("value") or ""
        if len(name) > 256:
            return "field_name_too_long"
        if len(value) > 1024:
            return "field_value_too_long"
        total_length += len(name) + len(value)

    if total_length > 6000:
        return "embed_too_large"

    return None
```

with:

```python
def is_embed_spec_empty(spec: dict) -> bool:
    title = spec.get("title") or ""
    description = spec.get("description") or ""
    image_url = (spec.get("image") or {}).get("url") or ""
    thumbnail_url = (spec.get("thumbnail") or {}).get("url") or ""
    fields = spec.get("fields") or []
    return not (title or description or fields or image_url or thumbnail_url)


def validate_embed_spec(spec: dict, content: str = "") -> str | None:
    title = spec.get("title") or ""
    description = spec.get("description") or ""
    author_name = (spec.get("author") or {}).get("name") or ""
    footer_text = (spec.get("footer") or {}).get("text") or ""
    fields = spec.get("fields") or []

    if is_embed_spec_empty(spec) and not content.strip():
        return "empty_embed"
    if len(title) > 256:
        return "title_too_long"
    if len(description) > 4096:
        return "description_too_long"
    if len(footer_text) > 2048:
        return "footer_too_long"
    if len(author_name) > 256:
        return "author_name_too_long"
    if len(fields) > 25:
        return "too_many_fields"

    total_length = len(title) + len(description) + len(footer_text) + len(author_name)
    for field in fields:
        name = field.get("name") or ""
        value = field.get("value") or ""
        if len(name) > 256:
            return "field_name_too_long"
        if len(value) > 1024:
            return "field_value_too_long"
        total_length += len(name) + len(value)

    if total_length > 6000:
        return "embed_too_large"

    return None
```

- [ ] **Step 4: Run all embed_builder core tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_embed_builder_core.py -v`
Expected: all tests PASS, including the pre-existing `test_validate_embed_spec_rejects_empty` (which calls `validate_embed_spec({})` with no `content` argument).

- [ ] **Step 5: Commit**

```bash
git add embed_builder.py dashboard/backend/tests/test_embed_builder_core.py
git commit -m "feat: allow embed spec validation to pass with content-only messages"
```

---

### Task 4: Backend routes send plain-text messages when the embed is empty

**Files:**
- Modify: `dashboard/backend/routes/embed_builder.py:54-97` (`create_embed_message`), `:132-183` (`update_embed_message`)
- Test: `dashboard/backend/tests/test_embed_builder_routes.py`

**Interfaces:**
- Consumes: `embed_builder.is_embed_spec_empty(spec: dict) -> bool` and `embed_builder.validate_embed_spec(spec: dict, content: str = "") -> str | None` from Task 3.

- [ ] **Step 1: Write the failing tests**

Add to the end of `dashboard/backend/tests/test_embed_builder_routes.py`:

```python
@pytest.mark.asyncio
async def test_create_embed_message_allows_content_only(aiohttp_client):
    channel = FakeChannel(500, next_message_id=999)
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages",
        json={"channel_id": "500", "content": "Just text", "embed": {}, "role_ids": []},
    )
    assert resp.status == 201
    assert channel.send_calls[0]["content"] == "Just text"
    assert channel.send_calls[0]["embed"] is None


@pytest.mark.asyncio
async def test_create_embed_message_rejects_blank_content_and_empty_embed(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages", json={"channel_id": "500", "content": "   ", "embed": {}, "role_ids": []}
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "empty_embed"


@pytest.mark.asyncio
async def test_update_embed_message_allows_content_only(aiohttp_client):
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/embed-messages/500/999",
        json={"content": "Just text", "embed": {}, "role_ids": []},
    )
    assert resp.status == 200
    assert message.edit_calls[0]["content"] == "Just text"
    assert message.edit_calls[0]["embed"] is None
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_embed_builder_routes.py -v -k "content_only or rejects_blank_content_and_empty_embed"`
Expected: FAIL — `test_create_embed_message_allows_content_only` and `test_update_embed_message_allows_content_only` fail because the current code always calls `embed_builder.build_embed(spec)`, so `channel.send_calls[0]["embed"]`/`message.edit_calls[0]["embed"]` is a real (empty) `discord.Embed`, not `None`. `test_create_embed_message_rejects_blank_content_and_empty_embed` fails with a 201 instead of 400, since `validate_embed_spec` is not yet called with `content`.

- [ ] **Step 3: Update `create_embed_message` to validate and send with content-only support**

In `dashboard/backend/routes/embed_builder.py`, replace `create_embed_message` (lines 54-97):

```python
@routes.post("/api/embed-messages")
@require_dashboard_access
async def create_embed_message(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    body, error = await _parse_body(request)
    if error:
        return error

    try:
        channel_id = int(body.get("channel_id"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)

    spec = body.get("embed") or {}
    content = body.get("content") or ""
    error_code = embed_builder.validate_embed_spec(spec, content)
    if error_code:
        return web.json_response({"error": error_code}, status=400)

    role_ids, error = _validate_role_ids_structure(body.get("role_ids") or [])
    if error:
        return error

    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    error = _validate_role_ids_assignable(role_ids, guild)
    if error:
        return error

    embed = None if embed_builder.is_embed_spec_empty(spec) else embed_builder.build_embed(spec)
    view = embed_builder.build_role_button_view(guild, role_ids) if role_ids else None

    try:
        message = await channel.send(content=content or None, embed=embed, view=view)
    except discord.HTTPException as exc:
        logger.warning("Failed to send embed message to channel %s: %s", channel_id, exc)
        return web.json_response({"error": "discord_error"}, status=502)

    return web.json_response({"message_id": str(message.id), "channel_id": str(channel_id)}, status=201)
```

- [ ] **Step 4: Update `update_embed_message` the same way**

In `dashboard/backend/routes/embed_builder.py`, replace `update_embed_message` (lines 132-183):

```python
@routes.put("/api/embed-messages/{channel_id}/{message_id}")
@require_dashboard_access
async def update_embed_message(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        channel_id = int(request.match_info["channel_id"])
        message_id = int(request.match_info["message_id"])
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    body, error = await _parse_body(request)
    if error:
        return error

    spec = body.get("embed") or {}
    content = body.get("content") or ""
    error_code = embed_builder.validate_embed_spec(spec, content)
    if error_code:
        return web.json_response({"error": error_code}, status=400)

    role_ids, error = _validate_role_ids_structure(body.get("role_ids") or [])
    if error:
        return error

    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    try:
        message = await channel.fetch_message(message_id)
    except discord.NotFound:
        return web.json_response({"error": "message_not_found"}, status=404)
    except discord.HTTPException:
        return web.json_response({"error": "discord_error"}, status=502)

    error = _validate_role_ids_assignable(role_ids, guild)
    if error:
        return error

    embed = None if embed_builder.is_embed_spec_empty(spec) else embed_builder.build_embed(spec)
    view = embed_builder.build_role_button_view(guild, role_ids) if role_ids else None

    try:
        await message.edit(content=content or None, embed=embed, view=view)
    except discord.HTTPException as exc:
        logger.warning("Failed to edit embed message %s in channel %s: %s", message_id, channel_id, exc)
        return web.json_response({"error": "discord_error"}, status=502)

    return web.json_response({"message_id": str(message_id), "channel_id": str(channel_id)})
```

- [ ] **Step 5: Run all embed_builder route tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_embed_builder_routes.py -v`
Expected: all tests PASS, including the pre-existing `test_create_embed_message_rejects_empty_embed`, `test_create_embed_message_success` (which asserts `channel.send_calls[0]["embed"].title == "Title"` — still a real embed since the spec has a title), and `test_update_embed_message_success`.

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/embed_builder.py dashboard/backend/tests/test_embed_builder_routes.py
git commit -m "feat: send plain-text messages when the embed builder spec is empty"
```

---

### Task 5: Frontend embed builder form allows content-only submission

**Files:**
- Modify: `dashboard/frontend/src/pages/EmbedBuilder.tsx:29-50` (`validateEmbedSpec`), `:124` (call site in `handleSave`)
- Test: `dashboard/frontend/src/pages/EmbedBuilder.test.tsx`

**Interfaces:**
- Produces: `validateEmbedSpec(spec: EmbedSpec, content: string): string | null` — signature changed from `validateEmbedSpec(spec: EmbedSpec)`. This is a module-private function (not exported), so the only caller to update is `handleSave` in the same file.

- [ ] **Step 1: Write the failing tests**

Add to the end of the `describe('EmbedBuilderPage', ...)` block in `dashboard/frontend/src/pages/EmbedBuilder.test.tsx` (before the closing `})`):

```tsx
  it('allows saving content-only messages without any embed field', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi
      .spyOn(client, 'createEmbedMessage')
      .mockResolvedValue({ message_id: '999', channel_id: '500' })

    render(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })
    fireEvent.change(screen.getByLabelText('Текст сообщения'), { target: { value: 'Just text' } })
    fireEvent.click(screen.getByText('Отправить'))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith('500', expect.objectContaining({ content: 'Just text' })),
    )
  })

  it('rejects blank content and a blank embed together', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createEmbedMessage')

    render(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })
    fireEvent.change(screen.getByLabelText('Текст сообщения'), { target: { value: '   ' } })
    fireEvent.click(screen.getByText('Отправить'))

    expect(await screen.findByText(/Заполните хотя бы/)).toBeInTheDocument()
    expect(createSpy).not.toHaveBeenCalled()
  })
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `npx vitest run src/pages/EmbedBuilder.test.tsx -t "content-only|blank content"` (from `dashboard/frontend`)
Expected: FAIL — both new tests fail because `validateEmbedSpec` still requires an embed field regardless of `content`, so submitting content-only shows the `empty_embed` validation message and never calls `createEmbedMessage`.

- [ ] **Step 3: Update `validateEmbedSpec` and its call site**

In `dashboard/frontend/src/pages/EmbedBuilder.tsx`, replace `validateEmbedSpec` (lines 29-50):

```tsx
function validateEmbedSpec(spec: EmbedSpec): string | null {
  if (!(spec.title || spec.description || spec.fields.length > 0 || spec.image.url || spec.thumbnail.url)) {
    return 'Заполните хотя бы title, description, поле или изображение'
  }
  if (spec.title.length > 256) return 'Title длиннее 256 символов'
  if (spec.description.length > 4096) return 'Description длиннее 4096 символов'
  if (spec.footer.text.length > 2048) return 'Текст footer длиннее 2048 символов'
  if (spec.author.name.length > 256) return 'Имя author длиннее 256 символов'
  if (spec.fields.length > 25) return 'Не больше 25 полей'
  for (const field of spec.fields) {
    if (field.name.length > 256) return 'Название поля длиннее 256 символов'
    if (field.value.length > 1024) return 'Значение поля длиннее 1024 символов'
  }
  const totalLength =
    spec.title.length +
    spec.description.length +
    spec.footer.text.length +
    spec.author.name.length +
    spec.fields.reduce((sum, field) => sum + field.name.length + field.value.length, 0)
  if (totalLength > 6000) return 'Суммарная длина текста эмбеда превышает 6000 символов'
  return null
}
```

with:

```tsx
function validateEmbedSpec(spec: EmbedSpec, content: string): string | null {
  const hasEmbedContent = Boolean(
    spec.title || spec.description || spec.fields.length > 0 || spec.image.url || spec.thumbnail.url,
  )
  if (!hasEmbedContent && !content.trim()) {
    return 'Заполните хотя бы текст сообщения, title, description, поле или изображение'
  }
  if (spec.title.length > 256) return 'Title длиннее 256 символов'
  if (spec.description.length > 4096) return 'Description длиннее 4096 символов'
  if (spec.footer.text.length > 2048) return 'Текст footer длиннее 2048 символов'
  if (spec.author.name.length > 256) return 'Имя author длиннее 256 символов'
  if (spec.fields.length > 25) return 'Не больше 25 полей'
  for (const field of spec.fields) {
    if (field.name.length > 256) return 'Название поля длиннее 256 символов'
    if (field.value.length > 1024) return 'Значение поля длиннее 1024 символов'
  }
  const totalLength =
    spec.title.length +
    spec.description.length +
    spec.footer.text.length +
    spec.author.name.length +
    spec.fields.reduce((sum, field) => sum + field.name.length + field.value.length, 0)
  if (totalLength > 6000) return 'Суммарная длина текста эмбеда превышает 6000 символов'
  return null
}
```

Then in the same file, update the call site in `handleSave` (line 124):

```tsx
    const validationError = validateEmbedSpec(embed)
```

to:

```tsx
    const validationError = validateEmbedSpec(embed, content)
```

- [ ] **Step 4: Run all EmbedBuilder frontend tests to verify they pass**

Run: `npx vitest run src/pages/EmbedBuilder.test.tsx` (from `dashboard/frontend`)
Expected: all tests PASS, including the pre-existing `rejects an empty embed before calling the API` test (its assertion `expect(await screen.findByText(/Заполните хотя бы/)).toBeInTheDocument()` still matches, since the new message text starts with the same prefix).

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/pages/EmbedBuilder.tsx dashboard/frontend/src/pages/EmbedBuilder.test.tsx
git commit -m "feat: allow the embed builder form to submit content-only messages"
```

---

## Final Verification

After all five tasks are complete:

- [ ] Run the full backend suite: `pytest` (from the repo root) — all tests pass.
- [ ] Run the full frontend suite: `npx vitest run` (from `dashboard/frontend`) — all tests pass.
- [ ] Manually verify in the browser (dev servers restarted): scrollbar styling across at least two different pages, the renamed title on both the login screen and the dashboard header/tab, and sending a real content-only message from the embed builder to a real Discord channel.
