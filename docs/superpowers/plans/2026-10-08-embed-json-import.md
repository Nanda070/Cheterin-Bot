# Embed Builder JSON Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Paste Discohook-style JSON (or a library of wrapped messages) on the Embeds tab and get a multi-embed message in the form, preview and Discord, with placeholder inputs, JSON export and bulk save to templates.

**Architecture:** `embeds: EmbedSpec[]` becomes first-class through the embed-builder stack (page state → API → `bot/core/embed_builder.py` → `components_v2`), with the legacy single `embed` still accepted and returned. JSON parsing/export and placeholder substitution are pure frontend modules; the backend never sees placeholders or raw JSON.

**Tech Stack:** Python 3 / aiohttp / discord.py 2.6+ / pytest (`asyncio_mode = auto`); React + TypeScript + Vite / vitest / oxlint.

**Spec:** `docs/superpowers/specs/2026-10-08-embed-json-import-design.md`

## Global Constraints

- Max 10 embeds per message (`MAX_EMBEDS = 10`); 6000 characters total across **all** embeds of one message.
- Legacy `embed` (single object) keeps working on every route, request and response.
- `MAX_TEMPLATES = 200`; bulk request carries 1–200 templates; template name ≤ 60 characters.
- Components V2 limits: 40 components, 4000 characters of TextDisplay text per message → `v2_too_large`.
- Placeholder pattern: `\{([A-Za-z_][A-Za-z0-9_]*)\}`; templates and JSON export keep raw `{…}` text.
- Other embed surfaces (welcome, feedback, events) and every existing `components_v2.send_message(embed=…)` caller must behave exactly as before.
- All new UI strings go to both `dashboard/frontend/src/i18n/ru/community.ts` and `…/en/community.ts`; new `apiError.*` strings to both `common.ts`.
- Commit messages: English, imperative sentence ending with a period (repo style), plus the `Co-Authored-By` trailer.
- Commands: backend `python -m pytest <path> -q` from repo root; frontend `npm test`, `npm run build`, `npm run lint` from `dashboard/frontend`.

## Review Focus

1. Pasted text is wrapped in a ```` ```json ```` code fence or starts with a BOM → parses as if clean. (Task 5)
2. JSON scalars of the wrong type — `"value": 100`, `"inline": "true"`, `"color": -5` / `16777216` / `1.5` → numbers become strings, `inline` only true for boolean `true`, out-of-range colour becomes no colour. (Task 5)
3. `embeds` array containing `null` / strings / numbers → those entries are skipped, the rest import. (Task 5 frontend, Task 1 backend returns `invalid_request`)
4. Editing an existing V1 message down to zero embeds → the old embeds are removed from the Discord message, not left behind. (Task 3)
5. Loading a 1-embed message while "Embed 4" is the active tab → active tab resets to the first embed instead of rendering an undefined spec. (Task 7)

---

### Task 1: Backend core — embed lists

**Files:**
- Modify: `bot/core/embed_builder.py`
- Test: `dashboard/backend/tests/test_embed_builder_core.py`

**Interfaces:**
- Produces:
  - `MAX_EMBEDS = 10`
  - `specs_from_body(body: dict) -> list[dict] | None` — reads `body["embeds"]` when the key is present and not `None`, else `[body.get("embed") or {}]`. Returns `None` when `embeds` is not a list or any entry is not a dict. Empty specs (`is_embed_spec_empty`) are dropped.
  - `validate_embed_specs(specs: list[dict], content: str = "") -> str | None` — error codes: `empty_embed` (no specs and blank content), `too_many_embeds`, the existing per-embed codes, `embed_too_large` when the summed text of all specs exceeds 6000.
  - `message_to_editor_payload(message)` adds `"embeds": list[dict]` (all embeds, at most 10; `[spec]` when there is one or none) next to the existing `"embed"` (first).
- `validate_embed_spec(spec, content)` keeps its signature and behaviour (welcome/feedback routes use it).

- [ ] **Step 1: Write failing tests**

```python
def test_specs_from_body_prefers_embeds_and_drops_empty():
    body = {"embeds": [{"title": "A"}, {}, {"description": "B"}], "embed": {"title": "legacy"}}
    assert [s.get("title") or s.get("description") for s in embed_builder.specs_from_body(body)] == ["A", "B"]

