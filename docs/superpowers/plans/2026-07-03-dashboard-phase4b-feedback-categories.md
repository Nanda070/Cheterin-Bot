# Дашборд, Фаза 4b (Категории обращений) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let staff create, edit, and delete feedback/complaint categories from the dashboard instead of the current single hardcoded category driven by env vars.

**Architecture:** A new repo-root module `feedback_categories.py` holds JSON-backed storage (`feedback_categories.json`, no caching — so dashboard edits apply immediately) plus structural validation. `feedback_menu.py::get_feedback_categories()` keeps its exact name and import path (zero changes needed in `feedback_core.py` or `dashboard/backend/routes/feedback.py`'s existing imports from Phase 4a) but becomes a thin wrapper over the new module. A one-time migration seeds the JSON file from the current env vars on first boot after this ships, so the existing "players" category and its case history/counter keep working uninterrupted. New dashboard routes append to the existing `dashboard/backend/routes/feedback.py` route table (already registered in `app.py` since Phase 4a — no new registration needed). The `/feedback` page gains a second tab, mirroring the `MessageBuilderPage` tabs pattern from Phase 3b.

**Tech Stack:** Python: discord.py, aiohttp, pytest + pytest-aiohttp (existing fakes, no extensions needed this phase). Frontend: React + TypeScript, existing design-system primitives, Vitest + Testing Library.

## Global Constraints

- All work happens in `C:\Users\adnan\Documents\coding\ChetMain_backup_20260701_211729`. Never touch `C:\Users\adnan\Documents\coding\ChetMain`.
- Local-only git repo: commit each task with `git add <specific files>` + `git commit` — never bare `git add -A`.
- Spec of record: `docs/superpowers/specs/2026-07-03-dashboard-phase4b-feedback-categories-design.md`.
- No caching in `feedback_categories.py` — `load_categories()` reads the JSON file fresh on every call, matching `reaction_roles.py`'s established pattern. This is a deliberate change from the old `_feedback_categories_cache` behavior: dashboard edits must take effect without a bot restart.
- IDs (`channel_id`, `review_role_ids` entries) are stored as **strings** in the JSON, matching `reaction_roles.json`'s established convention (Discord snowflake IDs can exceed JS's safe-integer range) — code that calls Discord API methods expecting `int` (`bot.get_channel`, `guild.get_role`) must explicitly convert with `int(...)` at the call site.
- `button_style` is NOT part of the stored category data — it stays a fixed `discord.ButtonStyle.secondary` constant in `feedback_menu.py`, matching current behavior (never varied) and the spec's explicit YAGNI call.
- `review_user_ids` (direct per-user reviewer mentions, not via role) is out of scope for dashboard editing in this phase — existing code that reads `config["review_user_ids"]` must be changed to `config.get("review_user_ids", [])` so category dicts that never set this key (all dashboard-created ones) don't raise `KeyError`.
- No routes registration needed in `dashboard/backend/app.py` — the new category routes are appended to the SAME `dashboard/backend/routes/feedback.py` file and `routes` table object that Phase 4a already registered.
- Validation order, binding for both create and edit: structural checks (key/prefix format, uniqueness, field count/labels, `mini_summary_key` must reference a real field) run first with zero Discord calls; channel/role existence checks run after.
- Existing suites must stay green throughout: 203 pytest + 54 Vitest tests before this plan.

---

### Task 1: `feedback_categories.py` — storage, validation, migration

**Files:**
- Create: `feedback_categories.py` (repo root, next to `feedback_core.py`)
- Test: `dashboard/backend/tests/test_feedback_categories.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `CONFIG_FILE = "feedback_categories.json"`; `load_categories() -> dict`; `save_categories(data: dict) -> None`; `validate_category_spec(spec: dict, categories: dict, existing_key: str | None = None) -> str | None` (returns an error code or `None`; `existing_key` is the category being edited, excluded from its own uniqueness checks, or `None` when creating); `migrate_from_env_if_needed() -> None`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_feedback_categories.py`:

```python
import pytest

import feedback_categories


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(feedback_categories, "CONFIG_FILE", str(tmp_path / "feedback_categories.json"))


def _valid_spec(key="players", case_prefix="PR"):
    return {
        "key": key,
        "title": "Жалоба на участника",
        "button_label": "Жалоба на участника",
        "channel_id": "500",
        "case_prefix": case_prefix,
        "case_title": "Жалоба на участника",
        "thread_name": "player-report",
        "review_role_ids": ["111"],
        "approved_text": "Участник наказан.",
        "denied_text": "Жалоба отклонена.",
        "modal_title": "Жалоба на участника",
        "fields": [
            {"key": "offender", "label": "Ник участника", "style": "short", "required": True, "max_length": 120},
        ],
        "mini_summary_key": "offender",
    }


def test_load_categories_returns_empty_dict_when_file_missing():
    assert feedback_categories.load_categories() == {}


def test_save_then_load_round_trip():
    data = {"players": {"title": "X"}}
    feedback_categories.save_categories(data)
    assert feedback_categories.load_categories() == data


def test_validate_category_spec_accepts_valid_spec():
    assert feedback_categories.validate_category_spec(_valid_spec(), {}) is None


def test_validate_category_spec_rejects_invalid_key_format():
    spec = _valid_spec(key="Players With Spaces")
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_key"


def test_validate_category_spec_rejects_duplicate_key_on_create():
    spec = _valid_spec(key="players")
    existing = {"players": {}}
    assert feedback_categories.validate_category_spec(spec, existing, existing_key=None) == "key_taken"


def test_validate_category_spec_allows_same_key_on_edit():
    spec = _valid_spec(key="players")
    existing = {"players": {"case_prefix": "OTHER"}}
    assert feedback_categories.validate_category_spec(spec, existing, existing_key="players") is None


def test_validate_category_spec_rejects_duplicate_case_prefix():
    spec = _valid_spec(key="staff", case_prefix="PR")
    existing = {"players": {"case_prefix": "PR"}}
    assert feedback_categories.validate_category_spec(spec, existing, existing_key=None) == "case_prefix_taken"


def test_validate_category_spec_allows_own_case_prefix_on_edit():
    spec = _valid_spec(key="players", case_prefix="PR")
    existing = {"players": {"case_prefix": "PR"}}
    assert feedback_categories.validate_category_spec(spec, existing, existing_key="players") is None


def test_validate_category_spec_rejects_too_many_fields():
    spec = _valid_spec()
    spec["fields"] = [
        {"key": f"f{i}", "label": f"Field {i}", "style": "short", "required": False, "max_length": 100}
        for i in range(6)
    ]
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_field_count"


def test_validate_category_spec_rejects_zero_fields():
    spec = _valid_spec()
    spec["fields"] = []
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_field_count"


def test_validate_category_spec_rejects_duplicate_field_keys():
    spec = _valid_spec()
    spec["fields"] = [
        {"key": "a", "label": "A", "style": "short", "required": False, "max_length": 100},
        {"key": "a", "label": "B", "style": "short", "required": False, "max_length": 100},
    ]
    spec["mini_summary_key"] = "a"
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_field_key"


def test_validate_category_spec_rejects_mini_summary_key_not_in_fields():
    spec = _valid_spec()
    spec["mini_summary_key"] = "does_not_exist"
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_mini_summary_key"


def test_validate_category_spec_rejects_invalid_field_style():
    spec = _valid_spec()
    spec["fields"][0]["style"] = "wrong"
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_field_style"


def test_migrate_from_env_if_needed_creates_config_from_env(monkeypatch):
    monkeypatch.setenv("CHANNEL_COMPLAINT_PLAY", "500")
    monkeypatch.setenv("ROLE_PLAYERS", "111")
    feedback_categories.migrate_from_env_if_needed()
    categories = feedback_categories.load_categories()
    assert "players" in categories
    assert categories["players"]["channel_id"] == "500"
    assert categories["players"]["case_prefix"] == "PR"


def test_migrate_from_env_if_needed_skips_when_file_already_exists(monkeypatch):
    monkeypatch.setenv("CHANNEL_COMPLAINT_PLAY", "500")
    monkeypatch.setenv("ROLE_PLAYERS", "111")
    feedback_categories.save_categories({"existing": {"case_prefix": "EX"}})
    feedback_categories.migrate_from_env_if_needed()
    categories = feedback_categories.load_categories()
    assert categories == {"existing": {"case_prefix": "EX"}}


def test_migrate_from_env_if_needed_skips_when_env_vars_missing():
    feedback_categories.migrate_from_env_if_needed()
    assert feedback_categories.load_categories() == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_feedback_categories.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'feedback_categories'`

