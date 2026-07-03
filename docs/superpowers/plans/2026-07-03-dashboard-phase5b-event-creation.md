# Phase 5b: Events/Voting — Dashboard Event Creation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let dashboard moderators create tournaments and polls from a web form, with full feature parity to the existing `/event setup` Discord builder, coexisting with it (not replacing it).

**Architecture:** `EventBuilderView.publish()`'s post-validation logic (build embed, send, build `event_obj`, save, attach participation view) gets extracted into `events_core.py` as `publish_event(bot, channel, spec, author_id)`, following the same `_core.py` pattern already used for `publish_feedback_panel`/`close_event`/`delete_event`/`notify_participants`. A new `validate_event_spec(spec)` function (matching `feedback_categories.validate_category_spec`'s error-string-return convention) replaces the Discord builder's current ad-hoc checks and gates the new `POST /api/events` route, so both paths validate identically. Frontend: one large create-event `Modal` added to the existing `Events.tsx` page.

**Tech Stack:** Python 3.12, discord.py, aiohttp (backend); React + TypeScript + Vite + Vitest (frontend). Same stack as every prior phase.

## Global Constraints

- No caching in `events.py`'s data-access layer (already true since Phase 5a).
- IDs (`channel_id`, `role_reward`) arrive as strings in the dashboard request/response boundary; `int(...)`-conversion happens only at the exact Discord API call site. Underlying `events_data.json` storage keeps native ints, matching Phase 5a's precedent — this plan does not change that storage format.
- The new route is gated by `@require_dashboard_access`.
- Validation order everywhere: structural checks first (`validate_event_spec`), Discord-existence checks second (channel/role resolve), permission last (already enforced by the decorator running before the handler body).
- Never bare `git add -A`/`git add .` — stage only the specific files each task touches.
- Never silently change a stated numeric/behavioral constant or weaken a test assertion to make it pass — if something in this plan looks wrong, flag it in the task report and fix the test's own data, not production code.
- `events.py`'s interaction-driven code (`EventBuilderView`, `TextModal`/`LimitsModal`/`OptionsModal`, `EventPublishSelect`) gets zero new pytest coverage — no `FakeInteraction` pattern exists in this project and none should be invented. Verify any change to it by careful, minimal, line-by-line diffing against the current source.
- `validate_event_spec`'s rules match exactly what the Discord builder's UI can actually produce today (e.g. `ping` only ever cycles through `none`/`everyone`/`here` in the current UI, so validation only accepts those three — not the theoretical role-id flexibility visible in `build_embed`'s unused fallback branch).
- Baseline before this plan: 276 backend (pytest) tests, 78 frontend (Vitest) tests, `tsc` clean, build clean, at commit `4812276`.

---

### Task 1: Extract `publish_event`/`validate_event_spec` into `events_core.py`, refactor the Discord builder to use them

**Files:**
- Modify: `events_core.py` (add `publish_event`, `validate_event_spec`)
- Modify: `events.py:175-185` (`EventPublishSelect.callback`)
- Modify: `events.py:309-381` (`EventBuilderView.publish`)
- Test: Create `dashboard/backend/tests/test_events_core_publish.py`

**Interfaces:**
- Consumes: `events.load_events`/`events.save_events`/`events.create_participation_view` (existing, from Phases 1 and 5a).
- Produces:
  - `def validate_event_spec(spec: dict) -> str | None` — returns an error code string or `None`. This is what Task 2's route calls, and what `EventPublishSelect.callback` also calls.
  - `async def publish_event(bot, channel, spec: dict, author_id: int) -> discord.Message` — `channel` must already be a resolved, sendable channel object (callers resolve it themselves — this function does not do the `get_channel`/`fetch_channel` fallback dance, since that's specific to `ChannelSelect`'s quirk on the Discord side and the dashboard route resolves its channel differently). `spec` keys: `type`, `title`, `description`, `banner_url`, `mode`, `require_info`, `max_limit`, `team_size`, `role_reward`, `ping`, `options`, `multi_select`.

This is the highest-risk task in this plan: `events.py` is interaction-driven Discord bot code with zero pytest coverage. Read `events.py` in full first — you need its exact current content to make a precise, minimal diff.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/backend/tests/test_events_core_publish.py`:

```python
import discord
import pytest

import events
import events_core
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild


@pytest.fixture(autouse=True)
def isolated_events_file(tmp_path, monkeypatch):
    monkeypatch.setattr(events, "EVENTS_FILE", str(tmp_path / "events_data.json"))


def _tournament_spec(**overrides):
    spec = {
        "type": "tournament",
        "title": "Летний турнир",
        "description": "Описание турнира",
        "banner_url": "",
        "mode": "solo",
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "ping": "none",
        "options": [],
        "multi_select": False,
    }
    spec.update(overrides)
    return spec


def _poll_spec(**overrides):
    spec = {
        "type": "poll",
        "title": "Опрос дня",
        "description": "Описание опроса",
        "banner_url": "",
        "mode": "solo",
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "ping": "none",
        "options": ["Да", "Нет"],
        "multi_select": False,
    }
    spec.update(overrides)
    return spec


# --- validate_event_spec ---


def test_validate_event_spec_rejects_invalid_type():
    assert events_core.validate_event_spec(_tournament_spec(type="bogus")) == "invalid_type"


def test_validate_event_spec_rejects_empty_title():
    assert events_core.validate_event_spec(_tournament_spec(title="")) == "invalid_title"


def test_validate_event_spec_rejects_title_too_long():
    assert events_core.validate_event_spec(_tournament_spec(title="x" * 101)) == "invalid_title"


def test_validate_event_spec_rejects_empty_description():
    assert events_core.validate_event_spec(_tournament_spec(description="")) == "invalid_description"


def test_validate_event_spec_rejects_description_too_long():
    assert events_core.validate_event_spec(_tournament_spec(description="x" * 2001)) == "invalid_description"


def test_validate_event_spec_rejects_invalid_ping():
    assert events_core.validate_event_spec(_tournament_spec(ping="role:123")) == "invalid_ping"


def test_validate_event_spec_rejects_invalid_mode_for_tournament():
    assert events_core.validate_event_spec(_tournament_spec(mode="bogus")) == "invalid_mode"


def test_validate_event_spec_rejects_negative_max_limit():
    assert events_core.validate_event_spec(_tournament_spec(max_limit=-1)) == "invalid_max_limit"


def test_validate_event_spec_rejects_team_size_below_2_when_not_solo():
    spec = _tournament_spec(mode="team_captain", team_size=1)
    assert events_core.validate_event_spec(spec) == "invalid_team_size"


def test_validate_event_spec_allows_missing_team_size_check_for_solo_mode():
    spec = _tournament_spec(mode="solo", team_size=1)
    assert events_core.validate_event_spec(spec) is None


def test_validate_event_spec_rejects_poll_with_too_few_options():
    assert events_core.validate_event_spec(_poll_spec(options=["Только один"])) == "invalid_options"


def test_validate_event_spec_rejects_poll_with_non_list_options():
    assert events_core.validate_event_spec(_poll_spec(options="Да, Нет")) == "invalid_options"


def test_validate_event_spec_accepts_valid_tournament_spec():
    assert events_core.validate_event_spec(_tournament_spec()) is None


def test_validate_event_spec_accepts_valid_poll_spec():
    assert events_core.validate_event_spec(_poll_spec()) is None


# --- publish_event ---


@pytest.mark.asyncio
async def test_publish_event_tournament_creates_matching_event_obj_and_view():
    channel = FakeChannel(500, name="tourneys")
    bot = FakeBot(FakeGuild())
    spec = _tournament_spec(max_limit=10, role_reward="200")

    message = await events_core.publish_event(bot, channel, spec, author_id=1)

    data = await events.load_events()
    ev = data["events"][str(message.id)]
    assert ev["type"] == "tournament"
    assert ev["channel_id"] == 500
    assert ev["author_id"] == 1
    assert ev["title"] == "Летний турнир"
    assert ev["mode"] == "solo"
    assert ev["max_limit"] == 10
    assert ev["role_reward"] == 200
    assert ev["status"] == "open"
    assert ev["participants"] == []
    assert ev["votes"] == {}
    assert len(channel.send_calls) == 1
    assert channel.send_calls[0]["embed"].title == "Летний турнир"
    sent_message = channel._messages[message.id]
    assert len(sent_message.edit_calls) == 1
    assert sent_message.edit_calls[0]["view"] is not None


@pytest.mark.asyncio
async def test_publish_event_poll_creates_matching_event_obj_and_view():
    channel = FakeChannel(500, name="polls")
    bot = FakeBot(FakeGuild())
    spec = _poll_spec(multi_select=True)

    message = await events_core.publish_event(bot, channel, spec, author_id=1)

    data = await events.load_events()
    ev = data["events"][str(message.id)]
    assert ev["type"] == "poll"
    assert ev["options"] == ["Да", "Нет"]
    assert ev["multi_select"] is True
    assert ev["votes"] == {}
    assert len(channel.send_calls) == 1


@pytest.mark.asyncio
async def test_publish_event_role_reward_none_stays_none():
    channel = FakeChannel(500, name="tourneys")
    bot = FakeBot(FakeGuild())
    spec = _tournament_spec(role_reward=None)

    message = await events_core.publish_event(bot, channel, spec, author_id=1)

    data = await events.load_events()
    assert data["events"][str(message.id)]["role_reward"] is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_events_core_publish.py -v`
Expected: all FAIL with `AttributeError: module 'events_core' has no attribute 'validate_event_spec'` (or `'publish_event'`).

- [ ] **Step 3: Add `validate_event_spec` and `publish_event` to `events_core.py`**

Append to `events_core.py` (after `notify_participants`, at the end of the file):

```python
def validate_event_spec(spec: dict) -> str | None:
    if spec.get("type") not in ("tournament", "poll"):
        return "invalid_type"

    title = spec.get("title", "")
    if not title or len(title) > 100:
        return "invalid_title"

    description = spec.get("description", "")
    if not description or len(description) > 2000:
        return "invalid_description"

    if spec.get("ping", "none") not in ("none", "everyone", "here"):
        return "invalid_ping"

    if spec["type"] == "tournament":
        if spec.get("mode") not in ("solo", "team_captain", "team_code"):
            return "invalid_mode"
        max_limit = spec.get("max_limit", 0)
        if not isinstance(max_limit, int) or max_limit < 0:
            return "invalid_max_limit"
        if spec.get("mode") != "solo":
            team_size = spec.get("team_size", 5)
            if not isinstance(team_size, int) or team_size < 2:
                return "invalid_team_size"
    else:
        options = spec.get("options")
        if (
            not isinstance(options, list)
            or not (2 <= len(options) <= 10)
            or not all(isinstance(o, str) and o.strip() for o in options)
        ):
            return "invalid_options"

    return None


async def publish_event(bot, channel, spec: dict, author_id: int) -> discord.Message:
    emb = discord.Embed(
        title=spec["title"],
        description=spec["description"],
        color=discord.Color.brand_red() if spec["type"] == "tournament" else discord.Color.blurple(),
    )
    banner_url = spec.get("banner_url") or ""
    if banner_url:
        emb.set_image(url=banner_url)

    if spec["type"] == "tournament":
        mode_str = {"solo": "Соло", "team_captain": "Командный", "team_code": "Командный (по коду)"}.get(
            spec.get("mode", "solo")
        )
        emb.add_field(name="Формат", value=mode_str, inline=True)
        max_limit = spec.get("max_limit", 0)
        if max_limit > 0:
            emb.add_field(name="Лимит", value=f"0 / {max_limit}", inline=True)
        else:
            emb.add_field(name="Участники", value="0", inline=True)
    else:
        for opt in spec.get("options", []):
            emb.add_field(name=opt, value="░░░░░░░░░░ 0% (0 гол.)", inline=False)

    emb.set_footer(text="🟢 Статус: Открыто")

    ping = spec.get("ping", "none")
    content = None
    if ping == "everyone":
        content = "@everyone"
    elif ping == "here":
        content = "@here"

    msg = await channel.send(content=content, embed=emb)

    role_reward_raw = spec.get("role_reward")
    event_obj = {
        "type": spec["type"],
        "channel_id": channel.id,
        "author_id": author_id,
        "title": spec["title"],
        "description": spec["description"],
        "banner_url": banner_url,
        "mode": spec.get("mode", "solo"),
        "require_info": spec.get("require_info", False),
        "max_limit": spec.get("max_limit", 0),
        "team_size": spec.get("team_size", 5),
        "role_reward": int(role_reward_raw) if role_reward_raw else None,
        "ping": ping,
        "status": "open",
        "participants": [],
        "options": spec.get("options", []),
        "multi_select": spec.get("multi_select", False),
        "votes": {},
    }

    data = await events.load_events()
    data["events"][str(msg.id)] = event_obj
    await events.save_events(data)

    view = events.create_participation_view(str(msg.id), event_obj)
    await msg.edit(view=view)

    return msg
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_events_core_publish.py -v`
Expected: all 17 pass.

- [ ] **Step 5: Refactor `EventBuilderView.publish` to call `publish_event`**

Read `events.py` in full first to confirm it still matches. Replace the current `publish` method body (currently lines 309-381) with:

```python
    async def publish(self, interaction: discord.Interaction, channel: discord.TextChannel):
        d = self.draft

        # ChannelSelect возвращает AppCommandChannel, у которого нет .send()
        # Нужно получить полный объект TextChannel
        resolved_channel = self.bot.get_channel(channel.id)
        if not resolved_channel:
            try:
                resolved_channel = await self.bot.fetch_channel(channel.id)
            except Exception:
                await interaction.edit_original_response(content="❌ Не удалось получить доступ к выбранному каналу.")
                return

        spec = {
            "type": d.type,
            "title": d.title,
            "description": d.description,
            "banner_url": d.banner_url,
            "mode": d.mode,
            "require_info": d.require_info,
            "max_limit": d.max_limit,
            "team_size": d.team_size,
            "role_reward": d.role_reward,
            "ping": d.ping,
            "options": d.options,
            "multi_select": d.multi_select,
        }
        msg = await events_core.publish_event(self.bot, resolved_channel, spec, author_id=d.author_id)

        self.clear_items()
        await interaction.edit_original_response(
            content=f"✅ Успешно опубликовано в {resolved_channel.mention}!\nID сообщения: `{msg.id}`",
            embed=None,
            view=None,
        )
```

This preserves the exact existing channel-resolution fallback and exact existing success message — only the embed-building/storage/view-attachment part (now inside `publish_event`) moved out.

- [ ] **Step 6: Refactor `EventPublishSelect.callback` to call `validate_event_spec`**

Replace the current `callback` method body (currently lines 175-185) with:

```python
    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        draft = self.builder_view.draft
        spec = {
            "type": draft.type,
            "title": draft.title,
            "description": draft.description,
            "banner_url": draft.banner_url,
            "mode": draft.mode,
            "require_info": draft.require_info,
            "max_limit": draft.max_limit,
            "team_size": draft.team_size,
            "role_reward": draft.role_reward,
            "ping": draft.ping,
            "options": draft.options,
            "multi_select": draft.multi_select,
        }
        error = events_core.validate_event_spec(spec)
        if error:
            await interaction.response.send_message(
                "❌ Проверьте настройки события (название, описание, варианты и т.д.) — что-то заполнено некорректно.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        await self.builder_view.publish(interaction, channel)
```

This replaces the two original ad-hoc checks (`if not title or not description`, `if poll and not options`) with the single shared `validate_event_spec` call — a deliberate strictness upgrade (adds the bounds the modals already enforce per-field but publish-time never double-checked), and guarantees the Discord and dashboard paths validate identically.

`events.py` already has `import events_core` at the top of the file (added in Phase 5a) — no new import needed.

- [ ] **Step 7: Verify `events.py` still imports cleanly**

Run: `python -c "import events"`
Expected: exits cleanly, no output.

- [ ] **Step 8: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `293 passed` (276 baseline + 17 new).

- [ ] **Step 9: Commit**

```bash
git add events_core.py events.py dashboard/backend/tests/test_events_core_publish.py
git commit -m "refactor: extract publish_event/validate_event_spec into events_core.py"
```

---

### Task 2: `POST /api/events` route

**Files:**
- Modify: `dashboard/backend/routes/events.py` (append; no `app.py` changes needed — this route table is already registered)
- Test: Modify `dashboard/backend/tests/test_events_routes.py` (append)

**Interfaces:**
- Consumes: `events_core.validate_event_spec`, `events_core.publish_event` (Task 1), `serialize_event_detail` (existing, from Phase 5a's own `dashboard/backend/routes/events.py`).
- Produces: `POST /api/events` — request body matches `validate_event_spec`'s expected shape plus `channel_id: string`; response `serialize_event_detail(message_id, ev)` with status `201` on success. Errors: `invalid_request` (400, malformed JSON/non-dict body/non-numeric `channel_id` or `role_reward`), whatever code `validate_event_spec` returns (400), `channel_not_found` (404), `role_not_found` (404), `service_unavailable` (503, no guild).

- [ ] **Step 1: Write the failing tests**

Append to `dashboard/backend/tests/test_events_routes.py` (add these two helper functions near the file's existing `_tournament_event`/`_poll_event`/`build` helpers, and the tests at the end of the file):

```python
def _tournament_create_spec(channel_id="500", **overrides):
    spec = {
        "channel_id": channel_id,
        "type": "tournament",
        "title": "Летний турнир",
        "description": "Описание",
        "banner_url": "",
        "ping": "none",
        "mode": "solo",
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "options": [],
        "multi_select": False,
    }
    spec.update(overrides)
    return spec


def _poll_create_spec(channel_id="500", **overrides):
    spec = {
        "channel_id": channel_id,
        "type": "poll",
        "title": "Опрос дня",
        "description": "Описание",
        "banner_url": "",
        "ping": "none",
        "mode": "solo",
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "options": ["Да", "Нет"],
        "multi_select": False,
    }
    spec.update(overrides)
    return spec


@pytest.mark.asyncio
async def test_create_event_tournament_success(aiohttp_client):
    channel = FakeChannel(500, name="tourneys")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_tournament_create_spec())
    assert resp.status == 201
    body = await resp.json()
    assert body["type"] == "tournament"
    assert body["title"] == "Летний турнир"
    assert len(channel.send_calls) == 1


@pytest.mark.asyncio
async def test_create_event_poll_success(aiohttp_client):
    channel = FakeChannel(500, name="polls")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_poll_create_spec())
    assert resp.status == 201
    body = await resp.json()
    assert body["type"] == "poll"
    assert body["options"] == [
        {"label": "Да", "votes": 0, "percent": 0},
        {"label": "Нет", "votes": 0, "percent": 0},
    ]


