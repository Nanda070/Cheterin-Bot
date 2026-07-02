# Дашборд, Фаза 3b (Конструктор эмбедов) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let staff compose a discohook-style embed message (with an optional attached row of up to 5 role-toggle buttons) and send it to a channel or edit a previously sent one, entirely through the dashboard.

**Architecture:** A new repo-root module `embed_builder.py` holds only pure functions (build/parse an embed, build/parse a role-button view) — no cog, no listener, no `setup()`. Role-button clicks continue to be handled entirely by `button.py`'s existing `on_interaction`, since the new module reuses its exact `btn_role_{role_id}` custom_id scheme. A new `dashboard/backend/routes/embed_builder.py` route table exposes create/load/edit endpoints, reusing `require_dashboard_access` and the existing `GET /api/channels`/`GET /api/roles`. The `/reaction-roles` page gains a second tab ("Эмбеды") that hosts a single-page compose form with a live Discord-style preview panel — no new route, no new sidebar entry.

**Tech Stack:** Python: discord.py, aiohttp, pytest + pytest-aiohttp (existing fakes, extended). Frontend: React + TypeScript, existing design-system primitives, Vitest + Testing Library.

## Global Constraints

- All work happens in `C:\Users\adnan\Documents\coding\ChetMain_backup_20260701_211729`. Never touch `C:\Users\adnan\Documents\coding\ChetMain`.
- Local-only git repo: commit each task with `git add <specific files>` + `git commit` — never bare `git add -A`.
- Spec of record: `docs/superpowers/specs/2026-07-02-dashboard-phase3b-embed-builder-design.md`.
- Stateless feature: no JSON config file. Creating sends a new message; editing requires the caller to supply `channel_id` + `message_id` directly (same "attach to existing ID" UX as Phase 3a's Reaction Roles), with the current content fetched and pre-filled into the form.
- One embed per message (no multi-embed). Optional plain-text `content` alongside the embed.
- Up to 5 role-toggle buttons per message (`MAX_ROLE_BUTTONS = 5`), reusing `button.py`'s exact `btn_role_{role_id}` custom_id scheme unmodified — `button.py` itself is never touched by this phase.
- Validation order is binding everywhere pairs/role_ids interact with Discord data (this is the exact bug class found and fixed in Phase 3a — do not repeat it): structural checks (embed spec shape, role_ids count) run first with zero Discord calls; channel/message existence checks run next; role-assignability (not `@everyone`, not managed, position below the bot's own top role) runs last, only after existence is confirmed.
- Discord's real embed limits, enforced server-side before any Discord API call: title ≤256 chars, description ≤4096, footer.text ≤2048, author.name ≤256, ≤25 fields, field.name ≤256/field.value ≤1024, total character budget ≤6000, and at least one of title/description/fields/image/thumbnail must be non-empty.
- Any `discord.HTTPException` from an actual send/edit call is logged via `logger.warning` before returning an error to the client (per the logging convention established in Phase 3a's final review) — never silently swallowed.
- No secrets in any committed file.
- Existing suites must stay green throughout: 130 pytest + 34 Vitest tests before this plan.

---

### Task 1: Test fakes — `FakeChannel.send`, `FakeMessage.edit`/`embeds`/`components`, `FakeComponentRow`

**Files:**
- Modify: `dashboard/backend/tests/fakes.py` (extend `FakeMessage`/`FakeChannel`, add `FakeComponentRow` — every existing call site keeps working unchanged)
- Test: `dashboard/backend/tests/test_fakes_embed_extensions.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `FakeMessage(message_id, embeds=None, components=None, content=None)` gains `.content`, `.embeds` (list), `.components` (list), `.edit_calls` (list), `.edit_raises`, and async `edit(**kwargs)` that records the call and updates `.content`/`.embeds`/`.components` from whichever of `content`/`embed`/`view` keys were passed; `FakeChannel(channel_id, name="channel", messages=None, next_message_id=1000)` gains `.send_calls` (list), `.send_raises`, and async `send(**kwargs)` that records the call, creates a new `FakeMessage` with an auto-incrementing id, stores it in the channel's message map, and returns it; `class FakeComponentRow(children)` — a thin holder with a `.children` list, used to represent one action-row of buttons on a message for `parse_role_button_ids` tests in later tasks.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_fakes_embed_extensions.py`:

```python
import discord
import pytest

from dashboard.backend.tests.fakes import FakeChannel, FakeComponentRow, FakeMessage


@pytest.mark.asyncio
async def test_fake_channel_send_creates_and_stores_message():
    channel = FakeChannel(500, next_message_id=999)
    embed = discord.Embed(title="Hello")
    message = await channel.send(content="hi", embed=embed)
    assert message.id == 999
    assert message.content == "hi"
    assert message.embeds == [embed]
    assert channel.send_calls == [{"content": "hi", "embed": embed}]
    fetched = await channel.fetch_message(999)
    assert fetched is message


@pytest.mark.asyncio
async def test_fake_channel_send_raises_when_configured():
    channel = FakeChannel(500)
    channel.send_raises = discord.HTTPException.__new__(discord.HTTPException)
    with pytest.raises(discord.HTTPException):
        await channel.send(content="hi")


@pytest.mark.asyncio
async def test_fake_message_edit_updates_content_embed_and_components():
    message = FakeMessage(1)
    new_embed = discord.Embed(title="Updated")
    new_view = "some-view-marker"
    await message.edit(content="new content", embed=new_embed, view=new_view)
    assert message.content == "new content"
    assert message.embeds == [new_embed]
    assert message.components == new_view
    assert message.edit_calls == [{"content": "new content", "embed": new_embed, "view": new_view}]


@pytest.mark.asyncio
async def test_fake_message_edit_raises_when_configured():
    message = FakeMessage(1)
    message.edit_raises = discord.HTTPException.__new__(discord.HTTPException)
    with pytest.raises(discord.HTTPException):
        await message.edit(content="x")


def test_fake_message_defaults_to_empty_embeds_and_components():
    message = FakeMessage(1)
    assert message.embeds == []
    assert message.components == []
    assert message.content is None


def test_fake_component_row_holds_children():
    button = discord.ui.Button(label="test", custom_id="btn_role_7")
    row = FakeComponentRow([button])
    assert row.children == [button]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_fakes_embed_extensions.py -v`
Expected: FAIL with `ImportError: cannot import name 'FakeComponentRow'` (and `FakeChannel`/`FakeMessage` missing `send`/`edit`)

- [ ] **Step 3: Modify `dashboard/backend/tests/fakes.py`**

Replace the current `FakeMessage` class:

```python
class FakeMessage:
    def __init__(self, message_id):
        self.id = message_id
        self.reaction_calls = []
        self.add_reaction_raises = None
        self.remove_reaction_raises = None

    async def add_reaction(self, emoji):
        if self.add_reaction_raises:
            raise self.add_reaction_raises
        self.reaction_calls.append(("add", str(emoji)))

    async def remove_reaction(self, emoji, member):
        if self.remove_reaction_raises:
            raise self.remove_reaction_raises
        self.reaction_calls.append(("remove", str(emoji)))
```

with:

```python
class FakeMessage:
    def __init__(self, message_id, embeds=None, components=None, content=None):
        self.id = message_id
        self.content = content
        self.embeds = embeds or []
        self.components = components or []
        self.reaction_calls = []
        self.add_reaction_raises = None
        self.remove_reaction_raises = None
        self.edit_calls = []
        self.edit_raises = None

    async def add_reaction(self, emoji):
        if self.add_reaction_raises:
            raise self.add_reaction_raises
        self.reaction_calls.append(("add", str(emoji)))

    async def remove_reaction(self, emoji, member):
        if self.remove_reaction_raises:
            raise self.remove_reaction_raises
        self.reaction_calls.append(("remove", str(emoji)))

    async def edit(self, **kwargs):
        if self.edit_raises:
            raise self.edit_raises
        self.edit_calls.append(kwargs)
        if "content" in kwargs:
            self.content = kwargs["content"]
        if "embed" in kwargs:
            self.embeds = [kwargs["embed"]] if kwargs["embed"] else []
        if "view" in kwargs:
            self.components = kwargs["view"]


class FakeComponentRow:
    def __init__(self, children):
        self.children = children
```

Replace the current `FakeChannel` class:

```python
class FakeChannel:
    def __init__(self, channel_id, name="channel", messages=None):
        self.id = channel_id
        self.name = name
        self._messages = messages or {}

    async def fetch_message(self, message_id):
        import discord

        message = self._messages.get(message_id)
        if message is None:
            raise discord.NotFound.__new__(discord.NotFound)
        return message
```

with:

```python
class FakeChannel:
    def __init__(self, channel_id, name="channel", messages=None, next_message_id=1000):
        self.id = channel_id
        self.name = name
        self._messages = messages or {}
        self._next_message_id = next_message_id
        self.send_calls = []
        self.send_raises = None

    async def fetch_message(self, message_id):
        import discord

        message = self._messages.get(message_id)
        if message is None:
            raise discord.NotFound.__new__(discord.NotFound)
        return message

    async def send(self, **kwargs):
        if self.send_raises:
            raise self.send_raises
        self.send_calls.append(kwargs)
        message = FakeMessage(
            self._next_message_id,
            embeds=[kwargs["embed"]] if kwargs.get("embed") else [],
            components=kwargs.get("view"),
            content=kwargs.get("content"),
        )
        self._messages[message.id] = message
        self._next_message_id += 1
        return message
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_fakes_embed_extensions.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Run the full backend suite to confirm no regressions**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (130 + 6 = 136)

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/tests/fakes.py dashboard/backend/tests/test_fakes_embed_extensions.py
git commit -m "test: extend fakes with FakeChannel.send/FakeMessage.edit for embed builder"
```

---

### Task 2: `embed_builder.py` — build/parse an embed spec

**Files:**
- Create: `embed_builder.py` (repo root, next to `reaction_roles.py`/`button.py`)
- Test: `dashboard/backend/tests/test_embed_builder_core.py`

**Interfaces:**
- Consumes: nothing new (uses `discord.Embed` directly, no fakes needed for this task).
- Produces: `build_embed(spec: dict) -> discord.Embed`; `embed_to_spec(embed: discord.Embed) -> dict`; `validate_embed_spec(spec: dict) -> str | None` (returns an error code string or `None`).

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_embed_builder_core.py`:

```python
import embed_builder


def test_build_embed_sets_basic_fields():
    embed = embed_builder.build_embed({"title": "Hi", "description": "Desc", "color": "#5865F2"})
    assert embed.title == "Hi"
    assert embed.description == "Desc"
    assert embed.color.value == 0x5865F2


def test_build_embed_sets_author_footer_image_thumbnail():
    spec = {
        "author": {"name": "Author", "url": "https://a.example", "icon_url": "https://a.example/i.png"},
        "footer": {"text": "Footer", "icon_url": "https://f.example/i.png"},
        "image": {"url": "https://img.example/1.png"},
        "thumbnail": {"url": "https://thumb.example/1.png"},
    }
    embed = embed_builder.build_embed(spec)
    assert embed.author.name == "Author"
    assert embed.footer.text == "Footer"
    assert embed.image.url == "https://img.example/1.png"
    assert embed.thumbnail.url == "https://thumb.example/1.png"


def test_build_embed_sets_fields():
    embed = embed_builder.build_embed({"fields": [{"name": "N1", "value": "V1", "inline": True}]})
    assert len(embed.fields) == 1
    assert embed.fields[0].name == "N1"
    assert embed.fields[0].value == "V1"
    assert embed.fields[0].inline is True


def test_build_embed_sets_timestamp():
    embed = embed_builder.build_embed({"timestamp": "2026-07-02T12:00:00Z"})
    assert embed.timestamp is not None
    assert embed.timestamp.year == 2026


def test_embed_to_spec_round_trips_build_embed():
    original = {
        "title": "Hi",
        "description": "Desc",
        "color": "#5865f2",
        "author": {"name": "Author", "url": "", "icon_url": ""},
        "footer": {"text": "Footer", "icon_url": ""},
        "image": {"url": "https://img.example/1.png"},
        "thumbnail": {"url": ""},
        "fields": [{"name": "N1", "value": "V1", "inline": True}],
    }
    embed = embed_builder.build_embed(original)
    spec = embed_builder.embed_to_spec(embed)
    assert spec["title"] == "Hi"
    assert spec["description"] == "Desc"
    assert spec["color"] == "#5865f2"
    assert spec["author"]["name"] == "Author"
    assert spec["footer"]["text"] == "Footer"
    assert spec["image"]["url"] == "https://img.example/1.png"
    assert spec["fields"] == [{"name": "N1", "value": "V1", "inline": True}]


def test_validate_embed_spec_rejects_empty():
    assert embed_builder.validate_embed_spec({}) == "empty_embed"


def test_validate_embed_spec_accepts_title_only():
    assert embed_builder.validate_embed_spec({"title": "Hi"}) is None


def test_validate_embed_spec_rejects_title_too_long():
    assert embed_builder.validate_embed_spec({"title": "x" * 257}) == "title_too_long"


def test_validate_embed_spec_rejects_description_too_long():
    assert embed_builder.validate_embed_spec({"description": "x" * 4097}) == "description_too_long"


def test_validate_embed_spec_rejects_too_many_fields():
    fields = [{"name": "n", "value": "v"} for _ in range(26)]
    assert embed_builder.validate_embed_spec({"title": "Hi", "fields": fields}) == "too_many_fields"


def test_validate_embed_spec_rejects_field_name_too_long():
    result = embed_builder.validate_embed_spec({"title": "Hi", "fields": [{"name": "x" * 257, "value": "v"}]})
    assert result == "field_name_too_long"


def test_validate_embed_spec_rejects_field_value_too_long():
    result = embed_builder.validate_embed_spec({"title": "Hi", "fields": [{"name": "n", "value": "x" * 1025}]})
    assert result == "field_value_too_long"


def test_validate_embed_spec_rejects_total_budget_exceeded():
    spec = {"title": "Hi", "description": "x" * 4096, "footer": {"text": "x" * 1900}}
    assert embed_builder.validate_embed_spec(spec) == "embed_too_large"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_embed_builder_core.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'embed_builder'`

- [ ] **Step 3: Implement `embed_builder.py`**

```python
from datetime import datetime

import discord


def build_embed(spec: dict) -> discord.Embed:
    color = spec.get("color")
    color_value = int(color.lstrip("#"), 16) if color else None
    embed = discord.Embed(
        title=spec.get("title") or None,
        description=spec.get("description") or None,
        url=spec.get("url") or None,
        color=color_value,
    )

    author = spec.get("author") or {}
    if author.get("name"):
        embed.set_author(
            name=author["name"], url=author.get("url") or None, icon_url=author.get("icon_url") or None
        )

    footer = spec.get("footer") or {}
    if footer.get("text"):
        embed.set_footer(text=footer["text"], icon_url=footer.get("icon_url") or None)

    image = spec.get("image") or {}
    if image.get("url"):
        embed.set_image(url=image["url"])

    thumbnail = spec.get("thumbnail") or {}
    if thumbnail.get("url"):
        embed.set_thumbnail(url=thumbnail["url"])

    if spec.get("timestamp"):
        embed.timestamp = datetime.fromisoformat(spec["timestamp"].replace("Z", "+00:00"))

    for field in spec.get("fields") or []:
        embed.add_field(
            name=field.get("name") or " ",
            value=field.get("value") or " ",
            inline=bool(field.get("inline")),
        )

    return embed


def embed_to_spec(embed: discord.Embed) -> dict:
    data = embed.to_dict()
    color_value = data.get("color")
    author = data.get("author", {})
    footer = data.get("footer", {})
    image = data.get("image", {})
    thumbnail = data.get("thumbnail", {})
    return {
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "url": data.get("url", ""),
        "color": f"#{color_value:06x}" if color_value is not None else "",
        "author": {
            "name": author.get("name", ""),
            "url": author.get("url", ""),
            "icon_url": author.get("icon_url", ""),
        },
        "footer": {"text": footer.get("text", ""), "icon_url": footer.get("icon_url", "")},
        "image": {"url": image.get("url", "")},
        "thumbnail": {"url": thumbnail.get("url", "")},
        "timestamp": data.get("timestamp"),
        "fields": [
            {"name": f.get("name", ""), "value": f.get("value", ""), "inline": bool(f.get("inline"))}
            for f in data.get("fields", [])
        ],
    }


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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_embed_builder_core.py -v`
Expected: PASS (13 tests)

- [ ] **Step 5: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (136 + 13 = 149)

- [ ] **Step 6: Commit**

```bash
git add embed_builder.py dashboard/backend/tests/test_embed_builder_core.py
git commit -m "feat: add embed_builder core build/parse/validate functions"
```

---

### Task 3: `embed_builder.py` — role-button view build/parse

**Files:**
- Modify: `embed_builder.py` (append)
- Test: `dashboard/backend/tests/test_embed_builder_buttons.py`

**Interfaces:**
- Consumes: `FakeGuild`, `FakeRole`, `FakeMessage`, `FakeComponentRow` (Task 1/existing).
- Produces: `build_role_button_view(guild, role_ids: list[int]) -> discord.ui.View`; `parse_role_button_ids(message) -> list[int]`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_embed_builder_buttons.py`:

```python
import discord

import embed_builder
from dashboard.backend.tests.fakes import FakeComponentRow, FakeGuild, FakeMessage, FakeRole


def test_build_role_button_view_creates_buttons_with_role_names():
    role = FakeRole(7, name="VIP")
    guild = FakeGuild(roles=[role])
    view = embed_builder.build_role_button_view(guild, [7])
    assert len(view.children) == 1
    button = view.children[0]
    assert button.custom_id == "btn_role_7"
    assert button.label == "VIP"


def test_build_role_button_view_falls_back_to_id_when_role_missing():
    guild = FakeGuild(roles=[])
    view = embed_builder.build_role_button_view(guild, [999])
    assert view.children[0].label == "999"


def test_parse_role_button_ids_extracts_matching_custom_ids():
    row = FakeComponentRow(
        [
            discord.ui.Button(label="a", custom_id="btn_role_7"),
            discord.ui.Button(label="b", custom_id="btn_role_8"),
        ]
    )
    message = FakeMessage(1, components=[row])
    assert embed_builder.parse_role_button_ids(message) == [7, 8]


def test_parse_role_button_ids_ignores_non_role_buttons():
    row = FakeComponentRow([discord.ui.Button(label="a", custom_id="btn_form_1")])
    message = FakeMessage(1, components=[row])
    assert embed_builder.parse_role_button_ids(message) == []


def test_parse_role_button_ids_handles_no_components():
    message = FakeMessage(1)
    assert embed_builder.parse_role_button_ids(message) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_embed_builder_buttons.py -v`
Expected: FAIL with `AttributeError: module 'embed_builder' has no attribute 'build_role_button_view'`

- [ ] **Step 3: Append to `embed_builder.py`**

```python
def build_role_button_view(guild, role_ids: list[int]) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    for role_id in role_ids:
        role = guild.get_role(role_id)
        label = role.name[:80] if role else str(role_id)
        view.add_item(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id=f"btn_role_{role_id}",
            )
        )
    return view


def parse_role_button_ids(message) -> list[int]:
    role_ids = []
    for row in getattr(message, "components", []) or []:
        for child in getattr(row, "children", []):
            custom_id = getattr(child, "custom_id", "") or ""
            if custom_id.startswith("btn_role_"):
                try:
                    role_ids.append(int(custom_id.removeprefix("btn_role_")))
                except ValueError:
                    continue
    return role_ids
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_embed_builder_buttons.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Verify the module still imports cleanly**

Run: `python -c "import embed_builder"`
Expected: no output, exit code 0

- [ ] **Step 6: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (149 + 5 = 154)

- [ ] **Step 7: Commit**

```bash
git add embed_builder.py dashboard/backend/tests/test_embed_builder_buttons.py
git commit -m "feat: add role-button view build/parse to embed_builder"
```

---

### Task 4: `POST /api/embed-messages`

**Files:**
- Create: `dashboard/backend/routes/embed_builder.py`
- Test: `dashboard/backend/tests/test_embed_builder_routes.py`

**Interfaces:**
- Consumes: `embed_builder.build_embed`/`validate_embed_spec`/`build_role_button_view` (Tasks 2-3, imported as `import embed_builder`, same bare top-level import style as `dashboard/backend/routes/reaction_roles.py` uses for `reaction_roles`); `require_dashboard_access` (Phase 2a); fakes from Task 1.
- Produces: `routes = web.RouteTableDef()` (this task's table gets more routes appended in Task 5); `MAX_ROLE_BUTTONS = 5`; `def _is_role_assignable(role, guild) -> bool`; `def _validate_role_ids_structure(role_ids_raw) -> tuple[list[int], web.Response | None]`; `def _validate_role_ids_assignable(role_ids: list[int], guild) -> web.Response | None` (must be called AFTER channel/message existence checks); `POST /api/embed-messages` → `201 {message_id, channel_id}` / `400`/`403`/`404`/`502`/`503`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_embed_builder_routes.py`:

```python
import discord
import pytest

from dashboard.backend.routes.embed_builder import routes as embed_builder_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)


def build(roles=None, channels=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot_top = FakeRole(900, name="bot-role", position=50)
    me = FakeMember(1, name="bot", top_role=bot_top)
    guild = FakeGuild(members=[moderator], roles=roles or [], channels=channels or [], me=me)
    return guild, make_moderation_app(FakeBot(guild), [embed_builder_routes])


@pytest.mark.asyncio
async def test_create_embed_message_success(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    channel = FakeChannel(500, next_message_id=999)
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages",
        json={"channel_id": "500", "content": "Hello", "embed": {"title": "Title"}, "role_ids": ["7"]},
    )
    assert resp.status == 201
    body = await resp.json()
    assert body == {"message_id": "999", "channel_id": "500"}
    assert channel.send_calls[0]["content"] == "Hello"
    assert channel.send_calls[0]["embed"].title == "Title"
    assert channel.send_calls[0]["view"].children[0].custom_id == "btn_role_7"


@pytest.mark.asyncio
async def test_create_embed_message_rejects_empty_embed(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/embed-messages", json={"channel_id": "500", "embed": {}, "role_ids": []})
    assert resp.status == 400
    assert (await resp.json())["error"] == "empty_embed"


@pytest.mark.asyncio
async def test_create_embed_message_rejects_too_many_roles(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages",
        json={"channel_id": "500", "embed": {"title": "T"}, "role_ids": ["1", "2", "3", "4", "5", "6"]},
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "too_many_roles"


@pytest.mark.asyncio
async def test_create_embed_message_checks_channel_before_role_assignability(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    _, app = build(roles=[role], channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages", json={"channel_id": "500", "embed": {"title": "T"}, "role_ids": ["9"]}
    )
    assert resp.status == 404
    assert (await resp.json())["error"] == "channel_not_found"


@pytest.mark.asyncio
async def test_create_embed_message_rejects_role_above_bot(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    channel = FakeChannel(500)
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/embed-messages", json={"channel_id": "500", "embed": {"title": "T"}, "role_ids": ["9"]}
    )
    assert resp.status == 403


@pytest.mark.asyncio
async def test_create_embed_message_channel_not_found(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/embed-messages", json={"channel_id": "500", "embed": {"title": "T"}})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_create_embed_message_discord_error_logged(aiohttp_client):
    channel = FakeChannel(500)
    channel.send_raises = discord.HTTPException.__new__(discord.HTTPException)
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/embed-messages", json={"channel_id": "500", "embed": {"title": "T"}})
    assert resp.status == 502


@pytest.mark.asyncio
async def test_create_embed_message_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/embed-messages", json={"channel_id": "500", "embed": {"title": "T"}})
    assert resp.status == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_embed_builder_routes.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.routes.embed_builder'`

- [ ] **Step 3: Implement `dashboard/backend/routes/embed_builder.py`**

```python
import logging

import discord
from aiohttp import web

import embed_builder
from ..access_middleware import require_dashboard_access

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()

MAX_ROLE_BUTTONS = 5


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


def _is_role_assignable(role, guild) -> bool:
    return not role.is_default() and not role.managed and role.position < guild.me.top_role.position


def _validate_role_ids_structure(role_ids_raw):
    """Checks that don't require Discord data: count and int-parseability.
    Returns (parsed_role_ids, None) on success, or ([], error_response)."""
    if len(role_ids_raw) > MAX_ROLE_BUTTONS:
        return [], web.json_response({"error": "too_many_roles"}, status=400)
    try:
        role_ids = [int(r) for r in role_ids_raw]
    except (TypeError, ValueError):
        return [], web.json_response({"error": "invalid_request"}, status=400)
    return role_ids, None


def _validate_role_ids_assignable(role_ids: list[int], guild):
    """Role-hierarchy check. Returns None on success, or an error
    web.Response. Must run AFTER channel/message existence checks."""
    for role_id in role_ids:
        role = guild.get_role(role_id)
        if role is None or not _is_role_assignable(role, guild):
            return web.json_response({"error": "role_not_assignable"}, status=403)
    return None


async def _parse_body(request):
    try:
        body = await request.json()
    except ValueError:
        return None, web.json_response({"error": "invalid_request"}, status=400)
    return body, None


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
    error_code = embed_builder.validate_embed_spec(spec)
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

    content = body.get("content") or None
    embed = embed_builder.build_embed(spec)
    view = embed_builder.build_role_button_view(guild, role_ids) if role_ids else None

    try:
        message = await channel.send(content=content, embed=embed, view=view)
    except discord.HTTPException as exc:
        logger.warning("Failed to send embed message to channel %s: %s", channel_id, exc)
        return web.json_response({"error": "discord_error"}, status=502)

    return web.json_response({"message_id": str(message.id), "channel_id": str(channel_id)}, status=201)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_embed_builder_routes.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routes/embed_builder.py dashboard/backend/tests/test_embed_builder_routes.py
git commit -m "feat(dashboard): add POST /api/embed-messages"
```

---

### Task 5: `GET`/`PUT /api/embed-messages/{channel_id}/{message_id}`

**Files:**
- Modify: `dashboard/backend/routes/embed_builder.py` (append)
- Test: `dashboard/backend/tests/test_embed_builder_routes.py` (append)

**Interfaces:**
- Consumes: everything from Task 4; `embed_builder.embed_to_spec`/`parse_role_button_ids` (Tasks 2-3).
- Produces: `GET /api/embed-messages/{channel_id}/{message_id}` → `200 {content, embed, role_ids}` / `400`/`404`/`502`/`503`; `PUT /api/embed-messages/{channel_id}/{message_id}` → `200 {message_id, channel_id}` / `400`/`403`/`404`/`502`/`503`.

- [ ] **Step 1: Write the failing test**

Append to `dashboard/backend/tests/test_embed_builder_routes.py` (add `import embed_builder` and `FakeComponentRow`/`FakeMessage` to the existing imports at the top of the file first):

```python
import embed_builder
from dashboard.backend.tests.fakes import FakeComponentRow, FakeMessage
```

Then append these tests:

```python
@pytest.mark.asyncio
async def test_get_embed_message_returns_parsed_spec_and_roles(aiohttp_client):
    embed = embed_builder.build_embed({"title": "Existing", "description": "Desc"})
    row = FakeComponentRow([discord.ui.Button(label="VIP", custom_id="btn_role_7")])
    message = FakeMessage(999, embeds=[embed], components=[row], content="hi")
    channel = FakeChannel(500, messages={999: message})
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/embed-messages/500/999")
    assert resp.status == 200
    body = await resp.json()
    assert body["content"] == "hi"
    assert body["embed"]["title"] == "Existing"
    assert body["role_ids"] == ["7"]


@pytest.mark.asyncio
async def test_get_embed_message_404_when_message_missing(aiohttp_client):
    channel = FakeChannel(500, messages={})
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/embed-messages/500/999")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_get_embed_message_404_when_channel_missing(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/embed-messages/500/999")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_update_embed_message_success(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put(
        "/api/embed-messages/500/999",
        json={"content": "updated", "embed": {"title": "Updated"}, "role_ids": ["7"]},
    )
    assert resp.status == 200
    assert message.edit_calls[0]["content"] == "updated"
    assert message.edit_calls[0]["embed"].title == "Updated"


@pytest.mark.asyncio
async def test_update_embed_message_checks_message_before_role_assignability(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    channel = FakeChannel(500, messages={})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/embed-messages/500/999", json={"embed": {"title": "T"}, "role_ids": ["9"]})
    assert resp.status == 404
    assert (await resp.json())["error"] == "message_not_found"


@pytest.mark.asyncio
async def test_update_embed_message_rejects_role_above_bot(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/embed-messages/500/999", json={"embed": {"title": "T"}, "role_ids": ["9"]})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_update_embed_message_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.put("/api/embed-messages/500/999", json={"embed": {"title": "T"}})
    assert resp.status == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_embed_builder_routes.py -v`
Expected: FAIL — `GET`/`PUT` routes don't exist yet (404s on the new tests).

- [ ] **Step 3: Append to `dashboard/backend/routes/embed_builder.py`**

```python
@routes.get("/api/embed-messages/{channel_id}/{message_id}")
@require_dashboard_access
async def get_embed_message(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        channel_id = int(request.match_info["channel_id"])
        message_id = int(request.match_info["message_id"])
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    try:
        message = await channel.fetch_message(message_id)
    except discord.NotFound:
        return web.json_response({"error": "message_not_found"}, status=404)
    except discord.HTTPException:
        return web.json_response({"error": "discord_error"}, status=502)

    spec = embed_builder.embed_to_spec(message.embeds[0]) if message.embeds else {}
    role_ids = embed_builder.parse_role_button_ids(message)

    return web.json_response(
        {"content": message.content, "embed": spec, "role_ids": [str(r) for r in role_ids]}
    )


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
    error_code = embed_builder.validate_embed_spec(spec)
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

    content = body.get("content") or None
    embed = embed_builder.build_embed(spec)
    view = embed_builder.build_role_button_view(guild, role_ids) if role_ids else None

    try:
        await message.edit(content=content, embed=embed, view=view)
    except discord.HTTPException as exc:
        logger.warning("Failed to edit embed message %s in channel %s: %s", message_id, channel_id, exc)
        return web.json_response({"error": "discord_error"}, status=502)

    return web.json_response({"message_id": str(message_id), "channel_id": str(channel_id)})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_embed_builder_routes.py -v`
Expected: PASS (15 tests total in this file)

- [ ] **Step 5: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (154 + 8 + 7 = 169)

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/embed_builder.py dashboard/backend/tests/test_embed_builder_routes.py
git commit -m "feat(dashboard): add GET/PUT embed-message routes for editing"
```

---

### Task 6: Register routes in `app.py`

**Files:**
- Modify: `dashboard/backend/app.py` (add one import + one `add_routes` line)

**Interfaces:**
- Consumes: `dashboard.backend.routes.embed_builder.routes` (Tasks 4-5).
- Produces: all Phase 3b endpoints live in the real app.

`main.py` is NOT touched by this task — `embed_builder.py` has no cog and no `setup()` function (per the design spec, this feature is entirely stateless helper functions called directly by the dashboard routes), so there is nothing to load as a bot extension.

- [ ] **Step 1: Add the import and route registration to `dashboard/backend/app.py`**

Read the current file first. Add this import alongside the existing route imports (after `from .routes.reaction_roles import routes as reaction_roles_routes`):

```python
from .routes.embed_builder import routes as embed_builder_routes
```

Add this line alongside the existing `app.add_routes(...)` calls (after `app.add_routes(reaction_roles_routes)`):

```python
    app.add_routes(embed_builder_routes)
```

- [ ] **Step 2: Verify the file still imports cleanly**

Run: `python -c "import main"`
Expected: no output, exit code 0

- [ ] **Step 3: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (169)

- [ ] **Step 4: Commit**

```bash
git add dashboard/backend/app.py
git commit -m "feat: register embed-builder routes"
```

---

### Task 7: Frontend API client — embed-message functions

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts` (append; do NOT change any existing export)
- Test: `dashboard/frontend/src/api/embedBuilder.test.ts`

**Interfaces:**
- Consumes: existing `apiFetch`, `jsonInit` (already in `client.ts`).
- Produces: `interface EmbedFieldSpec { name: string; value: string; inline: boolean }`; `interface EmbedSpec { title: string; description: string; url: string; color: string; author: {name: string; url: string; icon_url: string}; footer: {text: string; icon_url: string}; image: {url: string}; thumbnail: {url: string}; timestamp: string | null; fields: EmbedFieldSpec[] }`; `interface EmbedMessagePayload { content: string; embed: EmbedSpec; role_ids: string[] }`; `interface EmbedMessageResult { message_id: string; channel_id: string }`; `createEmbedMessage(channelId: string, payload: EmbedMessagePayload): Promise<EmbedMessageResult>`; `fetchEmbedMessage(channelId: string, messageId: string): Promise<EmbedMessagePayload>`; `updateEmbedMessage(channelId: string, messageId: string, payload: EmbedMessagePayload): Promise<EmbedMessageResult>`.

- [ ] **Step 1: Write the failing test**

`dashboard/frontend/src/api/embedBuilder.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createEmbedMessage, fetchEmbedMessage, updateEmbedMessage, type EmbedMessagePayload } from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

const samplePayload: EmbedMessagePayload = {
  content: 'hi',
  embed: {
    title: 'T',
    description: '',
    url: '',
    color: '',
    author: { name: '', url: '', icon_url: '' },
    footer: { text: '', icon_url: '' },
    image: { url: '' },
    thumbnail: { url: '' },
    timestamp: null,
    fields: [],
  },
  role_ids: ['7'],
}

describe('embed builder api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('createEmbedMessage POSTs channel_id alongside the payload', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ message_id: '999', channel_id: '500' }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await createEmbedMessage('500', samplePayload)
    expect(result).toEqual({ message_id: '999', channel_id: '500' })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/embed-messages',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ channel_id: '500', ...samplePayload }),
      }),
    )
  })

  it('fetchEmbedMessage GETs by channel and message id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson(samplePayload))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchEmbedMessage('500', '999')
    expect(result).toEqual(samplePayload)
    expect(fetchMock).toHaveBeenCalledWith('/api/embed-messages/500/999', expect.anything())
  })

  it('updateEmbedMessage PUTs the payload without channel_id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ message_id: '999', channel_id: '500' }))
    vi.stubGlobal('fetch', fetchMock)

    await updateEmbedMessage('500', '999', samplePayload)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/embed-messages/500/999',
      expect.objectContaining({ method: 'PUT', body: JSON.stringify(samplePayload) }),
    )
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd dashboard/frontend && npm run test`
Expected: FAIL — new exports don't exist.

- [ ] **Step 3: Append to `dashboard/frontend/src/api/client.ts`**

```ts
export interface EmbedFieldSpec {
  name: string
  value: string
  inline: boolean
}

export interface EmbedSpec {
  title: string
  description: string
  url: string
  color: string
  author: { name: string; url: string; icon_url: string }
  footer: { text: string; icon_url: string }
  image: { url: string }
  thumbnail: { url: string }
  timestamp: string | null
  fields: EmbedFieldSpec[]
}

export interface EmbedMessagePayload {
  content: string
  embed: EmbedSpec
  role_ids: string[]
}

export interface EmbedMessageResult {
  message_id: string
  channel_id: string
}

export function createEmbedMessage(channelId: string, payload: EmbedMessagePayload): Promise<EmbedMessageResult> {
  return apiFetch('/api/embed-messages', jsonInit('POST', { channel_id: channelId, ...payload }))
}

export function fetchEmbedMessage(channelId: string, messageId: string): Promise<EmbedMessagePayload> {
  return apiFetch(`/api/embed-messages/${channelId}/${messageId}`)
}

export function updateEmbedMessage(
  channelId: string,
  messageId: string,
  payload: EmbedMessagePayload,
): Promise<EmbedMessageResult> {
  return apiFetch(`/api/embed-messages/${channelId}/${messageId}`, jsonInit('PUT', payload))
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test`
Expected: PASS — 3 new + all existing (37 total)

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/embedBuilder.test.ts
git commit -m "feat(dashboard): add embed-message API client functions"
```

---

### Task 8: Frontend UI — tabs, `EmbedBuilderPage`, `EmbedPreview`, wiring

**Files:**
- Create: `dashboard/frontend/src/pages/MessageBuilder.tsx`
- Create: `dashboard/frontend/src/pages/EmbedBuilder.tsx`
- Create: `dashboard/frontend/src/components/EmbedPreview.tsx`
- Test: `dashboard/frontend/src/pages/EmbedBuilder.test.tsx`
- Test: `dashboard/frontend/src/pages/MessageBuilder.test.tsx`
- Modify: `dashboard/frontend/src/App.tsx` (swap the `/reaction-roles` route's element from `ReactionRolesPage` to the new `MessageBuilderPage`)

**Interfaces:**
- Consumes: `createEmbedMessage`, `fetchEmbedMessage`, `updateEmbedMessage`, `fetchChannels`, `fetchRoles`, types `EmbedSpec`/`EmbedFieldSpec`/`EmbedMessagePayload`/`ChannelInfo`/`RoleInfo` (Task 7 + earlier phases); `Button` (existing design system); `ReactionRolesPage` (Phase 3a, unchanged).
- Produces: `MessageBuilderPage()`; `EmbedBuilderPage()`; `EmbedPreview({ content, embed }: { content: string; embed: EmbedSpec })`.

- [ ] **Step 1: Write the failing tests**

`dashboard/frontend/src/pages/EmbedBuilder.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { EmbedBuilderPage } from './EmbedBuilder'

describe('EmbedBuilderPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('creates a new embed message', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    const createSpy = vi
      .spyOn(client, 'createEmbedMessage')
      .mockResolvedValue({ message_id: '999', channel_id: '500' })

    render(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Hello' } })
    fireEvent.click(screen.getByText('Отправить'))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith(
        '500',
        expect.objectContaining({ embed: expect.objectContaining({ title: 'Hello' }) }),
      ),
    )
    expect(await screen.findByText(/999/)).toBeInTheDocument()
  })

  it('rejects an empty embed before calling the API', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createEmbedMessage')

    render(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })
    fireEvent.click(screen.getByText('Отправить'))

    expect(await screen.findByText(/Заполните хотя бы/)).toBeInTheDocument()
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('adds and removes a field', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EmbedBuilderPage />)

    fireEvent.click(await screen.findByText('+ Добавить поле'))
    expect(screen.getByPlaceholderText('Название поля')).toBeInTheDocument()

    fireEvent.click(screen.getByText('×'))
    expect(screen.queryByPlaceholderText('Название поля')).not.toBeInTheDocument()
  })

  it('loads an existing message for editing and prefills the form', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchEmbedMessage').mockResolvedValue({
      content: 'existing content',
      embed: {
        title: 'Existing title',
        description: '',
        url: '',
        color: '#5865F2',
        author: { name: '', url: '', icon_url: '' },
        footer: { text: '', icon_url: '' },
        image: { url: '' },
        thumbnail: { url: '' },
        timestamp: null,
        fields: [],
      },
      role_ids: [],
    })

    render(<EmbedBuilderPage />)

    fireEvent.click(await screen.findByText('Редактировать существующее'))
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })
    fireEvent.change(screen.getByPlaceholderText('ID существующего сообщения'), { target: { value: '999' } })
    fireEvent.click(screen.getByText('Загрузить'))

    await waitFor(() => expect(screen.getByLabelText('Title')).toHaveValue('Existing title'))
    expect(screen.getByLabelText('Текст сообщения')).toHaveValue('existing content')
  })

  it('renders the live preview with the current title', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EmbedBuilderPage />)

    fireEvent.change(await screen.findByLabelText('Title'), { target: { value: 'Preview Title' } })
    await waitFor(() => expect(screen.getByText('Preview Title')).toBeInTheDocument())
  })
})
```

`dashboard/frontend/src/pages/MessageBuilder.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { MessageBuilderPage } from './MessageBuilder'

