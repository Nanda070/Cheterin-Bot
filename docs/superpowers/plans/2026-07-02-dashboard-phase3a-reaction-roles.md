# Дашборд, Фаза 3a (Reaction Roles) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **NOTE FROM CONTROLLER:** This plan was written but execution was explicitly deferred by the user ("составь план, но не начинай его"). Do not begin Task 1 until the user asks to proceed.

**Goal:** Let staff assign a role to members via emoji reactions on an existing Discord message, configured entirely through the dashboard, with the bot enforcing the mapping live.

**Architecture:** A new repo-root module `reaction_roles.py` holds a JSON-backed config (keyed by `message_id`) and both the pure data helpers and the discord.py cog (`on_raw_reaction_add`/`on_raw_reaction_remove`) — mirroring the `lockdown.py`/`lockdown_core.py` split, except here core logic and the cog live in one file per the approved spec. A new `dashboard/backend/routes/reaction_roles.py` route table (imports the repo-root module the same way `dashboard/backend/routes/lockdown.py` imports `lockdown_core`) exposes CRUD + supporting-data endpoints, reusing `require_dashboard_access` and the existing `GET /api/roles`. Frontend adds one list page + one create/edit form, reusing the design system and the `MassAssignModal`-style per-row-add pattern.

**Tech Stack:** Python: discord.py, aiohttp, pytest + pytest-aiohttp (existing fakes, extended). Frontend: React + TypeScript, existing `Modal`/`Button`/`Card` primitives, Vitest + Testing Library.

## Global Constraints

- All work happens in `C:\Users\adnan\Documents\coding\ChetMain_backup_20260701_211729`. Never touch `C:\Users\adnan\Documents\coding\ChetMain`.
- Local-only git repo: commit each task with `git add <specific files>` + `git commit` — never bare `git add -A`.
- Spec of record: `docs/superpowers/specs/2026-07-02-dashboard-phase3a-reaction-roles-design.md`.
- One reaction-role entry per `message_id` (natural primary key); a message may have one or many emoji→role pairs.
- No duplicate `emoji` values within one entry's `pairs` — reject with `400 duplicate_emoji` before any Discord call.
- Toggle behavior only: reacting grants the role, removing the reaction revokes it. No configurable "type".
- A role in `pairs` must be assignable: not `@everyone`, not `managed`, `position < guild.me.top_role.position` — reject with `403 role_not_assignable`.
- The bot does not compose messages — only attaches to an existing `message_id`/`channel_id` supplied by staff.
- Editing (`PUT`) only changes `pairs`; `channel_id`/`message_id` are immutable after creation (frontend renders them read-only).
- If a configured message is gone (`discord.NotFound` on fetch), the entry is silently removed from the config (self-healing), both during `PUT`/`DELETE` sync and at bot startup.
- No secrets in any committed file.
- Existing suites must stay green throughout: 88 pytest + 25 Vitest tests before this plan.

---

### Task 1: `reaction_roles.py` — config storage + pure helpers

**Files:**
- Create: `reaction_roles.py` (repo root, next to `lockdown_core.py`)
- Test: `dashboard/backend/tests/test_reaction_roles_core.py`

**Interfaces:**
- Produces: `CONFIG_FILE = "reaction_roles.json"`; `load_config() -> dict`; `save_config(data: dict) -> None`; `get_pairs_for_message(message_id: str) -> list | None`; `find_pair_by_emoji(pairs: list, emoji_str: str) -> dict | None`; `has_duplicate_emoji(pairs: list) -> bool`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_reaction_roles_core.py`:

```python
import json

import pytest

import reaction_roles


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(reaction_roles, "CONFIG_FILE", str(tmp_path / "reaction_roles.json"))


def test_load_config_returns_empty_dict_when_file_missing():
    assert reaction_roles.load_config() == {}


def test_save_then_load_round_trip():
    data = {"111": {"channel_id": "222", "pairs": [{"emoji": "📖", "role_id": "333"}]}}
    reaction_roles.save_config(data)
    assert reaction_roles.load_config() == data