@pytest.mark.asyncio
async def test_create_event_checks_structure_before_channel_existence(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_tournament_create_spec(title=""))
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_title"


@pytest.mark.asyncio
async def test_create_event_404_when_channel_missing(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_tournament_create_spec())
    assert resp.status == 404
    assert (await resp.json())["error"] == "channel_not_found"


@pytest.mark.asyncio
async def test_create_event_404_when_role_reward_missing(aiohttp_client):
    channel = FakeChannel(500, name="tourneys")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_tournament_create_spec(role_reward="999"))
    assert resp.status == 404
    assert (await resp.json())["error"] == "role_not_found"


@pytest.mark.asyncio
async def test_create_event_rejects_non_numeric_role_reward(aiohttp_client):
    channel = FakeChannel(500, name="tourneys")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_tournament_create_spec(role_reward="not-a-number"))
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_create_event_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/events", json=_tournament_create_spec())
    assert resp.status == 401


@pytest.mark.asyncio
async def test_create_event_round_trips_via_get_detail(aiohttp_client):
    channel = FakeChannel(500, name="tourneys")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    create_resp = await client.post("/api/events", json=_tournament_create_spec())
    message_id = (await create_resp.json())["message_id"]

    get_resp = await client.get(f"/api/events/{message_id}")
    assert get_resp.status == 200
    assert (await get_resp.json())["title"] == "Летний турнир"