describe('MessageBuilderPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('shows Reaction Roles content by default and switches to the Эмбеды tab', async () => {
    vi.spyOn(client, 'fetchReactionRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchEmojis').mockResolvedValue([])

    render(<MessageBuilderPage />)

    await waitFor(() => screen.getByText('Reaction Roles'))
    expect(screen.getByText('Пока ничего не настроено.')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Эмбеды'))
    await waitFor(() => screen.getByLabelText('Title'))
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm run test`
Expected: FAIL — `Cannot find module './EmbedBuilder'` / `Cannot find module './MessageBuilder'`.

- [ ] **Step 3: Implement `dashboard/frontend/src/components/EmbedPreview.tsx`**

```tsx
import type { EmbedSpec } from '../api/client'

interface Props {
  content: string
  embed: EmbedSpec
}

export function EmbedPreview({ content, embed }: Props) {
  const barColor = embed.color || '#4e5058'

  return (
    <div className="rounded-card border border-border bg-background p-4">
      {content && <p className="mb-2 whitespace-pre-wrap text-sm text-foreground">{content}</p>}
      <div className="flex rounded-control bg-surface" style={{ borderLeft: `4px solid ${barColor}` }}>
        <div className="flex-1 p-3">
          {embed.author.name && (
            <div className="mb-1 flex items-center gap-2 text-sm font-medium text-foreground">
              {embed.author.icon_url && <img src={embed.author.icon_url} alt="" className="h-5 w-5 rounded-full" />}
              <span>{embed.author.name}</span>
            </div>
          )}
          {embed.title && <p className="mb-1 text-base font-semibold text-foreground">{embed.title}</p>}
          {embed.description && (
            <p className="mb-2 whitespace-pre-wrap text-sm text-muted">{embed.description}</p>
          )}
          {embed.fields.length > 0 && (
            <div className="mb-2 grid grid-cols-2 gap-2">
              {embed.fields.map((field, index) => (
                <div key={index} className={field.inline ? '' : 'col-span-2'}>
                  <p className="text-xs font-semibold text-foreground">{field.name}</p>
                  <p className="whitespace-pre-wrap text-xs text-muted">{field.value}</p>
                </div>
              ))}
            </div>
          )}
          {embed.image.url && <img src={embed.image.url} alt="" className="mt-2 max-w-full rounded-control" />}
          {(embed.footer.text || embed.timestamp) && (
            <div className="mt-2 flex items-center gap-2 text-xs text-muted">
              {embed.footer.icon_url && (
                <img src={embed.footer.icon_url} alt="" className="h-4 w-4 rounded-full" />
              )}
              <span>
                {embed.footer.text}
                {embed.footer.text && embed.timestamp && ' • '}
                {embed.timestamp && new Date(embed.timestamp).toLocaleString()}
              </span>
            </div>
          )}
        </div>
        {embed.thumbnail.url && (
          <img src={embed.thumbnail.url} alt="" className="m-3 h-16 w-16 rounded-control object-cover" />
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Implement `dashboard/frontend/src/pages/EmbedBuilder.tsx`**

```tsx
import { useEffect, useState } from 'react'
import {
  createEmbedMessage,
  fetchChannels,
  fetchEmbedMessage,
  fetchRoles,
  updateEmbedMessage,
  type ChannelInfo,
  type EmbedFieldSpec,
  type EmbedSpec,
  type RoleInfo,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { EmbedPreview } from '../components/EmbedPreview'

const EMPTY_EMBED_SPEC: EmbedSpec = {
  title: '',
  description: '',
  url: '',
  color: '#5865F2',
  author: { name: '', url: '', icon_url: '' },
  footer: { text: '', icon_url: '' },
  image: { url: '' },
  thumbnail: { url: '' },
  timestamp: null,
  fields: [],
}

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
  return null
}

export function EmbedBuilderPage() {
  const [mode, setMode] = useState<'create' | 'edit'>('create')
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [channelId, setChannelId] = useState('')
  const [messageId, setMessageId] = useState('')
  const [content, setContent] = useState('')
  const [embed, setEmbed] = useState<EmbedSpec>(EMPTY_EMBED_SPEC)
  const [roleIds, setRoleIds] = useState<string[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedResult, setSavedResult] = useState<{ message_id: string; channel_id: string } | null>(null)

  useEffect(() => {
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
  }, [])

  const updateEmbedField = <K extends keyof EmbedSpec>(key: K, value: EmbedSpec[K]) => {
    setEmbed((prev) => ({ ...prev, [key]: value }))
  }

  const updateField = (index: number, patch: Partial<EmbedFieldSpec>) => {
    setEmbed((prev) => ({ ...prev, fields: prev.fields.map((f, i) => (i === index ? { ...f, ...patch } : f)) }))
  }

  const addField = () => {
    setEmbed((prev) => ({ ...prev, fields: [...prev.fields, { name: '', value: '', inline: false }] }))
  }

  const removeField = (index: number) => {
    setEmbed((prev) => ({ ...prev, fields: prev.fields.filter((_, i) => i !== index) }))
  }

  const toggleRole = (roleId: string) => {
    setRoleIds((prev) => (prev.includes(roleId) ? prev.filter((r) => r !== roleId) : [...prev, roleId]))
  }

  const handleLoad = async () => {
    setError('')
    if (!channelId || !messageId) {
      setError('Укажите канал и Message ID')
      return
    }
    setBusy(true)
    try {
      const data = await fetchEmbedMessage(channelId, messageId)
      setContent(data.content)
      setEmbed(data.embed)
      setRoleIds(data.role_ids)
    } catch {
      setError('Не удалось загрузить сообщение — проверьте канал/ID')
    } finally {
      setBusy(false)
    }
  }

  const handleSave = async () => {
    setError('')
    setSavedResult(null)
    if (!channelId) {
      setError('Укажите канал')
      return
    }
    if (mode === 'edit' && !messageId) {
      setError('Укажите Message ID')
      return
    }
    if (roleIds.length > 5) {
      setError('Не больше 5 роль-кнопок')
      return
    }
    const validationError = validateEmbedSpec(embed)
    if (validationError) {
      setError(validationError)
      return
    }

    setBusy(true)
    try {
      const payload = { content, embed, role_ids: roleIds }
      const result =
        mode === 'edit'
          ? await updateEmbedMessage(channelId, messageId, payload)
          : await createEmbedMessage(channelId, payload)
      setSavedResult(result)
    } catch {
      setError('Не удалось сохранить — проверьте канал/ID сообщения и права на роли')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="flex flex-col gap-3">
        <div className="flex gap-2">
          <Button variant={mode === 'create' ? 'primary' : 'secondary'} onClick={() => setMode('create')}>
            Новое сообщение
          </Button>
          <Button variant={mode === 'edit' ? 'primary' : 'secondary'} onClick={() => setMode('edit')}>
            Редактировать существующее
          </Button>
        </div>

        <label className="text-sm text-muted" htmlFor="eb-channel">
          Канал
        </label>
        <select
          id="eb-channel"
          value={channelId}
          onChange={(e) => setChannelId(e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
        >
          <option value="">Выберите канал…</option>
          {channels.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>

        {mode === 'edit' && (
          <div className="flex gap-2">
            <input
              value={messageId}
              onChange={(e) => setMessageId(e.target.value)}
              placeholder="ID существующего сообщения"
              className="flex-1 rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            />
            <Button variant="secondary" onClick={handleLoad} disabled={busy}>
              Загрузить
            </Button>
          </div>
        )}

        <label className="text-sm text-muted" htmlFor="eb-content">
          Текст сообщения
        </label>
        <textarea
          id="eb-content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          rows={2}
        />

        <label className="text-sm text-muted" htmlFor="eb-title">
          Title
        </label>
        <input
          id="eb-title"
          value={embed.title}
          onChange={(e) => updateEmbedField('title', e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-description">
          Description
        </label>
        <textarea
          id="eb-description"
          value={embed.description}
          onChange={(e) => updateEmbedField('description', e.target.value)}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          rows={3}
        />

        <label className="text-sm text-muted" htmlFor="eb-color">
          Цвет
        </label>
        <div className="flex gap-2">
          <input
            id="eb-color"
            type="color"
            value={embed.color || '#5865F2'}
            onChange={(e) => updateEmbedField('color', e.target.value)}
            className="h-9 w-12 rounded-control border border-border bg-background"
          />
          <input
            value={embed.color}
            onChange={(e) => updateEmbedField('color', e.target.value)}
            placeholder="#5865F2"
            className="flex-1 rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />
        </div>

        <label className="text-sm text-muted" htmlFor="eb-author-name">
          Author
        </label>
        <input
          id="eb-author-name"
          value={embed.author.name}
          onChange={(e) => updateEmbedField('author', { ...embed.author, name: e.target.value })}
          placeholder="Имя автора"
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-footer-text">
          Footer
        </label>
        <input
          id="eb-footer-text"
          value={embed.footer.text}
          onChange={(e) => updateEmbedField('footer', { ...embed.footer, text: e.target.value })}
          placeholder="Текст footer"
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-image-url">
          Image URL
        </label>
        <input
          id="eb-image-url"
          value={embed.image.url}
          onChange={(e) => updateEmbedField('image', { url: e.target.value })}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="text-sm text-muted" htmlFor="eb-thumbnail-url">
          Thumbnail URL
        </label>
        <input
          id="eb-thumbnail-url"
          value={embed.thumbnail.url}
          onChange={(e) => updateEmbedField('thumbnail', { url: e.target.value })}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />

        <label className="flex items-center gap-2 text-sm text-muted">
          <input
            type="checkbox"
            checked={embed.timestamp !== null}
            onChange={(e) => updateEmbedField('timestamp', e.target.checked ? new Date().toISOString() : null)}
          />
          Текущее время
        </label>

        <div className="flex flex-col gap-2">
          {embed.fields.map((field, index) => (
            <div key={index} className="flex flex-wrap items-center gap-2 rounded-control border border-border/60 p-2">
              <input
                value={field.name}
                onChange={(e) => updateField(index, { name: e.target.value })}
                placeholder="Название поля"
                className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
              />
              <input
                value={field.value}
                onChange={(e) => updateField(index, { value: e.target.value })}
                placeholder="Значение поля"
                className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
              />
              <label className="flex items-center gap-1 text-xs text-muted">
                <input type="checkbox" checked={field.inline} onChange={(e) => updateField(index, { inline: e.target.checked })} />
                inline
              </label>
              <button type="button" onClick={() => removeField(index)} className="cursor-pointer text-muted hover:text-danger">
                ×
              </button>
            </div>
          ))}
          <button type="button" onClick={addField} className="cursor-pointer self-start text-sm text-primary hover:text-primary-hover">
            + Добавить поле
          </button>
        </div>

        <div>
          <p className="mb-1 text-sm text-muted">Роль-кнопки (до 5)</p>
          <div className="flex flex-wrap gap-2">
            {roles.map((role) => (
              <label key={role.id} className="flex items-center gap-1 text-xs text-foreground">
                <input type="checkbox" checked={roleIds.includes(role.id)} onChange={() => toggleRole(role.id)} />
                {role.name}
              </label>
            ))}
          </div>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}
        {savedResult && (
          <p className="text-sm text-success">
            Сохранено: message_id {savedResult.message_id} в канале {savedResult.channel_id}
          </p>
        )}

        <Button variant="primary" onClick={handleSave} disabled={busy}>
          {busy ? 'Сохраняем…' : mode === 'edit' ? 'Сохранить' : 'Отправить'}
        </Button>
      </div>

      <div>
        <EmbedPreview content={content} embed={embed} />
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Implement `dashboard/frontend/src/pages/MessageBuilder.tsx`**

```tsx
import { useState } from 'react'
import { ReactionRolesPage } from './ReactionRoles'
import { EmbedBuilderPage } from './EmbedBuilder'

type Tab = 'reaction-roles' | 'embeds'

export function MessageBuilderPage() {
  const [tab, setTab] = useState<Tab>('reaction-roles')

  return (
    <div>
      <div className="mb-4 flex gap-2 border-b border-border">
        <button
          type="button"
          onClick={() => setTab('reaction-roles')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'reaction-roles' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          Reaction Roles
        </button>
        <button
          type="button"
          onClick={() => setTab('embeds')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'embeds' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          Эмбеды
        </button>
      </div>
      {tab === 'reaction-roles' ? <ReactionRolesPage /> : <EmbedBuilderPage />}
    </div>
  )
}
```

- [ ] **Step 6: Wire the route in `App.tsx`**

Read the current file first. Replace:

```tsx
import { ReactionRolesPage } from './pages/ReactionRoles'
```

with:

```tsx
import { MessageBuilderPage } from './pages/MessageBuilder'
```

Replace:

```tsx
            <Route path="reaction-roles" element={<ReactionRolesPage />} />
```

with:

```tsx
            <Route path="reaction-roles" element={<MessageBuilderPage />} />
```

- [ ] **Step 7: Run tests + typecheck + build**

Run: `npm run test`, `npx tsc --noEmit`, `npm run build`
Expected: all green (43 Vitest tests total), no debug artifacts, `git status --short` clean before committing.

- [ ] **Step 8: Commit**

```bash
git add dashboard/frontend/src/pages/MessageBuilder.tsx dashboard/frontend/src/pages/EmbedBuilder.tsx dashboard/frontend/src/components/EmbedPreview.tsx dashboard/frontend/src/pages/EmbedBuilder.test.tsx dashboard/frontend/src/pages/MessageBuilder.test.tsx dashboard/frontend/src/App.tsx
git commit -m "feat(dashboard): add embed builder UI with tabs and live preview"
```

---

### Task 9: Full end-to-end manual verification

**Files:** none (verification only).

- [ ] **Step 1:** Restart backend (`python main.py`) and frontend (`npm run dev`), open `http://localhost:5173`, log in.
- [ ] **Step 2:** Sidebar "Конструктор кнопок и эмбедов" (`/reaction-roles`) now shows two tabs. Confirm "Reaction Roles" tab still works exactly as before (Phase 3a unaffected).
- [ ] **Step 3:** Switch to the "Эмбеды" tab. Fill in a channel, a title, a description, a color, a field, and check "текущее время" — confirm the live preview panel updates on every keystroke and matches what you typed.
- [ ] **Step 4:** Select up to 5 roles as role-buttons, click "Отправить" — confirm the message appears in the target Discord channel with the correct embed AND the role-toggle buttons attached.
- [ ] **Step 5:** Click one of the role-buttons on the real Discord message as a normal user — confirm the role toggles exactly like an existing `button.py`-created role-button (this proves `btn_role_{role_id}` reuse works without touching `button.py`).
- [ ] **Step 6:** Switch to "Редактировать существующее", enter the channel + message ID from Step 4, click "Загрузить" — confirm the form (including the role-button checkboxes) is pre-filled with what was actually sent.
- [ ] **Step 7:** Change the title and one field, click "Сохранить" — confirm the Discord message updates in place (not a new message).
- [ ] **Step 8:** Try submitting with every field empty — confirm the client-side error appears and no request is sent (check network tab / no new message in Discord).
- [ ] **Step 9:** Record results in the progress ledger. No commit (nothing changed).

---

## Self-Review Notes

- **Spec coverage:** stateless data model (no config file) → Tasks 2-3 (`embed_builder.py`, pure functions only, no cog); button.py reuse (`btn_role_{role_id}` scheme, unmodified) → Task 3 (`build_role_button_view`/`parse_role_button_ids`); full discohook field set + single embed → Task 2 (`build_embed`/`embed_to_spec`/`validate_embed_spec`); create/edit with prefill → Tasks 4-5 (POST + GET/PUT); validation order (structural → existence → assignability, mirroring the Phase 3a fix) → Tasks 4-5, with dedicated cross-cutting regression tests in both; role-button cap of 5 → `MAX_ROLE_BUTTONS` in Task 4; tabs inside the existing `/reaction-roles` page → Task 8 (`MessageBuilderPage`); live preview → Task 8 (`EmbedPreview`). "Вне рамок" items (form-buttons, multi-embed, message history, mixing button types, scheduled sending) are correctly absent from every task.
- **Type consistency:** `EmbedSpec`/`EmbedFieldSpec` (Task 7) match `embed_builder.embed_to_spec`'s output shape (Task 2) field-for-field; `_validate_role_ids_structure`/`_validate_role_ids_assignable` (Task 4) are reused unmodified by Task 5's `PUT` handler, exactly mirroring the naming pattern Phase 3a settled on after its own validation-order fix (`_validate_pairs_structure`/`_validate_roles_assignable`); `FakeChannel.send`/`FakeMessage.edit`/`FakeComponentRow` (Task 1) are used consistently by Tasks 3, 4, and 5's tests with the same constructor signatures throughout.
- **Placeholder scan:** none found — every step has complete code.