def test_specs_from_body_falls_back_to_legacy_embed():
    assert embed_builder.specs_from_body({"embed": {"title": "T"}}) == [{"title": "T"}]
    assert embed_builder.specs_from_body({}) == []
    assert embed_builder.specs_from_body({"embeds": None, "embed": {"title": "T"}}) == [{"title": "T"}]

def test_specs_from_body_rejects_bad_shapes():
    assert embed_builder.specs_from_body({"embeds": "nope"}) is None
    assert embed_builder.specs_from_body({"embeds": [{"title": "A"}, None]}) is None

def test_validate_embed_specs_limits():
    one = {"title": "T"}
    assert embed_builder.validate_embed_specs([one] * 10) is None
    assert embed_builder.validate_embed_specs([one] * 11) == "too_many_embeds"
    assert embed_builder.validate_embed_specs([], "") == "empty_embed"
    assert embed_builder.validate_embed_specs([], "text") is None
    assert embed_builder.validate_embed_specs([one, {"title": "x" * 257}]) == "title_too_long"
    big = {"description": "x" * 3001}
    assert embed_builder.validate_embed_specs([big, big]) == "embed_too_large"

def test_message_to_editor_payload_returns_all_embeds():
    embeds = [embed_builder.build_embed({"title": f"E{i}"}) for i in range(3)]
    payload = embed_builder.message_to_editor_payload(FakeMessage(1, embeds=embeds, content="hi"))
    assert [e["title"] for e in payload["embeds"]] == ["E0", "E1", "E2"]
    assert payload["embed"]["title"] == "E0"
```

- [ ] **Step 2:** Run `python -m pytest dashboard/backend/tests/test_embed_builder_core.py -q` — new tests FAIL (attribute errors / KeyError `embeds`).
- [ ] **Step 3:** Implement the three items in `bot/core/embed_builder.py`. Share the per-embed limit checks between `validate_embed_spec` and `validate_embed_specs` instead of duplicating them.
- [ ] **Step 4:** Run the same file — all PASS.
- [ ] **Step 5:** Commit: `Add multi-embed spec parsing and validation to embed builder core.`

### Task 2: Components V2 — one container per embed

**Files:**
- Modify: `bot/core/components_v2.py`, `bot/core/embed_builder.py` (V2 read-back)
- Test: `dashboard/backend/tests/test_components_v2.py`, `dashboard/backend/tests/test_embed_builder_core.py`

**Interfaces:**
- Produces:
  - `build_layout_view(*, embed=None, embeds: list[discord.Embed] | None = None, content=None, source_view=None, keep_callbacks=False, timeout=None, image_files=None)` — `embeds` wins when not `None`; otherwise `[embed]` if given. One `Container` per embed with its own accent colour; `content` text blocks go first in the first container; action rows go in the last container. Zero embeds → the current single container.
  - `class LayoutTooLargeError(ValueError)`; `layout_limit_error(layout) -> str | None` returning `"v2_too_large"` when the layout holds more than 40 components (counting nested ones, `layout.walk_children()`) or more than 4000 characters of `TextDisplay` content.
  - `send_message(..., embeds: list[discord.Embed] | None = None, enforce_limits: bool = False)` and `edit_message(..., embeds=discord.utils.MISSING, enforce_limits: bool = False)`. V1: when `embeds` is supplied it is forwarded as the `embeds=` kwarg and `embed=` is omitted (so `embeds=[]` on edit clears old embeds). V2: passed to `build_layout_view`; with `enforce_limits=True` a too-large layout raises `LayoutTooLargeError` before any Discord call.
  - `embed_builder.v2_message_to_specs(message) -> tuple[list[dict], str, bool]` — with two or more top-level Containers, one spec per Container (empty ones dropped) and leftover content from the first; otherwise `[spec]` from the existing `v2_message_to_spec`. `message_to_editor_payload` uses it for V2 messages.
- Callers that pass neither `embeds` nor `enforce_limits` get byte-for-byte the old behaviour.

- [ ] **Step 1: Write failing tests**

```python
def _containers(layout):
    return [c for c in layout.children if isinstance(c, discord.ui.Container)]