- [ ] **Step 3: Implement `feedback_categories.py`**

```python
import json
import os
import re

CONFIG_FILE = "feedback_categories.json"

KEY_PATTERN = re.compile(r"^[a-z0-9_]+$")
PREFIX_PATTERN = re.compile(r"^[A-Z0-9]{1,6}$")


def load_categories() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_categories(data: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def validate_category_spec(spec: dict, categories: dict, existing_key: str | None = None) -> str | None:
    if existing_key is None:
        key = spec.get("key", "")
        if not KEY_PATTERN.match(key or ""):
            return "invalid_key"
        if key in categories:
            return "key_taken"

    case_prefix = spec.get("case_prefix", "")
    if not PREFIX_PATTERN.match(case_prefix or ""):
        return "invalid_case_prefix"
    for other_key, other in categories.items():
        if other_key == existing_key:
            continue
        if other.get("case_prefix") == case_prefix:
            return "case_prefix_taken"

    for text_field, max_len in (
        ("title", 80),
        ("button_label", 80),
        ("case_title", 80),
        ("modal_title", 80),
        ("approved_text", 1024),
        ("denied_text", 1024),
    ):
        value = spec.get(text_field, "")
        if not value or len(value) > max_len:
            return f"invalid_{text_field}"

    thread_name = spec.get("thread_name", "")
    if not thread_name or len(thread_name) > 80:
        return "invalid_thread_name"

    fields = spec.get("fields") or []
    if not (1 <= len(fields) <= 5):
        return "invalid_field_count"

    field_keys = set()
    for field in fields:
        field_key = field.get("key", "")
        if not field_key or field_key in field_keys:
            return "invalid_field_key"
        field_keys.add(field_key)
        label = field.get("label", "")
        if not label or len(label) > 45:
            return "invalid_field_label"
        max_length = field.get("max_length")
        if not isinstance(max_length, int) or not (1 <= max_length <= 4000):
            return "invalid_field_max_length"
        if field.get("style") not in ("short", "paragraph"):
            return "invalid_field_style"

    if spec.get("mini_summary_key") not in field_keys:
        return "invalid_mini_summary_key"

    return None


def migrate_from_env_if_needed() -> None:
    if os.path.exists(CONFIG_FILE):
        return
    channel_id_raw = os.getenv("CHANNEL_COMPLAINT_PLAY")
    role_id_raw = os.getenv("ROLE_PLAYERS")
    if not channel_id_raw or not role_id_raw:
        return

    categories = {
        "players": {
            "title": "Жалоба на участника",
            "button_label": "            Жалоба на участника            ",
            "channel_id": channel_id_raw,
            "case_prefix": "PR",
            "case_title": "Жалоба на участника",
            "thread_name": "player-report",
            "review_role_ids": [role_id_raw],
            "approved_text": "Участник наказан.",
            "denied_text": "Жалоба отклонена.",
            "modal_title": "Жалоба на участника",
            "fields": [
                {
                    "key": "offender",
                    "label": "Ник / ID участника",
                    "style": "short",
                    "required": True,
                    "max_length": 120,
                },
                {
                    "key": "complaint",
                    "label": "Суть жалобы",
                    "style": "paragraph",
                    "required": True,
                    "max_length": 1000,
                },
                {
                    "key": "datetime",
                    "label": "Дата и время ситуации",
                    "style": "short",
                    "required": False,
                    "max_length": 120,
                },
                {
                    "key": "proof",
                    "label": "Доказательства",
                    "style": "paragraph",
                    "required": False,
                    "max_length": 1000,
                },
            ],
            "mini_summary_key": "offender",
        },
    }
    save_categories(categories)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_feedback_categories.py -v`
Expected: PASS (16 tests)

- [ ] **Step 5: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (203 + 16 = 219)

- [ ] **Step 6: Commit**

```bash
git add feedback_categories.py dashboard/backend/tests/test_feedback_categories.py
git commit -m "feat: add feedback_categories storage, validation, and env migration"
```

---

### Task 2: Refactor `feedback_menu.py` to read categories from `feedback_categories.py`

**Files:**
- Modify: `feedback_menu.py`
- Modify: `dashboard/backend/tests/test_feedback_core.py` (fix a now-broken fixture — see below)
- Modify: `dashboard/backend/tests/test_feedback_routes.py` (fix a now-broken fixture — see below)

**Interfaces:**
- Consumes: `feedback_categories.load_categories` (Task 1).
- Produces: `feedback_menu.get_feedback_categories()` keeps its exact existing name/signature (zero call-site changes anywhere else in the codebase), now delegating to `feedback_categories.load_categories()`.

**Why this task also touches two test files:** Phase 4a's `test_feedback_core.py` and `test_feedback_routes.py` both have an autouse fixture that does `monkeypatch.setenv("CHANNEL_COMPLAINT_PLAY", ...)` and `monkeypatch.setattr(feedback_menu, "_feedback_categories_cache", None)`. This task DELETES `_feedback_categories_cache` from `feedback_menu.py` — `monkeypatch.setattr` raises `AttributeError` if the target attribute doesn't exist, so both fixtures would break the instant this task's `feedback_menu.py` changes land. Both fixtures must be replaced in the SAME commit as the `feedback_menu.py` refactor, or the existing 219 backend tests go red.

Like Task 3 of Phase 4a, `feedback_menu.py`'s interaction-driven code (`FeedbackView`, `FeedbackModal`, `create_feedback_case`, `add_reviewers`, `build_mentions`) has no dedicated pytest coverage — verify this task's correctness by reading the whole file first and making a precise, minimal diff, not by writing new interaction-mocking tests (none exist in this project; do not invent one).

- [ ] **Step 1: Read the current files**

Read `feedback_menu.py`, `dashboard/backend/tests/test_feedback_core.py`, and `dashboard/backend/tests/test_feedback_routes.py` in full first — you need their exact current content to make precise, minimal diffs.

- [ ] **Step 2: Replace the top of `feedback_menu.py`**

Find:

