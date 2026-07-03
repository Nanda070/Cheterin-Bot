# Phase 6: Dashboard Config Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move ~16 bot configuration values (channel IDs, role IDs, two ID lists, two URLs) from scattered `os.getenv(...)` calls across six files onto a dashboard-editable `config.json`, so changes apply live without a bot restart.

**Architecture:** A new `bot_config.py` module (mirroring `feedback_categories.py`'s established shape: `load_config`/`save_config`/no caching/`migrate_from_env_if_needed`) becomes the single source of truth. Six bot-side files switch their `os.getenv(KEY)` calls to `bot_config.get(KEY)`. A new `GET`/`PUT /api/config` route pair exposes it to the dashboard, and a new "Конфигурация" page (wiring the already-existing disabled sidebar placeholder) lets moderators edit it.

**Tech Stack:** Python 3.12, discord.py, aiohttp (backend); React + TypeScript + Vite + Vitest (frontend).

## Global Constraints

- No caching in `bot_config.py` — always read/write fresh from `config.json`.
- IDs (channel/role IDs, and the two ID-list fields' entries) are stored/serialized as strings; `int(...)`-conversion happens only at the exact Discord API call site.
- `BOT_TOKEN`, `GUILD_ID`, and the dashboard's own Discord OAuth secrets are NEVER migrated, NEVER dashboard-editable, and stay in `.env` exactly as they are today — no task in this plan touches any code path that reads them.
- Both routes gated by `@require_dashboard_access`.
- Validation order everywhere: structural checks first, Discord-existence checks second, permission last (enforced by the decorator running before the handler body).
- Never bare `git add -A`/`git add .` — stage only the specific files each task touches.
- Never silently change a stated numeric/behavioral constant or weaken a test assertion to make it pass — if something in this plan looks wrong, flag it in the task report and fix the test's own data, not production code.
- The six refactored bot-side files (`main.py`, `spam.py`, `welcome.py`, `tempban.py`, `memobb.py`, `button.py`) are event-listener/cog code — this project's standing convention (no `FakeInteraction`/event-simulation pattern exists, none gets invented) means these tasks get zero new pytest coverage; verify each by careful, minimal diff reading and a plain `python -c "import <module>"` check.
- Baseline before this plan: 301 backend (pytest) tests, 87 frontend (Vitest) tests, `tsc` clean, build clean, at commit `f50fcf6` (or later — confirm the actual current HEAD before starting; a small unrelated UX fix may have landed after this plan was written).

The 16 config keys, exactly as they appear in `.env` today (used verbatim as `config.json` keys):

| Key | Type | Discord kind |
|---|---|---|
| `LOG_CHANNEL_ID` | scalar | channel |
| `SPAM_EXCEPTION_CHANNELS` | list | channel |
| `TEMPBAN_CHANNEL_ID` | scalar | channel |
| `SPAM_LOG_CHANNEL_ID` | scalar | channel |
| `SPAM_LOG_ROLE_ID` | scalar | role |
| `WELCOME_CHANNEL_ID` | scalar | channel |
| `INVITE_LOG_CHANNEL_ID` | scalar | channel |
| `ANNOUNCEMENTS_CHANNEL_ID` | scalar | channel |
| `RULES_CHANNEL_ID` | scalar | channel |
| `ROLES_CHANNEL_ID` | scalar | channel |
| `SEARCH_PLAYERS_CHANNEL_ID` | scalar | channel |
| `CTD_ROLE_ID` | scalar | role |
| `CTD_CHANNEL_ID` | scalar | channel |
| `BUTTON_CREATE_ALLOWED_ROLES` | list | role |
| `BUTTON_WEBHOOK_URL` | scalar | text (URL, no Discord check) |
| `SERVER_INVITE_LINK` | scalar | text (URL, no Discord check) |

---

### Task 1: `bot_config.py`

**Files:**
- Create: `bot_config.py`
- Test: Create `dashboard/backend/tests/test_bot_config.py`

**Interfaces:**
- Produces: `load_config() -> dict`, `save_config(data: dict) -> None`, `get(key: str, default=None)`, `migrate_from_env_if_needed() -> None`. `CONFIG_FILE` module constant (used by tests to isolate the file path, same pattern as `feedback_categories.CONFIG_FILE`/`events.EVENTS_FILE`).

- [ ] **Step 1: Write the failing tests**

Create `dashboard/backend/tests/test_bot_config.py`:

```python
import json

import pytest

import bot_config


@pytest.fixture(autouse=True)
def isolated_config_file(tmp_path, monkeypatch):
    monkeypatch.setattr(bot_config, "CONFIG_FILE", str(tmp_path / "config.json"))


def test_load_config_returns_empty_dict_when_file_missing():
    assert bot_config.load_config() == {}


def test_save_then_load_roundtrips():
    bot_config.save_config({"LOG_CHANNEL_ID": "123"})
    assert bot_config.load_config() == {"LOG_CHANNEL_ID": "123"}


def test_load_config_reads_fresh_after_external_write():
    bot_config.load_config()
    with open(bot_config.CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"LOG_CHANNEL_ID": "999"}, f)
    assert bot_config.load_config() == {"LOG_CHANNEL_ID": "999"}


def test_get_returns_default_when_key_missing():
    bot_config.save_config({})
    assert bot_config.get("LOG_CHANNEL_ID", "fallback") == "fallback"


def test_get_returns_stored_value():
    bot_config.save_config({"LOG_CHANNEL_ID": "456"})
    assert bot_config.get("LOG_CHANNEL_ID") == "456"


def test_migrate_from_env_if_needed_creates_file_from_env(monkeypatch):
    monkeypatch.setenv("LOG_CHANNEL_ID", "100")
    monkeypatch.setenv("WELCOME_CHANNEL_ID", "200")
    bot_config.migrate_from_env_if_needed()
    data = bot_config.load_config()
    assert data["LOG_CHANNEL_ID"] == "100"
    assert data["WELCOME_CHANNEL_ID"] == "200"


def test_migrate_from_env_if_needed_defaults_missing_keys_to_empty(monkeypatch):
    monkeypatch.delenv("CTD_ROLE_ID", raising=False)
    bot_config.migrate_from_env_if_needed()
    data = bot_config.load_config()
    assert data["CTD_ROLE_ID"] == ""
    assert data["SPAM_EXCEPTION_CHANNELS"] == []


def test_migrate_from_env_if_needed_skips_if_file_exists(monkeypatch):
    bot_config.save_config({"LOG_CHANNEL_ID": "existing"})
    monkeypatch.setenv("LOG_CHANNEL_ID", "should_not_overwrite")
    bot_config.migrate_from_env_if_needed()
    assert bot_config.load_config()["LOG_CHANNEL_ID"] == "existing"


def test_migrate_from_env_if_needed_parses_list_keys_from_comma_separated_env(monkeypatch):
    monkeypatch.setenv("SPAM_EXCEPTION_CHANNELS", "111, 222,333")
    bot_config.migrate_from_env_if_needed()
    data = bot_config.load_config()
    assert data["SPAM_EXCEPTION_CHANNELS"] == ["111", "222", "333"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_bot_config.py -v`
Expected: all FAIL with `ModuleNotFoundError: No module named 'bot_config'`.

- [ ] **Step 3: Create `bot_config.py`**

```python
import json
import os

CONFIG_FILE = "config.json"

CONFIG_KEYS = [
    "LOG_CHANNEL_ID",
    "SPAM_EXCEPTION_CHANNELS",
    "TEMPBAN_CHANNEL_ID",
    "SPAM_LOG_CHANNEL_ID",
    "SPAM_LOG_ROLE_ID",
    "WELCOME_CHANNEL_ID",
    "INVITE_LOG_CHANNEL_ID",
    "ANNOUNCEMENTS_CHANNEL_ID",
    "RULES_CHANNEL_ID",
    "ROLES_CHANNEL_ID",
    "SEARCH_PLAYERS_CHANNEL_ID",
    "CTD_ROLE_ID",
    "CTD_CHANNEL_ID",
    "BUTTON_CREATE_ALLOWED_ROLES",
    "BUTTON_WEBHOOK_URL",
    "SERVER_INVITE_LINK",
]

LIST_KEYS = {"SPAM_EXCEPTION_CHANNELS", "BUTTON_CREATE_ALLOWED_ROLES"}


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


def get(key: str, default=None):
    return load_config().get(key, default)


def migrate_from_env_if_needed() -> None:
    if os.path.exists(CONFIG_FILE):
        return

    data = {}
    for key in CONFIG_KEYS:
        if key in LIST_KEYS:
            raw = os.getenv(key, "")
            data[key] = [v.strip() for v in raw.split(",") if v.strip()]
        else:
            data[key] = os.getenv(key, "")
    save_config(data)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_bot_config.py -v`
Expected: all 9 pass.

- [ ] **Step 5: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `310 passed` (301 baseline + 9 new).

- [ ] **Step 6: Commit**

```bash
git add bot_config.py dashboard/backend/tests/test_bot_config.py
git commit -m "feat: add bot_config.py for dashboard-editable bot configuration"
```

---

### Task 2: Refactor `main.py` and `spam.py`

**Files:**
- Modify: `main.py`
- Modify: `spam.py`

**Interfaces:**
- Consumes: `bot_config.get(key, default=None)`, `bot_config.migrate_from_env_if_needed()` (Task 1).

Read both files in full first — confirm they still match before editing.

- [ ] **Step 1: Wire the migration into `main.py` and refactor its one `os.getenv` config read**

Add `import bot_config` to `main.py`'s imports (alongside the existing `import feedback_categories`):

```python
import discord
from discord.ext import commands
import bot_config
import feedback_categories
import json
import os
import asyncio
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
```

In `setup_hook`, add the migration call right after the existing `feedback_categories.migrate_from_env_if_needed()` line:

```python
    async def setup_hook(self):
        feedback_categories.migrate_from_env_if_needed()
        bot_config.migrate_from_env_if_needed()
        await self.load_extension("feedback_menu")
```

In `send_log`, replace:

```python
    async def send_log(self, embed: discord.Embed):
        raw = os.getenv("LOG_CHANNEL_ID")
        if not raw:
            return
        ch = self.get_channel(int(raw))
        if ch:
            await ch.send(embed=embed)
```

with:

```python
    async def send_log(self, embed: discord.Embed):
        raw = bot_config.get("LOG_CHANNEL_ID")
        if not raw:
            return
        ch = self.get_channel(int(raw))
        if ch:
            await ch.send(embed=embed)
```

`import os` stays in `main.py` — it's still used for `GUILD_ID`, `BOT_TOKEN`, and `os.path.exists` in `load_data()`, none of which this task touches.

- [ ] **Step 2: Refactor `spam.py`**

Change the imports from:

```python
import discord
from discord.ext import commands, tasks
import os
import asyncio
from datetime import timedelta
import logging
```

to:

```python
import discord
from discord.ext import commands, tasks
import asyncio
from datetime import timedelta
import logging

import bot_config
```

(`os` is removed — after this task's changes, nothing in `spam.py` calls `os.` anymore.)

In `Spam.__init__`, remove the `self.exception_channels` block entirely — change:

```python
    def __init__(self, bot):
        self.bot = bot
        # {user_id: [ {"signature": str, "has_attachments": bool, "time": datetime, "channel_id": int}, ... ]}
        self.cache: dict[int, list] = {}
        # Набор user_id, для которых уже запущено наказание (защита от двойного срабатывания)
        self._processing: set[int] = set()

        env_val = os.getenv("SPAM_EXCEPTION_CHANNELS", "")
        self.exception_channels = [
            int(c.strip()) for c in env_val.split(",") if c.strip().isdigit()
        ]
        self._cleanup_cache.start()
```

to:

```python
    def __init__(self, bot):
        self.bot = bot
        # {user_id: [ {"signature": str, "has_attachments": bool, "time": datetime, "channel_id": int}, ... ]}
        self.cache: dict[int, list] = {}
        # Набор user_id, для которых уже запущено наказание (защита от двойного срабатывания)
        self._processing: set[int] = set()

        self._cleanup_cache.start()
```

This is a deliberate fix: `self.exception_channels` was previously computed once at cog-construction time, so even a `.env` edit needed a bot restart to take effect. Reading fresh at the point of use (next step) makes dashboard edits apply live, matching this project's established convention.

In `on_message`, replace:

```python
        # Не реагируем на канал Tempban
        tempban_channel_id = os.getenv("TEMPBAN_CHANNEL_ID")
        if tempban_channel_id and message.channel.id == int(tempban_channel_id):
            return
```

with:

```python
        # Не реагируем на канал Tempban
        tempban_channel_id = bot_config.get("TEMPBAN_CHANNEL_ID")
        if tempban_channel_id and message.channel.id == int(tempban_channel_id):
            return
```

Further down in the same `on_message`, replace:

```python
        # Игнорируем каналы-исключения
        if message.channel.id in self.exception_channels:
            return
```

with:

```python
        # Игнорируем каналы-исключения
        exception_channels = [int(c) for c in bot_config.get("SPAM_EXCEPTION_CHANNELS", [])]
        if message.channel.id in exception_channels:
            return
```

In `_punish`, replace:

```python
        log_channel_id = os.getenv("SPAM_LOG_CHANNEL_ID")
        role_ping_id = os.getenv("SPAM_LOG_ROLE_ID")
```

with:

```python
        log_channel_id = bot_config.get("SPAM_LOG_CHANNEL_ID")
        role_ping_id = bot_config.get("SPAM_LOG_ROLE_ID")
```

- [ ] **Step 3: Verify both files import cleanly**

Run: `python -c "import main"` then `python -c "import spam"`
Expected: both exit cleanly, no output, no traceback.

- [ ] **Step 4: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `310 passed` (unchanged from Task 1 — this task adds no new tests, per the standing convention for event-listener/cog code; the suite must not regress).

- [ ] **Step 5: Commit**

```bash
git add main.py spam.py
git commit -m "refactor: read config from bot_config.py in main.py and spam.py"
```

---

### Task 3: Refactor `welcome.py` and `tempban.py`

**Files:**
- Modify: `welcome.py`
- Modify: `tempban.py`

**Interfaces:**
- Consumes: `bot_config.get(key, default=None)` (Task 1).

Read both files in full first — confirm they still match before editing.

- [ ] **Step 1: Refactor `welcome.py`**

Change the imports from:

```python
import discord
from discord.ext import commands
from discord import app_commands
import os
```

to:

```python
import discord
from discord.ext import commands
from discord import app_commands

import bot_config
```

(`os` is removed — after this task's changes, nothing in `welcome.py` calls `os.` anymore.)

Replace:

```python
        welcome_ch_id = os.getenv("WELCOME_CHANNEL_ID")
        if welcome_ch_id:
            welcome_ch = self.bot.get_channel(int(welcome_ch_id))
```

with:

```python
        welcome_ch_id = bot_config.get("WELCOME_CHANNEL_ID")
        if welcome_ch_id:
            welcome_ch = self.bot.get_channel(int(welcome_ch_id))
```

Replace:

```python
            inv_ch_id = os.getenv("INVITE_LOG_CHANNEL_ID")
            if inv_ch_id:
                inv_ch = self.bot.get_channel(int(inv_ch_id))
```

with:

```python
            inv_ch_id = bot_config.get("INVITE_LOG_CHANNEL_ID")
            if inv_ch_id:
                inv_ch = self.bot.get_channel(int(inv_ch_id))
```

Replace:

```python
        dm_embed.add_field(name="〘❗〙 Объявления", value=f"<#{os.getenv('ANNOUNCEMENTS_CHANNEL_ID', '0')}> — все важные новости и анонсы", inline=False)
        dm_embed.add_field(name="〘📜〙 Правила", value=f"<#{os.getenv('RULES_CHANNEL_ID', '0')}> — ознакомься перед общением", inline=False)
        dm_embed.add_field(name="〘❗〙 Роли", value=f"<#{os.getenv('ROLES_CHANNEL_ID', '0')}> — получи доступ к привилегиям", inline=False)
        dm_embed.add_field(name="〘🔎〙 Поиск игроков", value=f"<#{os.getenv('SEARCH_PLAYERS_CHANNEL_ID', '0')}> — найдёшь тиммейтов под свои задачи", inline=False)
```

with:

```python
        dm_embed.add_field(name="〘❗〙 Объявления", value=f"<#{bot_config.get('ANNOUNCEMENTS_CHANNEL_ID') or '0'}> — все важные новости и анонсы", inline=False)
        dm_embed.add_field(name="〘📜〙 Правила", value=f"<#{bot_config.get('RULES_CHANNEL_ID') or '0'}> — ознакомься перед общением", inline=False)
        dm_embed.add_field(name="〘❗〙 Роли", value=f"<#{bot_config.get('ROLES_CHANNEL_ID') or '0'}> — получи доступ к привилегиям", inline=False)
        dm_embed.add_field(name="〘🔎〙 Поиск игроков", value=f"<#{bot_config.get('SEARCH_PLAYERS_CHANNEL_ID') or '0'}> — найдёшь тиммейтов под свои задачи", inline=False)
```

(`bot_config.get(key) or '0'` reproduces `os.getenv(key, '0')`'s exact fallback behavior: since `migrate_from_env_if_needed()` always creates every key with `""` as its empty default, a genuinely-unset value is `""`, and `"" or '0'` evaluates to `'0'` — same observable result as the original.)

- [ ] **Step 2: Refactor `tempban.py`**

Change the imports from:

```python
import discord
from discord.ext import commands
import os
import asyncio
import logging
```

to:

```python
import discord
from discord.ext import commands
import asyncio
import logging

import bot_config
```

(`os` is removed — after this task's changes, nothing in `tempban.py` calls `os.` anymore.)

Replace:

```python
        tempban_channel_id = os.getenv("TEMPBAN_CHANNEL_ID")
        if not tempban_channel_id or message.channel.id != int(tempban_channel_id):
            return
```

with:

```python
        tempban_channel_id = bot_config.get("TEMPBAN_CHANNEL_ID")
        if not tempban_channel_id or message.channel.id != int(tempban_channel_id):
            return
```

Replace:

```python
        log_channel_id = os.getenv("SPAM_LOG_CHANNEL_ID")
```

with:

```python
        log_channel_id = bot_config.get("SPAM_LOG_CHANNEL_ID")
```

Replace:

```python
        invite_link = os.getenv("SERVER_INVITE_LINK", "https://discord.gg/cheterin")
```

with:

```python
        invite_link = bot_config.get("SERVER_INVITE_LINK") or "https://discord.gg/cheterin"
```

- [ ] **Step 3: Verify both files import cleanly**

Run: `python -c "import welcome"` then `python -c "import tempban"`
Expected: both exit cleanly, no output, no traceback.

- [ ] **Step 4: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `310 passed` (unchanged — no new tests, per the standing convention).

- [ ] **Step 5: Commit**

```bash
git add welcome.py tempban.py
git commit -m "refactor: read config from bot_config.py in welcome.py and tempban.py"
```

---

### Task 4: Refactor `memobb.py` and `button.py`

**Files:**
- Modify: `memobb.py`
- Modify: `button.py`

**Interfaces:**
- Consumes: `bot_config.get(key, default=None)` (Task 1).

Read both files in full first — confirm they still match before editing.

- [ ] **Step 1: Refactor `memobb.py`**

Add `import bot_config` to the imports (`os` stays — `memobb.py`'s `_auto_close_tickets` loop still reads `GUILD_ID` via `os.getenv`, which is explicitly out of scope for this plan):

```python
import discord
from discord.ext import commands
from discord import app_commands
import os
import logging

import bot_config

logger = logging.getLogger("chetbot.memobb")
```

In `CTDCloseView.close_ticket`, replace:

```python
        raw_role_id = os.getenv("CTD_ROLE_ID")
```

with:

```python
        raw_role_id = bot_config.get("CTD_ROLE_ID")
```

In `CTDView.create_ticket`, replace:

```python
        raw_role_id = os.getenv("CTD_ROLE_ID")
```

with:

```python
        raw_role_id = bot_config.get("CTD_ROLE_ID")
```

In `CTD.ctd_setup`, replace:

```python
        raw_channel_id = os.getenv("CTD_CHANNEL_ID")
```

with:

```python
        raw_channel_id = bot_config.get("CTD_CHANNEL_ID")
```

Do NOT touch `_auto_close_tickets`'s `guild_id_raw = os.getenv("GUILD_ID")` — `GUILD_ID` stays in `.env`, out of scope.

- [ ] **Step 2: Refactor `button.py`**

Add `import bot_config` to the imports (`os` stays — `_load_buttons_config`/`_save_buttons_config` still use `os.path.exists`):

```python
import discord
from discord.ext import commands, tasks
from discord import app_commands
import time
import os
import json
import aiohttp

import bot_config

BUTTONS_FILE = "buttons_config.json"
COOLDOWN_SECONDS = 5
```

Replace:

```python
def _get_allowed_role_ids() -> set[int]:
    raw = os.getenv("BUTTON_CREATE_ALLOWED_ROLES", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip()}
```

with:

```python
def _get_allowed_role_ids() -> set[int]:
    raw = bot_config.get("BUTTON_CREATE_ALLOWED_ROLES", [])
    return {int(x) for x in raw}
```

(`BUTTON_CREATE_ALLOWED_ROLES` is now a genuine JSON array of ID strings in `config.json` — no more comma-splitting needed.)

Replace:

```python
        webhook_url = os.getenv("BUTTON_WEBHOOK_URL")
```

with:

```python
        webhook_url = bot_config.get("BUTTON_WEBHOOK_URL")
```

- [ ] **Step 3: Verify both files import cleanly**

Run: `python -c "import memobb"` then `python -c "import button"`
Expected: both exit cleanly, no output, no traceback.

- [ ] **Step 4: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `310 passed` (unchanged — no new tests, per the standing convention).

- [ ] **Step 5: Commit**

```bash
git add memobb.py button.py
git commit -m "refactor: read config from bot_config.py in memobb.py and button.py"
```

---

### Task 5: `GET /api/config` route

**Files:**
- Create: `dashboard/backend/routes/config.py`
- Modify: `dashboard/backend/app.py` (register the new route table)
- Test: Create `dashboard/backend/tests/test_config_routes.py`

**Interfaces:**
- Consumes: `bot_config.load_config()` (Task 1).
- Produces: `CHANNEL_FIELDS`, `ROLE_FIELDS`, `LIST_CHANNEL_FIELDS`, `LIST_ROLE_FIELDS`, `TEXT_FIELDS`, `ALL_FIELDS` (module-level lists in the new route file, all 16 keys partitioned by kind) — Task 6 reuses these unmodified for `PUT`'s validation.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/backend/tests/test_config_routes.py`:

```python
import pytest

import bot_config
from dashboard.backend.routes.config import routes as config_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_config_file(tmp_path, monkeypatch):
    monkeypatch.setattr(bot_config, "CONFIG_FILE", str(tmp_path / "config.json"))


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    return guild, make_moderation_app(FakeBot(guild), [config_routes])


@pytest.mark.asyncio
async def test_get_config_returns_defaults_when_file_missing(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/config")
    assert resp.status == 200
    body = await resp.json()
    assert body["LOG_CHANNEL_ID"] == ""
    assert body["SPAM_EXCEPTION_CHANNELS"] == []
    assert body["BUTTON_WEBHOOK_URL"] == ""


@pytest.mark.asyncio
async def test_get_config_returns_stored_values(aiohttp_client):
    bot_config.save_config(
        {
            "LOG_CHANNEL_ID": "500",
            "SPAM_EXCEPTION_CHANNELS": ["600", "700"],
            "SERVER_INVITE_LINK": "https://discord.gg/example",
        }
    )
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/config")
    body = await resp.json()
    assert body["LOG_CHANNEL_ID"] == "500"
    assert body["SPAM_EXCEPTION_CHANNELS"] == ["600", "700"]
    assert body["SERVER_INVITE_LINK"] == "https://discord.gg/example"


@pytest.mark.asyncio
async def test_get_config_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/config")
    assert resp.status == 401
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_config_routes.py -v`
Expected: all FAIL — `dashboard/backend/routes/config.py` doesn't exist yet, so the import at the top of the test file raises `ModuleNotFoundError`.

- [ ] **Step 3: Create `dashboard/backend/routes/config.py`**

```python
from aiohttp import web

import bot_config

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

CHANNEL_FIELDS = [
    "LOG_CHANNEL_ID",
    "TEMPBAN_CHANNEL_ID",
    "SPAM_LOG_CHANNEL_ID",
    "WELCOME_CHANNEL_ID",
    "INVITE_LOG_CHANNEL_ID",
    "ANNOUNCEMENTS_CHANNEL_ID",
    "RULES_CHANNEL_ID",
    "ROLES_CHANNEL_ID",
    "SEARCH_PLAYERS_CHANNEL_ID",
    "CTD_CHANNEL_ID",
]

ROLE_FIELDS = [
    "SPAM_LOG_ROLE_ID",
    "CTD_ROLE_ID",
]

LIST_CHANNEL_FIELDS = ["SPAM_EXCEPTION_CHANNELS"]
LIST_ROLE_FIELDS = ["BUTTON_CREATE_ALLOWED_ROLES"]

TEXT_FIELDS = ["BUTTON_WEBHOOK_URL", "SERVER_INVITE_LINK"]

ALL_FIELDS = CHANNEL_FIELDS + ROLE_FIELDS + LIST_CHANNEL_FIELDS + LIST_ROLE_FIELDS + TEXT_FIELDS
ALL_LIST_FIELDS = LIST_CHANNEL_FIELDS + LIST_ROLE_FIELDS


@routes.get("/api/config")
@require_dashboard_access
async def get_config(request: web.Request) -> web.Response:
    data = bot_config.load_config()
    result = {}
    for key in ALL_FIELDS:
        if key in ALL_LIST_FIELDS:
            result[key] = [str(v) for v in data.get(key, [])]
        else:
            result[key] = str(data.get(key) or "")
    return web.json_response(result)
```

- [ ] **Step 4: Register the route table in `app.py`**

In `dashboard/backend/app.py`, add the import (after the existing `from .routes.events import routes as events_routes` line):

```python
from .routes.config import routes as config_routes
```

And add the registration call (after the existing `app.add_routes(events_routes)` line):

```python
    app.add_routes(config_routes)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_config_routes.py -v`
Expected: all 3 pass.

- [ ] **Step 6: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `313 passed` (310 from Task 4 + 3 new).

- [ ] **Step 7: Commit**

```bash
git add dashboard/backend/routes/config.py dashboard/backend/app.py dashboard/backend/tests/test_config_routes.py
git commit -m "feat(dashboard): add GET /api/config route"
```

---

### Task 6: `PUT /api/config` route

**Files:**
- Modify: `dashboard/backend/routes/config.py` (append; no `app.py` changes needed — this route table is already registered from Task 5)
- Test: Modify `dashboard/backend/tests/test_config_routes.py` (append)

**Interfaces:**
- Consumes: `bot_config.save_config`, `CHANNEL_FIELDS`/`ROLE_FIELDS`/`LIST_CHANNEL_FIELDS`/`LIST_ROLE_FIELDS`/`TEXT_FIELDS`/`ALL_FIELDS`/`ALL_LIST_FIELDS` (Task 5).
- Produces: `PUT /api/config` — body is the same shape as `GET`'s response (all 16 keys); response is the saved config (same shape), status `200`. Errors: `invalid_request` (400, malformed JSON/non-dict body/wrong field type/non-numeric ID), `{field}_not_found` (404, a provided channel/role ID doesn't resolve in the guild), `service_unavailable` (503, no guild).

- [ ] **Step 1: Write the failing tests**

Append to `dashboard/backend/tests/test_config_routes.py`:

```python
from dashboard.backend.tests.fakes import FakeChannel, FakeRole


def _full_config(**overrides):
    cfg = {
        "LOG_CHANNEL_ID": "",
        "SPAM_EXCEPTION_CHANNELS": [],
        "TEMPBAN_CHANNEL_ID": "",
        "SPAM_LOG_CHANNEL_ID": "",
        "SPAM_LOG_ROLE_ID": "",
        "WELCOME_CHANNEL_ID": "",
        "INVITE_LOG_CHANNEL_ID": "",
        "ANNOUNCEMENTS_CHANNEL_ID": "",
        "RULES_CHANNEL_ID": "",
        "ROLES_CHANNEL_ID": "",
        "SEARCH_PLAYERS_CHANNEL_ID": "",
        "CTD_ROLE_ID": "",
        "CTD_CHANNEL_ID": "",
        "BUTTON_CREATE_ALLOWED_ROLES": [],
        "BUTTON_WEBHOOK_URL": "",
        "SERVER_INVITE_LINK": "",
    }
    cfg.update(overrides)
    return cfg


def build_with_guild(channels=None, roles=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator], channels=channels or [], roles=roles or [])
    return guild, make_moderation_app(FakeBot(guild), [config_routes])


@pytest.mark.asyncio
async def test_update_config_success_updates_all_fields(aiohttp_client):
    channel = FakeChannel(500, name="logs")
    _, app = build_with_guild(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(LOG_CHANNEL_ID="500"))
    assert resp.status == 200
    assert (await resp.json())["LOG_CHANNEL_ID"] == "500"
    assert bot_config.load_config()["LOG_CHANNEL_ID"] == "500"


@pytest.mark.asyncio
async def test_update_config_checks_structure_before_channel_existence(aiohttp_client):
    _, app = build_with_guild(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(SPAM_EXCEPTION_CHANNELS="not-a-list", LOG_CHANNEL_ID="500"))
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_spam_exception_channels"


@pytest.mark.asyncio
async def test_update_config_404_when_channel_not_found(aiohttp_client):
    _, app = build_with_guild(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(LOG_CHANNEL_ID="500"))
    assert resp.status == 404
    assert (await resp.json())["error"] == "log_channel_id_not_found"


@pytest.mark.asyncio
async def test_update_config_404_when_role_not_found(aiohttp_client):
    _, app = build_with_guild(roles=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(CTD_ROLE_ID="200"))
    assert resp.status == 404
    assert (await resp.json())["error"] == "ctd_role_id_not_found"


@pytest.mark.asyncio
async def test_update_config_404_when_list_channel_not_found(aiohttp_client):
    _, app = build_with_guild(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(SPAM_EXCEPTION_CHANNELS=["500"]))
    assert resp.status == 404
    assert (await resp.json())["error"] == "spam_exception_channels_not_found"


@pytest.mark.asyncio
async def test_update_config_404_when_list_role_not_found(aiohttp_client):
    _, app = build_with_guild(roles=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config(BUTTON_CREATE_ALLOWED_ROLES=["200"]))
    assert resp.status == 404
    assert (await resp.json())["error"] == "button_create_allowed_roles_not_found"


@pytest.mark.asyncio
async def test_update_config_allows_blank_optional_fields(aiohttp_client):
    _, app = build_with_guild(channels=[], roles=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/config", json=_full_config())
    assert resp.status == 200


@pytest.mark.asyncio
async def test_update_config_requires_auth(aiohttp_client):
    _, app = build_with_guild()
    client = await aiohttp_client(app)
    resp = await client.put("/api/config", json=_full_config())
    assert resp.status == 401


@pytest.mark.asyncio
async def test_update_config_round_trips_via_get(aiohttp_client):
    channel = FakeChannel(500, name="webhook-log")
    role = FakeRole(200, name="CTD")
    _, app = build_with_guild(channels=[channel], roles=[role])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.put("/api/config", json=_full_config(LOG_CHANNEL_ID="500", CTD_ROLE_ID="200"))
    resp = await client.get("/api/config")
    body = await resp.json()
    assert body["LOG_CHANNEL_ID"] == "500"
    assert body["CTD_ROLE_ID"] == "200"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_config_routes.py -v -k update_config`
Expected: all FAIL with 404 (route doesn't exist yet — aiohttp returns 404 for unmatched routes).

- [ ] **Step 3: Add the route**

Append to `dashboard/backend/routes/config.py` (at the end of the file):

```python
def _validate_structure(body: dict) -> str | None:
    for key in CHANNEL_FIELDS + ROLE_FIELDS + TEXT_FIELDS:
        value = body.get(key, "")
        if not isinstance(value, str):
            return f"invalid_{key.lower()}"
    for key in ALL_LIST_FIELDS:
        value = body.get(key, [])
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            return f"invalid_{key.lower()}"
    return None


def _check_channel(guild, key: str, raw_id: str) -> web.Response | None:
    try:
        channel_id = int(raw_id)
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)
    if guild.get_channel(channel_id) is None:
        return web.json_response({"error": f"{key.lower()}_not_found"}, status=404)
    return None


def _check_role(guild, key: str, raw_id: str) -> web.Response | None:
    try:
        role_id = int(raw_id)
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)
    if guild.get_role(role_id) is None:
        return web.json_response({"error": f"{key.lower()}_not_found"}, status=404)
    return None


def _validate_relations(body: dict, guild) -> web.Response | None:
    for key in CHANNEL_FIELDS:
        value = body.get(key, "")
        if value:
            error_response = _check_channel(guild, key, value)
            if error_response:
                return error_response

    for key in ROLE_FIELDS:
        value = body.get(key, "")
        if value:
            error_response = _check_role(guild, key, value)
            if error_response:
                return error_response

    for key in LIST_CHANNEL_FIELDS:
        for raw_id in body.get(key, []):
            error_response = _check_channel(guild, key, raw_id)
            if error_response:
                return error_response

    for key in LIST_ROLE_FIELDS:
        for raw_id in body.get(key, []):
            error_response = _check_role(guild, key, raw_id)
            if error_response:
                return error_response

    return None


@routes.put("/api/config")
@require_dashboard_access
async def update_config(request: web.Request) -> web.Response:
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

    error = _validate_structure(body)
    if error:
        return web.json_response({"error": error}, status=400)

    error_response = _validate_relations(body, guild)
    if error_response:
        return error_response

    data = {key: body.get(key, [] if key in ALL_LIST_FIELDS else "") for key in ALL_FIELDS}
    bot_config.save_config(data)

    result = {key: (list(data[key]) if key in ALL_LIST_FIELDS else str(data[key] or "")) for key in ALL_FIELDS}
    return web.json_response(result)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_config_routes.py -v`
Expected: all 12 pass (3 from Task 5 + 9 new).

- [ ] **Step 5: Run the full backend suite**

Run: `python -m pytest dashboard/backend/tests/ -q`
Expected: `322 passed` (313 from Task 5 + 9 new).

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/config.py dashboard/backend/tests/test_config_routes.py
git commit -m "feat(dashboard): add PUT /api/config route"
```

---

### Task 7: Frontend API client

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts` (append)
- Test: Create `dashboard/frontend/src/api/config.test.ts`

**Interfaces:**
- Consumes: `apiFetch<T>`, `jsonInit` (existing helpers).
- Produces:
  - `export interface BotConfig { LOG_CHANNEL_ID: string; SPAM_EXCEPTION_CHANNELS: string[]; TEMPBAN_CHANNEL_ID: string; SPAM_LOG_CHANNEL_ID: string; SPAM_LOG_ROLE_ID: string; WELCOME_CHANNEL_ID: string; INVITE_LOG_CHANNEL_ID: string; ANNOUNCEMENTS_CHANNEL_ID: string; RULES_CHANNEL_ID: string; ROLES_CHANNEL_ID: string; SEARCH_PLAYERS_CHANNEL_ID: string; CTD_ROLE_ID: string; CTD_CHANNEL_ID: string; BUTTON_CREATE_ALLOWED_ROLES: string[]; BUTTON_WEBHOOK_URL: string; SERVER_INVITE_LINK: string }`
  - `export function fetchConfig(): Promise<BotConfig>`
  - `export function updateConfig(config: BotConfig): Promise<BotConfig>`

- [ ] **Step 1: Write the failing test**

Create `dashboard/frontend/src/api/config.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchConfig, updateConfig, type BotConfig } from './client'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status })
}

const sampleConfig: BotConfig = {
  LOG_CHANNEL_ID: '500',
  SPAM_EXCEPTION_CHANNELS: ['600'],
  TEMPBAN_CHANNEL_ID: '',
  SPAM_LOG_CHANNEL_ID: '',
  SPAM_LOG_ROLE_ID: '',
  WELCOME_CHANNEL_ID: '',
  INVITE_LOG_CHANNEL_ID: '',
  ANNOUNCEMENTS_CHANNEL_ID: '',
  RULES_CHANNEL_ID: '',
  ROLES_CHANNEL_ID: '',
  SEARCH_PLAYERS_CHANNEL_ID: '',
  CTD_ROLE_ID: '',
  CTD_CHANNEL_ID: '',
  BUTTON_CREATE_ALLOWED_ROLES: [],
  BUTTON_WEBHOOK_URL: '',
  SERVER_INVITE_LINK: '',
}

describe('config API client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchConfig GETs the current config', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(sampleConfig))
    const result = await fetchConfig()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/config')
    expect(result).toEqual(sampleConfig)
  })

  it('updateConfig PUTs the full config and returns the saved result', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(sampleConfig))
    const result = await updateConfig(sampleConfig)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/config')
    expect(init?.method).toBe('PUT')
    expect(JSON.parse(init?.body as string)).toEqual(sampleConfig)
    expect(result).toEqual(sampleConfig)
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `dashboard/frontend/`): `npm run test -- config.test`
Expected: FAIL — `fetchConfig`/`updateConfig`/`BotConfig` are not exported from `./client` yet.

- [ ] **Step 3: Add the type and functions**

Append to `dashboard/frontend/src/api/client.ts` (at the end of the file):

```typescript
export interface BotConfig {
  LOG_CHANNEL_ID: string
  SPAM_EXCEPTION_CHANNELS: string[]
  TEMPBAN_CHANNEL_ID: string
  SPAM_LOG_CHANNEL_ID: string
  SPAM_LOG_ROLE_ID: string
  WELCOME_CHANNEL_ID: string
  INVITE_LOG_CHANNEL_ID: string
  ANNOUNCEMENTS_CHANNEL_ID: string
  RULES_CHANNEL_ID: string
  ROLES_CHANNEL_ID: string
  SEARCH_PLAYERS_CHANNEL_ID: string
  CTD_ROLE_ID: string
  CTD_CHANNEL_ID: string
  BUTTON_CREATE_ALLOWED_ROLES: string[]
  BUTTON_WEBHOOK_URL: string
  SERVER_INVITE_LINK: string
}

export function fetchConfig(): Promise<BotConfig> {
  return apiFetch('/api/config')
}

export function updateConfig(config: BotConfig): Promise<BotConfig> {
  return apiFetch('/api/config', jsonInit('PUT', config))
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm run test -- config.test`
Expected: PASS.

- [ ] **Step 5: Run the full frontend suite and typecheck**

Run: `npm run test` then `npx tsc --noEmit`
Expected: `89 passed` (87 baseline + 2 new), `tsc` clean.

- [ ] **Step 6: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/config.test.ts
git commit -m "feat(dashboard): add config API client functions"
```

---

### Task 8: Frontend UI — config editor page

**Files:**
- Create: `dashboard/frontend/src/pages/Config.tsx`
- Create: `dashboard/frontend/src/pages/Config.test.tsx`
- Modify: `dashboard/frontend/src/pages/DashboardShell.tsx` (wire the existing "Конфигурация" sidebar entry to `/config`)
- Modify: `dashboard/frontend/src/App.tsx` (add the `/config` route)

**Interfaces:**
- Consumes: `fetchConfig`, `updateConfig`, `BotConfig` (Task 7), `fetchChannels`, `fetchRoles`, `ChannelInfo`, `RoleInfo` (existing), `Button`/`Card` components.
- Produces: `export function ConfigPage()` — no other file consumes this beyond `App.tsx`'s route wiring.

`DashboardShell.tsx`'s `SECTIONS` array currently has, as its last entry:

```typescript
  { label: 'Конфигурация', icon: GearSix },
```

`GearSix` is already imported at the top of the file. This entry currently renders as a disabled "скоро" placeholder (no `to` field).

Read `dashboard/frontend/src/App.tsx` in full first to confirm its current routes before editing.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/frontend/src/pages/Config.test.tsx`:

```typescript
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { ConfigPage } from './Config'

const emptyConfig: client.BotConfig = {
  LOG_CHANNEL_ID: '',
  SPAM_EXCEPTION_CHANNELS: [],
  TEMPBAN_CHANNEL_ID: '',
  SPAM_LOG_CHANNEL_ID: '',
  SPAM_LOG_ROLE_ID: '',
  WELCOME_CHANNEL_ID: '',
  INVITE_LOG_CHANNEL_ID: '',
  ANNOUNCEMENTS_CHANNEL_ID: '',
  RULES_CHANNEL_ID: '',
  ROLES_CHANNEL_ID: '',
  SEARCH_PLAYERS_CHANNEL_ID: '',
  CTD_ROLE_ID: '',
  CTD_CHANNEL_ID: '',
  BUTTON_CREATE_ALLOWED_ROLES: [],
  BUTTON_WEBHOOK_URL: '',
  SERVER_INVITE_LINK: '',
}

describe('ConfigPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders all four config sections', async () => {
    vi.spyOn(client, 'fetchConfig').mockResolvedValue(emptyConfig)
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<ConfigPage />)

    expect(await screen.findByText('Модерация/спам')).toBeInTheDocument()
    expect(screen.getByText('Приветствия/онбординг')).toBeInTheDocument()
    expect(screen.getByText('CTD')).toBeInTheDocument()
    expect(screen.getByText('Кнопки/вебхуки')).toBeInTheDocument()
  })

  it('loads and displays existing config values', async () => {
    vi.spyOn(client, 'fetchConfig').mockResolvedValue({ ...emptyConfig, SERVER_INVITE_LINK: 'https://discord.gg/example' })
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<ConfigPage />)

    await waitFor(() => screen.getByLabelText('Ссылка-приглашение сервера'))
    expect((screen.getByLabelText('Ссылка-приглашение сервера') as HTMLInputElement).value).toBe(
      'https://discord.gg/example',
    )
  })

  it('saves the updated config', async () => {
    vi.spyOn(client, 'fetchConfig').mockResolvedValue(emptyConfig)
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'logs' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const updateSpy = vi.spyOn(client, 'updateConfig').mockResolvedValue(emptyConfig)

    render(<ConfigPage />)

    await waitFor(() => screen.getByLabelText('Канал логов'))
    fireEvent.change(screen.getByLabelText('Канал логов'), { target: { value: '500' } })
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith(expect.objectContaining({ LOG_CHANNEL_ID: '500' })),
    )
  })

  it('shows an error when save fails', async () => {
    vi.spyOn(client, 'fetchConfig').mockResolvedValue(emptyConfig)
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'updateConfig').mockRejectedValue(new Error('boom'))

    render(<ConfigPage />)

    await waitFor(() => screen.getByRole('button', { name: 'Сохранить' }))
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }))

    await waitFor(() => screen.getByText('Не удалось сохранить конфигурацию — проверьте поля'))
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm run test -- Config`
Expected: FAIL — `Config.tsx` doesn't exist yet.

- [ ] **Step 3: Create `dashboard/frontend/src/pages/Config.tsx`**

```tsx
import { useEffect, useState } from 'react'
import {
  fetchChannels,
  fetchConfig,
  fetchRoles,
  updateConfig,
  type BotConfig,
  type ChannelInfo,
  type RoleInfo,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

const EMPTY_CONFIG: BotConfig = {
  LOG_CHANNEL_ID: '',
  SPAM_EXCEPTION_CHANNELS: [],
  TEMPBAN_CHANNEL_ID: '',
  SPAM_LOG_CHANNEL_ID: '',
  SPAM_LOG_ROLE_ID: '',
  WELCOME_CHANNEL_ID: '',
  INVITE_LOG_CHANNEL_ID: '',
  ANNOUNCEMENTS_CHANNEL_ID: '',
  RULES_CHANNEL_ID: '',
  ROLES_CHANNEL_ID: '',
  SEARCH_PLAYERS_CHANNEL_ID: '',
  CTD_ROLE_ID: '',
  CTD_CHANNEL_ID: '',
  BUTTON_CREATE_ALLOWED_ROLES: [],
  BUTTON_WEBHOOK_URL: '',
  SERVER_INVITE_LINK: '',
}

export function ConfigPage() {
  const [config, setConfig] = useState<BotConfig>(EMPTY_CONFIG)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')

  useEffect(() => {
    Promise.all([fetchConfig(), fetchChannels(), fetchRoles()])
      .then(([cfg, ch, rl]) => {
        setConfig(cfg)
        setChannels(ch)
        setRoles(rl)
      })
      .catch(() => setError('Не удалось загрузить конфигурацию'))
      .finally(() => setLoading(false))
  }, [])

  const setField = (key: keyof BotConfig, value: string) => {
    setConfig((prev) => ({ ...prev, [key]: value }))
  }

  const toggleListField = (key: 'SPAM_EXCEPTION_CHANNELS' | 'BUTTON_CREATE_ALLOWED_ROLES', id: string) => {
    setConfig((prev) => ({
      ...prev,
      [key]: prev[key].includes(id) ? prev[key].filter((v) => v !== id) : [...prev[key], id],
    }))
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const updated = await updateConfig(config)
      setConfig(updated)
      setSavedMessage('Сохранено.')
    } catch {
      setError('Не удалось сохранить конфигурацию — проверьте поля')
    } finally {
      setBusy(false)
    }
  }

  const channelField = (label: string, key: keyof BotConfig) => (
    <div key={key} className="flex flex-col gap-1">
      <label className="text-sm text-muted" htmlFor={key}>
        {label}
      </label>
      <select
        id={key}
        value={config[key] as string}
        onChange={(e) => setField(key, e.target.value)}
        className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
      >
        <option value="">Не задано</option>
        {channels.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>
    </div>
  )

  const roleField = (label: string, key: keyof BotConfig) => (
    <div key={key} className="flex flex-col gap-1">
      <label className="text-sm text-muted" htmlFor={key}>
        {label}
      </label>
      <select
        id={key}
        value={config[key] as string}
        onChange={(e) => setField(key, e.target.value)}
        className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
      >
        <option value="">Не задано</option>
        {roles.map((r) => (
          <option key={r.id} value={r.id}>
            {r.name}
          </option>
        ))}
      </select>
    </div>
  )

  const textField = (label: string, key: keyof BotConfig) => (
    <div key={key} className="flex flex-col gap-1">
      <label className="text-sm text-muted" htmlFor={key}>
        {label}
      </label>
      <input
        id={key}
        value={config[key] as string}
        onChange={(e) => setField(key, e.target.value)}
        className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
      />
    </div>
  )

  if (loading) {
    return <p className="text-sm text-muted">Загрузка…</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <h1 className="text-lg font-semibold text-foreground">Конфигурация</h1>

      {error && <p className="text-sm text-danger">{error}</p>}
      {savedMessage && <p className="text-sm text-primary">{savedMessage}</p>}

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Модерация/спам</h2>
        {channelField('Канал логов', 'LOG_CHANNEL_ID')}
        {channelField('Канал Tempban', 'TEMPBAN_CHANNEL_ID')}
        {channelField('Канал логов спама', 'SPAM_LOG_CHANNEL_ID')}
        {roleField('Роль для пинга при спаме', 'SPAM_LOG_ROLE_ID')}
        <div>
          <p className="mb-1 text-sm text-muted">Каналы-исключения из анти-спама</p>
          <div className="flex flex-wrap gap-2">
            {channels.map((c) => (
              <label key={c.id} className="flex items-center gap-1 text-xs text-foreground">
                <input
                  type="checkbox"
                  checked={config.SPAM_EXCEPTION_CHANNELS.includes(c.id)}
                  onChange={() => toggleListField('SPAM_EXCEPTION_CHANNELS', c.id)}
                />
                {c.name}
              </label>
            ))}
          </div>
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Приветствия/онбординг</h2>
        {channelField('Канал приветствий', 'WELCOME_CHANNEL_ID')}
        {channelField('Канал лога приглашений', 'INVITE_LOG_CHANNEL_ID')}
        {channelField('Канал объявлений', 'ANNOUNCEMENTS_CHANNEL_ID')}
        {channelField('Канал правил', 'RULES_CHANNEL_ID')}
        {channelField('Канал ролей', 'ROLES_CHANNEL_ID')}
        {channelField('Канал поиска игроков', 'SEARCH_PLAYERS_CHANNEL_ID')}
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">CTD</h2>
        {roleField('Роль CTD', 'CTD_ROLE_ID')}
        {channelField('Канал CTD', 'CTD_CHANNEL_ID')}
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Кнопки/вебхуки</h2>
        <div>
          <p className="mb-1 text-sm text-muted">Роли, которым разрешено создавать кнопки</p>
          <div className="flex flex-wrap gap-2">
            {roles.map((r) => (
              <label key={r.id} className="flex items-center gap-1 text-xs text-foreground">
                <input
                  type="checkbox"
                  checked={config.BUTTON_CREATE_ALLOWED_ROLES.includes(r.id)}
                  onChange={() => toggleListField('BUTTON_CREATE_ALLOWED_ROLES', r.id)}
                />
                {r.name}
              </label>
            ))}
          </div>
        </div>
        {textField('URL вебхука для кнопок', 'BUTTON_WEBHOOK_URL')}
        {textField('Ссылка-приглашение сервера', 'SERVER_INVITE_LINK')}
      </Card>

      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </Button>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Wire the sidebar and route**

In `dashboard/frontend/src/pages/DashboardShell.tsx`, change the `SECTIONS` array's last entry from:

```typescript
  { label: 'Конфигурация', icon: GearSix },
```

to:

```typescript
  { label: 'Конфигурация', icon: GearSix, to: '/config' },
```

In `dashboard/frontend/src/App.tsx`, add the import (alongside the existing page imports):

```typescript
import { ConfigPage } from './pages/Config'
```

And add the route (alongside the existing routes inside the `DashboardShell` route's children):

```tsx
            <Route path="config" element={<ConfigPage />} />
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `npm run test -- Config`
Expected: all 4 pass.

- [ ] **Step 6: Run the full frontend suite, typecheck, and build**

Run: `npm run test` then `npx tsc --noEmit` then `npm run build`
Expected: `93 passed` (89 from Task 7 + 4 new), `tsc` clean, build clean.

- [ ] **Step 7: Commit**

```bash
git add dashboard/frontend/src/pages/Config.tsx dashboard/frontend/src/pages/Config.test.tsx dashboard/frontend/src/pages/DashboardShell.tsx dashboard/frontend/src/App.tsx
git commit -m "feat(dashboard): add config editor page, wire into sidebar"
```

---

### Task 9: Manual E2E verification (user-performed, not a subagent task)

Not automatable — requires a live Discord test server and, for full confidence, an actual bot restart to confirm the migration. Steps for the user:

1. Restart the backend and frontend dev servers (done by the assistant before handoff, per standing project convention).
2. Confirm `config.json` was created on this startup, populated from whatever `.env` values were already set (the migration runs once, automatically).
3. On the "Конфигурация" sidebar entry, confirm it's now a live link (no more "скоро" badge).
4. Edit a channel field (e.g. `LOG_CHANNEL_ID`) via the dashboard, save, and confirm — WITHOUT restarting the bot — that a moderation action that logs to that channel (e.g. trigger `/event manage` → notify, or any `bot.send_log` call) now posts to the newly-selected channel. This proves the no-restart-needed promise holds for real.
5. Toggle a channel in/out of "Каналы-исключения из анти-спама", save, and confirm the anti-spam detector's exception behavior changes immediately (no restart) — this specifically verifies Task 2's `self.exception_channels` → fresh-read fix.
6. Confirm `BOT_TOKEN`/`GUILD_ID` remain in `.env`, are not shown anywhere on the config page, and the bot still starts and syncs commands normally.
7. Try saving with a channel ID that doesn't exist in the guild (e.g. by temporarily editing the raw request, or via a field the UI doesn't fully guard) and confirm a clean 404 comes back, not a crash.

---

## Self-Review Notes

- **Spec coverage:** storage (`bot_config.py`, Task 1) → per-file refactor (Tasks 2-4, covering all six files and all 16 keys) → API (Tasks 5-6) → frontend (Tasks 7-8) → testing section's specific call-outs (no-cache regression, migration partial/skip/list-parsing tests, structural-then-existence route test, event-listener zero-coverage convention) are each addressed in the corresponding task.
- **Placeholder scan:** none found — every step has complete code.
- **Type/name consistency:** `bot_config.get(key, default=None)` is defined once (Task 1) and consumed identically by all six refactored files (Tasks 2-4) and both routes (Tasks 5-6). `CHANNEL_FIELDS`/`ROLE_FIELDS`/`LIST_CHANNEL_FIELDS`/`LIST_ROLE_FIELDS`/`TEXT_FIELDS`/`ALL_FIELDS`/`ALL_LIST_FIELDS` are defined once in Task 5 and reused unmodified by Task 6 — not redefined or renamed. `BotConfig`'s 16 fields (Task 7) match `ALL_FIELDS`'s 16 keys exactly, same order, same list-vs-scalar typing, and `Config.tsx` (Task 8) consumes every one of them. Test count progression double-checked by direct arithmetic: 301 → 310 (Task 1, +9) → 310 (Task 2, +0) → 310 (Task 3, +0) → 310 (Task 4, +0) → 313 (Task 5, +3) → 322 (Task 6, +9) backend; 87 → 89 (Task 7, +2) → 93 (Task 8, +4) frontend.
- **Cross-task risk caught during planning:** `spam.py`'s `self.exception_channels` was cached at cog-construction time in the original code — carrying this pattern forward unchanged would have silently defeated the entire phase's "no restart needed" promise for that one field, since the cog is only constructed once at bot startup. Task 2 explicitly removes the cached attribute and reads fresh at the point of use instead, and Task 9's manual E2E checklist (step 5) specifically re-verifies this exact behavior live, not just via a code read.
- **Cross-task risk caught during planning:** the `bot_config.get(key) or '0'` / `bot_config.get(key) or "https://discord.gg/cheterin"` pattern used in Tasks 2-3 for fields that had a `os.getenv(key, default)` fallback in the original code is verified to produce the identical observable result: since `migrate_from_env_if_needed()` always creates every key (defaulting truly-unset env vars to `""`, never omitting the key), `bot_config.get(key)` can only ever return `""` or a real value for these fields — never `None` — so `"" or default` is a faithful, minimal substitution for `os.getenv(key, default)`, not an approximation.