def test_build_layout_view_makes_one_container_per_embed():
    embeds = [discord.Embed(title="A", colour=0x111111), discord.Embed(title="B", colour=0x222222)]
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="R", custom_id="btn_role_7"))
    layout = components_v2.build_layout_view(embeds=embeds, content="hello", source_view=view)
    first, last = _containers(layout)
    assert [int(c.accent_colour.value) for c in (first, last)] == [0x111111, 0x222222]
    assert first.children[0].content == "hello"
    assert not any(isinstance(i, discord.ui.ActionRow) for i in first.children)
    assert any(isinstance(i, discord.ui.ActionRow) for i in last.children)

def test_layout_limit_error_flags_text_over_4000():
    embeds = [discord.Embed(description="x" * 2100), discord.Embed(description="y" * 2100)]
    assert components_v2.layout_limit_error(components_v2.build_layout_view(embeds=embeds)) == "v2_too_large"
    assert components_v2.layout_limit_error(components_v2.build_layout_view(embed=discord.Embed(title="ok"))) is None

async def test_send_message_v1_forwards_embeds_list():
    channel = FakeChannel(1)
    embeds = [discord.Embed(title="A"), discord.Embed(title="B")]
    await components_v2.send_message(channel, version="v1", embeds=embeds)
    assert channel.send_calls[0]["embeds"] == embeds and "embed" not in channel.send_calls[0]

async def test_send_message_v2_enforce_limits_raises_before_send():
    channel = FakeChannel(1)
    embeds = [discord.Embed(description="x" * 2100), discord.Embed(description="y" * 2100)]
    with pytest.raises(components_v2.LayoutTooLargeError):
        await components_v2.send_message(channel, version="v2", embeds=embeds, enforce_limits=True)
    assert channel.send_calls == []
```

In `test_embed_builder_core.py`: build a layout from two embeds (`A`/`B`) with `build_layout_view`, wrap it in a `FakeMessage(..., components=layout.children, components_v2=True)`, and assert `v2_message_to_specs` returns two specs titled `A` and `B`.

- [ ] **Step 2:** Run both test files — new tests FAIL.
- [ ] **Step 3:** Implement. `dashboard/backend/tests/fakes.py`: `FakeChannel.send` / `FakeThread.send` must record `embeds=` from kwargs on the created `FakeMessage` (they only read `embed` today).
- [ ] **Step 4:** Run `python -m pytest dashboard/backend/tests -q -k "components_v2 or embed_builder or fakes"` — PASS.
- [ ] **Step 5:** Commit: `Render and read back multiple embeds as Components V2 containers.`

### Task 3: Message routes

**Files:**
- Modify: `dashboard/backend/routes/embed_builder.py`
- Test: `dashboard/backend/tests/test_embed_builder_routes.py`

**Interfaces:**
- Consumes: `specs_from_body`, `validate_embed_specs`, `send_message(embeds=, enforce_limits=True)`, `edit_message(embeds=, enforce_limits=True)`, `LayoutTooLargeError`.
- Produces: `POST /api/embed-messages` and `PUT /api/embed-messages/{c}/{m}` accept `embeds` or legacy `embed`; `specs_from_body` → `None` gives 400 `invalid_request`; `LayoutTooLargeError` gives 400 `v2_too_large`. Both always call Discord with `embeds=[…]` (a possibly empty list). `GET` returns `embeds` + `embed`; its exception fallback payload also carries `"embeds": []`.

- [ ] **Step 1: Write failing tests** (reuse the file's `build()` helper)

```python
async def test_create_embed_message_with_two_embeds(aiohttp_client):
    channel = FakeChannel(500, next_message_id=999)
    _, app = build(channels=[channel])
    client = await aiohttp_client(app); await force_login(client, 10)
    resp = await client.post("/api/embed-messages", json={
        "channel_id": "500", "embeds": [{"title": "A"}, {}, {"title": "B"}], "role_ids": []})
    assert resp.status == 201
    assert [e.title for e in channel.send_calls[0]["embeds"]] == ["A", "B"]

async def test_create_embed_message_rejects_eleven_embeds(aiohttp_client):   # → 400 too_many_embeds
async def test_create_embed_message_rejects_non_object_embed(aiohttp_client): # "embeds": [{"title": "A"}, None] → 400 invalid_request
async def test_create_embed_message_v2_too_large(aiohttp_client):
    # components_version "v2", two embeds with 2100-char descriptions → 400 v2_too_large, channel.send_calls == []