```python
import discord
from discord.ext import commands
from discord import app_commands
import os
from typing import Optional
import logging

import feedback_core

logger = logging.getLogger("chetbot.feedback")

_feedback_categories_cache = None

PANEL_BANNER_URL = "https://i.imgur.com/vLAcc7q.png"


def _env_int(key: str) -> int:
    """Безопасно читает переменную окружения и конвертирует в int."""
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Переменная окружения {key} не задана.")
    return int(val)


def get_feedback_categories():
    global _feedback_categories_cache
    if _feedback_categories_cache is not None:
        return _feedback_categories_cache

    _feedback_categories_cache = {
        "players": {
            "title": "Жалоба на участника",
            "button_label": "            Жалоба на участника            ",
            "button_style": discord.ButtonStyle.secondary,
            "channel_id": _env_int("CHANNEL_COMPLAINT_PLAY"),
            "case_prefix": "PR",
            "case_title": "Жалоба на участника",
            "thread_name": "player-report",
            "review_role_ids": [_env_int("ROLE_PLAYERS")],
            "review_user_ids": [],
            "approved_text": "Участник наказан.",
            "denied_text": "Жалоба отклонена.",
            "modal_title": "Жалоба на участника",
            "fields": [
                {"key": "offender", "label": "Ник / ID участника", "style": discord.TextStyle.short, "required": True, "max_length": 120},
                {"key": "complaint", "label": "Суть жалобы", "style": discord.TextStyle.paragraph, "required": True, "max_length": 1000},
                {"key": "datetime", "label": "Дата и время ситуации", "style": discord.TextStyle.short, "required": False, "max_length": 120},
                {"key": "proof", "label": "Доказательства", "style": discord.TextStyle.paragraph, "required": False, "max_length": 1000},
            ],
            "mini_summary_key": "offender",
        },
    }
    return _feedback_categories_cache
```

Replace with:

```python
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

import feedback_categories
import feedback_core

logger = logging.getLogger("chetbot.feedback")

PANEL_BANNER_URL = "https://i.imgur.com/vLAcc7q.png"


def get_feedback_categories():
    return feedback_categories.load_categories()
```

(Note: `import os` is removed since `_env_int` — its only user in this file — is deleted.)

- [ ] **Step 3: Hardcode the button style in `FeedbackView.__init__`**

Find:

```python
        for category_key, config in categories.items():
            button = discord.ui.Button(
                label=config["button_label"],
                style=config["button_style"],
                custom_id=f"feedback_open:{category_key}",
                row=0,
            )
```

Replace with:

```python
        for category_key, config in categories.items():
            button = discord.ui.Button(
                label=config["button_label"],
                style=discord.ButtonStyle.secondary,
                custom_id=f"feedback_open:{category_key}",
                row=0,
            )
```

- [ ] **Step 4: Convert field style strings to `discord.TextStyle` in `FeedbackModal.__init__`**

Find:

```python
        self.field_keys = []
        for field in config["fields"]:
            input_item = discord.ui.TextInput(
                label=field["label"],
                style=field["style"],
                required=field["required"],
                max_length=field["max_length"],
            )
            self.add_item(input_item)
            self.field_keys.append(field["key"])
```

Replace with:

```python
        self.field_keys = []
        for field in config["fields"]:
            style = discord.TextStyle.short if field["style"] == "short" else discord.TextStyle.paragraph
            input_item = discord.ui.TextInput(
                label=field["label"],
                style=style,
                required=field["required"],
                max_length=field["max_length"],
            )
            self.add_item(input_item)
            self.field_keys.append(field["key"])
```

- [ ] **Step 5: Guard `review_user_ids` with `.get(..., [])` in `build_mentions`**

Find:

```python
def build_mentions(config: dict) -> str:
    parts = [f"<@&{r_id}>" for r_id in config["review_role_ids"]]
    parts.extend(f"<@{u_id}>" for u_id in config["review_user_ids"])
    return " ".join(parts).strip() or "Без упоминаний"
```

Replace with:

```python
def build_mentions(config: dict) -> str:
    parts = [f"<@&{r_id}>" for r_id in config["review_role_ids"]]
    parts.extend(f"<@{u_id}>" for u_id in config.get("review_user_ids", []))
    return " ".join(parts).strip() or "Без упоминаний"
```

- [ ] **Step 6: Convert role/user IDs to `int` in `add_reviewers`, and guard `review_user_ids`**

Find:

```python
async def add_reviewers(thread: discord.Thread, guild: discord.Guild, config: dict):
    added_ids = set()
    for role_id in config["review_role_ids"]:
        role = guild.get_role(role_id)
        if not role:
            continue
        for member in role.members:
            if not member.bot and member.id not in added_ids:
                try:
                    await thread.add_user(member)
                    added_ids.add(member.id)
                except Exception as e:
                    logger.debug("Не удалось добавить %s в тред: %s", member.id, e)

    for user_id in config["review_user_ids"]:
        member = guild.get_member(user_id)
        if member and not member.bot and member.id not in added_ids:
            try:
                await thread.add_user(member)
                added_ids.add(member.id)
            except Exception as e:
                logger.debug("Не удалось добавить %s в тред: %s", member.id, e)
```

Replace with:

```python
async def add_reviewers(thread: discord.Thread, guild: discord.Guild, config: dict):
    added_ids = set()
    for role_id in config["review_role_ids"]:
        role = guild.get_role(int(role_id))
        if not role:
            continue
        for member in role.members:
            if not member.bot and member.id not in added_ids:
                try:
                    await thread.add_user(member)
                    added_ids.add(member.id)
                except Exception as e:
                    logger.debug("Не удалось добавить %s в тред: %s", member.id, e)

    for user_id in config.get("review_user_ids", []):
        member = guild.get_member(int(user_id))
        if member and not member.bot and member.id not in added_ids:
            try:
                await thread.add_user(member)
                added_ids.add(member.id)
            except Exception as e:
                logger.debug("Не удалось добавить %s в тред: %s", member.id, e)
```

- [ ] **Step 7: Convert `channel_id` to `int` in `create_feedback_case`**

Find:

```python
    parent_channel = bot.get_channel(config["channel_id"])
```

Replace with:

```python
    parent_channel = bot.get_channel(int(config["channel_id"]))
```

- [ ] **Step 8: Fix the now-broken fixture in `dashboard/backend/tests/test_feedback_core.py`**

Find:

```python
@pytest.fixture(autouse=True)
def isolated_feedback_categories(monkeypatch):
    monkeypatch.setenv("CHANNEL_COMPLAINT_PLAY", "500")
    monkeypatch.setenv("ROLE_PLAYERS", "111")
    import feedback_menu

    monkeypatch.setattr(feedback_menu, "_feedback_categories_cache", None)
    yield
```

Replace with:

```python
@pytest.fixture(autouse=True)
def isolated_feedback_categories(tmp_path, monkeypatch):
    import feedback_categories

    monkeypatch.setattr(feedback_categories, "CONFIG_FILE", str(tmp_path / "feedback_categories.json"))
    feedback_categories.save_categories(
        {
            "players": {
                "title": "Жалоба на участника",
                "button_label": "Жалоба на участника",
                "channel_id": "500",
                "case_prefix": "PR",
                "case_title": "Жалоба на участника",
                "thread_name": "player-report",
                "review_role_ids": ["111"],
                "review_user_ids": [],
                "approved_text": "Участник наказан.",
                "denied_text": "Жалоба отклонена.",
                "modal_title": "Жалоба на участника",
                "fields": [
                    {
                        "key": "offender",
                        "label": "Ник / ID участника",
                        "style": "short",
                        "required": True,
                        "max_length": 120,
                    },
                    {
                        "key": "complaint",
                        "label": "Суть жалобы",
                        "style": "paragraph",
                        "required": True,
                        "max_length": 1000,
                    },
                    {
                        "key": "datetime",
                        "label": "Дата и время ситуации",
                        "style": "short",
                        "required": False,
                        "max_length": 120,
                    },
                    {
                        "key": "proof",
                        "label": "Доказательства",
                        "style": "paragraph",
                        "required": False,
                        "max_length": 1000,
                    },
                ],
                "mini_summary_key": "offender",
            },
        }
    )
    yield
```