```

Note: `build()` in this test file constructs a guild+app with the moderator only (no channels/roles) unless you pass `channels=`/`roles=` — check the existing `build()` helper's signature at the top of `test_events_routes.py` before assuming its exact parameter names; adjust the calls above only if the existing signature differs (it should already accept `channels=` per Phase 5a's Task 3, since these tests build on that same helper).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_events_routes.py -v -k create_event`
Expected: all FAIL with 404 (route doesn't exist yet — aiohttp returns 404 for unmatched routes).

- [ ] **Step 3: Add the route**

Append to `dashboard/backend/routes/events.py` (at the end of the file):

```python
@routes.post("/api/events")
@require_dashboard_access
async def create_event(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request.app["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    error = events_core.validate_event_spec(body)
    if error:
        return web.json_response({"error": error}, status=400)

    channel_id_raw = body.get("channel_id")
    try:
        channel_id = int(channel_id_raw)
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)
    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    role_reward_raw = body.get("role_reward")
    if role_reward_raw:
        try:
            role_id = int(role_reward_raw)
        except (TypeError, ValueError):
            return web.json_response({"error": "invalid_request"}, status=400)
        if guild.get_role(role_id) is None:
            return web.json_response({"error": "role_not_found"}, status=404)

    moderator = request["moderator"]
    message = await events_core.publish_event(bot, channel, body, author_id=moderator.id)

    data = await events.load_events()
    ev = data["events"][str(message.id)]
    return web.json_response(serialize_event_detail(str(message.id), ev), status=201)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_events_routes.py -v`
Expected: all pass (27 existing from Phase 5a + 8 new = 35 in this file).

- [ ] **Step 5: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `301 passed` (293 from Task 1 + 8 new).

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/events.py dashboard/backend/tests/test_events_routes.py
git commit -m "feat(dashboard): add POST /api/events route"
```

---

### Task 3: Frontend API client

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts` (append)
- Test: Modify `dashboard/frontend/src/api/events.test.ts` (append)

**Interfaces:**
- Consumes: `apiFetch<T>`, `jsonInit` (existing helpers), `EventDetail` (Phase 5a's existing type).
- Produces:
  - `export interface CreateEventSpec { channel_id: string; type: 'tournament' | 'poll'; title: string; description: string; banner_url: string; ping: 'none' | 'everyone' | 'here'; mode: 'solo' | 'team_captain' | 'team_code'; require_info: boolean; max_limit: number; team_size: number; role_reward: string | null; options: string[]; multi_select: boolean }`
  - `export function createEvent(spec: CreateEventSpec): Promise<EventDetail>`

- [ ] **Step 1: Write the failing tests**

Append to `dashboard/frontend/src/api/events.test.ts` (inside the existing `describe('events API client', ...)` block, or as a new top-level `describe` block if the existing file structures tests that way — check the file's current structure first):

```typescript
it('createEvent POSTs the full spec and returns the created event', async () => {
  const spec: client.CreateEventSpec = {
    channel_id: '500',
    type: 'tournament',
    title: 'Летний турнир',
    description: 'desc',
    banner_url: '',
    ping: 'none',
    mode: 'solo',
    require_info: false,
    max_limit: 0,
    team_size: 5,
    role_reward: null,
    options: [],
    multi_select: false,
  }
  const created = { message_id: '900', type: 'tournament', title: 'Летний турнир', status: 'open', channel_id: '500', count: 0, description: 'desc', role_reward: null }
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(created, 201))

  const result = await client.createEvent(spec)

  const [url, init] = fetchMock.mock.calls[0]
  expect(url).toBe('/api/events')
  expect(init?.method).toBe('POST')
  expect(JSON.parse(init?.body as string)).toEqual(spec)
  expect(result).toEqual(created)
})

it('createEvent sends poll-shaped specs unchanged', async () => {
  const spec: client.CreateEventSpec = {
    channel_id: '500',
    type: 'poll',
    title: 'Опрос дня',
    description: 'desc',
    banner_url: '',
    ping: 'none',
    mode: 'solo',
    require_info: false,
    max_limit: 0,
    team_size: 5,
    role_reward: null,
    options: ['Да', 'Нет'],
    multi_select: true,
  }
  const created = { message_id: '901', type: 'poll', title: 'Опрос дня', status: 'open', channel_id: '500', count: 0, description: 'desc', role_reward: null }
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(created, 201))

  await client.createEvent(spec)

  const [, init] = fetchMock.mock.calls[0]
  expect(JSON.parse(init?.body as string).options).toEqual(['Да', 'Нет'])
})
```

If `dashboard/frontend/src/api/events.test.ts` doesn't already have a local `jsonResponse` helper (check the top of the file — Phase 5a's Task 5 added one), add:

```typescript
function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status })
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `dashboard/frontend/`): `npm run test -- events.test`
Expected: FAIL — `createEvent` and `CreateEventSpec` are not exported from `./client` yet.

- [ ] **Step 3: Add the type and function**

Append to `dashboard/frontend/src/api/client.ts` (at the end of the file):

```typescript
export interface CreateEventSpec {
  channel_id: string
  type: 'tournament' | 'poll'
  title: string
  description: string
  banner_url: string
  ping: 'none' | 'everyone' | 'here'
  mode: 'solo' | 'team_captain' | 'team_code'
  require_info: boolean
  max_limit: number
  team_size: number
  role_reward: string | null
  options: string[]
  multi_select: boolean
}

export function createEvent(spec: CreateEventSpec): Promise<EventDetail> {
  return apiFetch('/api/events', jsonInit('POST', spec))
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm run test -- events.test`
Expected: PASS.

- [ ] **Step 5: Run the full frontend suite and typecheck**

Run: `npm run test` then `npx tsc --noEmit`
Expected: `80 passed` (78 baseline + 2 new), `tsc` clean.

- [ ] **Step 6: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/events.test.ts
git commit -m "feat(dashboard): add createEvent API client function"
```

---

### Task 4: Frontend UI — event creation form

**Files:**
- Modify: `dashboard/frontend/src/pages/Events.tsx`
- Modify: `dashboard/frontend/src/pages/Events.test.tsx` (append)

**Interfaces:**
- Consumes: `createEvent`, `CreateEventSpec` (Task 3), `fetchChannels`, `fetchRoles`, `ChannelInfo`, `RoleInfo` (existing, already used by `FeedbackCategories.tsx`), existing `Modal`/`Button`/`Card` components, `EventsPage`'s own existing `status`/`events`/`selectedId`/`error`/`reload` state (Phase 5a).
- Produces: no new exports — purely additive to `EventsPage`.

Read `dashboard/frontend/src/pages/Events.tsx` in full first — you need its exact current content (from Phase 5a) to add the create form without disturbing the existing list/filter/detail-panel code.

- [ ] **Step 1: Write the failing tests**

Read `dashboard/frontend/src/pages/Events.test.tsx` in full first to see its existing imports/patterns. Append these tests at the end of the file (add a second `describe` block, or extend the existing one — match whichever the file already uses):

```typescript
describe('EventsPage create flow', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('creates a tournament event', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'tourneys' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '200', name: 'Winner', color: '#000000', position: 1 }])
    const createSpy = vi.spyOn(client, 'createEvent').mockResolvedValue({
      message_id: '900',
      type: 'tournament',
      title: 'Летний турнир',
      status: 'open',
      channel_id: '500',
      count: 0,
      description: 'desc',
      role_reward: null,
    })

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByLabelText('Название'))
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'Летний турнир' } })
    fireEvent.change(screen.getByLabelText('Описание'), { target: { value: 'desc' } })
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })

    fireEvent.click(screen.getByRole('button', { name: 'Создать' }))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'tournament', title: 'Летний турнир', channel_id: '500' }),
      ),
    )
  })

  it('creates a poll event with newline-separated options parsed into an array', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'polls' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createEvent').mockResolvedValue({
      message_id: '901',
      type: 'poll',
      title: 'Опрос',
      status: 'open',
      channel_id: '500',
      count: 0,
      description: 'desc',
      role_reward: null,
    })

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByText('Опрос'))
    fireEvent.click(screen.getByText('Опрос'))

    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'Опрос' } })
    fireEvent.change(screen.getByLabelText('Описание'), { target: { value: 'desc' } })
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })
    fireEvent.change(screen.getByLabelText('Варианты ответа (каждый с новой строки, 2–10)'), {
      target: { value: 'Да\nНет' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Создать' }))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith(expect.objectContaining({ type: 'poll', options: ['Да', 'Нет'] })),
    )
  })

  it('toggles between tournament and poll sections', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByLabelText('Формат'))
    expect(screen.queryByLabelText('Варианты ответа (каждый с новой строки, 2–10)')).not.toBeInTheDocument()

    fireEvent.click(screen.getByText('Опрос'))

    await waitFor(() => screen.getByLabelText('Варианты ответа (каждый с новой строки, 2–10)'))
    expect(screen.queryByLabelText('Формат')).not.toBeInTheDocument()
  })

  it('shows an error when creation fails', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'tourneys' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'createEvent').mockRejectedValue(new Error('boom'))

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByLabelText('Название'))
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'T' } })
    fireEvent.change(screen.getByLabelText('Описание'), { target: { value: 'd' } })
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })

    fireEvent.click(screen.getByRole('button', { name: 'Создать' }))

    await waitFor(() => screen.getByText('Не удалось создать событие — проверьте поля'))
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm run test -- Events`
Expected: the 4 new tests FAIL — no "Создать событие" button exists yet.

- [ ] **Step 3: Add the create form to `Events.tsx`**

Add these imports to the top of `dashboard/frontend/src/pages/Events.tsx` (merge with the existing `import { ... } from '../api/client'` line rather than duplicating it — add `createEvent`, `fetchChannels`, `fetchRoles`, `type ChannelInfo`, `type CreateEventSpec`, `type RoleInfo` to the existing import list):

```typescript
import { Modal } from '../components/ui/Modal'
```

Add this helper function above the `EventsPage` component:

```typescript
function emptyCreateSpec(): CreateEventSpec {
  return {
    channel_id: '',
    type: 'tournament',
    title: '',
    description: '',
    banner_url: '',
    ping: 'none',
    mode: 'solo',
    require_info: false,
    max_limit: 0,
    team_size: 5,
    role_reward: null,
    options: [],
    multi_select: false,
  }
}
```

Inside `EventsPage`, add this state (alongside the existing `status`/`events`/`selectedId`/`error` state):

```typescript
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [createOpen, setCreateOpen] = useState(false)
  const [createSpec, setCreateSpec] = useState<CreateEventSpec>(emptyCreateSpec())
  const [optionsText, setOptionsText] = useState('')
  const [createError, setCreateError] = useState('')
  const [createBusy, setCreateBusy] = useState(false)
```

Change the existing `reload` function to also fetch channels/roles:

```typescript
  const reload = () => {
    fetchEvents(status)
      .then(setEvents)
      .catch(() => setError('Не удалось загрузить события'))
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
  }
```

Add these handlers (after `reload`, before the `return`):

```typescript
  const openCreate = () => {
    setCreateSpec(emptyCreateSpec())
    setOptionsText('')
    setCreateError('')
    setCreateOpen(true)
  }

  const saveCreate = async () => {
    setCreateBusy(true)
    setCreateError('')
    try {
      const spec: CreateEventSpec = {
        ...createSpec,
        options: optionsText
          .split('\n')
          .map((line) => line.trim())
          .filter(Boolean),
      }
      await createEvent(spec)
      setCreateOpen(false)
      reload()
    } catch {
      setCreateError('Не удалось создать событие — проверьте поля')
    } finally {
      setCreateBusy(false)
    }
  }
```

Add a "Создать событие" button to the existing header row (find the `<div className="mb-4 flex items-center gap-3">` block and add the button, e.g. right after the `<h1>`):

```tsx
          <Button variant="primary" onClick={openCreate} className="ml-auto">
            Создать событие
          </Button>
```

(If the header row already has an `ml-auto` on the status `<select>`'s `<label>`, move that `ml-auto` off the label and onto this new button instead, so the button is the one pushed to the right — check the current JSX before editing.)

Add the create-event `Modal` as the last element before the closing `</div>` at the end of the component's return, after the existing `{selectedId && (...)}` block:

```tsx
      <Modal open={createOpen} title="Создать событие" onClose={() => setCreateOpen(false)}>
        <div className="flex max-h-[70vh] flex-col gap-3 overflow-y-auto">
          <div className="flex gap-2">
            <Button
              variant={createSpec.type === 'tournament' ? 'primary' : 'secondary'}
              onClick={() => setCreateSpec((prev) => ({ ...prev, type: 'tournament' }))}
            >
              Турнир
            </Button>
            <Button
              variant={createSpec.type === 'poll' ? 'primary' : 'secondary'}
              onClick={() => setCreateSpec((prev) => ({ ...prev, type: 'poll' }))}
            >
              Опрос
            </Button>
          </div>

          <label className="text-sm text-muted" htmlFor="event-title">
            Название
          </label>
          <input
            id="event-title"
            value={createSpec.title}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="event-description">
            Описание
          </label>
          <textarea
            id="event-description"
            value={createSpec.description}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, description: e.target.value }))}
            rows={3}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="event-banner">
            URL баннера (опционально)
          </label>
          <input
            id="event-banner"
            value={createSpec.banner_url}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, banner_url: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="event-ping">
            Пинг
          </label>
          <select
            id="event-ping"
            value={createSpec.ping}
            onChange={(e) =>
              setCreateSpec((prev) => ({ ...prev, ping: e.target.value as CreateEventSpec['ping'] }))
            }
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="none">Нет</option>
            <option value="everyone">@everyone</option>
            <option value="here">@here</option>
          </select>

          <label className="text-sm text-muted" htmlFor="event-channel">
            Канал
          </label>
          <select
            id="event-channel"
            value={createSpec.channel_id}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, channel_id: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="">Выберите канал…</option>
            {channels.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          {createSpec.type === 'tournament' ? (
            <>
              <label className="text-sm text-muted" htmlFor="event-mode">
                Формат
              </label>
              <select
                id="event-mode"
                value={createSpec.mode}
                onChange={(e) =>
                  setCreateSpec((prev) => ({ ...prev, mode: e.target.value as CreateEventSpec['mode'] }))
                }
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
              >
                <option value="solo">Соло</option>
                <option value="team_captain">Командный (Капитан)</option>
                <option value="team_code">Командный (По коду)</option>
              </select>

              <label className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  checked={createSpec.require_info}
                  onChange={(e) => setCreateSpec((prev) => ({ ...prev, require_info: e.target.checked }))}
                />
                Анкета (запрашивать игровой ник)
              </label>

              <label className="text-sm text-muted" htmlFor="event-max-limit">
                Макс. участников/команд (0 = безлимит)
              </label>
              <input
                id="event-max-limit"
                type="number"
                min={0}
                value={createSpec.max_limit}
                onChange={(e) => setCreateSpec((prev) => ({ ...prev, max_limit: Number(e.target.value) }))}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />

              {createSpec.mode !== 'solo' && (
                <>
                  <label className="text-sm text-muted" htmlFor="event-team-size">
                    Размер команды
                  </label>
                  <input
                    id="event-team-size"
                    type="number"
                    min={2}
                    value={createSpec.team_size}
                    onChange={(e) => setCreateSpec((prev) => ({ ...prev, team_size: Number(e.target.value) }))}
                    className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                  />
                </>
              )}

              <label className="text-sm text-muted" htmlFor="event-role-reward">
                Выдаваемая роль (опционально)
              </label>
              <select
                id="event-role-reward"
                value={createSpec.role_reward ?? ''}
                onChange={(e) => setCreateSpec((prev) => ({ ...prev, role_reward: e.target.value || null }))}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
              >
                <option value="">Без роли</option>
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </>
          ) : (
            <>
              <label className="text-sm text-muted" htmlFor="event-options">
                Варианты ответа (каждый с новой строки, 2–10)
              </label>
              <textarea
                id="event-options"
                value={optionsText}
                onChange={(e) => setOptionsText(e.target.value)}
                rows={4}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />

              <label className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  checked={createSpec.multi_select}
                  onChange={(e) => setCreateSpec((prev) => ({ ...prev, multi_select: e.target.checked }))}
                />
                Мульти-выбор
              </label>
            </>
          )}

          {createError && <p className="text-sm text-danger">{createError}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setCreateOpen(false)} disabled={createBusy}>
              Отмена
            </Button>
            <Button variant="primary" onClick={saveCreate} disabled={createBusy}>
              {createBusy ? 'Создаём…' : 'Создать'}
            </Button>
          </div>
        </div>
      </Modal>
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm run test -- Events`
Expected: all pass, including the 4 new create-flow tests.

- [ ] **Step 5: Run the full frontend suite, typecheck, and build**

Run: `npm run test` then `npx tsc --noEmit` then `npm run build`
Expected: `84 passed` (80 from Task 3 + 4 new), `tsc` clean, build clean.

- [ ] **Step 6: Commit**

```bash
git add dashboard/frontend/src/pages/Events.tsx dashboard/frontend/src/pages/Events.test.tsx
git commit -m "feat(dashboard): add event creation form to Events page"
```

---

### Task 5: Manual E2E verification (user-performed, not a subagent task)

Not automatable — requires a live Discord test server. Steps for the user:

1. Restart the backend and frontend dev servers (done by the assistant before handoff, per standing project convention).
2. On the Events page, click "Создать событие", create a tournament with `mode=team_code`, a role reward, and a participant limit — confirm it appears in Discord with the expected embed fields and functioning registration buttons (create-team/join-code/leave/list), matching what `/event setup` would produce for the same configuration.
3. Create a poll with 3 options and multi-select enabled — confirm the vote buttons work and percentages update, matching what `/event setup` produces.
4. Confirm both newly-created events immediately appear correctly in the Phase 5a events list/detail panel (proving the created `event_obj` shape is genuinely compatible with the existing view/management code, not just superficially similar).
5. Confirm `/event setup` still works unchanged, for parity — build and publish an event through the Discord flow and confirm it behaves identically to before this phase.
6. Try submitting the dashboard form with invalid data (e.g. a poll with only 1 option, or team_captain mode with team_size 1) and confirm a clear rejection happens client-side or via the API, never a broken/partial event getting created.

---

## Self-Review Notes

- **Spec coverage:** the spec's extraction section maps to Task 1, the API section maps to Task 2, the frontend section maps to Tasks 3-4, and the testing section's specific call-outs (`validate_event_spec` structural coverage, `publish_event`'s cross-phase contract with Phase 5a's serializers, the Discord builder's zero-new-coverage convention, the route's structural-then-existence order, the frontend type-toggle and query-collision discipline) are each addressed by name in the corresponding task.
- **Placeholder scan:** none found — every step has complete code.
- **Type/name consistency:** `events_core.validate_event_spec(spec)` / `publish_event(bot, channel, spec, author_id)` are defined once in Task 1 and consumed with identical signatures in Task 1's own refactored `EventPublishSelect.callback`/`EventBuilderView.publish` and Task 2's route. `CreateEventSpec` (Task 3) is consumed identically by `Events.tsx` (Task 4). Test count progression double-checked by direct arithmetic: 276 → 293 (Task 1, +17) → 301 (Task 2, +8) backend; 78 → 80 (Task 3, +2) → 84 (Task 4, +4) frontend.
- **Cross-task risk caught during planning:** `publish_event`'s created `event_obj` must exactly match the shape Phase 5a's `serialize_event_summary`/`serialize_event_detail`/`_serialize_participants`/`_serialize_poll_options` already expect to read (same key names: `type`, `channel_id`, `mode`, `max_limit`, `role_reward`, `options`, `votes`, etc.) — Task 1's own tests assert on this dict directly rather than just trusting it compiles, and Task 5's manual E2E step 4 explicitly re-verifies this cross-phase contract holds for real, live-Discord-created events, not just fixture data.
- **Cross-task risk caught during planning (test-query discipline):** `Events.tsx`'s create-modal title ("Создать событие") duplicates its own trigger button's text — this exact pattern already shipped safely in `FeedbackCategories.tsx` (Phase 4b: "Создать категорию" trigger + modal title), since all of this plan's tests query "Создать событие" only once, before the modal opens, and never re-query it after — matching that established, working precedent rather than needing new disambiguation machinery.