def test_load_config_returns_empty_dict_on_corrupt_json():
    with open(reaction_roles.CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("{not valid json")
    assert reaction_roles.load_config() == {}


def test_get_pairs_for_message_returns_pairs_when_present():
    pairs = [{"emoji": "📖", "role_id": "333"}]
    reaction_roles.save_config({"111": {"channel_id": "222", "pairs": pairs}})
    assert reaction_roles.get_pairs_for_message("111") == pairs


def test_get_pairs_for_message_returns_none_when_absent():
    reaction_roles.save_config({})
    assert reaction_roles.get_pairs_for_message("999") is None


def test_find_pair_by_emoji_matches():
    pairs = [{"emoji": "📖", "role_id": "aaa"}, {"emoji": "✅", "role_id": "bbb"}]
    assert reaction_roles.find_pair_by_emoji(pairs, "✅") == {"emoji": "✅", "role_id": "bbb"}


def test_find_pair_by_emoji_no_match():
    pairs = [{"emoji": "📖", "role_id": "aaa"}]
    assert reaction_roles.find_pair_by_emoji(pairs, "❌") is None


def test_has_duplicate_emoji_true():
    pairs = [{"emoji": "📖", "role_id": "aaa"}, {"emoji": "📖", "role_id": "bbb"}]
    assert reaction_roles.has_duplicate_emoji(pairs) is True


def test_has_duplicate_emoji_false():
    pairs = [{"emoji": "📖", "role_id": "aaa"}, {"emoji": "✅", "role_id": "bbb"}]
    assert reaction_roles.has_duplicate_emoji(pairs) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_reaction_roles_core.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'reaction_roles'`

- [ ] **Step 3: Implement `reaction_roles.py`**

```python
import json
import os

CONFIG_FILE = "reaction_roles.json"


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_pairs_for_message(message_id: str) -> list | None:
    config = load_config()
    entry = config.get(str(message_id))
    return entry["pairs"] if entry else None


def find_pair_by_emoji(pairs: list, emoji_str: str) -> dict | None:
    for pair in pairs:
        if pair["emoji"] == emoji_str:
            return pair
    return None


def has_duplicate_emoji(pairs: list) -> bool:
    emojis = [p["emoji"] for p in pairs]
    return len(emojis) != len(set(emojis))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_reaction_roles_core.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add reaction_roles.py dashboard/backend/tests/test_reaction_roles_core.py
git commit -m "feat: add reaction_roles config storage and pure helpers"
```

---

### Task 2: Test fakes — `FakeChannel`, `FakeMessage`, `FakeCustomEmoji`, `FakeGuild`/`FakeBot` extensions

**Files:**
- Modify: `dashboard/backend/tests/fakes.py` (append new classes; extend `FakeGuild.__init__` and `FakeBot.__init__` with new optional keyword params — every existing call site keeps working unchanged)

**Interfaces:**
- Consumes: nothing new.
- Produces: `class FakeCustomEmoji(emoji_id, name)` (`.id`, `.name`, `.url`, `__str__` → `<:name:id>`); `class FakeMessage(message_id)` (`.id`, `.reaction_calls: list[tuple[str, str]]`, `.add_reaction_raises`, `.remove_reaction_raises`, async `add_reaction(emoji)`, async `remove_reaction(emoji, member)`); `class FakeChannel(channel_id, name="channel", messages=None)` (`.id`, `.name`, async `fetch_message(message_id)` — raises `discord.NotFound` if absent); `FakeGuild.__init__` gains `channels=None, emojis=None` (defaults `[]`) plus a new `get_channel(channel_id)` method; `FakeBot.__init__` gains `user=None` (defaults to a `FakeMember(999999, name="ChetBot", bot=True)`), exposed as `self.user`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_fakes_reaction_extensions.py` (a throwaway-style test file just for this task, proving the new fakes behave correctly before other tasks depend on them):

```python
import discord
import pytest

from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeCustomEmoji,
    FakeGuild,
    FakeMember,
    FakeMessage,
)


def test_fake_custom_emoji_str_format():
    emoji = FakeCustomEmoji(555, "pepehands")
    assert str(emoji) == "<:pepehands:555>"


@pytest.mark.asyncio
async def test_fake_message_records_add_reaction():
    message = FakeMessage(1)
    await message.add_reaction("📖")
    assert message.reaction_calls == [("add", "📖")]


@pytest.mark.asyncio
async def test_fake_message_records_remove_reaction():
    message = FakeMessage(1)
    bot_user = FakeMember(2, name="bot")
    await message.remove_reaction("📖", bot_user)
    assert message.reaction_calls == [("remove", "📖")]


@pytest.mark.asyncio
async def test_fake_channel_fetch_message_returns_existing():
    message = FakeMessage(42)
    channel = FakeChannel(1, messages={42: message})
    fetched = await channel.fetch_message(42)
    assert fetched is message


@pytest.mark.asyncio
async def test_fake_channel_fetch_message_raises_not_found():
    channel = FakeChannel(1, messages={})
    with pytest.raises(discord.NotFound):
        await channel.fetch_message(999)


def test_fake_guild_get_channel_and_defaults():
    channel = FakeChannel(10, name="general")
    emoji = FakeCustomEmoji(20, "wave")
    guild = FakeGuild(channels=[channel], emojis=[emoji])
    assert guild.get_channel(10) is channel
    assert guild.get_channel(999) is None
    assert guild.emojis == [emoji]
    # Backward compatibility: no channels/emojis passed still works
    bare_guild = FakeGuild()
    assert bare_guild.channels == []
    assert bare_guild.emojis == []


def test_fake_bot_has_user_by_default():
    guild = FakeGuild()
    bot = FakeBot(guild)
    assert bot.user.name == "ChetBot"
    assert bot.user.bot is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_fakes_reaction_extensions.py -v`
Expected: FAIL with `ImportError: cannot import name 'FakeChannel' from 'dashboard.backend.tests.fakes'`

- [ ] **Step 3: Append to `dashboard/backend/tests/fakes.py`**

Add these new classes anywhere after `FakeAsset` and before `FakeGuild` (order doesn't matter functionally, but keep related fakes grouped):

```python
class FakeCustomEmoji:
    def __init__(self, emoji_id, name):
        self.id = emoji_id
        self.name = name
        self.url = f"https://cdn.example/emojis/{emoji_id}.png"

    def __str__(self):
        return f"<:{self.name}:{self.id}>"


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

Then modify `FakeGuild.__init__` — replace:

```python
class FakeGuild:
    def __init__(self, members=None, roles=None, me=None):
        self.members = members or []
        self.roles = roles or []
        self.me = me or FakeMember(1, name="bot", top_role=FakeRole(900, name="bot-role", position=50))
```

with:

```python
class FakeGuild:
    def __init__(self, members=None, roles=None, me=None, channels=None, emojis=None):
        self.members = members or []
        self.roles = roles or []
        self.me = me or FakeMember(1, name="bot", top_role=FakeRole(900, name="bot-role", position=50))
        self.channels = channels or []
        self.emojis = emojis or []
```

and add a new method inside `FakeGuild` (next to `get_member`/`get_role`):

```python
    def get_channel(self, channel_id):
        return next((c for c in self.channels if c.id == channel_id), None)
```

Then modify `FakeBot.__init__` — replace:

```python
class FakeBot:
    def __init__(self, guild):
        self._guild = guild
        self.stats = {}
        self.feedback_cases = {}
        self.sent_logs = []
```

with:

```python
class FakeBot:
    def __init__(self, guild, user=None):
        self._guild = guild
        self.user = user or FakeMember(999999, name="ChetBot", bot=True)
        self.stats = {}
        self.feedback_cases = {}
        self.sent_logs = []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_fakes_reaction_extensions.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Run the full backend suite to confirm no regressions**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (88 existing + 9 from Task 1 + 7 from this task = 104)

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/tests/fakes.py dashboard/backend/tests/test_fakes_reaction_extensions.py
git commit -m "test: extend fakes with FakeChannel/FakeMessage/FakeCustomEmoji for reaction roles"
```

---

### Task 3: Bot cog — reaction listeners + startup self-check

**Files:**
- Modify: `reaction_roles.py` (append)
- Test: `dashboard/backend/tests/test_reaction_roles_cog.py`

**Interfaces:**
- Consumes: `load_config`, `save_config`, `get_pairs_for_message`, `find_pair_by_emoji` (Task 1); `FakeBot`, `FakeGuild`, `FakeChannel`, `FakeMessage`, `FakeMember`, `FakeRole` (Task 2).
- Produces: `async def resolve_reacting_member(guild, user_id: int)`; `def build_reason(action: str, message_id) -> str`; `async def handle_reaction_change(bot, payload, action: str) -> None`; `class ReactionRoles(commands.Cog)` with `on_raw_reaction_add`/`on_raw_reaction_remove`; `async def cleanup_missing_messages(bot, guild_id: int) -> int`; `async def setup(bot)`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_reaction_roles_cog.py`:

```python
import discord
import pytest

import reaction_roles
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, FakeMessage, FakeRole


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(reaction_roles, "CONFIG_FILE", str(tmp_path / "reaction_roles.json"))


class FakePayload:
    def __init__(self, message_id, user_id, guild_id, emoji, member=None):
        self.message_id = message_id
        self.user_id = user_id
        self.guild_id = guild_id
        self.emoji = emoji
        self.member = member


def _setup_config(message_id, role_id, emoji="📖"):
    reaction_roles.save_config(
        {str(message_id): {"channel_id": "500", "pairs": [{"emoji": emoji, "role_id": str(role_id)}]}}
    )


@pytest.mark.asyncio
async def test_handle_reaction_change_add_grants_role_using_payload_member():
    role = FakeRole(7, name="VIP", position=5)
    reactor = FakeMember(50, name="reactor")
    guild = FakeGuild(members=[reactor], roles=[role])
    bot = FakeBot(guild)
    _setup_config(999, 7)

    payload = FakePayload(message_id=999, user_id=50, guild_id=1, emoji="📖", member=reactor)
    await reaction_roles.handle_reaction_change(bot, payload, "add")

    action, kwargs = reactor.action_calls[0]
    assert action == "add_roles"
    assert kwargs["role"].id == 7
    assert "Reaction role: add" in kwargs["reason"]


@pytest.mark.asyncio
async def test_handle_reaction_change_remove_revokes_role_by_resolving_member():
    role = FakeRole(7, name="VIP", position=5)
    reactor = FakeMember(50, name="reactor")
    guild = FakeGuild(members=[reactor], roles=[role])
    bot = FakeBot(guild)
    _setup_config(999, 7)

    # on_raw_reaction_remove never carries payload.member — must resolve via guild
    payload = FakePayload(message_id=999, user_id=50, guild_id=1, emoji="📖", member=None)
    await reaction_roles.handle_reaction_change(bot, payload, "remove")

    action, kwargs = reactor.action_calls[0]
    assert action == "remove_roles"
    assert kwargs["role"].id == 7


@pytest.mark.asyncio
async def test_handle_reaction_change_ignores_bots_own_reaction():
    role = FakeRole(7, name="VIP", position=5)
    guild = FakeGuild(roles=[role])
    bot = FakeBot(guild)
    _setup_config(999, 7)

    payload = FakePayload(message_id=999, user_id=bot.user.id, guild_id=1, emoji="📖")
    await reaction_roles.handle_reaction_change(bot, payload, "add")
    # No exception, and nothing to assert on since no member was touched — the
    # test's job is to prove this path returns early without crashing when
    # bot.get_guild/get_member would otherwise be exercised.


@pytest.mark.asyncio
async def test_handle_reaction_change_ignores_unconfigured_message():
    guild = FakeGuild()
    bot = FakeBot(guild)
    payload = FakePayload(message_id=12345, user_id=50, guild_id=1, emoji="📖")
    await reaction_roles.handle_reaction_change(bot, payload, "add")
    # No config exists for this message — should be a silent no-op.


@pytest.mark.asyncio
async def test_handle_reaction_change_ignores_unmatched_emoji():
    role = FakeRole(7, name="VIP", position=5)
    reactor = FakeMember(50, name="reactor")
    guild = FakeGuild(members=[reactor], roles=[role])
    bot = FakeBot(guild)
    _setup_config(999, 7, emoji="📖")

    payload = FakePayload(message_id=999, user_id=50, guild_id=1, emoji="❌", member=reactor)
    await reaction_roles.handle_reaction_change(bot, payload, "add")
    assert reactor.action_calls == []


@pytest.mark.asyncio
async def test_cleanup_missing_messages_removes_entries_for_deleted_messages():
    channel = FakeChannel(500, messages={})  # message 999 does NOT exist
    guild = FakeGuild(channels=[channel])
    bot = FakeBot(guild)
    _setup_config(999, 7)

    removed = await reaction_roles.cleanup_missing_messages(bot, guild_id=1)

    assert removed == 1
    assert reaction_roles.load_config() == {}


@pytest.mark.asyncio
async def test_cleanup_missing_messages_keeps_entries_for_existing_messages():
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    guild = FakeGuild(channels=[channel])
    bot = FakeBot(guild)
    _setup_config(999, 7)

    removed = await reaction_roles.cleanup_missing_messages(bot, guild_id=1)

    assert removed == 0
    assert "999" in reaction_roles.load_config()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_reaction_roles_cog.py -v`
Expected: FAIL with `AttributeError: module 'reaction_roles' has no attribute 'handle_reaction_change'`

- [ ] **Step 3: Append to `reaction_roles.py`**

Add these imports at the top of the file (above `CONFIG_FILE = ...`):

```python
import os

import discord
from discord.ext import commands
```

(Note: `import json` and `import os` already exist from Task 1 — do not duplicate `import os`, just add `discord`/`commands` alongside the existing imports.)

Then append at the end of the file:

```python
async def resolve_reacting_member(guild, user_id: int):
    member = guild.get_member(user_id)
    if member is not None:
        return member
    try:
        return await guild.fetch_member(user_id)
    except discord.HTTPException:
        return None


def build_reason(action: str, message_id) -> str:
    return f"Reaction role: {action} — by reaction on message {message_id}"


async def handle_reaction_change(bot, payload, action: str) -> None:
    if payload.user_id == bot.user.id:
        return

    pairs = get_pairs_for_message(str(payload.message_id))
    if pairs is None:
        return

    pair = find_pair_by_emoji(pairs, str(payload.emoji))
    if pair is None:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    role = guild.get_role(int(pair["role_id"]))
    if role is None:
        return

    if action == "add" and payload.member is not None:
        member = payload.member
    else:
        member = await resolve_reacting_member(guild, payload.user_id)
    if member is None:
        return

    reason = build_reason(action, payload.message_id)
    try:
        if action == "add":
            await member.add_roles(role, reason=reason)
        else:
            await member.remove_roles(role, reason=reason)
    except discord.HTTPException:
        return


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await handle_reaction_change(self.bot, payload, "add")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await handle_reaction_change(self.bot, payload, "remove")


async def cleanup_missing_messages(bot, guild_id: int) -> int:
    """Removes config entries whose message or channel no longer exists.

    Returns the number of entries removed."""
    config = load_config()
    guild = bot.get_guild(guild_id)
    if guild is None:
        return 0

    removed = 0
    for message_id, entry in list(config.items()):
        channel = guild.get_channel(int(entry["channel_id"]))
        if channel is None:
            del config[message_id]
            removed += 1
            continue
        try:
            await channel.fetch_message(int(message_id))
        except discord.NotFound:
            del config[message_id]
            removed += 1
        except discord.HTTPException:
            continue

    if removed:
        save_config(config)
    return removed


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
    guild_id_raw = os.getenv("GUILD_ID")
    if guild_id_raw:
        await cleanup_missing_messages(bot, int(guild_id_raw))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_reaction_roles_cog.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Verify the module still imports cleanly**

Run: `python -c "import reaction_roles"`
Expected: no output, exit code 0

- [ ] **Step 6: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (104 + 7 = 111)

- [ ] **Step 7: Commit**

```bash
git add reaction_roles.py dashboard/backend/tests/test_reaction_roles_cog.py
git commit -m "feat: add reaction role listeners and startup self-check"
```

---

### Task 4: `GET`/`POST /api/reaction-roles`

**Files:**
- Create: `dashboard/backend/routes/reaction_roles.py`
- Test: `dashboard/backend/tests/test_reaction_roles_routes.py`

**Interfaces:**
- Consumes: `reaction_roles.load_config`/`save_config`/`has_duplicate_emoji` (Task 1, imported as `import reaction_roles` — same bare top-level import style `dashboard/backend/routes/lockdown.py` already uses for `lockdown_core`); `require_dashboard_access` (Phase 2a); fakes from Task 2.
- Produces: `routes = web.RouteTableDef()` (this task's table gets more routes appended in Task 5); `def serialize_entry(message_id, entry) -> dict`; `def _is_role_assignable(role, guild) -> bool`; `async def _validate_pairs(pairs, guild) -> web.Response | None`; `GET /api/reaction-roles` → `200 {"reaction_roles": [...]}`; `POST /api/reaction-roles` → `201 {message_id, channel_id, pairs}` / `400`/`403`/`404`/`503`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_reaction_roles_routes.py`:

```python
import pytest

import reaction_roles
from dashboard.backend.routes.reaction_roles import routes as reaction_roles_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    FakeMessage,
    FakeRole,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(reaction_roles, "CONFIG_FILE", str(tmp_path / "reaction_roles.json"))


def build(roles=None, channels=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot_top = FakeRole(900, name="bot-role", position=50)
    me = FakeMember(1, name="bot", top_role=bot_top)
    guild = FakeGuild(members=[moderator], roles=roles or [], channels=channels or [], me=me)
    return guild, make_moderation_app(FakeBot(guild), [reaction_roles_routes])


@pytest.mark.asyncio
async def test_list_reaction_roles_empty(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/reaction-roles")
    assert resp.status == 200
    assert (await resp.json()) == {"reaction_roles": []}


@pytest.mark.asyncio
async def test_create_reaction_role_success(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    assert resp.status == 201
    body = await resp.json()
    assert body["message_id"] == "999"
    assert body["pairs"] == [{"emoji": "📖", "role_id": "7"}]
    assert message.reaction_calls == [("add", "📖")]
    assert reaction_roles.load_config()["999"]["channel_id"] == "500"


@pytest.mark.asyncio
async def test_create_reaction_role_rejects_duplicate_emoji(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    other_role = FakeRole(8, name="Other", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role, other_role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={
            "channel_id": "500",
            "message_id": "999",
            "pairs": [{"emoji": "📖", "role_id": "7"}, {"emoji": "📖", "role_id": "8"}],
        },
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "duplicate_emoji"


@pytest.mark.asyncio
async def test_create_reaction_role_rejects_role_above_bot(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "9"}]},
    )
    assert resp.status == 403


@pytest.mark.asyncio
async def test_create_reaction_role_channel_not_found(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    _, app = build(roles=[role], channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    assert resp.status == 404


@pytest.mark.asyncio
async def test_create_reaction_role_message_not_found(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    channel = FakeChannel(500, messages={})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    assert resp.status == 404


@pytest.mark.asyncio
async def test_create_reaction_role_empty_pairs_rejected(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/reaction-roles", json={"channel_id": "500", "message_id": "999", "pairs": []}
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/reaction-roles")
    assert resp.status == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_reaction_roles_routes.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.routes.reaction_roles'`

- [ ] **Step 3: Implement `dashboard/backend/routes/reaction_roles.py`**

```python
import discord
from aiohttp import web

import reaction_roles
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


def _is_role_assignable(role, guild) -> bool:
    return not role.is_default() and not role.managed and role.position < guild.me.top_role.position


def serialize_entry(message_id: str, entry: dict) -> dict:
    return {"message_id": message_id, "channel_id": entry["channel_id"], "pairs": entry["pairs"]}


@routes.get("/api/reaction-roles")
@require_dashboard_access
async def list_reaction_roles(request: web.Request) -> web.Response:
    config = reaction_roles.load_config()
    return web.json_response(
        {"reaction_roles": [serialize_entry(mid, entry) for mid, entry in config.items()]}
    )


async def _validate_pairs(pairs, guild):
    """Returns None on success, or an error web.Response."""
    if not pairs:
        return web.json_response({"error": "invalid_request"}, status=400)
    if reaction_roles.has_duplicate_emoji(pairs):
        return web.json_response({"error": "duplicate_emoji"}, status=400)
    for pair in pairs:
        if not pair.get("emoji"):
            return web.json_response({"error": "invalid_request"}, status=400)
        try:
            role_id = int(pair.get("role_id"))
        except (TypeError, ValueError):
            return web.json_response({"error": "invalid_request"}, status=400)
        role = guild.get_role(role_id)
        if role is None or not _is_role_assignable(role, guild):
            return web.json_response({"error": "role_not_assignable"}, status=403)
    return None


@routes.post("/api/reaction-roles")
@require_dashboard_access
async def create_reaction_role(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    try:
        channel_id = int(body.get("channel_id"))
        message_id = int(body.get("message_id"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)

    pairs = body.get("pairs") or []
    error = await _validate_pairs(pairs, guild)
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

    config = reaction_roles.load_config()
    config[str(message_id)] = {"channel_id": str(channel_id), "pairs": pairs}
    reaction_roles.save_config(config)

    for pair in pairs:
        try:
            await message.add_reaction(pair["emoji"])
        except discord.HTTPException:
            continue

    return web.json_response(serialize_entry(str(message_id), config[str(message_id)]), status=201)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_reaction_roles_routes.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routes/reaction_roles.py dashboard/backend/tests/test_reaction_roles_routes.py
git commit -m "feat(dashboard): add GET/POST /api/reaction-roles"
```

---

### Task 5: `PUT`/`DELETE /api/reaction-roles/{message_id}` + `GET /api/emojis` + `GET /api/channels`

**Files:**
- Modify: `dashboard/backend/routes/reaction_roles.py` (append)
- Test: `dashboard/backend/tests/test_reaction_roles_routes.py` (append)

**Interfaces:**
- Consumes: everything from Task 4.
- Produces: `PUT /api/reaction-roles/{message_id}` → `200 {message_id, channel_id, pairs}` / `400`/`403`/`404`/`502`/`503`; `DELETE /api/reaction-roles/{message_id}` → `200 {"ok": true}` / `404`; `GET /api/emojis` → `200 {"emojis": [{id, name, url}]}`; `GET /api/channels` → `200 {"channels": [{id, name}]}`.

- [ ] **Step 1: Write the failing test**

Append to `dashboard/backend/tests/test_reaction_roles_routes.py`:

```python
@pytest.mark.asyncio
async def test_update_reaction_role_syncs_reactions(aiohttp_client):
    role_a = FakeRole(7, name="A", position=5)
    role_b = FakeRole(8, name="B", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role_a, role_b], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    message.reaction_calls.clear()

    resp = await client.put(
        "/api/reaction-roles/999", json={"pairs": [{"emoji": "✅", "role_id": "8"}]}
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["pairs"] == [{"emoji": "✅", "role_id": "8"}]
    assert ("remove", "📖") in message.reaction_calls
    assert ("add", "✅") in message.reaction_calls


@pytest.mark.asyncio
async def test_update_reaction_role_404_when_unknown(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    _, app = build(roles=[role])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/reaction-roles/999", json={"pairs": [{"emoji": "📖", "role_id": "7"}]})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_update_reaction_role_resets_binding_when_message_gone(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    del channel._messages[999]  # simulate the message being deleted in Discord

    resp = await client.put("/api/reaction-roles/999", json={"pairs": [{"emoji": "✅", "role_id": "7"}]})
    assert resp.status == 404
    assert reaction_roles.load_config() == {}


@pytest.mark.asyncio
async def test_delete_reaction_role_removes_config_and_reactions(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    message = FakeMessage(999)
    channel = FakeChannel(500, messages={999: message})
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post(
        "/api/reaction-roles",
        json={"channel_id": "500", "message_id": "999", "pairs": [{"emoji": "📖", "role_id": "7"}]},
    )
    resp = await client.delete("/api/reaction-roles/999")
    assert resp.status == 200
    assert reaction_roles.load_config() == {}
    assert ("remove", "📖") in message.reaction_calls


@pytest.mark.asyncio
async def test_delete_reaction_role_404_when_unknown(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    resp = await client.delete("/api/reaction-roles/999")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_list_emojis(aiohttp_client):
    from dashboard.backend.tests.fakes import FakeCustomEmoji

    emoji = FakeCustomEmoji(20, "wave")
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator], emojis=[emoji])
    app = make_moderation_app(FakeBot(guild), [reaction_roles_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/emojis")
    assert resp.status == 200
    body = await resp.json()
    assert body["emojis"] == [{"id": "20", "name": "wave", "url": "https://cdn.example/emojis/20.png"}]


@pytest.mark.asyncio
async def test_list_channels(aiohttp_client):
    channel = FakeChannel(500, name="general")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/channels")
    assert resp.status == 200
    body = await resp.json()
    assert body["channels"] == [{"id": "500", "name": "general"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_reaction_roles_routes.py -v`
Expected: FAIL — `PUT`/`DELETE`/`/api/emojis`/`/api/channels` routes don't exist yet (404s on the new tests).

- [ ] **Step 3: Append to `dashboard/backend/routes/reaction_roles.py`**

```python
@routes.put("/api/reaction-roles/{message_id}")
@require_dashboard_access
async def update_reaction_role(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    message_id_raw = request.match_info["message_id"]
    config = reaction_roles.load_config()
    entry = config.get(message_id_raw)
    if entry is None:
        return web.json_response({"error": "not_found"}, status=404)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    pairs = body.get("pairs") or []
    error = await _validate_pairs(pairs, guild)
    if error:
        return error

    channel = guild.get_channel(int(entry["channel_id"]))
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    try:
        message = await channel.fetch_message(int(message_id_raw))
    except discord.NotFound:
        del config[message_id_raw]
        reaction_roles.save_config(config)
        return web.json_response({"error": "message_not_found"}, status=404)
    except discord.HTTPException:
        return web.json_response({"error": "discord_error"}, status=502)

    old_emojis = {p["emoji"] for p in entry["pairs"]}
    new_emojis = {p["emoji"] for p in pairs}

    for emoji in old_emojis - new_emojis:
        try:
            await message.remove_reaction(emoji, request.app["bot"].user)
        except discord.HTTPException:
            continue
    for emoji in new_emojis - old_emojis:
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            continue

    config[message_id_raw] = {"channel_id": entry["channel_id"], "pairs": pairs}
    reaction_roles.save_config(config)

    return web.json_response(serialize_entry(message_id_raw, config[message_id_raw]))


@routes.delete("/api/reaction-roles/{message_id}")
@require_dashboard_access
async def delete_reaction_role(request: web.Request) -> web.Response:
    message_id_raw = request.match_info["message_id"]
    config = reaction_roles.load_config()
    entry = config.get(message_id_raw)
    if entry is None:
        return web.json_response({"error": "not_found"}, status=404)

    guild = _get_guild_or_none(request)
    if guild is not None:
        channel = guild.get_channel(int(entry["channel_id"]))
        if channel is not None:
            try:
                message = await channel.fetch_message(int(message_id_raw))
                for pair in entry["pairs"]:
                    try:
                        await message.remove_reaction(pair["emoji"], request.app["bot"].user)
                    except discord.HTTPException:
                        continue
            except discord.NotFound:
                pass
            except discord.HTTPException:
                pass

    del config[message_id_raw]
    reaction_roles.save_config(config)
    return web.json_response({"ok": True})


@routes.get("/api/emojis")
@require_dashboard_access
async def list_emojis(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)
    return web.json_response(
        {"emojis": [{"id": str(e.id), "name": e.name, "url": str(e.url)} for e in guild.emojis]}
    )


@routes.get("/api/channels")
@require_dashboard_access
async def list_channels(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)
    return web.json_response(
        {"channels": [{"id": str(c.id), "name": c.name} for c in guild.channels]}
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_reaction_roles_routes.py -v`
Expected: PASS (15 tests total in this file)

- [ ] **Step 5: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (111 + 8 + 7 = 126)

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/reaction_roles.py dashboard/backend/tests/test_reaction_roles_routes.py
git commit -m "feat(dashboard): add PUT/DELETE reaction-role routes plus emoji/channel listing"
```

---

### Task 6: Register routes + load the bot cog

**Files:**
- Modify: `dashboard/backend/app.py` (add one import + one `add_routes` line)
- Modify: `main.py` (add one `load_extension` line to `setup_hook`)

**Interfaces:**
- Consumes: `dashboard.backend.routes.reaction_roles.routes` (Task 4/5); `reaction_roles.setup` (Task 3, called implicitly by `load_extension`).
- Produces: all Phase 3a endpoints live in the real app; the bot loads the `ReactionRoles` cog on startup.

`app.py` and `main.py` are both already-reviewed code from earlier phases — touch ONLY the two specified lines in each, nothing else.

- [ ] **Step 1: Add the import and route registration to `dashboard/backend/app.py`**

Read the current file first. Add this import alongside the existing route imports (after `from .routes.moderation import routes as moderation_routes`):

```python
from .routes.reaction_roles import routes as reaction_roles_routes
```

Add this line alongside the existing `app.add_routes(...)` calls (after `app.add_routes(lockdown_routes)`):

```python
    app.add_routes(reaction_roles_routes)
```

- [ ] **Step 2: Add the extension load to `main.py`**

Read the current file first. In `ChetBot.setup_hook`, add one line alongside the existing `await self.load_extension(...)` calls (after `await self.load_extension("events")`):

```python
        await self.load_extension("reaction_roles")
```

- [ ] **Step 3: Verify both files still import cleanly**

Run: `python -c "import main"`
Expected: no output, exit code 0 (this exercises `main.py`'s module-level code, including the `dashboard.backend.app` import chain that now includes the new route table; `setup_hook` itself only runs when the bot actually connects, but this catches any import-time error in the new wiring)

- [ ] **Step 4: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (126 — Phase 1's `test_app.py` health/startup tests confirm `create_app` still builds with the new route table registered)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/app.py main.py
git commit -m "feat: register reaction-role routes and load the bot cog"
```

---

### Task 7: Frontend API client — reaction-role functions

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts` (append; do NOT change any existing export)
- Test: `dashboard/frontend/src/api/reactionRoles.test.ts`

**Interfaces:**
- Consumes: existing `apiFetch`, `jsonInit` (already in `client.ts` — read the current file before appending).
- Produces: `interface ReactionRolePair { emoji: string; role_id: string }`; `interface ReactionRoleEntry { message_id: string; channel_id: string; pairs: ReactionRolePair[] }`; `interface CustomEmoji { id: string; name: string; url: string }`; `interface ChannelInfo { id: string; name: string }`; `fetchReactionRoles(): Promise<ReactionRoleEntry[]>`; `createReactionRole(channelId: string, messageId: string, pairs: ReactionRolePair[]): Promise<ReactionRoleEntry>`; `updateReactionRole(messageId: string, pairs: ReactionRolePair[]): Promise<ReactionRoleEntry>`; `deleteReactionRole(messageId: string): Promise<void>`; `fetchEmojis(): Promise<CustomEmoji[]>`; `fetchChannels(): Promise<ChannelInfo[]>`.

- [ ] **Step 1: Write the failing test**

`dashboard/frontend/src/api/reactionRoles.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createReactionRole,
  deleteReactionRole,
  fetchChannels,
  fetchEmojis,
  fetchReactionRoles,
  updateReactionRole,
} from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('reaction roles api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchReactionRoles unwraps the list', async () => {
    const entries = [{ message_id: '1', channel_id: '2', pairs: [] }]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(okJson({ reaction_roles: entries })))
    const result = await fetchReactionRoles()
    expect(result).toEqual(entries)
  })

  it('createReactionRole POSTs channel_id/message_id/pairs', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ message_id: '1', channel_id: '2', pairs: [] }))
    vi.stubGlobal('fetch', fetchMock)

    await createReactionRole('2', '1', [{ emoji: '📖', role_id: '7' }])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/reaction-roles',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ channel_id: '2', message_id: '1', pairs: [{ emoji: '📖', role_id: '7' }] }),
      }),
    )
  })

  it('updateReactionRole PUTs only pairs', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ message_id: '1', channel_id: '2', pairs: [] }))
    vi.stubGlobal('fetch', fetchMock)

    await updateReactionRole('1', [{ emoji: '✅', role_id: '8' }])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/reaction-roles/1',
      expect.objectContaining({ method: 'PUT', body: JSON.stringify({ pairs: [{ emoji: '✅', role_id: '8' }] }) }),
    )
  })

  it('deleteReactionRole DELETEs by message id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await deleteReactionRole('1')
    expect(fetchMock).toHaveBeenCalledWith('/api/reaction-roles/1', expect.objectContaining({ method: 'DELETE' }))
  })

  it('fetchEmojis unwraps the list', async () => {
    const emojis = [{ id: '20', name: 'wave', url: 'https://cdn.example/emojis/20.png' }]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(okJson({ emojis })))
    expect(await fetchEmojis()).toEqual(emojis)
  })

  it('fetchChannels unwraps the list', async () => {
    const channels = [{ id: '500', name: 'general' }]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(okJson({ channels })))
    expect(await fetchChannels()).toEqual(channels)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd dashboard/frontend && npm run test`
Expected: FAIL — new exports don't exist.

- [ ] **Step 3: Append to `dashboard/frontend/src/api/client.ts`**

```ts
export interface ReactionRolePair {
  emoji: string
  role_id: string
}

export interface ReactionRoleEntry {
  message_id: string
  channel_id: string
  pairs: ReactionRolePair[]
}

export interface CustomEmoji {
  id: string
  name: string
  url: string
}

export interface ChannelInfo {
  id: string
  name: string
}

export async function fetchReactionRoles(): Promise<ReactionRoleEntry[]> {
  const body = await apiFetch<{ reaction_roles: ReactionRoleEntry[] }>('/api/reaction-roles')
  return body.reaction_roles
}

export function createReactionRole(
  channelId: string,
  messageId: string,
  pairs: ReactionRolePair[],
): Promise<ReactionRoleEntry> {
  return apiFetch(
    '/api/reaction-roles',
    jsonInit('POST', { channel_id: channelId, message_id: messageId, pairs }),
  )
}

export function updateReactionRole(messageId: string, pairs: ReactionRolePair[]): Promise<ReactionRoleEntry> {
  return apiFetch(`/api/reaction-roles/${messageId}`, jsonInit('PUT', { pairs }))
}

export async function deleteReactionRole(messageId: string): Promise<void> {
  await apiFetch(`/api/reaction-roles/${messageId}`, jsonInit('DELETE'))
}

export async function fetchEmojis(): Promise<CustomEmoji[]> {
  const body = await apiFetch<{ emojis: CustomEmoji[] }>('/api/emojis')
  return body.emojis
}

export async function fetchChannels(): Promise<ChannelInfo[]> {
  const body = await apiFetch<{ channels: ChannelInfo[] }>('/api/channels')
  return body.channels
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test`
Expected: PASS — 6 new + all existing (31 total)

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/reactionRoles.test.ts
git commit -m "feat(dashboard): add reaction-role API client functions"
```

---

### Task 8: `ReactionRolesPage` + `ReactionRoleForm` + wiring

**Files:**
- Create: `dashboard/frontend/src/pages/ReactionRoles.tsx`
- Create: `dashboard/frontend/src/components/ReactionRoleForm.tsx`
- Test: `dashboard/frontend/src/pages/ReactionRoles.test.tsx`
- Modify: `dashboard/frontend/src/App.tsx` (replace the "Конструктор кнопок и эмбедов" placeholder route with the real page)
- Modify: `dashboard/frontend/src/pages/DashboardShell.tsx` (give that sidebar entry a `to: '/reaction-roles'`)

**Interfaces:**
- Consumes: `fetchReactionRoles`, `createReactionRole`, `updateReactionRole`, `deleteReactionRole`, `fetchEmojis`, `fetchChannels`, `fetchRoles` (Phase 2a), types `ReactionRoleEntry`/`ReactionRolePair`/`CustomEmoji`/`ChannelInfo`/`RoleInfo` (Task 7 + Phase 2a); `Card`, `Button`, `Modal` (existing design system).
- Produces: `ReactionRolesPage()`; `ReactionRoleForm({ open, onClose, editing, onSaved }: { open: boolean; onClose: () => void; editing: ReactionRoleEntry | null; onSaved: () => void })`.

- [ ] **Step 1: Write the failing test**

`dashboard/frontend/src/pages/ReactionRoles.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { ReactionRolesPage } from './ReactionRoles'

describe('ReactionRolesPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lists existing reaction roles with resolved channel/role names', async () => {
    vi.spyOn(client, 'fetchReactionRoles').mockResolvedValue([
      { message_id: '999', channel_id: '500', pairs: [{ emoji: '📖', role_id: '7' }] },
    ])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    vi.spyOn(client, 'fetchEmojis').mockResolvedValue([])

    render(
      <MemoryRouter>
        <ReactionRolesPage />
      </MemoryRouter>,
    )

    await waitFor(() => expect(screen.getByText('general')).toBeInTheDocument())
    expect(screen.getByText('VIP')).toBeInTheDocument()
  })

  it('opens the create form and submits a new reaction role', async () => {
    vi.spyOn(client, 'fetchReactionRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    vi.spyOn(client, 'fetchEmojis').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createReactionRole').mockResolvedValue({
      message_id: '999',
      channel_id: '500',
      pairs: [{ emoji: '📖', role_id: '7' }],
    })

    render(
      <MemoryRouter>
        <ReactionRolesPage />
      </MemoryRouter>,
    )

    await waitFor(() => screen.getByText('Создать reaction role'))
    fireEvent.click(screen.getByText('Создать reaction role'))

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })
    fireEvent.change(screen.getByLabelText('Message ID'), { target: { value: '999' } })
    fireEvent.change(screen.getByPlaceholderText('Эмодзи (вставьте unicode или выберите ниже)'), {
      target: { value: '📖' },
    })
    fireEvent.change(screen.getByLabelText('Роль для этой пары'), { target: { value: '7' } })
    fireEvent.click(screen.getByText('Сохранить'))

    await waitFor(() => expect(createSpy).toHaveBeenCalledWith('500', '999', [{ emoji: '📖', role_id: '7' }]))
  })

  it('rejects submit with duplicate emoji before calling the API', async () => {
    vi.spyOn(client, 'fetchReactionRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([
      { id: '7', name: 'VIP', color: '#5865f2', position: 5 },
      { id: '8', name: 'Other', color: '#000000', position: 5 },
    ])
    vi.spyOn(client, 'fetchEmojis').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createReactionRole')

    render(
      <MemoryRouter>
        <ReactionRolesPage />
      </MemoryRouter>,
    )

    await waitFor(() => screen.getByText('Создать reaction role'))
    fireEvent.click(screen.getByText('Создать reaction role'))
    await waitFor(() => screen.getByLabelText('Канал'))

    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })
    fireEvent.change(screen.getByLabelText('Message ID'), { target: { value: '999' } })
    fireEvent.change(screen.getByPlaceholderText('Эмодзи (вставьте unicode или выберите ниже)'), {
      target: { value: '📖' },
    })
    fireEvent.change(screen.getByLabelText('Роль для этой пары'), { target: { value: '7' } })

    fireEvent.click(screen.getByText('+ Добавить пару'))
    const emojiInputs = screen.getAllByPlaceholderText('Эмодзи (вставьте unicode или выберите ниже)')
    fireEvent.change(emojiInputs[1], { target: { value: '📖' } })
    const roleSelects = screen.getAllByLabelText('Роль для этой пары')
    fireEvent.change(roleSelects[1], { target: { value: '8' } })

    fireEvent.click(screen.getByText('Сохранить'))

    expect(await screen.findByText(/повторяющ/i)).toBeInTheDocument()
    expect(createSpy).not.toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test`
Expected: FAIL — `Cannot find module './ReactionRoles'`.

- [ ] **Step 3: Implement `dashboard/frontend/src/components/ReactionRoleForm.tsx`**

```tsx
import { useEffect, useState } from 'react'
import {
  createReactionRole,
  fetchChannels,
  fetchEmojis,
  fetchRoles,
  updateReactionRole,
  type ChannelInfo,
  type CustomEmoji,
  type ReactionRoleEntry,
  type ReactionRolePair,
  type RoleInfo,
} from '../api/client'
import { Button } from './ui/Button'
import { Modal } from './ui/Modal'

interface Props {
  open: boolean
  onClose: () => void
  editing: ReactionRoleEntry | null
  onSaved: () => void
}

function hasDuplicateEmoji(pairs: ReactionRolePair[]): boolean {
  const emojis = pairs.map((p) => p.emoji).filter(Boolean)
  return new Set(emojis).size !== emojis.length
}

export function ReactionRoleForm({ open, onClose, editing, onSaved }: Props) {
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [emojis, setEmojis] = useState<CustomEmoji[]>([])
  const [channelId, setChannelId] = useState('')
  const [messageId, setMessageId] = useState('')
  const [pairs, setPairs] = useState<ReactionRolePair[]>([{ emoji: '', role_id: '' }])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!open) return
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
    fetchEmojis().then(setEmojis).catch(() => {})
    if (editing) {
      setChannelId(editing.channel_id)
      setMessageId(editing.message_id)
      setPairs(editing.pairs.length > 0 ? editing.pairs : [{ emoji: '', role_id: '' }])
    } else {
      setChannelId('')
      setMessageId('')
      setPairs([{ emoji: '', role_id: '' }])
    }
    setError('')
  }, [open, editing])

  const updatePair = (index: number, patch: Partial<ReactionRolePair>) => {
    setPairs((prev) => prev.map((p, i) => (i === index ? { ...p, ...patch } : p)))
  }

  const removePair = (index: number) => {
    setPairs((prev) => prev.filter((_, i) => i !== index))
  }

  const addPair = () => {
    setPairs((prev) => [...prev, { emoji: '', role_id: '' }])
  }

  const handleSave = async () => {
    setError('')
    if (!channelId || !messageId) {
      setError('Укажите канал и Message ID')
      return
    }
    const validPairs = pairs.filter((p) => p.emoji && p.role_id)
    if (validPairs.length === 0) {
      setError('Добавьте хотя бы одну пару эмодзи → роль')
      return
    }
    if (hasDuplicateEmoji(validPairs)) {
      setError('Повторяющийся эмодзи в списке пар')
      return
    }

    setBusy(true)
    try {
      if (editing) {
        await updateReactionRole(editing.message_id, validPairs)
      } else {
        await createReactionRole(channelId, messageId, validPairs)
      }
      onSaved()
      onClose()
    } catch {
      setError('Не удалось сохранить — проверьте канал/ID сообщения и права на роли')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open={open} title={editing ? 'Редактировать reaction role' : 'Создать reaction role'} onClose={onClose}>
      <div className="flex flex-col gap-3">
        <label className="text-sm text-muted" htmlFor="rr-channel">
          Канал
        </label>
        <select
          id="rr-channel"
          value={channelId}
          onChange={(e) => setChannelId(e.target.value)}
          disabled={!!editing}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground disabled:opacity-50"
        >
          <option value="">Выберите канал…</option>
          {channels.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>

        <label className="text-sm text-muted" htmlFor="rr-message-id">
          Message ID
        </label>
        <input
          id="rr-message-id"
          value={messageId}
          onChange={(e) => setMessageId(e.target.value)}
          disabled={!!editing}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary disabled:opacity-50"
          placeholder="ID существующего сообщения"
        />

        <div className="flex flex-col gap-2">
          {pairs.map((pair, index) => (
            <div key={index} className="flex items-center gap-2">
              <input
                value={pair.emoji}
                onChange={(e) => updatePair(index, { emoji: e.target.value })}
                placeholder="Эмодзи (вставьте unicode или выберите ниже)"
                className="flex-1 rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
              />
              <select
                aria-label="Свой эмодзи сервера"
                value=""
                onChange={(e) => {
                  const custom = emojis.find((em) => em.id === e.target.value)
                  if (custom) updatePair(index, { emoji: `<:${custom.name}:${custom.id}>` })
                }}
                className="rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground"
              >
                <option value="">Свой эмодзи…</option>
                {emojis.map((em) => (
                  <option key={em.id} value={em.id}>
                    {em.name}
                  </option>
                ))}
              </select>
              <select
                aria-label="Роль для этой пары"
                value={pair.role_id}
                onChange={(e) => updatePair(index, { role_id: e.target.value })}
                className="rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground"
              >
                <option value="">Роль…</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => removePair(index)}
                className="cursor-pointer text-muted hover:text-danger"
              >
                ×
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={addPair}
            className="cursor-pointer self-start text-sm text-primary hover:text-primary-hover"
          >
            + Добавить пару
          </button>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Отмена
          </Button>
          <Button variant="primary" onClick={handleSave} disabled={busy}>
            {busy ? 'Сохраняем…' : 'Сохранить'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
```

- [ ] **Step 4: Implement `dashboard/frontend/src/pages/ReactionRoles.tsx`**

```tsx
import { useEffect, useState } from 'react'
import {
  deleteReactionRole,
  fetchChannels,
  fetchReactionRoles,
  fetchRoles,
  type ChannelInfo,
  type ReactionRoleEntry,
  type RoleInfo,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { ReactionRoleForm } from '../components/ReactionRoleForm'

export function ReactionRolesPage() {
  const [entries, setEntries] = useState<ReactionRoleEntry[]>([])
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [error, setError] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<ReactionRoleEntry | null>(null)
  const [pendingDelete, setPendingDelete] = useState<string | null>(null)

  const reload = () => {
    fetchReactionRoles()
      .then(setEntries)
      .catch(() => setError('Не удалось загрузить reaction roles'))
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
  }

  useEffect(reload, [])

  const channelName = (id: string) => channels.find((c) => c.id === id)?.name ?? id
  const roleNames = (pairIds: string[]) =>
    pairIds.map((id) => roles.find((r) => r.id === id)?.name ?? id).join(', ')

  const confirmDelete = async () => {
    if (!pendingDelete) return
    try {
      await deleteReactionRole(pendingDelete)
      setPendingDelete(null)
      reload()
    } catch {
      setError('Не удалось удалить')
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-foreground">Reaction Roles</h1>
        <Button
          variant="primary"
          onClick={() => {
            setEditing(null)
            setFormOpen(true)
          }}
        >
          Создать reaction role
        </Button>
      </div>

      {error && <p className="mb-4 text-sm text-danger">{error}</p>}

      <div className="flex flex-col gap-2">
        {entries.map((entry) => (
          <Card key={entry.message_id} className="flex items-center justify-between !p-3">
            <div>
              <p className="text-sm text-foreground">{channelName(entry.channel_id)}</p>
              <p className="text-xs text-muted">{roleNames(entry.pairs.map((p) => p.role_id))}</p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                onClick={() => {
                  setEditing(entry)
                  setFormOpen(true)
                }}
              >
                Edit
              </Button>
              <Button variant="danger" onClick={() => setPendingDelete(entry.message_id)}>
                Delete
              </Button>
            </div>
          </Card>
        ))}
        {entries.length === 0 && <p className="text-sm text-muted">Пока ничего не настроено.</p>}
      </div>

      <ReactionRoleForm
        open={formOpen}
        editing={editing}
        onClose={() => setFormOpen(false)}
        onSaved={reload}
      />

      <Modal open={pendingDelete !== null} title="Удалить reaction role?" onClose={() => setPendingDelete(null)}>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={() => setPendingDelete(null)}>
            Отмена
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Удалить
          </Button>
        </div>
      </Modal>
    </div>
  )
}
```

- [ ] **Step 5: Wire the route in `App.tsx`**

Read the current file first. Add the import:

```tsx
import { ReactionRolesPage } from './pages/ReactionRoles'
```

Replace the `members`/`lockdown` route block's neighboring line — add a new sibling route:

```tsx
            <Route path="reaction-roles" element={<ReactionRolesPage />} />
```

- [ ] **Step 6: Wire the sidebar link in `DashboardShell.tsx`**

Read the current file first. In the `SECTIONS` array, change:

```tsx
  { label: 'Конструктор кнопок и эмбедов', icon: Stack },
```

to:

```tsx
  { label: 'Конструктор кнопок и эмбедов', icon: Stack, to: '/reaction-roles' },
```

- [ ] **Step 7: Run tests + typecheck + build**

Run: `npm run test`, `npx tsc --noEmit`, `npm run build`
Expected: all green, no debug artifacts, no stray files (`git status --short` clean before committing).

- [ ] **Step 8: Commit**

```bash
git add dashboard/frontend/src/pages/ReactionRoles.tsx dashboard/frontend/src/components/ReactionRoleForm.tsx dashboard/frontend/src/pages/ReactionRoles.test.tsx dashboard/frontend/src/App.tsx dashboard/frontend/src/pages/DashboardShell.tsx
git commit -m "feat(dashboard): add Reaction Roles page and form, wire into sidebar"
```

---

### Task 9: Full end-to-end manual verification

**Files:** none (verification only).

- [ ] **Step 1:** Start backend (`python main.py`) and frontend (`npm run dev`), log in at `http://localhost:5173`.
- [ ] **Step 2:** Sidebar "Конструктор кнопок и эмбедов" is now a working link to `/reaction-roles`, showing an empty list first time.
- [ ] **Step 3:** In your test Discord server, post a plain message in some channel and copy its message ID (enable Developer Mode → right-click message → Copy Message ID).
- [ ] **Step 4:** In the dashboard, create a reaction role: pick that channel, paste the message ID, add one unicode emoji → role pair and one custom-server-emoji → role pair. Save. Confirm both reactions appear on the actual Discord message (bot added them).
- [ ] **Step 5:** React to the message with each configured emoji (as a normal user, not the bot) — confirm the corresponding role is granted. Remove the reaction — confirm the role is revoked.
- [ ] **Step 6:** React with an emoji NOT in the config — confirm nothing happens (no role change, no error in bot logs).
- [ ] **Step 7:** Edit the reaction role in the dashboard: remove one pair, add a different one. Confirm on Discord that the bot's old reaction is gone and the new one appears; react with the new emoji, confirm the new role is granted.
- [ ] **Step 8:** Delete the reaction role from the dashboard. Confirm the bot's reactions are removed from the message and the entry disappears from the list.
- [ ] **Step 9:** Manually delete the underlying Discord message (create a fresh test reaction-role first if needed), then restart the bot (`python main.py`) — confirm the dangling entry is auto-removed from `reaction_roles.json` and no longer shows in the dashboard list.
- [ ] **Step 10:** Record results in the progress ledger. No commit (nothing changed).

---

## Self-Review Notes

- **Spec coverage:** data model + config helpers → Task 1; bot listeners (raw events, `payload.member` availability nuance, toggle behavior, reason format) → Task 3; startup self-check/self-healing → Task 3 (`cleanup_missing_messages`, called from `setup()`); full CRUD API with the exact validation order from the spec (empty → duplicate emoji → channel → message → role assignability) → Tasks 4-5; `GET /api/emojis` → Task 5; UI (list, create/edit form, read-only channel/message on edit, per-pair emoji+role picker, "+ добавить пару") → Task 8; sidebar wiring → Task 8. "Вне рамок" (allow/blacklist by role, bot-composed messages) are correctly absent from every task.
- **Gap found and closed during planning:** the spec's UI section calls for a channel `select` in the creation form but never defined a `GET /api/channels` endpoint in its API section. Added it to Task 5 alongside `GET /api/emojis` (both are "supporting picker data" reads) — a minimal, obviously-required addition to make the approved UI possible, not scope creep.
- **Type consistency:** `ReactionRolePair`/`ReactionRoleEntry` (Task 7) match the backend's `serialize_entry` output (Task 4) field-for-field; `_is_role_assignable`/`_validate_pairs` (Task 4) are reused unmodified by Task 5's `PUT` handler; `FakeChannel`/`FakeMessage`/`FakeCustomEmoji`/`FakeBot.user` (Task 2) are used consistently by Tasks 3, 4, and 5's tests with the same constructor signatures throughout.
- **Placeholder scan:** none found — every step has complete code.