- [ ] **Step 9: Apply the exact same fixture fix to `dashboard/backend/tests/test_feedback_routes.py`**

Find the identical `isolated_feedback_categories` fixture in this file (it was written identically to the one in `test_feedback_core.py` when Phase 4a created it) and replace it with the exact same new fixture body from Step 8.

- [ ] **Step 10: Verify the module still imports cleanly**

Run: `python -c "import feedback_menu"`
Expected: no output, exit code 0

- [ ] **Step 11: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (219 — this task adds no new test file, but fixes two existing fixtures; the suite staying green confirms both the `feedback_menu.py` refactor AND the fixture fixes are correct)

- [ ] **Step 12: Commit**

```bash
git add feedback_menu.py dashboard/backend/tests/test_feedback_core.py dashboard/backend/tests/test_feedback_routes.py
git commit -m "refactor: read feedback categories from feedback_categories.py instead of hardcoded env vars"
```

---

### Task 3: Wire the env-var migration into `main.py`

**Files:**
- Modify: `main.py` (add one import + one function call)

**Interfaces:**
- Consumes: `feedback_categories.migrate_from_env_if_needed` (Task 1).
- Produces: the migration runs once at bot startup, before `feedback_menu` loads.

- [ ] **Step 1: Read the current file**

Read `main.py` first to see its exact current imports and `setup_hook` body.

- [ ] **Step 2: Add the import**

Add this import alongside `main.py`'s existing top-level imports (after `import discord`):

```python
import feedback_categories
```

- [ ] **Step 3: Call the migration before `feedback_menu` loads**

Find:

```python
    async def setup_hook(self):
        await self.load_extension("feedback_menu")
```

Replace with:

```python
    async def setup_hook(self):
        feedback_categories.migrate_from_env_if_needed()
        await self.load_extension("feedback_menu")
```

- [ ] **Step 4: Verify the file still imports cleanly**

Run: `python -c "import main"`
Expected: no output, exit code 0

- [ ] **Step 5: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (219)

- [ ] **Step 6: Commit**

```bash
git add main.py
git commit -m "feat: run feedback-category env migration at bot startup"
```

---

### Task 4: `GET`/`POST /api/feedback-categories`

**Files:**
- Modify: `dashboard/backend/routes/feedback.py` (append)
- Test: `dashboard/backend/tests/test_feedback_category_routes.py`

**Interfaces:**
- Consumes: `feedback_categories.load_categories`/`save_categories`/`validate_category_spec` (Task 1, imported as `import feedback_categories` — same bare top-level import style already used for `feedback_core`/`feedback_menu` in this file); `require_dashboard_access`; `_get_guild_or_none` (already defined in this file from Phase 4a).
- Produces: `def _validate_category_relations(spec, guild) -> web.Response | None` (Discord-existence checks — must run AFTER `validate_category_spec`); `def serialize_category(key, entry) -> dict`; `GET /api/feedback-categories` → `200 {"categories": [...]}`; `POST /api/feedback-categories` → `201 {...}` / `400`/`404`/`409`/`503`.

- [ ] **Step 1: Write the failing test**

`dashboard/backend/tests/test_feedback_category_routes.py`:

```python
import pytest

from dashboard.backend.routes.feedback import routes as feedback_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)

import feedback_categories


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(feedback_categories, "CONFIG_FILE", str(tmp_path / "feedback_categories.json"))


def _spec(key="players", case_prefix="PR", channel_id="500", role_id="111"):
    return {
        "key": key,
        "title": "Жалоба на участника",
        "button_label": "Жалоба на участника",
        "channel_id": channel_id,
        "case_prefix": case_prefix,
        "case_title": "Жалоба на участника",
        "thread_name": "player-report",
        "review_role_ids": [role_id],
        "approved_text": "Участник наказан.",
        "denied_text": "Жалоба отклонена.",
        "modal_title": "Жалоба на участника",
        "fields": [
            {"key": "offender", "label": "Ник участника", "style": "short", "required": True, "max_length": 120},
        ],
        "mini_summary_key": "offender",
    }


def build(roles=None, channels=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator], roles=roles or [], channels=channels or [])
    return guild, make_moderation_app(FakeBot(guild), [feedback_routes])


@pytest.mark.asyncio
async def test_list_feedback_categories_empty(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/feedback-categories")
    assert resp.status == 200
    assert (await resp.json()) == {"categories": []}


@pytest.mark.asyncio
async def test_create_feedback_category_success(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-categories", json=_spec())
    assert resp.status == 201
    body = await resp.json()
    assert body["key"] == "players"
    assert body["case_prefix"] == "PR"
    assert feedback_categories.load_categories()["players"]["channel_id"] == "500"


@pytest.mark.asyncio
async def test_create_feedback_category_rejects_invalid_key(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-categories", json=_spec(key="Bad Key"))
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_key"


@pytest.mark.asyncio
async def test_create_feedback_category_rejects_duplicate_key(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    resp = await client.post("/api/feedback-categories", json=_spec())
    assert resp.status == 409
    assert (await resp.json())["error"] == "key_taken"


@pytest.mark.asyncio
async def test_create_feedback_category_checks_structure_before_channel_existence(aiohttp_client):
    # Invalid key AND a channel that doesn't exist -- must get the structural
    # 400, not a 404, proving structural checks run first.
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-categories", json=_spec(key="Bad Key"))
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_key"


@pytest.mark.asyncio
async def test_create_feedback_category_404_when_channel_missing(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    _, app = build(roles=[role], channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-categories", json=_spec())
    assert resp.status == 404
    assert (await resp.json())["error"] == "channel_not_found"


@pytest.mark.asyncio
async def test_create_feedback_category_404_when_role_missing(aiohttp_client):
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-categories", json=_spec())
    assert resp.status == 404
    assert (await resp.json())["error"] == "role_not_found"


@pytest.mark.asyncio
async def test_list_feedback_categories_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/feedback-categories")
    assert resp.status == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_feedback_category_routes.py -v`
Expected: FAIL — routes don't exist yet (404s on GET/POST).

- [ ] **Step 3: Append to `dashboard/backend/routes/feedback.py`**

Add this import at the top of the file, alongside the existing `import feedback_core`/`import feedback_menu`:

```python
import feedback_categories
```

Then append at the end of the file:

```python
def _validate_category_relations(spec: dict, guild) -> web.Response | None:
    """Discord-existence checks. Must run AFTER validate_category_spec."""
    try:
        channel_id = int(spec.get("channel_id"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)
    if guild.get_channel(channel_id) is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    for role_id_raw in spec.get("review_role_ids") or []:
        try:
            role_id = int(role_id_raw)
        except (TypeError, ValueError):
            return web.json_response({"error": "invalid_request"}, status=400)
        if guild.get_role(role_id) is None:
            return web.json_response({"error": "role_not_found"}, status=404)
    return None


def serialize_category(key: str, entry: dict) -> dict:
    return {"key": key, **entry}


@routes.get("/api/feedback-categories")
@require_dashboard_access
async def list_feedback_categories(request: web.Request) -> web.Response:
    categories = feedback_categories.load_categories()
    return web.json_response(
        {"categories": [serialize_category(key, entry) for key, entry in categories.items()]}
    )


@routes.post("/api/feedback-categories")
@require_dashboard_access
async def create_feedback_category(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    categories = feedback_categories.load_categories()
    error = feedback_categories.validate_category_spec(body, categories, existing_key=None)
    if error:
        status_code = 409 if error in ("key_taken", "case_prefix_taken") else 400
        return web.json_response({"error": error}, status=status_code)

    error_response = _validate_category_relations(body, guild)
    if error_response:
        return error_response

    key = body["key"]
    entry = {k: v for k, v in body.items() if k != "key"}
    categories[key] = entry
    feedback_categories.save_categories(categories)

    return web.json_response(serialize_category(key, entry), status=201)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_feedback_category_routes.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routes/feedback.py dashboard/backend/tests/test_feedback_category_routes.py
git commit -m "feat(dashboard): add GET/POST /api/feedback-categories"
```

