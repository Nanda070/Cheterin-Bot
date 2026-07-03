# Дашборд, Фаза 4a (Обращения / Feedback Cases) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let staff view, filter, and accept/reject feedback/complaint cases (обращения) from the dashboard instead of only through Discord's private-thread buttons.

**Architecture:** The existing `close_case()` logic in `feedback_menu.py` is refactored into a new repo-root `feedback_core.py` module — a single `decide_case()` function shared by both the Discord button callback (thin wrapper) and a new dashboard route, exactly mirroring the `lockdown_core.py` precedent from Phase 2a. `create_feedback_case()` gains one line to persist the submitted answers (currently lost after the modal embed is built). New dashboard routes expose list/detail/decide endpoints reading `bot.feedback_cases` and `feedback_menu.get_feedback_categories()` directly (no duplicated config). Frontend adds a case list + detail panel, reusing the `Members`/`MemberDetailPanel` list-and-panel pattern from Phase 2a.

**Tech Stack:** Python: discord.py, aiohttp, pytest + pytest-aiohttp (existing fakes, extended). Frontend: React + TypeScript, existing design-system primitives, Vitest + Testing Library.

## Global Constraints

- All work happens in `C:\Users\adnan\Documents\coding\ChetMain_backup_20260701_211729`. Never touch `C:\Users\adnan\Documents\coding\ChetMain`.
- Local-only git repo: commit each task with `git add <specific files>` + `git commit` — never bare `git add -A`.
- Spec of record: `docs/superpowers/specs/2026-07-03-dashboard-phase4a-feedback-cases-design.md`.
- `close_case()`'s refactor into `feedback_core.decide_case()` must not change the bot's existing Discord behavior in any observable way — same embeds, same DM, same thread lock/archive, same ephemeral messages on early-exit. This is a behavior-preserving extraction, not a redesign.
- **Deliberate, documented deviation from the original code**: the original `close_case()` guards the public-channel and thread update blocks with `isinstance(x, discord.TextChannel)` / `isinstance(x, discord.Thread)`. `decide_case()` uses `x is not None` instead — matching the `is None` check convention every dashboard route in this codebase already uses (`reaction_roles.py`, `embed_builder.py`), and making the function testable against this project's plain-Python fakes (which are not real discord.py subclasses, so `isinstance` checks against them are always `False`). In practice `bot.get_channel()` returning the wrong type for IDs captured from a real `TextChannel.send()`/`create_thread()` call is not a realistic scenario, so this is not a behavior change for the real bot.
- Feedback categories remain fully code-defined in this phase (`feedback_menu.get_feedback_categories()`) — the dashboard reads that same function, never duplicates or hardcodes category data. Category *editing* is out of scope (Phase 4b).
- Case state (`bot.feedback_cases`) is mutated only through `feedback_core.decide_case()` — no route writes to it directly.
- Session-derived acting user: `request["moderator"]` (a resolved `discord.Member`, set by `require_dashboard_access` — the established pattern from every prior phase), never a client-supplied ID.
- No secrets in any committed file. `.env` at the repo root contains real credentials — never read from it directly in test code; tests must monkeypatch the two env vars `get_feedback_categories()` needs (`CHANNEL_COMPLAINT_PLAY`, `ROLE_PLAYERS`) with dummy values, and reset `feedback_menu._feedback_categories_cache` to `None` first (it's a module-level cache that persists across test runs in the same process).
- Existing suites must stay green throughout: 171 pytest + 44 Vitest tests before this plan.

---

### Task 1: Test fakes — `FakeThread`, `FakeBot.get_channel`/`fetch_user`/`update_file`, `FakeMember.send`

**Files:**
- Modify: `dashboard/backend/tests/fakes.py` (extend `FakeMember`/`FakeGuild`/`FakeBot`, add `FakeThread` — every existing call site keeps working unchanged)
- Test: `dashboard/backend/tests/test_fakes_feedback_extensions.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `class FakeThread(thread_id, name="thread", messages=None, next_message_id=2000)` — `.archived`, `.locked` (bool, default `False`), `.send_calls`, `.send_raises`, `.edit_calls`, `.edit_raises`, async `fetch_message(message_id)` (raises `discord.NotFound` if absent, same as `FakeChannel`), async `send(**kwargs)` (creates and stores a `FakeMessage`, same behavior as `FakeChannel.send`), async `edit(**kwargs)` (records the call, updates `.archived`/`.locked` from `archived=`/`locked=` kwargs); `FakeGuild(...)` gains `threads=None` (defaults `[]`); `FakeBot(...)` gains `fetchable_users=None` (defaults `[]`) and `.update_file_calls` (int, starts `0`), plus `def get_channel(self, channel_id)` (checks `self._guild.get_channel(channel_id)` first, then `self._guild.threads`, else `None`), async `fetch_user(self, user_id)` (checks `self._guild.get_member(user_id)` first, then `self._fetchable_users`, raises `discord.NotFound` if nowhere found), async `update_file(self)` (increments `.update_file_calls`); `FakeMember(...)` gains `.send_calls`, `.send_raises`, async `send(self, **kwargs)` (records the call, raises `.send_raises` if set — used to simulate DM delivery).

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_fakes_feedback_extensions.py`:

```python
import discord
import pytest

from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, FakeThread


@pytest.mark.asyncio
async def test_fake_thread_send_creates_and_stores_message():
    thread = FakeThread(700, next_message_id=3000)
    embed = discord.Embed(title="Hello")
    message = await thread.send(embed=embed)
    assert message.id == 3000
    assert message.embeds == [embed]
    fetched = await thread.fetch_message(3000)
    assert fetched is message


@pytest.mark.asyncio
async def test_fake_thread_edit_records_archived_and_locked():
    thread = FakeThread(700)
    await thread.edit(archived=True, locked=True)
    assert thread.archived is True
    assert thread.locked is True
    assert thread.edit_calls == [{"archived": True, "locked": True}]


@pytest.mark.asyncio
async def test_fake_thread_send_raises_when_configured():
    thread = FakeThread(700)
    thread.send_raises = discord.HTTPException.__new__(discord.HTTPException)
    with pytest.raises(discord.HTTPException):
        await thread.send(content="hi")


@pytest.mark.asyncio
async def test_fake_thread_fetch_message_raises_not_found():
    thread = FakeThread(700, messages={})
    with pytest.raises(discord.NotFound):
        await thread.fetch_message(999)


def test_fake_bot_get_channel_finds_channel_and_thread():
    channel = FakeChannel(500)
    thread = FakeThread(700)
    guild = FakeGuild(channels=[channel], threads=[thread])
    bot = FakeBot(guild)
    assert bot.get_channel(500) is channel
    assert bot.get_channel(700) is thread
    assert bot.get_channel(999) is None


@pytest.mark.asyncio
async def test_fake_bot_fetch_user_falls_back_when_not_in_guild():
    submitter = FakeMember(50, name="gone")
    guild = FakeGuild(members=[])
    bot = FakeBot(guild, fetchable_users=[submitter])
    user = await bot.fetch_user(50)
    assert user is submitter


@pytest.mark.asyncio
async def test_fake_bot_fetch_user_raises_when_nowhere_found():
    guild = FakeGuild()
    bot = FakeBot(guild)
    with pytest.raises(discord.NotFound):
        await bot.fetch_user(999)


@pytest.mark.asyncio
async def test_fake_bot_update_file_records_calls():
    guild = FakeGuild()
    bot = FakeBot(guild)
    await bot.update_file()
    await bot.update_file()
    assert bot.update_file_calls == 2


@pytest.mark.asyncio
async def test_fake_member_send_records_dm():
    member = FakeMember(50, name="user")
    embed = discord.Embed(title="DM")
    await member.send(embed=embed)
    assert member.send_calls == [{"embed": embed}]


@pytest.mark.asyncio
async def test_fake_member_send_raises_when_configured():
    member = FakeMember(50, name="user")
    member.send_raises = discord.HTTPException.__new__(discord.HTTPException)
    with pytest.raises(discord.HTTPException):
        await member.send(content="hi")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_fakes_feedback_extensions.py -v`
Expected: FAIL with `ImportError: cannot import name 'FakeThread'` (and `FakeGuild`/`FakeBot`/`FakeMember` missing the new params/methods)

- [ ] **Step 3: Modify `dashboard/backend/tests/fakes.py`**

Replace the current `FakeMember` class's `__init__` and add a `send` method. Find:

```python
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
```

Add these lines right after `self.action_raises = None` (still inside `__init__`):

```python
        self.send_calls = []
        self.send_raises = None
```

Then add this method inside the `FakeMember` class, alongside `ban`/`kick`/`add_roles`/`remove_roles`:

```python
    async def send(self, **kwargs):
        if self.send_raises:
            raise self.send_raises
        self.send_calls.append(kwargs)
```

Replace the current `FakeGuild.__init__`:

```python
class FakeGuild:
    def __init__(self, members=None, roles=None, me=None, channels=None, emojis=None, fetchable_members=None):
        self.members = members or []
        self.roles = roles or []
        self.me = me or FakeMember(1, name="bot", top_role=FakeRole(900, name="bot-role", position=50))
        self.channels = channels or []
        self.emojis = emojis or []
        self._fetchable_members = fetchable_members or []
```

with:

```python
class FakeGuild:
    def __init__(
        self, members=None, roles=None, me=None, channels=None, emojis=None, fetchable_members=None, threads=None
    ):
        self.members = members or []
        self.roles = roles or []
        self.me = me or FakeMember(1, name="bot", top_role=FakeRole(900, name="bot-role", position=50))
        self.channels = channels or []
        self.emojis = emojis or []
        self._fetchable_members = fetchable_members or []
        self.threads = threads or []
```

Add a new `FakeThread` class right after `FakeChannel`'s class body:

```python
class FakeThread:
    def __init__(self, thread_id, name="thread", messages=None, next_message_id=2000):
        self.id = thread_id
        self.name = name
        self._messages = messages or {}
        self._next_message_id = next_message_id
        self.send_calls = []
        self.send_raises = None
        self.edit_calls = []
        self.edit_raises = None
        self.archived = False
        self.locked = False

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

    async def edit(self, **kwargs):
        if self.edit_raises:
            raise self.edit_raises
        self.edit_calls.append(kwargs)
        if "archived" in kwargs:
            self.archived = kwargs["archived"]
        if "locked" in kwargs:
            self.locked = kwargs["locked"]
```

Replace the current `FakeBot` class:

```python
class FakeBot:
    def __init__(self, guild, user=None):
        self._guild = guild
        self.user = user or FakeMember(999999, name="ChetBot", bot=True)
        self.stats = {}
        self.feedback_cases = {}
        self.sent_logs = []

    def get_guild(self, guild_id):
        return self._guild

    async def send_log(self, embed):
        self.sent_logs.append(embed)

    def utcnow(self):
        return datetime.now(timezone.utc)
```

with:

```python
class FakeBot:
    def __init__(self, guild, user=None, fetchable_users=None):
        self._guild = guild
        self.user = user or FakeMember(999999, name="ChetBot", bot=True)
        self.stats = {}
        self.feedback_cases = {}
        self.sent_logs = []
        self._fetchable_users = fetchable_users or []
        self.update_file_calls = 0

    def get_guild(self, guild_id):
        return self._guild

    def get_channel(self, channel_id):
        found = self._guild.get_channel(channel_id)
        if found is not None:
            return found
        return next((t for t in self._guild.threads if t.id == channel_id), None)

    async def fetch_user(self, user_id):
        import discord

        member = self._guild.get_member(user_id)
        if member is not None:
            return member
        found = next((u for u in self._fetchable_users if u.id == user_id), None)
        if found is not None:
            return found
        raise discord.NotFound.__new__(discord.NotFound)

    async def update_file(self):
        self.update_file_calls += 1

    async def send_log(self, embed):
        self.sent_logs.append(embed)

    def utcnow(self):
        return datetime.now(timezone.utc)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_fakes_feedback_extensions.py -v`
Expected: PASS (10 tests)

- [ ] **Step 5: Run the full backend suite to confirm no regressions**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (171 + 10 = 181)

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/tests/fakes.py dashboard/backend/tests/test_fakes_feedback_extensions.py
git commit -m "test: extend fakes with FakeThread, FakeBot.get_channel/fetch_user, FakeMember.send"
```

---

### Task 2: `feedback_core.py` — `decide_case()` shared decision logic

**Files:**
- Create: `feedback_core.py` (repo root, next to `lockdown_core.py`)
- Test: `dashboard/backend/tests/test_feedback_core.py`

**Interfaces:**
- Consumes: `FakeBot`, `FakeGuild`, `FakeMember`, `FakeChannel`, `FakeThread`, `FakeMessage` (Task 1); `feedback_menu.get_feedback_categories`/`FeedbackDecisionView` (existing, imported locally inside the function to avoid a circular import — `feedback_menu.py` will import `feedback_core` at module level in Task 3).
- Produces: `upsert_embed_field(embed, field_name, value, inline=False)`; `async def decide_case(bot, guild, case_id: str, approved: bool, decided_by_id: int, decided_by_mention: str) -> dict` — returns `{"ok": True, "error": None}` on success, or `{"ok": False, "error": "not_found" | "already_decided"}` on early rejection.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_feedback_core.py`:

```python
import discord
import pytest

import feedback_core
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, FakeMessage, FakeThread


@pytest.fixture(autouse=True)
def isolated_feedback_categories(monkeypatch):
    monkeypatch.setenv("CHANNEL_COMPLAINT_PLAY", "500")
    monkeypatch.setenv("ROLE_PLAYERS", "111")
    import feedback_menu

    monkeypatch.setattr(feedback_menu, "_feedback_categories_cache", None)
    yield


def _base_embed(title="Case"):
    return discord.Embed(title=title, color=discord.Color.orange())


def _build_case(public_message_id, decision_message_id, status="pending"):
    return {
        "case_id": "PR-0001",
        "category_key": "players",
        "submitter_id": 50,
        "public_channel_id": 500,
        "public_message_id": public_message_id,
        "thread_id": 700,
        "decision_message_id": decision_message_id,
        "status": status,
        "created_at": "2026-07-03T00:00:00+00:00",
    }


@pytest.mark.asyncio
async def test_decide_case_not_found_returns_error():
    guild = FakeGuild()
    bot = FakeBot(guild)
    result = await feedback_core.decide_case(bot, guild, "MISSING", True, decided_by_id=10, decided_by_mention="<@10>")
    assert result == {"ok": False, "error": "not_found"}


@pytest.mark.asyncio
async def test_decide_case_already_decided_returns_error():
    guild = FakeGuild()
    bot = FakeBot(guild)
    bot.feedback_cases["PR-0001"] = _build_case(900, 901, status="approved")
    result = await feedback_core.decide_case(
        bot, guild, "PR-0001", True, decided_by_id=10, decided_by_mention="<@10>"
    )
    assert result == {"ok": False, "error": "already_decided"}


@pytest.mark.asyncio
async def test_decide_case_approve_updates_status_persists_and_notifies():
    submitter = FakeMember(50, name="submitter")
    public_message = FakeMessage(900, embeds=[_base_embed()])
    channel = FakeChannel(500, messages={900: public_message})
    decision_message = FakeMessage(901, embeds=[_base_embed()])
    thread = FakeThread(700, messages={901: decision_message})
    guild = FakeGuild(members=[submitter], channels=[channel], threads=[thread])
    bot = FakeBot(guild)
    bot.feedback_cases["PR-0001"] = _build_case(900, 901)

    result = await feedback_core.decide_case(
        bot, guild, "PR-0001", True, decided_by_id=10, decided_by_mention="<@10>"
    )

    assert result == {"ok": True, "error": None}
    assert bot.feedback_cases["PR-0001"]["status"] == "approved"
    assert bot.feedback_cases["PR-0001"]["reviewed_by"] == 10
    assert bot.update_file_calls == 1
    assert public_message.edit_calls[0]["embed"].color.value == discord.Color.green().value
    assert decision_message.edit_calls[0]["embed"].color.value == discord.Color.green().value
    assert len(submitter.send_calls) == 1
    assert thread.archived is True
    assert thread.locked is True
    assert len(thread.send_calls) == 1


@pytest.mark.asyncio
async def test_decide_case_reject_sets_denied_status_and_red_color():
    submitter = FakeMember(50, name="submitter")
    public_message = FakeMessage(900, embeds=[_base_embed()])
    channel = FakeChannel(500, messages={900: public_message})
    decision_message = FakeMessage(901, embeds=[_base_embed()])
    thread = FakeThread(700, messages={901: decision_message})
    guild = FakeGuild(members=[submitter], channels=[channel], threads=[thread])
    bot = FakeBot(guild)
    bot.feedback_cases["PR-0001"] = _build_case(900, 901)

    result = await feedback_core.decide_case(
        bot, guild, "PR-0001", False, decided_by_id=10, decided_by_mention="<@10>"
    )

    assert result == {"ok": True, "error": None}
    assert bot.feedback_cases["PR-0001"]["status"] == "denied"
    assert public_message.edit_calls[0]["embed"].color.value == discord.Color.red().value


@pytest.mark.asyncio
async def test_decide_case_dm_falls_back_to_fetch_user_when_submitter_left_guild():
    gone_submitter = FakeMember(50, name="gone")
    decision_message = FakeMessage(901, embeds=[_base_embed()])
    thread = FakeThread(700, messages={901: decision_message})
    guild = FakeGuild(members=[], threads=[thread])  # submitter NOT in guild.members
    bot = FakeBot(guild, fetchable_users=[gone_submitter])
    bot.feedback_cases["PR-0001"] = _build_case(900, 901)

    result = await feedback_core.decide_case(
        bot, guild, "PR-0001", True, decided_by_id=10, decided_by_mention="<@10>"
    )

    assert result == {"ok": True, "error": None}
    assert len(gone_submitter.send_calls) == 1


@pytest.mark.asyncio
async def test_decide_case_survives_missing_public_channel():
    submitter = FakeMember(50, name="submitter")
    decision_message = FakeMessage(901, embeds=[_base_embed()])
    thread = FakeThread(700, messages={901: decision_message})
    # No channels configured -- public_channel_id 500 won't resolve.
    guild = FakeGuild(members=[submitter], channels=[], threads=[thread])
    bot = FakeBot(guild)
    bot.feedback_cases["PR-0001"] = _build_case(900, 901)

    result = await feedback_core.decide_case(
        bot, guild, "PR-0001", True, decided_by_id=10, decided_by_mention="<@10>"
    )

    assert result == {"ok": True, "error": None}
    assert bot.feedback_cases["PR-0001"]["status"] == "approved"
    assert len(submitter.send_calls) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_feedback_core.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'feedback_core'`

- [ ] **Step 3: Implement `feedback_core.py`**

```python
import logging

import discord

logger = logging.getLogger(__name__)


def upsert_embed_field(embed: discord.Embed, field_name: str, value: str, inline: bool = False):
    for index, field in enumerate(embed.fields):
        if field.name == field_name:
            embed.set_field_at(index, name=field_name, value=value, inline=inline)
            return
    embed.add_field(name=field_name, value=value, inline=inline)


async def decide_case(bot, guild, case_id: str, approved: bool, decided_by_id: int, decided_by_mention: str) -> dict:
    from feedback_menu import FeedbackDecisionView, get_feedback_categories

    case_data = bot.feedback_cases.get(case_id)
    if not case_data:
        return {"ok": False, "error": "not_found"}
    if case_data.get("status") != "pending":
        return {"ok": False, "error": "already_decided"}

    category_key = case_data["category_key"]
    config = get_feedback_categories()[category_key]
    status_text = "Принято" if approved else "Отклонено"
    reviewed_status = f"Рассмотрено · {status_text}"

    case_data["status"] = "approved" if approved else "denied"
    case_data["status_label"] = reviewed_status
    case_data["reviewed_by"] = decided_by_id
    case_data["reviewed_at"] = bot.utcnow().isoformat()
    await bot.update_file()

    color = discord.Color.green() if approved else discord.Color.red()

    public_channel = bot.get_channel(case_data.get("public_channel_id"))
    if public_channel is not None:
        try:
            public_message = await public_channel.fetch_message(case_data["public_message_id"])
            if public_message.embeds:
                emb = public_message.embeds[0].copy()
                emb.color = color
                upsert_embed_field(emb, "Статус", reviewed_status, inline=True)
                upsert_embed_field(emb, "Рассмотрел", decided_by_mention, inline=False)
                await public_message.edit(embed=emb)
        except Exception as e:
            logger.warning("Не удалось обновить публичное сообщение для %s: %s", case_id, e)

    thread = bot.get_channel(case_data.get("thread_id"))
    if thread is not None:
        try:
            decision_message = await thread.fetch_message(case_data["decision_message_id"])
            if decision_message.embeds:
                emb = decision_message.embeds[0].copy()
                emb.color = color
                upsert_embed_field(emb, "Статус", reviewed_status, inline=False)
                upsert_embed_field(emb, "Рассмотрел", f"{decided_by_mention} (`{decided_by_id}`)", inline=False)
                await decision_message.edit(
                    embed=emb,
                    view=FeedbackDecisionView(bot, case_id, case_data["submitter_id"], category_key, disabled=True),
                )
        except Exception as e:
            logger.warning("Не удалось обновить сообщение решения для %s: %s", case_id, e)

    user = guild.get_member(case_data["submitter_id"]) if guild else None
    if user is None:
        try:
            user = await bot.fetch_user(case_data["submitter_id"])
        except Exception as e:
            logger.debug("Не удалось получить пользователя %s: %s", case_data["submitter_id"], e)

    dm_ok = False
    if user:
        dm_emb = discord.Embed(
            title=f"Результат по обращению №{case_id}",
            description="Ваше обращение было рассмотрено.",
            color=color,
            timestamp=bot.utcnow(),
        )
        dm_emb.add_field(name="Статус", value="Рассмотрено", inline=False)
        dm_emb.add_field(
            name="Итог", value=config["approved_text"] if approved else config["denied_text"], inline=False
        )
        dm_emb.add_field(name="Рассмотрел", value=f"{decided_by_mention} (`{decided_by_id}`)", inline=False)
        dm_emb.set_footer(text=f"Номер обращения: {case_id}")
        try:
            await user.send(embed=dm_emb)
            dm_ok = True
        except Exception as e:
            logger.debug("Не удалось отправить DM пользователю %s: %s", user.id, e)

    log_emb = discord.Embed(
        title="📌 Решение по обращению",
        description=(
            f"**Номер:** `{case_id}`\n"
            f"**Статус:** Рассмотрено\n"
            f"**Решение:** {status_text}\n"
            f"**Рассмотрел:** {decided_by_mention} (`{decided_by_id}`)\n"
            f"**DM:** {'Успешно' if dm_ok else 'Не удалось отправить'}"
        ),
        color=color,
        timestamp=bot.utcnow(),
    )
    await bot.send_log(log_emb)

    if thread is not None:
        dec_emb = discord.Embed(
            title=f"Решение по обращению {case_id}",
            color=color,
            timestamp=bot.utcnow(),
        )
        dec_emb.add_field(name="Статус", value=status_text, inline=False)
        dec_emb.add_field(name="Рассмотрел", value=f"{decided_by_mention} (`{decided_by_id}`)", inline=False)
        try:
            await thread.send(embed=dec_emb)
            await thread.edit(archived=True, locked=True)
        except Exception as e:
            logger.warning("Не удалось закрыть тред %s: %s", thread.id, e)

    return {"ok": True, "error": None}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_feedback_core.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Verify the module still imports cleanly**

Run: `python -c "import feedback_core"`
Expected: no output, exit code 0

- [ ] **Step 6: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (181 + 6 = 187)

- [ ] **Step 7: Commit**

```bash
git add feedback_core.py dashboard/backend/tests/test_feedback_core.py
git commit -m "feat: add feedback_core.decide_case shared decision logic"
```

---

### Task 3: Refactor `feedback_menu.py` to use `feedback_core.decide_case()`; persist submitted answers

**Files:**
- Modify: `feedback_menu.py`

**Interfaces:**
- Consumes: `feedback_core.decide_case` (Task 2).
- Produces: `close_case()` keeps its exact existing signature and observable behavior (same ephemeral messages, same embeds, same DM), now delegating to `feedback_core.decide_case()`; `bot.feedback_cases[case_id]["answers"]` — the submitted modal answers, now persisted (previously discarded after being rendered into the thread embed).

This task touches already-reviewed bot code that has no existing pytest coverage (Discord slash-command/interaction-driven code in this project is verified manually via Discord, never unit-tested — the same pattern `lockdown.py`'s slash commands follow, with only the extracted `_core.py` logic getting pytest coverage). Do not invent interaction-mocking tests for this task — verification is the import smoke test below plus a careful line-by-line diff review confirming no behavior changed.

- [ ] **Step 1: Read the current file**

Read `feedback_menu.py` in full first — you need its exact current content to make a precise, minimal diff. Do not guess at line numbers.

- [ ] **Step 2: Add the `feedback_core` import**

Near the top of the file, alongside the existing imports (after `import logging`), add:

```python
import feedback_core
```

- [ ] **Step 3: Delete the `upsert_embed_field` function**

Find and delete this entire function (it has moved to `feedback_core.py` in Task 2 and is no longer used anywhere in `feedback_menu.py` after this task's Step 4):

```python
def upsert_embed_field(embed: discord.Embed, field_name: str, value: str, inline: bool = False):
    for index, field in enumerate(embed.fields):
        if field.name == field_name:
            embed.set_field_at(index, name=field_name, value=value, inline=inline)
            return
    embed.add_field(name=field_name, value=value, inline=inline)
```

- [ ] **Step 4: Replace `close_case()` with a thin wrapper**

Find the entire existing `close_case()` function (from `async def close_case(interaction: discord.Interaction, bot, case_id: str, approved: bool):` down to its closing `except Exception as e:` block, roughly 100 lines) and replace it in full with:

```python
async def close_case(interaction: discord.Interaction, bot, case_id: str, approved: bool):
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    try:
        result = await feedback_core.decide_case(
            bot,
            interaction.guild,
            case_id,
            approved,
            decided_by_id=interaction.user.id,
            decided_by_mention=interaction.user.mention,
        )
        if not result["ok"]:
            await interaction.followup.send("Обращение не найдено или уже закрыто.", ephemeral=True)
    except Exception as e:
        logger.error("Ошибка при закрытии обращения %s: %s", case_id, e)
        await interaction.followup.send(
            "❌ Произошла ошибка при закрытии обращения. Администраторы уведомлены.", ephemeral=True
        )
```

- [ ] **Step 5: Persist submitted answers in `create_feedback_case()`**

Find the dict literal assigned to `bot.feedback_cases[case_id]` inside `create_feedback_case()`:

```python
    bot.feedback_cases[case_id] = {
        "case_id": case_id,
        "category_key": category_key,
        "submitter_id": interaction.user.id,
        "public_channel_id": parent_channel.id,
        "public_message_id": public_message.id,
        "thread_id": thread.id,
        "decision_message_id": decision_message.id,
        "status": "pending",
        "created_at": bot.utcnow().isoformat(),
    }
```

Add one new key, `"answers": answers,`, so it reads:

```python
    bot.feedback_cases[case_id] = {
        "case_id": case_id,
        "category_key": category_key,
        "submitter_id": interaction.user.id,
        "public_channel_id": parent_channel.id,
        "public_message_id": public_message.id,
        "thread_id": thread.id,
        "decision_message_id": decision_message.id,
        "status": "pending",
        "created_at": bot.utcnow().isoformat(),
        "answers": answers,
    }
```

- [ ] **Step 6: Verify the module still imports cleanly**

Run: `python -c "import feedback_menu"`
Expected: no output, exit code 0

- [ ] **Step 7: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (187 — this task adds no new tests, it's a behavior-preserving refactor of code with no existing pytest coverage; the suite must stay green because nothing else in `feedback_menu.py` changed)

- [ ] **Step 8: Commit**

```bash
git add feedback_menu.py
git commit -m "refactor: delegate close_case to feedback_core.decide_case, persist submitted answers"
```

---

### Task 4: `GET /api/feedback-cases` (list) + `GET /api/feedback-cases/{case_id}` (detail)

**Files:**
- Create: `dashboard/backend/routes/feedback.py`
- Test: `dashboard/backend/tests/test_feedback_routes.py`

**Interfaces:**
- Consumes: `feedback_menu.get_feedback_categories` (existing, imported as `import feedback_menu`, same bare top-level import style already used for `reaction_roles`/`embed_builder`); `require_dashboard_access` (Phase 2a); fakes from Task 1.
- Produces: `routes = web.RouteTableDef()` (this task's table gets one more route appended in Task 5); `VALID_STATUSES = {"pending", "approved", "denied"}`; `def serialize_case_summary(case_id, case_data, guild) -> dict`; `def serialize_case_detail(case_id, case_data, guild) -> dict`; `GET /api/feedback-cases` → `200 {"cases": [...]}` / `400`; `GET /api/feedback-cases/{case_id}` → `200 {...}` / `404`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_feedback_routes.py`:

```python
import pytest

from dashboard.backend.routes.feedback import routes as feedback_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_feedback_categories(monkeypatch):
    monkeypatch.setenv("CHANNEL_COMPLAINT_PLAY", "500")
    monkeypatch.setenv("ROLE_PLAYERS", "111")
    import feedback_menu

    monkeypatch.setattr(feedback_menu, "_feedback_categories_cache", None)
    yield


def _case(status="pending", submitter_id=50, created_at="2026-07-03T00:00:00+00:00"):
    return {
        "case_id": "PR-0001",
        "category_key": "players",
        "submitter_id": submitter_id,
        "public_channel_id": 500,
        "public_message_id": 900,
        "thread_id": 700,
        "decision_message_id": 901,
        "status": status,
        "created_at": created_at,
        "answers": {"offender": "SomePlayer", "complaint": "Grief"},
    }


def build(members=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    submitter = FakeMember(50, name="submitter")
    guild = FakeGuild(members=[moderator, submitter] + (members or []))
    return guild, make_moderation_app(FakeBot(guild), [feedback_routes])


@pytest.mark.asyncio
async def test_list_feedback_cases_empty(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/feedback-cases")
    assert resp.status == 200
    assert (await resp.json()) == {"cases": []}


@pytest.mark.asyncio
async def test_list_feedback_cases_returns_all_by_default(aiohttp_client):
    guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    app_bot = app["bot"]
    app_bot.feedback_cases["PR-0001"] = _case(status="pending")
    app_bot.feedback_cases["PR-0002"] = _case(status="approved", created_at="2026-07-02T00:00:00+00:00")

    resp = await client.get("/api/feedback-cases")
    assert resp.status == 200
    body = await resp.json()
    assert len(body["cases"]) == 2
    # newest first
    assert body["cases"][0]["case_id"] == "PR-0001"


@pytest.mark.asyncio
async def test_list_feedback_cases_filters_by_status(aiohttp_client):
    guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    app["bot"].feedback_cases["PR-0001"] = _case(status="pending")
    app["bot"].feedback_cases["PR-0002"] = _case(status="approved")

    resp = await client.get("/api/feedback-cases?status=pending")
    assert resp.status == 200
    body = await resp.json()
    assert [c["case_id"] for c in body["cases"]] == ["PR-0001"]


@pytest.mark.asyncio
async def test_list_feedback_cases_rejects_invalid_status(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/feedback-cases?status=bogus")
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_status"


@pytest.mark.asyncio
async def test_list_feedback_cases_resolves_submitter_display_name(aiohttp_client):
    guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    app["bot"].feedback_cases["PR-0001"] = _case(submitter_id=50)

    resp = await client.get("/api/feedback-cases")
    body = await resp.json()
    assert body["cases"][0]["submitter_display"] == "submitter"


@pytest.mark.asyncio
async def test_list_feedback_cases_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/feedback-cases")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_get_feedback_case_returns_full_detail_with_answers(aiohttp_client):
    guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    app["bot"].feedback_cases["PR-0001"] = _case()

    resp = await client.get("/api/feedback-cases/PR-0001")
    assert resp.status == 200
    body = await resp.json()
    assert body["case_id"] == "PR-0001"
    assert body["status"] == "pending"
    field_by_key = {f["key"]: f["value"] for f in body["fields"]}
    assert field_by_key["offender"] == "SomePlayer"
    assert field_by_key["complaint"] == "Grief"
    assert field_by_key["datetime"] == "—"  # not submitted, config field exists


@pytest.mark.asyncio
async def test_get_feedback_case_404_when_unknown(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/feedback-cases/MISSING")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_get_feedback_case_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/feedback-cases/PR-0001")
    assert resp.status == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_feedback_routes.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.routes.feedback'`

- [ ] **Step 3: Implement `dashboard/backend/routes/feedback.py`**

```python
from aiohttp import web

import feedback_menu
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

VALID_STATUSES = {"pending", "approved", "denied"}


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


def serialize_case_summary(case_id: str, case_data: dict, guild) -> dict:
    category_key = case_data["category_key"]
    config = feedback_menu.get_feedback_categories().get(category_key, {})
    submitter_id = case_data["submitter_id"]
    member = guild.get_member(submitter_id) if guild else None
    return {
        "case_id": case_id,
        "category_key": category_key,
        "category_title": config.get("case_title", category_key),
        "submitter_id": str(submitter_id),
        "submitter_display": member.display_name if member else str(submitter_id),
        "status": case_data["status"],
        "created_at": case_data.get("created_at"),
    }


def serialize_case_detail(case_id: str, case_data: dict, guild) -> dict:
    category_key = case_data["category_key"]
    config = feedback_menu.get_feedback_categories().get(category_key, {})
    submitter_id = case_data["submitter_id"]
    member = guild.get_member(submitter_id) if guild else None
    answers = case_data.get("answers", {})
    fields = [
        {"key": f["key"], "label": f["label"], "value": answers.get(f["key"], "—")}
        for f in config.get("fields", [])
    ]
    return {
        "case_id": case_id,
        "category_key": category_key,
        "category_title": config.get("case_title", category_key),
        "submitter_id": str(submitter_id),
        "submitter_display": member.display_name if member else str(submitter_id),
        "status": case_data["status"],
        "created_at": case_data.get("created_at"),
        "fields": fields,
        "public_channel_id": str(case_data["public_channel_id"]) if case_data.get("public_channel_id") else None,
        "public_message_id": str(case_data["public_message_id"]) if case_data.get("public_message_id") else None,
        "thread_id": str(case_data["thread_id"]) if case_data.get("thread_id") else None,
    }


@routes.get("/api/feedback-cases")
@require_dashboard_access
async def list_feedback_cases(request: web.Request) -> web.Response:
    status = request.query.get("status")
    if status and status not in VALID_STATUSES:
        return web.json_response({"error": "invalid_status"}, status=400)

    guild = _get_guild_or_none(request)
    bot = request.app["bot"]
    cases = [
        serialize_case_summary(case_id, case_data, guild)
        for case_id, case_data in bot.feedback_cases.items()
        if status is None or case_data.get("status") == status
    ]
    cases.sort(key=lambda c: c["created_at"] or "", reverse=True)

    return web.json_response({"cases": cases})


@routes.get("/api/feedback-cases/{case_id}")
@require_dashboard_access
async def get_feedback_case(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    case_id = request.match_info["case_id"]
    case_data = bot.feedback_cases.get(case_id)
    if case_data is None:
        return web.json_response({"error": "not_found"}, status=404)

    guild = _get_guild_or_none(request)
    return web.json_response(serialize_case_detail(case_id, case_data, guild))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_feedback_routes.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routes/feedback.py dashboard/backend/tests/test_feedback_routes.py
git commit -m "feat(dashboard): add GET list/detail routes for feedback cases"
```

---

### Task 5: `POST /api/feedback-cases/{case_id}/decide`

**Files:**
- Modify: `dashboard/backend/routes/feedback.py` (append)
- Test: `dashboard/backend/tests/test_feedback_routes.py` (append)

**Interfaces:**
- Consumes: everything from Task 4; `feedback_core.decide_case` (Task 2, imported as `import feedback_core`).
- Produces: `POST /api/feedback-cases/{case_id}/decide` → `200 {"ok": true}` / `400`/`404`/`409`/`503`.

- [ ] **Step 1: Write the failing test**

Append to `dashboard/backend/tests/test_feedback_routes.py` (add `import discord`, `import feedback_core`, and `FakeChannel, FakeMessage, FakeThread` to the existing imports at the top of the file first):

```python
import discord

import feedback_core
from dashboard.backend.tests.fakes import FakeChannel, FakeMessage, FakeThread
```

Then append these tests:

```python
def build_with_channels():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    submitter = FakeMember(50, name="submitter")
    public_message = FakeMessage(900, embeds=[discord.Embed(title="Case")])
    channel = FakeChannel(500, messages={900: public_message})
    decision_message = FakeMessage(901, embeds=[discord.Embed(title="Case")])
    thread = FakeThread(700, messages={901: decision_message})
    guild = FakeGuild(members=[moderator, submitter], channels=[channel], threads=[thread])
    return guild, make_moderation_app(FakeBot(guild), [feedback_routes])


@pytest.mark.asyncio
async def test_decide_feedback_case_approves_and_persists(aiohttp_client):
    guild, app = build_with_channels()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    app["bot"].feedback_cases["PR-0001"] = _case(status="pending")

    resp = await client.post("/api/feedback-cases/PR-0001/decide", json={"approved": True})
    assert resp.status == 200
    assert (await resp.json()) == {"ok": True}
    assert app["bot"].feedback_cases["PR-0001"]["status"] == "approved"
    assert app["bot"].feedback_cases["PR-0001"]["reviewed_by"] == 10


@pytest.mark.asyncio
async def test_decide_feedback_case_404_when_unknown(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-cases/MISSING/decide", json={"approved": True})
    assert resp.status == 404
    assert (await resp.json())["error"] == "not_found"


@pytest.mark.asyncio
async def test_decide_feedback_case_409_when_already_decided(aiohttp_client):
    guild, app = build_with_channels()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    app["bot"].feedback_cases["PR-0001"] = _case(status="approved")

    resp = await client.post("/api/feedback-cases/PR-0001/decide", json={"approved": True})
    assert resp.status == 409
    assert (await resp.json())["error"] == "already_decided"


@pytest.mark.asyncio
async def test_decide_feedback_case_rejects_non_boolean_approved(aiohttp_client):
    guild, app = build_with_channels()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    app["bot"].feedback_cases["PR-0001"] = _case(status="pending")

    resp = await client.post("/api/feedback-cases/PR-0001/decide", json={"approved": "yes"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_decide_feedback_case_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/feedback-cases/PR-0001/decide", json={"approved": True})
    assert resp.status == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_feedback_routes.py -v`
Expected: FAIL — `POST /api/feedback-cases/{case_id}/decide` route doesn't exist yet (404s on the new tests).

- [ ] **Step 3: Append to `dashboard/backend/routes/feedback.py`**

Add this import at the top of the file, alongside `import feedback_menu`:

```python
import feedback_core
```

Then append this route at the end of the file:

```python
@routes.post("/api/feedback-cases/{case_id}/decide")
@require_dashboard_access
async def decide_feedback_case(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    bot = request.app["bot"]
    case_id = request.match_info["case_id"]

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    approved = body.get("approved")
    if not isinstance(approved, bool):
        return web.json_response({"error": "invalid_request"}, status=400)

    moderator = request["moderator"]
    result = await feedback_core.decide_case(
        bot,
        guild,
        case_id,
        approved,
        decided_by_id=moderator.id,
        decided_by_mention=f"<@{moderator.id}>",
    )
    if not result["ok"]:
        status_code = 404 if result["error"] == "not_found" else 409
        return web.json_response({"error": result["error"]}, status=status_code)

    return web.json_response({"ok": True})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_feedback_routes.py -v`
Expected: PASS (14 tests total in this file)

- [ ] **Step 5: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (187 + 9 + 5 = 201)

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/feedback.py dashboard/backend/tests/test_feedback_routes.py
git commit -m "feat(dashboard): add POST decide route for feedback cases"
```

---

### Task 6: Register routes in `app.py`

**Files:**
- Modify: `dashboard/backend/app.py` (add one import + one `add_routes` line)

**Interfaces:**
- Consumes: `dashboard.backend.routes.feedback.routes` (Tasks 4-5).
- Produces: all Phase 4a endpoints live in the real app.

`main.py` is NOT touched by this task — the `FeedbackMenu` cog is already loaded via the existing `setup_hook` (from before this project's dashboard work began); only the new dashboard route table needs registering.

- [ ] **Step 1: Add the import and route registration to `dashboard/backend/app.py`**

Read the current file first. Add this import alongside the existing route imports (after `from .routes.embed_builder import routes as embed_builder_routes`):

```python
from .routes.feedback import routes as feedback_routes
```

Add this line alongside the existing `app.add_routes(...)` calls (after `app.add_routes(embed_builder_routes)`):

```python
    app.add_routes(feedback_routes)
```

- [ ] **Step 2: Verify the file still imports cleanly**

Run: `python -c "import main"`
Expected: no output, exit code 0

- [ ] **Step 3: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (201)

- [ ] **Step 4: Commit**

```bash
git add dashboard/backend/app.py
git commit -m "feat: register feedback-cases routes"
```

---

### Task 7: Frontend API client — feedback-case functions

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts` (append; do NOT change any existing export)
- Test: `dashboard/frontend/src/api/feedback.test.ts`

**Interfaces:**
- Consumes: existing `apiFetch`, `jsonInit` (already in `client.ts`).
- Produces: `interface FeedbackCaseSummary { case_id: string; category_key: string; category_title: string; submitter_id: string; submitter_display: string; status: 'pending' | 'approved' | 'denied'; created_at: string | null }`; `interface FeedbackCaseField { key: string; label: string; value: string }`; `interface FeedbackCaseDetail extends FeedbackCaseSummary { fields: FeedbackCaseField[]; public_channel_id: string | null; public_message_id: string | null; thread_id: string | null }`; `fetchFeedbackCases(status?: string): Promise<FeedbackCaseSummary[]>`; `fetchFeedbackCaseDetail(caseId: string): Promise<FeedbackCaseDetail>`; `decideFeedbackCase(caseId: string, approved: boolean): Promise<void>`.

- [ ] **Step 1: Write the failing test**

`dashboard/frontend/src/api/feedback.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from 'vitest'
import { decideFeedbackCase, fetchFeedbackCaseDetail, fetchFeedbackCases } from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('feedback cases api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchFeedbackCases unwraps the list with no status filter', async () => {
    const cases = [
      {
        case_id: 'PR-0001',
        category_key: 'players',
        category_title: 'Жалоба на участника',
        submitter_id: '50',
        submitter_display: 'submitter',
        status: 'pending',
        created_at: '2026-07-03T00:00:00+00:00',
      },
    ]
    const fetchMock = vi.fn().mockResolvedValue(okJson({ cases }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchFeedbackCases()
    expect(result).toEqual(cases)
    expect(fetchMock).toHaveBeenCalledWith('/api/feedback-cases', expect.anything())
  })

  it('fetchFeedbackCases includes the status query param when given', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ cases: [] }))
    vi.stubGlobal('fetch', fetchMock)

    await fetchFeedbackCases('pending')
    expect(fetchMock).toHaveBeenCalledWith('/api/feedback-cases?status=pending', expect.anything())
  })

  it('fetchFeedbackCaseDetail GETs by case id', async () => {
    const detail = {
      case_id: 'PR-0001',
      category_key: 'players',
      category_title: 'Жалоба на участника',
      submitter_id: '50',
      submitter_display: 'submitter',
      status: 'pending',
      created_at: '2026-07-03T00:00:00+00:00',
      fields: [{ key: 'offender', label: 'Ник / ID участника', value: 'SomePlayer' }],
      public_channel_id: '500',
      public_message_id: '900',
      thread_id: '700',
    }
    const fetchMock = vi.fn().mockResolvedValue(okJson(detail))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchFeedbackCaseDetail('PR-0001')
    expect(result).toEqual(detail)
    expect(fetchMock).toHaveBeenCalledWith('/api/feedback-cases/PR-0001', expect.anything())
  })

  it('decideFeedbackCase POSTs the approved flag', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await decideFeedbackCase('PR-0001', true)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/feedback-cases/PR-0001/decide',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ approved: true }) }),
    )
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd dashboard/frontend && npm run test`
Expected: FAIL — new exports don't exist.

- [ ] **Step 3: Append to `dashboard/frontend/src/api/client.ts`**

```ts
export interface FeedbackCaseSummary {
  case_id: string
  category_key: string
  category_title: string
  submitter_id: string
  submitter_display: string
  status: 'pending' | 'approved' | 'denied'
  created_at: string | null
}

export interface FeedbackCaseField {
  key: string
  label: string
  value: string
}

export interface FeedbackCaseDetail extends FeedbackCaseSummary {
  fields: FeedbackCaseField[]
  public_channel_id: string | null
  public_message_id: string | null
  thread_id: string | null
}

export async function fetchFeedbackCases(status?: string): Promise<FeedbackCaseSummary[]> {
  const path = status ? `/api/feedback-cases?status=${status}` : '/api/feedback-cases'
  const body = await apiFetch<{ cases: FeedbackCaseSummary[] }>(path)
  return body.cases
}

export function fetchFeedbackCaseDetail(caseId: string): Promise<FeedbackCaseDetail> {
  return apiFetch(`/api/feedback-cases/${caseId}`)
}

export async function decideFeedbackCase(caseId: string, approved: boolean): Promise<void> {
  await apiFetch(`/api/feedback-cases/${caseId}/decide`, jsonInit('POST', { approved }))
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test`
Expected: PASS — 4 new + all existing (48 total)

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/feedback.test.ts
git commit -m "feat(dashboard): add feedback-case API client functions"
```

---

### Task 8: Frontend UI — `FeedbackCasesPage` + `FeedbackCaseDetailPanel`, wire into sidebar

**Files:**
- Create: `dashboard/frontend/src/pages/FeedbackCases.tsx`
- Create: `dashboard/frontend/src/pages/FeedbackCaseDetailPanel.tsx`
- Test: `dashboard/frontend/src/pages/FeedbackCases.test.tsx`
- Test: `dashboard/frontend/src/pages/FeedbackCaseDetailPanel.test.tsx`
- Modify: `dashboard/frontend/src/App.tsx` (add a new `feedback` route)
- Modify: `dashboard/frontend/src/pages/DashboardShell.tsx` (give the "Feedback и тикеты" sidebar entry a `to: '/feedback'`)

**Interfaces:**
- Consumes: `fetchFeedbackCases`, `fetchFeedbackCaseDetail`, `decideFeedbackCase`, types `FeedbackCaseSummary`/`FeedbackCaseDetail`/`FeedbackCaseField` (Task 7); `Card`, `Button` (existing design system).
- Produces: `FeedbackCasesPage()`; `FeedbackCaseDetailPanel({ caseId, onClose, onDecided }: { caseId: string; onClose: () => void; onDecided: () => void })`.

- [ ] **Step 1: Write the failing tests**

`dashboard/frontend/src/pages/FeedbackCaseDetailPanel.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { FeedbackCaseDetailPanel } from './FeedbackCaseDetailPanel'

const sampleDetail: client.FeedbackCaseDetail = {
  case_id: 'PR-0001',
  category_key: 'players',
  category_title: 'Жалоба на участника',
  submitter_id: '50',
  submitter_display: 'submitter',
  status: 'pending',
  created_at: '2026-07-03T00:00:00+00:00',
  fields: [{ key: 'offender', label: 'Ник / ID участника', value: 'SomePlayer' }],
  public_channel_id: '500',
  public_message_id: '900',
  thread_id: '700',
}

describe('FeedbackCaseDetailPanel', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('shows the case fields and category title', async () => {
    vi.spyOn(client, 'fetchFeedbackCaseDetail').mockResolvedValue(sampleDetail)

    render(<FeedbackCaseDetailPanel caseId="PR-0001" onClose={() => {}} onDecided={() => {}} />)

    await waitFor(() => screen.getByText('Жалоба на участника'))
    expect(screen.getByText('SomePlayer')).toBeInTheDocument()
  })

  it('accepts a pending case', async () => {
    vi.spyOn(client, 'fetchFeedbackCaseDetail').mockResolvedValue(sampleDetail)
    const decideSpy = vi.spyOn(client, 'decideFeedbackCase').mockResolvedValue(undefined)
    const onDecided = vi.fn()

    render(<FeedbackCaseDetailPanel caseId="PR-0001" onClose={() => {}} onDecided={onDecided} />)

    await waitFor(() => screen.getByText('Принять'))
    fireEvent.click(screen.getByText('Принять'))

    await waitFor(() => expect(decideSpy).toHaveBeenCalledWith('PR-0001', true))
    await waitFor(() => expect(onDecided).toHaveBeenCalled())
  })

  it('disables decision buttons when the case is already decided', async () => {
    vi.spyOn(client, 'fetchFeedbackCaseDetail').mockResolvedValue({ ...sampleDetail, status: 'approved' })

    render(<FeedbackCaseDetailPanel caseId="PR-0001" onClose={() => {}} onDecided={() => {}} />)

    await waitFor(() => screen.getByText('Принять'))
    expect(screen.getByText('Принять')).toBeDisabled()
    expect(screen.getByText('Отклонить')).toBeDisabled()
  })
})
```

`dashboard/frontend/src/pages/FeedbackCases.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { FeedbackCasesPage } from './FeedbackCases'