async def test_update_embed_message_with_no_embeds_clears_existing(aiohttp_client):
    # message has one embed; PUT {"content": "only text", "embeds": []} → 200 and message.embeds == []
async def test_get_embed_message_returns_all_embeds(aiohttp_client):
    # message with 2 embeds → body["embeds"] has 2 titles, body["embed"]["title"] is the first
```

- [ ] **Step 2:** Run the file — new tests FAIL.
- [ ] **Step 3:** Implement. Existing assertions on `send_calls[0]["embed"]` in this file change to `send_calls[0]["embeds"][0]`.
- [ ] **Step 4:** Run the file — all PASS.
- [ ] **Step 5:** Commit: `Accept and return embed lists on embed message routes.`

### Task 4: Templates — embed lists and bulk save

**Files:**
- Modify: `bot/core/embed_builder.py`, `dashboard/backend/routes/embed_builder.py`
- Test: `dashboard/backend/tests/test_embed_builder_core.py`, `dashboard/backend/tests/test_embed_builder_routes.py`

**Interfaces:**
- Produces:
  - `MAX_TEMPLATES = 200`, `MAX_BULK_TEMPLATES = 200`.
  - `save_template(guild_id, name, content, embed_specs: list[dict], role_ids)` stores `"embeds"`; `list_templates` returns each template with `embeds` (stored `embeds`, else `[embed]`, else `[]`) **and** `embed` (first or `{}`). `save_template` returns the same shape.
  - `save_templates_bulk(guild_id: int, items: list[dict]) -> dict` → `{"created": [template…], "skipped": [{"name": str, "reason": str}…]}`. Per item, in order: name is stripped and truncated to 60 chars; blank → `invalid_name`; `specs_from_body(item)` is `None` → `invalid_request`; `validate_embed_specs` error → that code; name already stored or already created in this call → `duplicate_name`; limit reached → `too_many_templates`. One `settings_db.put` for the whole call. Bulk templates get `role_ids: []`.
  - `POST /api/embed-templates/bulk`, body `{"templates": [...]}`; not a list, empty, or longer than 200 → 400 `invalid_request`; otherwise 200 with the dict above.
  - `POST /api/embed-templates` accepts `embeds` or `embed`.

- [ ] **Step 1: Write failing tests**

```python
def test_list_templates_reads_legacy_single_embed():
    settings_db.put(1, "embed_templates", {"seq": 1, "templates": [
        {"id": "1", "name": "Old", "content": "", "embed": {"title": "T"}, "role_ids": []}]})
    (template,) = embed_builder.list_templates(1)
    assert template["embeds"] == [{"title": "T"}] and template["embed"] == {"title": "T"}

def test_save_template_stores_embed_list():
    saved = embed_builder.save_template(1, "Multi", "", [{"title": "A"}, {"title": "B"}], [])
    assert [e["title"] for e in saved["embeds"]] == ["A", "B"]

def test_save_templates_bulk_creates_and_skips():
    embed_builder.save_template(1, "Taken", "", [{"title": "T"}], [])
    result = embed_builder.save_templates_bulk(1, [
        {"name": "One", "content": "c", "embeds": [{"title": "A"}]},
        {"name": "Taken", "embeds": [{"title": "A"}]},
        {"name": "One", "embeds": [{"title": "A"}]},
        {"name": "  ", "embeds": [{"title": "A"}]},
        {"name": "Empty", "embeds": []},
        {"name": "x" * 80, "embeds": [{"title": "A"}]},
    ])
    assert [t["name"] for t in result["created"]] == ["One", "x" * 60]
    assert [s["reason"] for s in result["skipped"]] == ["duplicate_name", "duplicate_name", "invalid_name", "empty_embed"]
    assert len(embed_builder.list_templates(1)) == 3

def test_save_templates_bulk_stops_at_limit(monkeypatch):
    monkeypatch.setattr(embed_builder, "MAX_TEMPLATES", 2)
    result = embed_builder.save_templates_bulk(1, [{"name": f"N{i}", "embeds": [{"title": "A"}]} for i in range(3)])
    assert len(result["created"]) == 2 and result["skipped"] == [{"name": "N2", "reason": "too_many_templates"}]