---

### Task 5: `PUT`/`DELETE /api/feedback-categories/{category_key}`

**Files:**
- Modify: `dashboard/backend/routes/feedback.py` (append)
- Test: `dashboard/backend/tests/test_feedback_category_routes.py` (append)

**Interfaces:**
- Consumes: everything from Task 4.
- Produces: `PUT /api/feedback-categories/{category_key}` → `200 {...}` / `400`/`404`/`409`/`503`; `DELETE /api/feedback-categories/{category_key}` → `200 {"ok": true}` / `404`.

- [ ] **Step 1: Write the failing test**

Append to `dashboard/backend/tests/test_feedback_category_routes.py`:

```python
@pytest.mark.asyncio
async def test_update_feedback_category_success(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    updated = _spec()
    updated["title"] = "Обновлённая жалоба"

    resp = await client.put("/api/feedback-categories/players", json=updated)
    assert resp.status == 200
    body = await resp.json()
    assert body["title"] == "Обновлённая жалоба"
    assert feedback_categories.load_categories()["players"]["title"] == "Обновлённая жалоба"


@pytest.mark.asyncio
async def test_update_feedback_category_404_when_unknown(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/feedback-categories/missing", json=_spec())
    assert resp.status == 404
    assert (await resp.json())["error"] == "not_found"


@pytest.mark.asyncio
async def test_update_feedback_category_keeps_own_case_prefix(aiohttp_client):
    # Editing a category and re-submitting its own unchanged case_prefix must
    # NOT be rejected as a duplicate against itself.
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    resp = await client.put("/api/feedback-categories/players", json=_spec())
    assert resp.status == 200


@pytest.mark.asyncio
async def test_delete_feedback_category_removes_it(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    resp = await client.delete("/api/feedback-categories/players")
    assert resp.status == 200
    assert feedback_categories.load_categories() == {}


@pytest.mark.asyncio
async def test_delete_feedback_category_404_when_unknown(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete("/api/feedback-categories/missing")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_delete_feedback_category_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.delete("/api/feedback-categories/players")
    assert resp.status == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest dashboard/backend/tests/test_feedback_category_routes.py -v`
Expected: FAIL — `PUT`/`DELETE` routes don't exist yet.

- [ ] **Step 3: Append to `dashboard/backend/routes/feedback.py`**

```python
@routes.put("/api/feedback-categories/{category_key}")
@require_dashboard_access
async def update_feedback_category(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    category_key = request.match_info["category_key"]
    categories = feedback_categories.load_categories()
    if category_key not in categories:
        return web.json_response({"error": "not_found"}, status=404)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    spec = {**body, "key": category_key}
    error = feedback_categories.validate_category_spec(spec, categories, existing_key=category_key)
    if error:
        status_code = 409 if error in ("key_taken", "case_prefix_taken") else 400
        return web.json_response({"error": error}, status=status_code)

    error_response = _validate_category_relations(spec, guild)
    if error_response:
        return error_response

    entry = {k: v for k, v in body.items() if k != "key"}
    categories[category_key] = entry
    feedback_categories.save_categories(categories)

    return web.json_response(serialize_category(category_key, entry))


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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest dashboard/backend/tests/test_feedback_category_routes.py -v`
Expected: PASS (14 tests total in this file)

- [ ] **Step 5: Run the full backend suite**

Run: `pytest dashboard/backend/tests/ -q`
Expected: all pass (219 + 8 + 6 = 233)

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/feedback.py dashboard/backend/tests/test_feedback_category_routes.py
git commit -m "feat(dashboard): add PUT/DELETE feedback-category routes"
```

---

### Task 6: Frontend API client — feedback-category functions

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts` (append; do NOT change any existing export)
- Test: `dashboard/frontend/src/api/feedbackCategories.test.ts`

**Interfaces:**
- Consumes: existing `apiFetch`, `jsonInit` (already in `client.ts`).
- Produces: `interface FeedbackCategoryFieldSpec { key: string; label: string; style: 'short' | 'paragraph'; required: boolean; max_length: number }`; `interface FeedbackCategorySpec { key: string; title: string; button_label: string; channel_id: string; case_prefix: string; case_title: string; thread_name: string; review_role_ids: string[]; approved_text: string; denied_text: string; modal_title: string; fields: FeedbackCategoryFieldSpec[]; mini_summary_key: string }`; `fetchFeedbackCategories(): Promise<FeedbackCategorySpec[]>`; `createFeedbackCategory(spec: FeedbackCategorySpec): Promise<FeedbackCategorySpec>`; `updateFeedbackCategory(key: string, spec: Omit<FeedbackCategorySpec, 'key'>): Promise<FeedbackCategorySpec>`; `deleteFeedbackCategory(key: string): Promise<void>`.

- [ ] **Step 1: Write the failing test**

`dashboard/frontend/src/api/feedbackCategories.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createFeedbackCategory,
  deleteFeedbackCategory,
  fetchFeedbackCategories,
  updateFeedbackCategory,
  type FeedbackCategorySpec,
} from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

const sampleSpec: FeedbackCategorySpec = {
  key: 'players',
  title: 'Жалоба на участника',
  button_label: 'Жалоба на участника',
  channel_id: '500',
  case_prefix: 'PR',
  case_title: 'Жалоба на участника',
  thread_name: 'player-report',
  review_role_ids: ['111'],
  approved_text: 'Участник наказан.',
  denied_text: 'Жалоба отклонена.',
  modal_title: 'Жалоба на участника',
  fields: [{ key: 'offender', label: 'Ник участника', style: 'short', required: true, max_length: 120 }],
  mini_summary_key: 'offender',
}

describe('feedback categories api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchFeedbackCategories unwraps the list', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ categories: [sampleSpec] }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchFeedbackCategories()
    expect(result).toEqual([sampleSpec])
    expect(fetchMock).toHaveBeenCalledWith('/api/feedback-categories', expect.anything())
  })

  it('createFeedbackCategory POSTs the full spec including key', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson(sampleSpec))
    vi.stubGlobal('fetch', fetchMock)

    await createFeedbackCategory(sampleSpec)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/feedback-categories',
      expect.objectContaining({ method: 'POST', body: JSON.stringify(sampleSpec) }),
    )
  })

  it('updateFeedbackCategory PUTs by key with the spec minus key', async () => {
    const { key, ...rest } = sampleSpec
    const fetchMock = vi.fn().mockResolvedValue(okJson(sampleSpec))
    vi.stubGlobal('fetch', fetchMock)

    await updateFeedbackCategory(key, rest)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/feedback-categories/players',
      expect.objectContaining({ method: 'PUT', body: JSON.stringify(rest) }),
    )
  })

  it('deleteFeedbackCategory DELETEs by key', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await deleteFeedbackCategory('players')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/feedback-categories/players',
      expect.objectContaining({ method: 'DELETE' }),
    )
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd dashboard/frontend && npm run test`
Expected: FAIL — new exports don't exist.

- [ ] **Step 3: Append to `dashboard/frontend/src/api/client.ts`**