describe('FeedbackCasesPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('lists cases filtered to pending by default', async () => {
    vi.spyOn(client, 'fetchFeedbackCases').mockResolvedValue([
      {
        case_id: 'PR-0001',
        category_key: 'players',
        category_title: 'Жалоба на участника',
        submitter_id: '50',
        submitter_display: 'submitter',
        status: 'pending',
        created_at: '2026-07-03T00:00:00+00:00',
      },
    ])

    render(<FeedbackCasesPage />)

    await waitFor(() => expect(client.fetchFeedbackCases).toHaveBeenCalledWith('pending'))
    expect(await screen.findByText('submitter')).toBeInTheDocument()
  })

  it('reloads with the selected status filter', async () => {
    const fetchSpy = vi.spyOn(client, 'fetchFeedbackCases').mockResolvedValue([])

    render(<FeedbackCasesPage />)

    await waitFor(() => screen.getByLabelText('Статус'))
    fireEvent.change(screen.getByLabelText('Статус'), { target: { value: 'approved' } })

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith('approved'))
  })

  it('shows empty state when there are no cases', async () => {
    vi.spyOn(client, 'fetchFeedbackCases').mockResolvedValue([])

    render(<FeedbackCasesPage />)

    expect(await screen.findByText('Обращений нет.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm run test`
Expected: FAIL — `Cannot find module './FeedbackCaseDetailPanel'` / `Cannot find module './FeedbackCases'`.

- [ ] **Step 3: Implement `dashboard/frontend/src/pages/FeedbackCaseDetailPanel.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { decideFeedbackCase, fetchFeedbackCaseDetail, type FeedbackCaseDetail } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

interface Props {
  caseId: string
  onClose: () => void
  onDecided: () => void
}

export function FeedbackCaseDetailPanel({ caseId, onClose, onDecided }: Props) {
  const [detail, setDetail] = useState<FeedbackCaseDetail | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchFeedbackCaseDetail(caseId)
      .then(setDetail)
      .catch(() => setError('Не удалось загрузить обращение'))
  }, [caseId])

  const decide = async (approved: boolean) => {
    setBusy(true)
    setError('')
    try {
      await decideFeedbackCase(caseId, approved)
      onDecided()
    } catch {
      setError('Не удалось принять решение')
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

  const decided = detail.status !== 'pending'

  return (
    <Card className="animate-fade-in-up flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-semibold text-foreground">
            {detail.category_title} · {detail.case_id}
          </h2>
          <p className="text-xs text-muted">
            От {detail.submitter_display} · {detail.status}
          </p>
        </div>
        <button onClick={onClose} className="cursor-pointer text-muted hover:text-foreground">
          ×
        </button>
      </div>

      <dl className="flex flex-col gap-2 text-sm">
        {detail.fields.map((field) => (
          <div key={field.key}>
            <dt className="text-muted">{field.label}</dt>
            <dd className="whitespace-pre-wrap text-foreground">{field.value}</dd>
          </div>
        ))}
      </dl>

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="flex gap-2 border-t border-border pt-4">
        <Button variant="primary" onClick={() => decide(true)} disabled={busy || decided}>
          Принять
        </Button>
        <Button variant="danger" onClick={() => decide(false)} disabled={busy || decided}>
          Отклонить
        </Button>
      </div>
    </Card>
  )
}
```

- [ ] **Step 4: Implement `dashboard/frontend/src/pages/FeedbackCases.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { fetchFeedbackCases, type FeedbackCaseSummary } from '../api/client'
import { Card } from '../components/ui/Card'
import { FeedbackCaseDetailPanel } from './FeedbackCaseDetailPanel'

type StatusFilter = 'pending' | 'approved' | 'denied' | 'all'

export function FeedbackCasesPage() {
  const [status, setStatus] = useState<StatusFilter>('pending')
  const [cases, setCases] = useState<FeedbackCaseSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState('')

  const reload = () => {
    fetchFeedbackCases(status === 'all' ? undefined : status)
      .then(setCases)
      .catch(() => setError('Не удалось загрузить обращения'))
  }

  useEffect(reload, [status])

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <div className="mb-4 flex items-center gap-3">
          <h1 className="text-lg font-semibold text-foreground">Обращения</h1>
          <label className="ml-auto text-sm text-muted" htmlFor="feedback-status">
            Статус
          </label>
          <select
            id="feedback-status"
            value={status}
            onChange={(e) => setStatus(e.target.value as StatusFilter)}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="pending">На рассмотрении</option>
            <option value="approved">Принято</option>
            <option value="denied">Отклонено</option>
            <option value="all">Все</option>
          </select>
        </div>

        {error && <p className="mb-4 text-sm text-danger">{error}</p>}

        <div className="flex flex-col gap-2">
          {cases.map((c) => (
            <Card key={c.case_id} interactive className="!p-3" onClick={() => setSelectedId(c.case_id)}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-foreground">
                    {c.category_title} · {c.case_id}
                  </p>
                  <p className="text-xs text-muted">
                    {c.submitter_display} · {c.status}
                  </p>
                </div>
              </div>
            </Card>
          ))}
          {cases.length === 0 && <p className="text-sm text-muted">Обращений нет.</p>}
        </div>
      </div>

      {selectedId && (
        <div className="w-96 shrink-0">
          <FeedbackCaseDetailPanel
            caseId={selectedId}
            onClose={() => setSelectedId(null)}
            onDecided={() => {
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

- [ ] **Step 5: Wire the route in `App.tsx`**

Read the current file first. Add the import:

```tsx
import { FeedbackCasesPage } from './pages/FeedbackCases'
```

Add a new sibling route inside the existing protected route block:

```tsx
            <Route path="feedback" element={<FeedbackCasesPage />} />
```

- [ ] **Step 6: Wire the sidebar link in `DashboardShell.tsx`**

Read the current file first. In the `SECTIONS` array, change:

```tsx
  { label: 'Feedback и тикеты', icon: ChatCircleText },
```

to:

```tsx
  { label: 'Feedback и тикеты', icon: ChatCircleText, to: '/feedback' },
```

- [ ] **Step 7: Run tests + typecheck + build**

Run: `npm run test`, `npx tsc --noEmit`, `npm run build`
Expected: all green (54 Vitest tests total: 48 + 3 detail-panel + 3 list), no debug artifacts, `git status --short` clean before committing.

- [ ] **Step 8: Commit**

```bash
git add dashboard/frontend/src/pages/FeedbackCases.tsx dashboard/frontend/src/pages/FeedbackCaseDetailPanel.tsx dashboard/frontend/src/pages/FeedbackCases.test.tsx dashboard/frontend/src/pages/FeedbackCaseDetailPanel.test.tsx dashboard/frontend/src/App.tsx dashboard/frontend/src/pages/DashboardShell.tsx
git commit -m "feat(dashboard): add feedback cases list/detail UI, wire into sidebar"
```

---

### Task 9: Full end-to-end manual verification

**Files:** none (verification only).

- [ ] **Step 1:** Restart backend (`python main.py`) and frontend (`npm run dev`), open `http://localhost:5173`, log in.
- [ ] **Step 2:** Sidebar "Feedback и тикеты" (`/feedback`) is now a working link, showing pending cases by default.
- [ ] **Step 3:** In Discord, submit a real feedback case via the panel (`/feedback_panel send` if none is currently posted) — fill in the modal fields.
- [ ] **Step 4:** Confirm the new case appears in the dashboard's pending list, and clicking it shows the exact answers you submitted in the modal.
- [ ] **Step 5:** Click "Принять" (Accept) from the dashboard. Confirm in Discord: the public tracker embed updates to green/"Принято", the thread's decision embed updates and its buttons become disabled, a decision-announcement message appears in the thread and the thread is archived+locked, and you (as the submitter) receive a DM with the result.
- [ ] **Step 6:** Submit a second case, this time reject it from the Discord thread's own "Отклонить" button (not the dashboard) — confirm it still works exactly as before (this proves the refactor didn't change the bot's own behavior) and that the case now shows as "denied" in the dashboard list under the "Отклонено" filter.
- [ ] **Step 7:** Try clicking Accept/Reject on an already-decided case from the dashboard (e.g. reload the detail panel for a case you already decided) — confirm the buttons are disabled and no duplicate decision is possible.
- [ ] **Step 8:** Record results in the progress ledger. No commit (nothing changed).

---

## Self-Review Notes

- **Spec coverage:** shared decision logic reused between Discord and dashboard (no behavior drift) → Tasks 2-3 (`feedback_core.decide_case`, `close_case()` thin wrapper); persisted answers so the dashboard can show submitted content → Task 3 (`create_feedback_case()` one-line addition), consumed by Task 4's `serialize_case_detail`; list + status filter → Task 4; case detail with resolved field labels from `get_feedback_categories()` (no config duplication) → Task 4; accept/reject from the dashboard mirroring the Discord buttons exactly → Task 5; sidebar wiring → Task 8. "Вне рамок" items (category management, panel publishing, rejection-reason field) are correctly absent from every task.
- **Type consistency:** `FeedbackCaseSummary`/`FeedbackCaseDetail`/`FeedbackCaseField` (Task 7) match `serialize_case_summary`/`serialize_case_detail` (Task 4) field-for-field; `feedback_core.decide_case`'s `{"ok", "error"}` return shape is consumed identically by both `close_case()` (Task 3, translates to ephemeral text) and the dashboard route (Task 5, translates to HTTP status codes); `FakeThread`/`FakeBot.get_channel`/`fetch_user`/`update_file`/`FakeMember.send` (Task 1) are used consistently by Tasks 2, 4, and 5's tests with the same constructor signatures throughout.
- **Placeholder scan:** none found — every step has complete code.
- **Deliberate deviation documented:** the `isinstance` → `is not None` change in `decide_case()` (see Global Constraints) is called out explicitly rather than silently introduced, so a reviewer can independently judge it rather than discover it as an unexplained diff.