```

Routes: bulk happy path (200, `created` length 2); `{"templates": []}` and `{"templates": "x"}` → 400 `invalid_request`; `POST /api/embed-templates` with `embeds` of two specs returns both.

- [ ] **Step 2:** Run both files — new tests FAIL. Existing `save_template(…, {"title": "T"}, …)` calls in tests are updated to pass a list.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run `python -m pytest dashboard/backend/tests -q` — whole backend suite PASS.
- [ ] **Step 5:** Commit: `Store embed lists in templates and add bulk template save.`

### Task 5: Frontend — message JSON parser and exporter

**Files:**
- Create: `dashboard/frontend/src/utils/messageJson.ts`, `dashboard/frontend/src/utils/messageJson.test.ts`

**Interfaces:**
- Consumes: `EmbedSpec` from `../api/client`, `EMPTY_EMBED_SPEC` from `./embedUtils`.
- Produces (exact shapes from the spec's "Формат JSON" section):

```ts
export interface JsonNotice { key: string; params?: Record<string, string | number> }
export interface ImportedMessage { name: string; group: string; content: string; embeds: EmbedSpec[] }
export type ParseResult =
  | { ok: true; messages: ImportedMessage[]; warnings: JsonNotice[] }
  | { ok: false; error: JsonNotice }
export function parseMessageJson(text: string): ParseResult
export function exportMessageJson(content: string, embeds: EmbedSpec[]): string
```

- Notice keys: errors `embedBuilder.json.error.syntax` (`{detail}`), `…error.shape`, `…error.noMessages`; warnings `embedBuilder.json.warn.ignoredKeys` (`{keys}` comma-joined, one notice for the whole parse, keys de-duplicated), `…warn.tooManyEmbeds` (`{name}`), `…warn.skippedItems` (`{count}`).
- `name` is `''` when no source field exists; the UI supplies the "Сообщение N" fallback.
- Empty embeds are dropped from `ImportedMessage.embeds`; a message with no content and no embeds counts as unrecognised.

- [ ] **Step 1: Write failing tests** covering, each as its own `it`:
  - Discohook message `{content:"hi", embeds:[{title:"A", color:5814783},{title:"B"}]}` → 1 message, colours `['#58b9ff', '']`.
  - Backup `{messages:[{data:{content:"a"}},{data:{embeds:[{title:"T"}]}}]}` → 2 messages.
  - Wrapper `{category:"oneball", score:1, event:"Brawlhalla", embed:{plainText:"<@&1>", author:{name:"Brawlhalla"}, description:"d", color:3092790, fields:[{name:"Ведущий", value:"{Eventer}", inline:true}]}}` → `name:'Brawlhalla'`, `group:'oneball'`, `content:'<@&1>'`, colour `'#2f3136'`, one inline field, **no warnings**.
  - Array of two such wrappers → 2 messages; array of 3 bare embeds → 1 message with 3 embeds; array of 11 bare embeds → 11 messages; bare embed with `plainText` → content set.
  - `{embeds:[…12 items]}` → 10 embeds + `warn.tooManyEmbeds`.
  - `{content:"x", username:"u", avatar_url:"a", components:[{}], attachments:[]}` → one `warn.ignoredKeys` with `keys: 'username, avatar_url, components'`.
  - Review Focus: input wrapped in ```` ```json … ``` ```` and input prefixed with `﻿` parse; `{embeds:[null,"x",{title:"A"}]}` → one embed; field `{name:1, value:100, inline:"true"}` → `{name:'1', value:'100', inline:false}`; colours `-5`, `16777216`, `1.5`, `"red"` → `''`; `"2f3136"` and `"#2F3136"` → `'#2f3136'`.
  - Errors: `'{oops'` → `error.syntax`; `'42'` → `error.shape`; `'[{"foo":1}]'` → `error.noMessages`.
  - Export: `exportMessageJson('hi', [spec])` parses to `{content:'hi', embeds:[{title:'T', color:3092790, fields:[…]}], attachments:[]}` with no empty-string keys; empty content → `content: null`; no embeds → `embeds: null`; `parseMessageJson(exportMessageJson(c, e))` round-trips content and embeds.
- [ ] **Step 2:** Run `npm test -- messageJson` — FAIL (module missing).
- [ ] **Step 3:** Implement per the spec's recognition order (messages → embeds/content → `embed` wrapper → bare embed).
- [ ] **Step 4:** Run `npm test -- messageJson` — PASS.
- [ ] **Step 5:** Commit: `Add Discohook-style message JSON parser and exporter.`

### Task 6: Frontend — placeholders, list validation, API client

**Files:**
- Create: `dashboard/frontend/src/utils/placeholders.ts`, `dashboard/frontend/src/utils/placeholders.test.ts`
- Modify: `dashboard/frontend/src/utils/embedUtils.ts`, `dashboard/frontend/src/utils/embedUtils.test.ts`, `dashboard/frontend/src/api/client.ts`, `dashboard/frontend/src/api/errors.ts`, `dashboard/frontend/src/i18n/{ru,en}/common.ts`

**Interfaces:**
- Produces:

```ts
// placeholders.ts
export function findPlaceholders(content: string, embeds: EmbedSpec[]): string[]
export function applyPlaceholders(content: string, embeds: EmbedSpec[], values: Record<string, string>):
  { content: string; embeds: EmbedSpec[] }