```ts
export interface FeedbackCategoryFieldSpec {
  key: string
  label: string
  style: 'short' | 'paragraph'
  required: boolean
  max_length: number
}

export interface FeedbackCategorySpec {
  key: string
  title: string
  button_label: string
  channel_id: string
  case_prefix: string
  case_title: string
  thread_name: string
  review_role_ids: string[]
  approved_text: string
  denied_text: string
  modal_title: string
  fields: FeedbackCategoryFieldSpec[]
  mini_summary_key: string
}

export async function fetchFeedbackCategories(): Promise<FeedbackCategorySpec[]> {
  const body = await apiFetch<{ categories: FeedbackCategorySpec[] }>('/api/feedback-categories')
  return body.categories
}

export function createFeedbackCategory(spec: FeedbackCategorySpec): Promise<FeedbackCategorySpec> {
  return apiFetch('/api/feedback-categories', jsonInit('POST', spec))
}

export function updateFeedbackCategory(
  key: string,
  spec: Omit<FeedbackCategorySpec, 'key'>,
): Promise<FeedbackCategorySpec> {
  return apiFetch(`/api/feedback-categories/${key}`, jsonInit('PUT', spec))
}

export async function deleteFeedbackCategory(key: string): Promise<void> {
  await apiFetch(`/api/feedback-categories/${key}`, jsonInit('DELETE'))
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test`
Expected: PASS — 4 new + all existing (58 total)

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/feedbackCategories.test.ts
git commit -m "feat(dashboard): add feedback-category API client functions"
```

---

### Task 7: Frontend UI — tabs on `/feedback`, `FeedbackCategoriesPage`

**Files:**
- Create: `dashboard/frontend/src/pages/Feedback.tsx` (new tab-wrapper page)
- Create: `dashboard/frontend/src/pages/FeedbackCategories.tsx`
- Test: `dashboard/frontend/src/pages/FeedbackCategories.test.tsx`
- Test: `dashboard/frontend/src/pages/Feedback.test.tsx`
- Modify: `dashboard/frontend/src/App.tsx` (swap the `/feedback` route's element from `FeedbackCasesPage` directly to the new `FeedbackPage` wrapper)

**Interfaces:**
- Consumes: `fetchFeedbackCategories`, `createFeedbackCategory`, `updateFeedbackCategory`, `deleteFeedbackCategory`, types `FeedbackCategorySpec`/`FeedbackCategoryFieldSpec` (Task 6); `fetchChannels`/`ChannelInfo` (Phase 3b); `fetchRoles`/`RoleInfo` (Phase 2a); `FeedbackCasesPage` (Phase 4a, unchanged); `Button`, `Card`, `Modal` (existing design system).
- Produces: `FeedbackPage()`; `FeedbackCategoriesPage()`.

`dashboard/frontend/src/pages/FeedbackCases.tsx` (Phase 4a) must NOT be modified at all — only imported and rendered unchanged as one of two tabs, exactly like `ReactionRolesPage` was left untouched when `MessageBuilderPage` wrapped it in Phase 3b.

- [ ] **Step 1: Write the failing tests**

`dashboard/frontend/src/pages/FeedbackCategories.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { FeedbackCategoriesPage } from './FeedbackCategories'

const sampleCategory: client.FeedbackCategorySpec = {
  key: 'players',
  title: 'Жалоба на участника',
  button_label: 'Жалоба на участника',
  channel_id: '500',
  case_prefix: 'PR',
  case_title: 'Жалоба на участника',
  thread_name: 'player-report',
  review_role_ids: ['111'],
  approved_text: 'Участник наказан.',
  denied_text: 'Жалоба отклонена.',
  modal_title: 'Жалоба на участника',
  fields: [{ key: 'offender', label: 'Ник участника', style: 'short', required: true, max_length: 120 }],
  mini_summary_key: 'offender',
}

describe('FeedbackCategoriesPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('lists existing categories', async () => {
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([sampleCategory])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'reports' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '111', name: 'Reviewers', color: '#000000', position: 1 }])

    render(<FeedbackCategoriesPage />)

    expect(await screen.findByText('Жалоба на участника')).toBeInTheDocument()
    expect(screen.getByText('PR')).toBeInTheDocument()
  })

  it('creates a new category', async () => {
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'reports' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '111', name: 'Reviewers', color: '#000000', position: 1 }])
    const createSpy = vi.spyOn(client, 'createFeedbackCategory').mockResolvedValue(sampleCategory)

    render(<FeedbackCategoriesPage />)

    await waitFor(() => screen.getByText('Создать категорию'))
    fireEvent.click(screen.getByText('Создать категорию'))

    await waitFor(() => screen.getByLabelText('Ключ'))
    fireEvent.change(screen.getByLabelText('Ключ'), { target: { value: 'players' } })
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'Жалоба на участника' } })
    fireEvent.change(screen.getByLabelText('Текст кнопки'), { target: { value: 'Жалоба на участника' } })
    fireEvent.change(screen.getByLabelText('Заголовок дела'), { target: { value: 'Жалоба на участника' } })
    fireEvent.change(screen.getByLabelText('Заголовок формы'), { target: { value: 'Жалоба на участника' } })
    fireEvent.change(screen.getByLabelText('Имя треда'), { target: { value: 'player-report' } })
    fireEvent.change(screen.getByLabelText('Префикс дела'), { target: { value: 'PR' } })
    fireEvent.change(screen.getByLabelText('Канал'), { target: { value: '500' } })
    fireEvent.change(screen.getByLabelText('Текст при принятии'), { target: { value: 'Участник наказан.' } })
    fireEvent.change(screen.getByLabelText('Текст при отклонении'), { target: { value: 'Жалоба отклонена.' } })
    fireEvent.change(screen.getByPlaceholderText('Ключ поля'), { target: { value: 'offender' } })
    fireEvent.change(screen.getByPlaceholderText('Название поля'), { target: { value: 'Ник участника' } })

    fireEvent.click(screen.getByText('Сохранить'))

    await waitFor(() => expect(createSpy).toHaveBeenCalled())
  })

  it('deletes a category after confirmation', async () => {
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([sampleCategory])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'reports' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const deleteSpy = vi.spyOn(client, 'deleteFeedbackCategory').mockResolvedValue(undefined)

    render(<FeedbackCategoriesPage />)

    await waitFor(() => screen.getByText('Удалить'))
    fireEvent.click(screen.getByText('Удалить'))
    fireEvent.click(screen.getByText('Удалить категорию'))

    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith('players'))
  })
})
```

`dashboard/frontend/src/pages/Feedback.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { FeedbackPage } from './Feedback'