// embedUtils.ts
export const MAX_EMBEDS = 10
export function isEmbedSpecEmpty(spec: EmbedSpec): boolean
export function embedsFromPayload(raw: { embeds?: unknown; embed?: unknown }): EmbedSpec[]  // normalised, never empty: falls back to [EMPTY_EMBED_SPEC]
export function validateEmbedSpecs(specs: EmbedSpec[], content: string): string | null      // i18n key or null
// client.ts
export interface EmbedMessagePayload { content: string; embeds: EmbedSpec[]; embed?: EmbedSpec; role_ids: string[]; components_version?: 'v1' | 'v2' }
export interface EmbedTemplate { id: string; name: string; content: string; embeds: EmbedSpec[]; embed?: EmbedSpec; role_ids: string[] }
export function saveEmbedTemplate(input: { name: string; content: string; embeds: EmbedSpec[]; role_ids: string[] }): Promise<EmbedTemplate>
export function saveEmbedTemplatesBulk(templates: { name: string; content: string; embeds: EmbedSpec[] }[]):
  Promise<{ created: EmbedTemplate[]; skipped: { name: string; reason: string }[] }>
```

- `findPlaceholders`: unique names in order of first appearance, scanning content then each embed's title, description, url, author.*, footer.*, image.url, thumbnail.url, field names and values.
- `applyPlaceholders`: single pass (a substituted value containing `{Other}` is not expanded again); empty or missing value leaves `{Name}` intact; returns new objects.
- `validateEmbedSpecs`: ignores empty specs; `embedBuilder.error.validation.embedsCount` for more than 10; existing per-embed keys; `…validation.totalLength` for more than 6000 across all; `…validation.empty` when nothing at all.
- `errors.ts`: map `too_many_embeds`, `v2_too_large`. Copy — RU: «Не больше 10 эмбедов в одном сообщении» / «Сообщение не помещается в Components V2 (макс. 40 компонентов и 4000 символов) — сократите текст или переключитесь на V1»; EN: "No more than 10 embeds per message" / "Message does not fit Components V2 (max 40 components and 4000 characters) — shorten it or switch to V1".

- [ ] **Step 1: Write failing tests**

```ts
it('finds placeholders across fields in first-seen order', () => {
  const e = normalizeEmbedSpec({ description: '[{DateNow}](x) [go]({Channel})', fields: [{ name: 'Ведущий', value: '{Eventer}' }, { name: 'x', value: '{DateNow}' }] })
  expect(findPlaceholders('<@&742> <:1Primogem:772> {Channel}', [e])).toEqual(['Channel', 'DateNow', 'Eventer'])
})
it('applies values in one pass and keeps unfilled names', () => {
  const e = normalizeEmbedSpec({ title: '{A} {B} {C}' })
  const out = applyPlaceholders('{A}', [e], { A: '{B}', B: 'b', C: '' })
  expect(out.content).toBe('{B}')
  expect(out.embeds[0].title).toBe('{B} b {C}')
  expect(e.title).toBe('{A} {B} {C}')
})
it('ignores non-identifier braces', () => {
  expect(findPlaceholders('{} {1a} { x } {ok_1}', [])).toEqual(['ok_1'])
})
// embedUtils.test.ts
it('validates the list as a whole', () => {
  const one = normalizeEmbedSpec({ title: 'T' })
  expect(validateEmbedSpecs(Array(10).fill(one), '')).toBeNull()
  expect(validateEmbedSpecs(Array(11).fill(one), '')).toBe('embedBuilder.error.validation.embedsCount')
  const big = normalizeEmbedSpec({ description: 'x'.repeat(3001) })
  expect(validateEmbedSpecs([big, big], '')).toBe('embedBuilder.error.validation.totalLength')
  expect(validateEmbedSpecs([EMPTY_EMBED_SPEC], '')).toBe('embedBuilder.error.validation.empty')
  expect(validateEmbedSpecs([EMPTY_EMBED_SPEC], 'hi')).toBeNull()
})
it('reads embeds or the legacy embed and never returns an empty list', () => {
  expect(embedsFromPayload({ embeds: [{ title: 'A' }, { title: 'B' }] }).map((e) => e.title)).toEqual(['A', 'B'])
  expect(embedsFromPayload({ embed: { title: 'L' } })[0].title).toBe('L')
  expect(embedsFromPayload({ embeds: [] })).toHaveLength(1)
})
```

- [ ] **Step 2:** Run `npm test` — new tests FAIL.
- [ ] **Step 3:** Implement. `EmbedBuilder.tsx` will not compile against the new client types until Task 7; that is expected — only `npm test` gates this task.
- [ ] **Step 4:** Run `npm test` — PASS.
- [ ] **Step 5:** Commit: `Add placeholder substitution, embed list validation and bulk template client.`

### Task 7: Frontend — UI

**Files:**
- Create: `dashboard/frontend/src/components/EmbedFieldsForm.tsx`, `…/components/JsonImportPanel.tsx`, `…/components/PlaceholderInputs.tsx`
- Modify: `dashboard/frontend/src/pages/EmbedBuilder.tsx`, `…/components/EmbedPreview.tsx`, `…/i18n/{ru,en}/community.ts`

**Interfaces:**
- Consumes: everything Tasks 5–6 produce.
- Produces:
  - `EmbedFieldsForm({ embed: EmbedSpec; onChange: (embed: EmbedSpec) => void })` — the title…fields inputs moved verbatim out of `EmbedBuilder.tsx` (same labels, ids, placeholders).
  - `PlaceholderInputs({ names: string[]; values: Record<string, string>; onChange: (name: string, value: string) => void })` — renders nothing when `names` is empty.
  - `JsonImportPanel({ exportJson: () => string; onLoad: (message: ImportedMessage) => void; onSaveAll: (messages: ImportedMessage[]) => Promise<{ created: number; skipped: number }>; busy: boolean })` — owns the textarea text, parse result, search query and active row. Apply with one message calls `onLoad` immediately; with several shows the list (scrollable, `max-h-64`), search filters by name (case-insensitive), row shows name and group, click calls `onLoad`. "Copy JSON" writes `exportJson()` into the textarea and `navigator.clipboard` (clipboard failure is ignored). Unnamed messages display `t('embedBuilder.json.unnamed', { n })` and that same string is the template name on save-all.
  - `EmbedPreview({ content, embed?, embeds? })` — `embeds` wins; each non-empty embed rendered in a column; other pages keep passing `embed`.
- Page state changes in `EmbedBuilder.tsx`: `embeds: EmbedSpec[]` (replaces `embed`), `activeEmbed: number`, `placeholderValues: Record<string, string>`. A single `loadMessage(content, embeds)` helper sets content, embeds (via `embedsFromPayload`-style non-empty guarantee) **and resets `activeEmbed` to 0**; template apply, message load and JSON load all go through it. Removing an embed clamps `activeEmbed`. Add is disabled at `MAX_EMBEDS`; remove is disabled with one slot left.
- Send: `applyPlaceholders` → drop empty specs → `validateEmbedSpecs` → API with `embeds`. Preview shows the substituted result. Save-as-template and export use raw state. Unfilled placeholders show `embedBuilder.placeholders.unfilled` next to the send button without blocking.
- Layout order in the left column follows the spec's "Интерфейс" section.

i18n keys (RU / EN):

| Key | RU | EN |
|---|---|---|
| `embedBuilder.json.title` | JSON | JSON |
| `embedBuilder.json.hint` | Вставьте JSON из Discohook или список сообщений | Paste JSON from Discohook or a list of messages |
| `embedBuilder.json.apply` | Применить JSON | Apply JSON |
| `embedBuilder.json.copy` | Скопировать JSON | Copy JSON |
| `embedBuilder.json.copied` | JSON текущего сообщения скопирован | Current message JSON copied |
| `embedBuilder.json.loaded` | Сообщение загружено в форму | Message loaded into the form |
| `embedBuilder.json.messages` | Сообщений в JSON: {count} | Messages in JSON: {count} |
| `embedBuilder.json.search` | Поиск по названию | Search by name |
| `embedBuilder.json.unnamed` | Сообщение {n} | Message {n} |
| `embedBuilder.json.saveAll` | Сохранить все как шаблоны ({count}) | Save all as templates ({count}) |
| `embedBuilder.json.savedAll` | Шаблоны: создано {created}, пропущено {skipped} | Templates: {created} created, {skipped} skipped |
| `embedBuilder.json.error.syntax` | Некорректный JSON: {detail} | Invalid JSON: {detail} |
| `embedBuilder.json.error.shape` | JSON должен быть объектом или массивом | JSON must be an object or an array |
| `embedBuilder.json.error.noMessages` | В JSON не найдено ни одного сообщения или эмбеда | No message or embed found in the JSON |
| `embedBuilder.json.error.saveAll` | Не удалось сохранить шаблоны | Failed to save templates |
| `embedBuilder.json.warn.ignoredKeys` | Не поддерживается и пропущено: {keys} | Not supported and skipped: {keys} |
| `embedBuilder.json.warn.tooManyEmbeds` | «{name}»: больше 10 эмбедов, лишние отброшены | "{name}": more than 10 embeds, extras dropped |
| `embedBuilder.json.warn.skippedItems` | Пропущено нераспознанных элементов: {count} | Unrecognised items skipped: {count} |
| `embedBuilder.embedTab` | Эмбед {n} | Embed {n} |
| `embedBuilder.addEmbed` | + Добавить эмбед | + Add embed |
| `embedBuilder.removeEmbed` | Удалить эмбед | Remove embed |
| `embedBuilder.placeholders.title` | Подстановки | Placeholders |
| `embedBuilder.placeholders.hint` | Значения подставятся при отправке; в шаблонах остаётся {…} | Values are filled in on send; templates keep {…} |
| `embedBuilder.placeholders.unfilled` | Не заполнено: {names} | Not filled: {names} |
| `embedBuilder.error.validation.embedsCount` | Не больше 10 эмбедов в одном сообщении | No more than 10 embeds per message |

Also update `embedBuilder.error.validation.totalLength` to say «всех эмбедов» / "all embeds".

- [ ] **Step 1:** Extract `EmbedFieldsForm`, switch the page to `embeds[]` + tabs, update `EmbedPreview`. Run `npm run build` — compiles.
- [ ] **Step 2:** Add `JsonImportPanel`, `PlaceholderInputs`, wire `loadMessage`, save-all and send substitution, add i18n keys to both languages.
- [ ] **Step 3:** Run `npm test && npm run build && npm run lint` — all clean.
- [ ] **Step 4:** Commit: `Add JSON import, multi-embed tabs and placeholder inputs to the embed builder.`

### Task 8: End-to-end verification

- [ ] **Step 1:** `python -m pytest dashboard/backend/tests -q` — PASS. `npm test && npm run build && npm run lint` in `dashboard/frontend` — clean.
- [ ] **Step 2:** In a browser against the running dashboard: paste the 49-event library → list of 49 with search; pick "Brawlhalla" → form + preview filled, three placeholder inputs; fill them → preview updates. Paste a Discohook JSON with two embeds → two tabs, two preview cards. "Copy JSON" → textarea holds Discohook-shaped JSON.
- [ ] **Step 3:** Record anything that could not be exercised (e.g. real Discord send) in the hand-off message.