describe('FeedbackPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('shows cases by default and switches to categories tab', async () => {
    vi.spyOn(client, 'fetchFeedbackCases').mockResolvedValue([])
    vi.spyOn(client, 'fetchFeedbackCategories').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<FeedbackPage />)

    await waitFor(() => screen.getByText('Обращения'))
    expect(screen.getByText('Обращений нет.')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Категории'))
    await waitFor(() => screen.getByText('Создать категорию'))
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm run test`
Expected: FAIL — `Cannot find module './FeedbackCategories'` / `Cannot find module './Feedback'`.

- [ ] **Step 3: Implement `dashboard/frontend/src/pages/FeedbackCategories.tsx`**

```tsx
import { useEffect, useState } from 'react'
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
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'

const EMPTY_FIELD: FeedbackCategoryFieldSpec = { key: '', label: '', style: 'short', required: true, max_length: 200 }

function emptySpec(): FeedbackCategorySpec {
  return {
    key: '',
    title: '',
    button_label: '',
    channel_id: '',
    case_prefix: '',
    case_title: '',
    thread_name: '',
    review_role_ids: [],
    approved_text: '',
    denied_text: '',
    modal_title: '',
    fields: [{ ...EMPTY_FIELD }],
    mini_summary_key: '',
  }
}

export function FeedbackCategoriesPage() {
  const [categories, setCategories] = useState<FeedbackCategorySpec[]>([])
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [formOpen, setFormOpen] = useState(false)
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [spec, setSpec] = useState<FeedbackCategorySpec>(emptySpec())
  const [pendingDelete, setPendingDelete] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const reload = () => {
    fetchFeedbackCategories().then(setCategories).catch(() => setError('Не удалось загрузить категории'))
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
  }

  useEffect(reload, [])

  const channelName = (id: string) => channels.find((c) => c.id === id)?.name ?? id

  const openCreate = () => {
    setEditingKey(null)
    setSpec(emptySpec())
    setError('')
    setFormOpen(true)
  }

  const openEdit = (category: FeedbackCategorySpec) => {
    setEditingKey(category.key)
    setSpec({ ...category })
    setError('')
    setFormOpen(true)
  }

  const updateField = (index: number, patch: Partial<FeedbackCategoryFieldSpec>) => {
    setSpec((prev) => ({
      ...prev,
      fields: prev.fields.map((f, i) => (i === index ? { ...f, ...patch } : f)),
    }))
  }

  const addField = () => {
    if (spec.fields.length >= 5) return
    setSpec((prev) => ({ ...prev, fields: [...prev.fields, { ...EMPTY_FIELD }] }))
  }

  const removeField = (index: number) => {
    setSpec((prev) => ({ ...prev, fields: prev.fields.filter((_, i) => i !== index) }))
  }

  const toggleRole = (roleId: string) => {
    setSpec((prev) => ({
      ...prev,
      review_role_ids: prev.review_role_ids.includes(roleId)
        ? prev.review_role_ids.filter((r) => r !== roleId)
        : [...prev.review_role_ids, roleId],
    }))
  }

  const save = async () => {
    setError('')
    setBusy(true)
    try {
      const { key, ...rest } = spec
      if (editingKey) {
        await updateFeedbackCategory(editingKey, rest)
      } else {
        await createFeedbackCategory(spec)
      }
      setFormOpen(false)
      reload()
    } catch {
      setError('Не удалось сохранить категорию — проверьте ключ, префикс, канал и роли')
    } finally {
      setBusy(false)
    }
  }

  const confirmDelete = async () => {
    if (!pendingDelete) return
    try {
      await deleteFeedbackCategory(pendingDelete)
      setPendingDelete(null)
      reload()
    } catch {
      setError('Не удалось удалить категорию')
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-foreground">Категории обращений</h1>
        <Button variant="primary" onClick={openCreate}>
          Создать категорию
        </Button>
      </div>

      {error && !formOpen && <p className="mb-4 text-sm text-danger">{error}</p>}

      <div className="flex flex-col gap-2">
        {categories.map((category) => (
          <Card key={category.key} className="flex items-center justify-between !p-3">
            <div>
              <p className="text-sm text-foreground">{category.title}</p>
              <p className="text-xs text-muted">
                {category.case_prefix} · {channelName(category.channel_id)} · полей: {category.fields.length}
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => openEdit(category)}>
                Edit
              </Button>
              <Button variant="danger" onClick={() => setPendingDelete(category.key)}>
                Удалить
              </Button>
            </div>
          </Card>
        ))}
        {categories.length === 0 && <p className="text-sm text-muted">Категорий пока нет.</p>}
      </div>

      <Modal
        open={formOpen}
        title={editingKey ? 'Редактировать категорию' : 'Создать категорию'}
        onClose={() => setFormOpen(false)}
      >
        <div className="flex max-h-[70vh] flex-col gap-3 overflow-y-auto">
          <label className="text-sm text-muted" htmlFor="fc-key">
            Ключ
          </label>
          <input
            id="fc-key"
            value={spec.key}
            onChange={(e) => setSpec((prev) => ({ ...prev, key: e.target.value }))}
            disabled={!!editingKey}
            placeholder="players"
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary disabled:opacity-50"
          />

          <label className="text-sm text-muted" htmlFor="fc-title">
            Название
          </label>
          <input
            id="fc-title"
            value={spec.title}
            onChange={(e) => setSpec((prev) => ({ ...prev, title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-button-label">
            Текст кнопки
          </label>
          <input
            id="fc-button-label"
            value={spec.button_label}
            onChange={(e) => setSpec((prev) => ({ ...prev, button_label: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-case-title">
            Заголовок дела
          </label>
          <input
            id="fc-case-title"
            value={spec.case_title}
            onChange={(e) => setSpec((prev) => ({ ...prev, case_title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-modal-title">
            Заголовок формы
          </label>
          <input
            id="fc-modal-title"
            value={spec.modal_title}
            onChange={(e) => setSpec((prev) => ({ ...prev, modal_title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-thread-name">
            Имя треда
          </label>
          <input
            id="fc-thread-name"
            value={spec.thread_name}
            onChange={(e) => setSpec((prev) => ({ ...prev, thread_name: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-case-prefix">
            Префикс дела
          </label>
          <input
            id="fc-case-prefix"
            value={spec.case_prefix}
            onChange={(e) => setSpec((prev) => ({ ...prev, case_prefix: e.target.value.toUpperCase() }))}
            placeholder="PR"
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-channel">
            Канал
          </label>
          <select
            id="fc-channel"
            value={spec.channel_id}
            onChange={(e) => setSpec((prev) => ({ ...prev, channel_id: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="">Выберите канал…</option>
            {channels.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          <div>
            <p className="mb-1 text-sm text-muted">Роли-ревьюеры</p>
            <div className="flex flex-wrap gap-2">
              {roles.map((role) => (
                <label key={role.id} className="flex items-center gap-1 text-xs text-foreground">
                  <input
                    type="checkbox"
                    checked={spec.review_role_ids.includes(role.id)}
                    onChange={() => toggleRole(role.id)}
                  />
                  {role.name}
                </label>
              ))}
            </div>
          </div>

          <label className="text-sm text-muted" htmlFor="fc-approved-text">
            Текст при принятии
          </label>
          <input
            id="fc-approved-text"
            value={spec.approved_text}
            onChange={(e) => setSpec((prev) => ({ ...prev, approved_text: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="fc-denied-text">
            Текст при отклонении
          </label>
          <input
            id="fc-denied-text"
            value={spec.denied_text}
            onChange={(e) => setSpec((prev) => ({ ...prev, denied_text: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <div className="flex flex-col gap-2">
            <p className="text-sm text-muted">Поля формы (до 5)</p>
            {spec.fields.map((field, index) => (
              <div key={index} className="flex flex-wrap items-center gap-2 rounded-control border border-border/60 p-2">
                <input
                  value={field.key}
                  onChange={(e) => updateField(index, { key: e.target.value })}
                  placeholder="Ключ поля"
                  className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
                />
                <input
                  value={field.label}
                  onChange={(e) => updateField(index, { label: e.target.value })}
                  placeholder="Название поля"
                  className="min-w-0 flex-1 basis-full rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary"
                />
                <select
                  aria-label="Тип поля"
                  value={field.style}
                  onChange={(e) => updateField(index, { style: e.target.value as 'short' | 'paragraph' })}
                  className="rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground"
                >
                  <option value="short">Короткий</option>
                  <option value="paragraph">Многострочный</option>
                </select>
                <label className="flex items-center gap-1 text-xs text-muted">
                  <input
                    type="checkbox"
                    checked={field.required}
                    onChange={(e) => updateField(index, { required: e.target.checked })}
                  />
                  обязательное
                </label>
                <button
                  type="button"
                  onClick={() => removeField(index)}
                  className="cursor-pointer text-muted hover:text-danger"
                >
                  ×
                </button>
              </div>
            ))}
            {spec.fields.length < 5 && (
              <button
                type="button"
                onClick={addField}
                className="cursor-pointer self-start text-sm text-primary hover:text-primary-hover"
              >
                + Добавить поле
              </button>
            )}
          </div>

          <label className="text-sm text-muted" htmlFor="fc-mini-summary">
            Поле для краткого превью
          </label>
          <select
            id="fc-mini-summary"
            value={spec.mini_summary_key}
            onChange={(e) => setSpec((prev) => ({ ...prev, mini_summary_key: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          >
            <option value="">Выберите поле…</option>
            {spec.fields
              .filter((f) => f.key)
              .map((f) => (
                <option key={f.key} value={f.key}>
                  {f.label || f.key}
                </option>
              ))}
          </select>

          {error && <p className="text-sm text-danger">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setFormOpen(false)} disabled={busy}>
              Отмена
            </Button>
            <Button variant="primary" onClick={save} disabled={busy}>
              {busy ? 'Сохраняем…' : 'Сохранить'}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal open={pendingDelete !== null} title="Удалить категорию?" onClose={() => setPendingDelete(null)}>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={() => setPendingDelete(null)}>
            Отмена
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Удалить категорию
          </Button>
        </div>
      </Modal>
    </div>
  )
}
```

- [ ] **Step 4: Implement `dashboard/frontend/src/pages/Feedback.tsx`**

```tsx
import { useState } from 'react'
import { FeedbackCasesPage } from './FeedbackCases'
import { FeedbackCategoriesPage } from './FeedbackCategories'

type Tab = 'cases' | 'categories'

export function FeedbackPage() {
  const [tab, setTab] = useState<Tab>('cases')

  return (
    <div>
      <div className="mb-4 flex gap-2 border-b border-border">
        <button
          type="button"
          onClick={() => setTab('cases')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'cases' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          Обращения
        </button>
        <button
          type="button"
          onClick={() => setTab('categories')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'categories' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          Категории
        </button>
      </div>
      {tab === 'cases' ? <FeedbackCasesPage /> : <FeedbackCategoriesPage />}
    </div>
  )
}
```

- [ ] **Step 5: Wire the route in `App.tsx`**

Read the current file first. Replace:

```tsx
import { FeedbackCasesPage } from './pages/FeedbackCases'
```

with:

```tsx
import { FeedbackPage } from './pages/Feedback'
```

Replace:

```tsx
            <Route path="feedback" element={<FeedbackCasesPage />} />
```

with:

```tsx
            <Route path="feedback" element={<FeedbackPage />} />
```

- [ ] **Step 6: Run tests + typecheck + build**

Run: `npm run test`, `npx tsc --noEmit`, `npm run build`
Expected: all green (62 Vitest tests total: 58 + 3 categories + 1 tab-switch), no debug artifacts, `git status --short` clean before committing.

- [ ] **Step 7: Commit**

```bash
git add dashboard/frontend/src/pages/Feedback.tsx dashboard/frontend/src/pages/FeedbackCategories.tsx dashboard/frontend/src/pages/FeedbackCategories.test.tsx dashboard/frontend/src/pages/Feedback.test.tsx dashboard/frontend/src/App.tsx
git commit -m "feat(dashboard): add feedback category management UI with tabs"
```

---

### Task 8: Full end-to-end manual verification

**Files:** none (verification only).

- [ ] **Step 1:** Restart backend (`python main.py`) and frontend (`npm run dev`), open `http://localhost:5173`, log in. Confirm on backend startup (check for no crash) that `feedback_categories.json` was created (migration ran) with the existing "players" category matching the previous env-var-driven values.
- [ ] **Step 2:** Sidebar "Feedback и тикеты" (`/feedback`) now shows two tabs. Confirm "Обращения" tab still works exactly as before (Phase 4a unaffected) — existing/new cases still list and can be accepted/rejected.
- [ ] **Step 3:** Switch to "Категории" tab. Confirm the existing "players" category (migrated from env vars) appears with its 4 fields.
- [ ] **Step 4:** Edit the "players" category — change its title, save. Confirm the change is reflected immediately in the list (no restart needed).
- [ ] **Step 5:** Create a brand new category (different `key`, `case_prefix`, channel, 1-2 fields). Save. In Discord, run `/feedback_panel send` in some channel — confirm the panel now shows TWO buttons, one per category.
- [ ] **Step 6:** Click the new category's button on the panel, fill in the modal, submit. Confirm a case is created under the new category's channel/thread, with the new `case_prefix` used in its case ID (e.g. starting at `-0001` for its own counter, independent of "players"'s counter).
- [ ] **Step 7:** Confirm the new case appears correctly in the dashboard's "Обращения" tab, showing the new category's title and submitted field values.
- [ ] **Step 8:** Delete the new category from the dashboard. Confirm the existing case created under it still appears in the "Обращения" list (degraded gracefully — shows the raw key instead of a title, per spec).
- [ ] **Step 9:** Try creating a category with a `case_prefix` already used by "players" — confirm the dashboard rejects it with a clear error before any Discord call.
- [ ] **Step 10:** Record results in the progress ledger. No commit (nothing changed).

---

## Self-Review Notes

- **Spec coverage:** JSON-backed storage replacing env vars, no caching → Task 1 (`feedback_categories.py`); one-time migration preserving the existing category's `case_prefix` (counter continuity) → Task 1's `migrate_from_env_if_needed`, wired at boot → Task 3; `feedback_menu.get_feedback_categories()` keeping its exact name/import path → Task 2; `button_style` fixed, not dashboard-editable → Task 2 Step 3; `review_user_ids` out of scope, defensively guarded → Task 2 Steps 5-6; full CRUD API with binding validation order (structural → Discord existence) → Tasks 4-5, with a dedicated test proving structural checks run first; case_prefix uniqueness excluding self on edit → Task 1's `validate_category_spec` + Task 5's regression test; deletion allowed without blocking on existing cases (relies on Phase 4a's already-verified graceful degradation) → no new code needed, confirmed via Task 8 Step 8; tabs on `/feedback`, `FeedbackCasesPage` untouched → Task 7. "Вне рамок" items (`review_user_ids` dashboard editing, `button_style` editing, auto-refreshing already-posted panels, panel publishing from the dashboard) are correctly absent from every task.
- **Cross-task compatibility risk found and resolved during planning:** Task 2's `feedback_menu.py` refactor deletes `_feedback_categories_cache`, which two existing Phase-4a test fixtures (`test_feedback_core.py`, `test_feedback_routes.py`) monkeypatch by name — `monkeypatch.setattr` raises `AttributeError` on a nonexistent target, so both fixtures would break the moment this task's code changes land. Both fixture replacements are folded into Task 2's own commit (Steps 8-9), not left for a later task, so the suite never goes red mid-plan.
- **Type consistency:** `FeedbackCategorySpec`/`FeedbackCategoryFieldSpec` (Task 6) match `serialize_category`'s output (Task 4) field-for-field; `_validate_category_relations` (Task 4) is reused unmodified by Task 5's `PUT` handler; IDs are strings end-to-end (JSON storage → API response → frontend types → `int()` conversion only at the exact three Discord-API call sites identified in Task 2).
- **Placeholder scan:** none found — every step has complete code.
