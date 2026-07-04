# Dashboard: Tournament Bracket Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the single-elimination tournament bracket generator approved in `docs/superpowers/specs/2026-07-04-dashboard-bracket-generator-design.md` (commit `538b475`): create brackets from a tournament event's participants or by typing names manually, click through winners round by round, and share a read-only public link.

**Architecture:** A new root module `brackets.py` (no discord.py cog — this feature never touches Discord) owns storage and the pure bracket-generation/advancement logic. A new `dashboard/backend/routes/brackets.py` exposes CRUD, winner-advancement, and share-link routes, plus one deliberately unauthenticated public route. Three new frontend pages (`Brackets.tsx` list/create, `BracketDetail.tsx` the interactive grid, `PublicBracket.tsx` the read-only public view mounted outside the authenticated shell) round it out.

**Tech Stack:** Python + aiohttp.web (backend), React + TypeScript + Vite (frontend), pytest + pytest-asyncio (backend tests), Vitest + Testing Library (frontend tests).

## Global Constraints

- Single-elimination only. No double-elimination, round-robin, or group stages.
- A bracket is a snapshot: entries are copied in at creation time and never retroactively synced if the source event's participants change later.
- Byes are placed using the standard recursive bracket-seeding algorithm (see Task 1), NOT naive end-padding + sequential pairing — the naive approach produces an unresolvable bye-vs-bye match for almost every entry count that isn't itself a power of two, confirmed both mathematically and by brute-force check across n=2..24 with zero double-null cases under the standard algorithm. This is a correction to the literal wording in the approved spec's "entries" example, confirmed with the user during planning.
- A bracket requires at least 2 entries; creation is rejected below that.
- `entries` on a bracket record is the organizer's final submitted order (unpadded, pre-seeding) — `rounds[0]` is what actually reflects the seeded/padded bracket-slot arrangement after the standard seeding algorithm is applied. These are deliberately different: `entries` is an audit trail of what was submitted, `rounds` is the generated structure.
- Picking a different winner than previously recorded overwrites the pick and clears ALL downstream picks that depended on it (any change to either slot of an already-decided next-round match clears that match's decision, conservatively — this never silently assumes a downstream human judgment still applies after an upstream correction).
- `user_id`/`moderator_id`-style IDs (`created_by`) are stored as strings, matching the project-wide convention for Discord snowflakes.
- `share_token` is generated via `secrets.token_urlsafe(32)`, independent of the bracket's own `id`. The public route requires zero authentication and returns 404 for an unknown/cleared token. No route anywhere allows writing via a share token.
- `brackets_data.json` must be added to `.gitignore`.

---

## File Structure

- `brackets.py` (new, root) — storage (`load_brackets`/`save_brackets`), entry-extraction from events (`extract_entries_from_event`), bracket generation (`generate_rounds` and its helpers), winner-advancement (`set_winner`), and `create_bracket`.
- `dashboard/backend/routes/brackets.py` (new) — all HTTP routes, calling into `brackets.py`.
- `dashboard/frontend/src/api/client.ts` (modified) — new types + functions.
- `dashboard/frontend/src/pages/Brackets.tsx` (new) — list + create flow.
- `dashboard/frontend/src/pages/BracketDetail.tsx` (new) — the interactive grid.
- `dashboard/frontend/src/pages/PublicBracket.tsx` (new) — public read-only view.
- `dashboard/frontend/src/pages/DashboardShell.tsx` (modified) — nav entry.
- `dashboard/frontend/src/App.tsx` (modified) — routes.
- `.gitignore` (modified).

---

### Task 1: `brackets.py` — storage, entry extraction, bracket generation

**Files:**
- Create: `brackets.py`
- Test: `dashboard/backend/tests/test_brackets_core.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `brackets.BRACKETS_FILE: str` (module attribute, for monkeypatching in tests), `brackets.load_brackets() -> dict`, `brackets.save_brackets(data: dict) -> None` — flat dict keyed by bracket id (no wrapper key), matching `reaction_roles.json`'s style.
- Produces: `brackets.extract_entries_from_event(ev: dict, guild) -> list[str]` — `ev` is a raw event dict from `events_data.json`'s `"events"` mapping (must have `ev["type"] == "tournament"`). `guild` is a discord.py `Guild`-like object with `get_member(user_id)`, or `None`.
- Produces: `brackets.generate_rounds(entries: list[str]) -> list[list[dict]]` — each match dict is `{"slot_a": str|None, "slot_b": str|None, "winner": "a"|"b"|None}`.
- Produces: `brackets.create_bracket(title: str, entries: list[str], source_event_id: str|None, created_by: int) -> dict` — returns a full bracket record as shown in the spec's JSON shape.
- Produces: `brackets.set_winner(bracket: dict, round_index: int, match_index: int, winner: str) -> None` — mutates `bracket` in place. Task 2 tests this in more depth; this task only needs it to exist and be importable, since `create_bracket`'s own tests don't call it.

- [ ] **Step 1: Write the failing tests for storage and entry extraction**

Create `dashboard/backend/tests/test_brackets_core.py`:

```python
import pytest

import brackets


@pytest.fixture(autouse=True)
def isolated_brackets_file(tmp_path, monkeypatch):
    monkeypatch.setattr(brackets, "BRACKETS_FILE", str(tmp_path / "brackets_data.json"))


def test_load_brackets_returns_empty_dict_when_file_missing():
    assert brackets.load_brackets() == {}


def test_load_brackets_returns_empty_dict_on_corrupt_json():
    with open(brackets.BRACKETS_FILE, "w", encoding="utf-8") as f:
        f.write("{not valid json")
    assert brackets.load_brackets() == {}


def test_save_then_load_round_trip():
    data = {"abc": {"id": "abc", "title": "T"}}
    brackets.save_brackets(data)
    assert brackets.load_brackets() == data


class _FakeMember:
    def __init__(self, member_id, display_name):
        self.id = member_id
        self.display_name = display_name


class _FakeGuild:
    def __init__(self, members):
        self._members = members

    def get_member(self, user_id):
        return next((m for m in self._members if m.id == user_id), None)


def test_extract_entries_solo_mode_uses_ign():
    ev = {"type": "tournament", "mode": "solo", "participants": [{"user_id": 1, "ign": "Nickname"}]}
    assert brackets.extract_entries_from_event(ev, guild=None) == ["Nickname"]


def test_extract_entries_solo_mode_falls_back_to_member_display_name():
    ev = {"type": "tournament", "mode": "solo", "participants": [{"user_id": 42, "ign": None}]}
    guild = _FakeGuild([_FakeMember(42, "DiscordName")])
    assert brackets.extract_entries_from_event(ev, guild) == ["DiscordName"]


def test_extract_entries_solo_mode_falls_back_to_user_id_when_no_member():
    ev = {"type": "tournament", "mode": "solo", "participants": [{"user_id": 99, "ign": None}]}
    assert brackets.extract_entries_from_event(ev, guild=None) == ["User 99"]


def test_extract_entries_team_captain_mode():
    ev = {
        "type": "tournament",
        "mode": "team_captain",
        "participants": [
            {"user_id": 1, "team_name": "Alpha", "members": "a, b, c"},
            {"user_id": 2, "team_name": "Beta", "members": "d, e, f"},
        ],
    }
    assert brackets.extract_entries_from_event(ev, guild=None) == ["Alpha", "Beta"]


def test_extract_entries_team_code_mode_groups_by_code_and_uses_captain_name():
    ev = {
        "type": "tournament",
        "mode": "team_code",
        "participants": [
            {"user_id": 1, "team_code": "ABC123", "team_name": "Alpha", "is_captain": True},
            {"user_id": 2, "team_code": "ABC123", "team_name": "Alpha", "is_captain": False},
            {"user_id": 3, "team_code": "XYZ999", "team_name": "Beta", "is_captain": True},
        ],
    }
    assert brackets.extract_entries_from_event(ev, guild=None) == ["Alpha", "Beta"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_brackets_core.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'brackets'`.

- [ ] **Step 3: Implement storage and entry extraction**

Create `brackets.py`:

```python
import json
import os
import uuid
from datetime import datetime, timezone

BRACKETS_FILE = "brackets_data.json"


def load_brackets() -> dict:
    if os.path.exists(BRACKETS_FILE):
        with open(BRACKETS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_brackets(data: dict) -> None:
    with open(BRACKETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def extract_entries_from_event(ev: dict, guild) -> list[str]:
    mode = ev.get("mode", "solo")
    participants = ev.get("participants", [])

    if mode == "solo":
        entries = []
        for p in participants:
            ign = p.get("ign")
            if ign:
                entries.append(ign)
                continue
            member = guild.get_member(p["user_id"]) if guild else None
            entries.append(member.display_name if member else f"User {p['user_id']}")
        return entries

    if mode == "team_captain":
        return [p.get("team_name", "") for p in participants]

    teams: dict = {}
    for p in participants:
        teams.setdefault(p.get("team_code"), []).append(p)
    result = []
    for members in teams.values():
        captain = next((m for m in members if m.get("is_captain")), members[0] if members else None)
        result.append(captain.get("team_name", "") if captain else "")
    return result
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_brackets_core.py -v`
Expected: 6 tests PASS.

- [ ] **Step 5: Write the failing tests for the seeding and generation algorithm**

Add to `dashboard/backend/tests/test_brackets_core.py`:

```python
@pytest.mark.parametrize("n,expected", [(1, 1), (2, 2), (3, 4), (4, 4), (5, 8), (8, 8), (9, 16)])
def test_next_power_of_two(n, expected):
    assert brackets._next_power_of_two(n) == expected


@pytest.mark.parametrize(
    "size,expected",
    [
        (2, [1, 2]),
        (4, [1, 4, 2, 3]),
        (8, [1, 8, 4, 5, 2, 7, 3, 6]),
    ],
)
def test_seed_order(size, expected):
    assert brackets._seed_order(size) == expected


def test_generate_rounds_no_byes_perfect_power_of_two():
    rounds = brackets.generate_rounds(["A", "B", "C", "D"])
    assert len(rounds) == 2
    assert rounds[0] == [
        {"slot_a": "A", "slot_b": "D", "winner": None},
        {"slot_a": "B", "slot_b": "C", "winner": None},
    ]
    assert rounds[1] == [{"slot_a": None, "slot_b": None, "winner": None}]


def test_generate_rounds_with_byes_auto_resolves():
    rounds = brackets.generate_rounds(["A", "B", "C", "D", "E"])
    assert rounds[0] == [
        {"slot_a": "A", "slot_b": None, "winner": "a"},
        {"slot_a": "D", "slot_b": "E", "winner": None},
        {"slot_a": "B", "slot_b": None, "winner": "a"},
        {"slot_a": "C", "slot_b": None, "winner": "a"},
    ]
    assert rounds[1] == [
        {"slot_a": "A", "slot_b": None, "winner": None},
        {"slot_a": "B", "slot_b": "C", "winner": None},
    ]
    assert rounds[2] == [{"slot_a": None, "slot_b": None, "winner": None}]


@pytest.mark.parametrize("n", list(range(2, 25)))
def test_generate_rounds_never_produces_a_double_bye_match(n):
    entries = [f"E{i}" for i in range(n)]
    rounds = brackets.generate_rounds(entries)
    for match in rounds[0]:
        assert not (match["slot_a"] is None and match["slot_b"] is None)


def test_create_bracket_builds_expected_shape():
    bracket = brackets.create_bracket("Летний турнир", ["A", "B", "C", "D"], None, 10)
    assert bracket["title"] == "Летний турнир"
    assert bracket["source_event_id"] is None
    assert bracket["entries"] == ["A", "B", "C", "D"]
    assert bracket["created_by"] == "10"
    assert bracket["share_token"] is None
    assert len(bracket["rounds"]) == 2
    assert "id" in bracket
    assert "created_at" in bracket
```

- [ ] **Step 6: Run the tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_brackets_core.py -v -k "power_of_two or seed_order or generate_rounds or create_bracket"`
Expected: FAIL — `AttributeError: module 'brackets' has no attribute '_next_power_of_two'` (and similarly for the other new functions).

- [ ] **Step 7: Implement the seeding and generation algorithm**

Add to `brackets.py` (after `extract_entries_from_event`):

```python
def _next_power_of_two(n: int) -> int:
    power = 1
    while power < n:
        power *= 2
    return power


def _seed_order(size: int) -> list[int]:
    """Standard recursive bracket-seeding order: guarantees a bye (a seed
    number beyond the real entry count) is always paired against a real
    entry in round 1, never against another bye. This is the same
    algorithm used by every real single-elimination bracket tool."""
    order = [1]
    while len(order) < size:
        next_size = len(order) * 2
        new_order = []
        for seed in order:
            new_order.append(seed)
            new_order.append(next_size + 1 - seed)
        order = new_order
    return order


def _match_winner_entry(match: dict) -> str | None:
    if match["winner"] == "a":
        return match["slot_a"]
    if match["winner"] == "b":
        return match["slot_b"]
    return None


def generate_rounds(entries: list[str]) -> list[list[dict]]:
    n = len(entries)
    size = _next_power_of_two(n)
    order = _seed_order(size)
    slots = [entries[seed - 1] if seed <= n else None for seed in order]

    num_rounds = size.bit_length() - 1
    rounds = []

    round1 = []
    for i in range(0, size, 2):
        slot_a, slot_b = slots[i], slots[i + 1]
        match = {"slot_a": slot_a, "slot_b": slot_b, "winner": None}
        if slot_a is not None and slot_b is None:
            match["winner"] = "a"
        elif slot_a is None and slot_b is not None:
            match["winner"] = "b"
        round1.append(match)
    rounds.append(round1)

    prev_round = round1
    for _ in range(1, num_rounds):
        this_round = []
        for i in range(0, len(prev_round), 2):
            slot_a = _match_winner_entry(prev_round[i])
            slot_b = _match_winner_entry(prev_round[i + 1])
            this_round.append({"slot_a": slot_a, "slot_b": slot_b, "winner": None})
        rounds.append(this_round)
        prev_round = this_round

    return rounds


def create_bracket(title: str, entries: list[str], source_event_id: str | None, created_by: int) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "source_event_id": source_event_id,
        "entries": entries,
        "rounds": generate_rounds(entries),
        "created_by": str(created_by),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "share_token": None,
    }
```

- [ ] **Step 8: Run the tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_brackets_core.py -v`
Expected: all tests PASS (6 from Step 4 + the new ones: 7 `next_power_of_two` cases + 3 `seed_order` cases + 4 generation/creation tests + 23 `test_generate_rounds_never_produces_a_double_bye_match` parametrized cases = 43 total).

- [ ] **Step 9: Add `brackets_data.json` to `.gitignore`**

In `.gitignore`, add a new line after the existing `moderation_log.json` entry (the file currently ends with `feedback_categories.json` / `reaction_roles.json` / `moderation_log.json` on the last three lines):

```
brackets_data.json
```

- [ ] **Step 10: Commit**

```bash
git add brackets.py dashboard/backend/tests/test_brackets_core.py .gitignore
git commit -m "feat: add brackets module — storage, entry extraction, generation"
```

---

### Task 2: `brackets.py` — winner advancement

**Files:**
- Modify: `brackets.py` (add `set_winner`)
- Test: `dashboard/backend/tests/test_brackets_core.py`

**Interfaces:**
- Consumes: `brackets.generate_rounds` from Task 1 (used to build test fixtures).
- Produces: `brackets.set_winner(bracket: dict, round_index: int, match_index: int, winner: "a"|"b") -> None` — mutates `bracket["rounds"]` in place. Task 4 (the winner-setting route) calls this.

- [ ] **Step 1: Write the failing tests**

Add to the end of `dashboard/backend/tests/test_brackets_core.py`:

```python
def _bracket_from_entries(entries):
    return brackets.create_bracket("Test", entries, None, 1)


def test_set_winner_advances_entry_to_next_round():
    bracket = _bracket_from_entries(["A", "B", "C", "D"])
    brackets.set_winner(bracket, 0, 0, "a")
    assert bracket["rounds"][0][0]["winner"] == "a"
    assert bracket["rounds"][1][0]["slot_a"] == "A"
    assert bracket["rounds"][1][0]["winner"] is None


def test_set_winner_completes_the_final_match():
    bracket = _bracket_from_entries(["A", "B", "C", "D"])
    brackets.set_winner(bracket, 0, 0, "a")
    brackets.set_winner(bracket, 0, 1, "a")
    brackets.set_winner(bracket, 1, 0, "a")
    assert bracket["rounds"][1][0]["winner"] == "a"
    assert bracket["rounds"][1][0]["slot_a"] == "A"


def test_set_winner_overwriting_a_pick_clears_the_downstream_pick():
    bracket = _bracket_from_entries(["A", "B", "C", "D"])
    brackets.set_winner(bracket, 0, 0, "a")  # A advances
    brackets.set_winner(bracket, 0, 1, "a")  # B advances
    brackets.set_winner(bracket, 1, 0, "a")  # A wins the final
    assert bracket["rounds"][1][0]["winner"] == "a"

    brackets.set_winner(bracket, 0, 0, "b")  # correction: D actually won, not A
    assert bracket["rounds"][1][0]["slot_a"] == "D"
    assert bracket["rounds"][1][0]["winner"] is None  # the final's pick was cleared


def test_set_winner_changing_the_other_semifinal_also_clears_the_final():
    bracket = _bracket_from_entries(["A", "B", "C", "D"])
    brackets.set_winner(bracket, 0, 0, "a")  # A advances
    brackets.set_winner(bracket, 0, 1, "a")  # B advances
    brackets.set_winner(bracket, 1, 0, "a")  # A wins the final
    assert bracket["rounds"][1][0]["winner"] == "a"

    brackets.set_winner(bracket, 0, 1, "b")  # correction: C advances instead of B
    assert bracket["rounds"][1][0]["slot_b"] == "C"
    assert bracket["rounds"][1][0]["winner"] is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_brackets_core.py -v -k "set_winner"`
Expected: FAIL — `AttributeError: module 'brackets' has no attribute 'set_winner'`.

- [ ] **Step 3: Implement `set_winner`**

Add to the end of `brackets.py`:

```python
def set_winner(bracket: dict, round_index: int, match_index: int, winner: str) -> None:
    match = bracket["rounds"][round_index][match_index]
    match["winner"] = winner
    entry = match["slot_a"] if winner == "a" else match["slot_b"]
    _propagate(bracket, round_index, match_index, entry)


def _propagate(bracket: dict, round_index: int, match_index: int, entry) -> None:
    rounds = bracket["rounds"]
    next_round_index = round_index + 1
    if next_round_index >= len(rounds):
        return
    next_match_index = match_index // 2
    slot_key = "slot_a" if match_index % 2 == 0 else "slot_b"
    next_match = rounds[next_round_index][next_match_index]
    next_match[slot_key] = entry
    if next_match["winner"] is not None:
        next_match["winner"] = None
        _propagate(bracket, next_round_index, next_match_index, None)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_brackets_core.py -v`
Expected: all tests PASS (47 total: the 43 from Task 1 plus these 4 new ones).

- [ ] **Step 5: Commit**

```bash
git add brackets.py dashboard/backend/tests/test_brackets_core.py
git commit -m "feat: add winner-advancement logic to the brackets module"
```

---

### Task 3: Backend CRUD routes + event-entries preview

**Files:**
- Create: `dashboard/backend/routes/brackets.py`
- Test: `dashboard/backend/tests/test_brackets_routes.py`

**Interfaces:**
- Consumes: `brackets.load_brackets`, `brackets.save_brackets`, `brackets.create_bracket`, `brackets.extract_entries_from_event` from Tasks 1-2. `events.load_events()` (existing, from `events.py`).
- Produces: `GET /api/brackets`, `POST /api/brackets`, `GET /api/brackets/{id}`, `DELETE /api/brackets/{id}`, `GET /api/brackets/entries-from-event/{event_id}`. `serialize_bracket_summary`/`serialize_bracket_detail` functions — Tasks 4-5 reuse `serialize_bracket_detail`.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/backend/tests/test_brackets_routes.py`:

```python
import pytest

import brackets
import events
from dashboard.backend.routes.brackets import routes as brackets_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_files(tmp_path, monkeypatch):
    monkeypatch.setattr(brackets, "BRACKETS_FILE", str(tmp_path / "brackets_data.json"))
    monkeypatch.setattr(events, "EVENTS_FILE", str(tmp_path / "events_data.json"))


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    return make_moderation_app(FakeBot(guild), [brackets_routes])


def _tournament_event(mode="solo", participants=None, **overrides):
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
        "status": "open",
        "participants": participants or [],
        "options": [],
        "multi_select": False,
        "votes": {},
    }
    ev.update(overrides)
    return ev


@pytest.mark.asyncio
async def test_list_brackets_returns_summaries(aiohttp_client):
    data = {"b1": brackets.create_bracket("T1", ["A", "B"], None, 10)}
    brackets.save_brackets(data)
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/brackets")
    assert resp.status == 200
    body = await resp.json()
    assert body["brackets"][0]["title"] == "T1"
    assert body["brackets"][0]["entry_count"] == 2


@pytest.mark.asyncio
async def test_list_brackets_requires_auth(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/brackets")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_create_bracket_manual(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/brackets", json={"title": "Manual", "entries": ["X", "Y", "Z"]}
    )
    assert resp.status == 201
    body = await resp.json()
    assert body["title"] == "Manual"
    assert body["entries"] == ["X", "Y", "Z"]
    assert len(body["rounds"]) == 2

    stored = brackets.load_brackets()
    assert len(stored) == 1


@pytest.mark.asyncio
async def test_create_bracket_rejects_fewer_than_two_entries(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/brackets", json={"title": "Manual", "entries": ["X"]})
    assert resp.status == 400
    assert (await resp.json())["error"] == "not_enough_entries"


@pytest.mark.asyncio
async def test_create_bracket_rejects_blank_title(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/brackets", json={"title": "  ", "entries": ["X", "Y"]})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_create_bracket_from_event(aiohttp_client):
    await events.save_events(
        {
            "events": {
                "900": _tournament_event(
                    mode="solo", participants=[{"user_id": 1, "ign": "A"}, {"user_id": 2, "ign": "B"}]
                )
            }
        }
    )
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/brackets", json={"title": "From Event", "source_event_id": "900", "entries": ["B", "A"]}
    )
    assert resp.status == 201
    body = await resp.json()
    assert body["source_event_id"] == "900"
    assert body["entries"] == ["B", "A"]


@pytest.mark.asyncio
async def test_create_bracket_from_event_rejects_tampered_entries(aiohttp_client):
    await events.save_events(
        {
            "events": {
                "900": _tournament_event(
                    mode="solo", participants=[{"user_id": 1, "ign": "A"}, {"user_id": 2, "ign": "B"}]
                )
            }
        }
    )
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/brackets",
        json={"title": "From Event", "source_event_id": "900", "entries": ["A", "Hacker"]},
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "entries_mismatch"


@pytest.mark.asyncio
async def test_create_bracket_from_missing_event_404s(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/brackets", json={"title": "From Event", "source_event_id": "999", "entries": ["A", "B"]}
    )
    assert resp.status == 404
    assert (await resp.json())["error"] == "event_not_found"


@pytest.mark.asyncio
async def test_get_bracket_detail(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B"], None, 10)
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get(f"/api/brackets/{bracket['id']}")
    assert resp.status == 200
    assert (await resp.json())["title"] == "T1"


@pytest.mark.asyncio
async def test_get_bracket_detail_404_when_missing(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/brackets/does-not-exist")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_delete_bracket(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B"], None, 10)
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete(f"/api/brackets/{bracket['id']}")
    assert resp.status == 200
    assert brackets.load_brackets() == {}


@pytest.mark.asyncio
async def test_entries_from_event_preview(aiohttp_client):
    await events.save_events(
        {
            "events": {
                "900": _tournament_event(
                    mode="team_captain",
                    participants=[
                        {"user_id": 1, "team_name": "Alpha", "members": ""},
                        {"user_id": 2, "team_name": "Beta", "members": ""},
                    ],
                )
            }
        }
    )
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/brackets/entries-from-event/900")
    assert resp.status == 200
    assert (await resp.json())["entries"] == ["Alpha", "Beta"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_brackets_routes.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dashboard.backend.routes.brackets'`.

- [ ] **Step 3: Implement the routes**

Create `dashboard/backend/routes/brackets.py`:

```python
from aiohttp import web

import brackets
import events
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


def serialize_bracket_summary(bracket: dict) -> dict:
    return {
        "id": bracket["id"],
        "title": bracket["title"],
        "source_event_id": bracket.get("source_event_id"),
        "entry_count": len(bracket.get("entries", [])),
        "created_at": bracket["created_at"],
    }


def serialize_bracket_detail(bracket: dict) -> dict:
    return {
        "id": bracket["id"],
        "title": bracket["title"],
        "source_event_id": bracket.get("source_event_id"),
        "entries": bracket.get("entries", []),
        "rounds": bracket.get("rounds", []),
        "share_token": bracket.get("share_token"),
    }


@routes.get("/api/brackets")
@require_dashboard_access
async def list_brackets(request: web.Request) -> web.Response:
    data = brackets.load_brackets()
    return web.json_response({"brackets": [serialize_bracket_summary(b) for b in data.values()]})


@routes.post("/api/brackets")
@require_dashboard_access
async def create_bracket_route(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    title = (body.get("title") or "").strip()
    entries = body.get("entries") or []
    source_event_id = body.get("source_event_id")

    if not title:
        return web.json_response({"error": "invalid_request"}, status=400)
    if len(entries) < 2:
        return web.json_response({"error": "not_enough_entries"}, status=400)

    if source_event_id:
        events_data = await events.load_events()
        ev = events_data.get("events", {}).get(str(source_event_id))
        if ev is None or ev.get("type") != "tournament":
            return web.json_response({"error": "event_not_found"}, status=404)
        guild = _get_guild_or_none(request)
        expected = brackets.extract_entries_from_event(ev, guild)
        if sorted(entries) != sorted(expected):
            return web.json_response({"error": "entries_mismatch"}, status=400)

    moderator = request["moderator"]
    bracket = brackets.create_bracket(
        title, entries, str(source_event_id) if source_event_id else None, moderator.id
    )
    data = brackets.load_brackets()
    data[bracket["id"]] = bracket
    brackets.save_brackets(data)
    return web.json_response(serialize_bracket_detail(bracket), status=201)


@routes.get("/api/brackets/entries-from-event/{event_id}")
@require_dashboard_access
async def entries_from_event(request: web.Request) -> web.Response:
    events_data = await events.load_events()
    ev = events_data.get("events", {}).get(request.match_info["event_id"])
    if ev is None or ev.get("type") != "tournament":
        return web.json_response({"error": "event_not_found"}, status=404)
    guild = _get_guild_or_none(request)
    return web.json_response({"entries": brackets.extract_entries_from_event(ev, guild)})


@routes.get("/api/brackets/{id}")
@require_dashboard_access
async def get_bracket(request: web.Request) -> web.Response:
    data = brackets.load_brackets()
    bracket = data.get(request.match_info["id"])
    if bracket is None:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    return web.json_response(serialize_bracket_detail(bracket))


@routes.delete("/api/brackets/{id}")
@require_dashboard_access
async def delete_bracket(request: web.Request) -> web.Response:
    data = brackets.load_brackets()
    bracket_id = request.match_info["id"]
    if bracket_id not in data:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    del data[bracket_id]
    brackets.save_brackets(data)
    return web.json_response({"ok": True})
```

**Note on route paths**: `/api/brackets/entries-from-event/{event_id}` has two path segments after `/api/brackets/`, while `/api/brackets/{id}` matches exactly one — so there is no real ambiguity between them; a request to `/api/brackets/entries-from-event/900` cannot match the single-segment `{id}` pattern at all. `entries_from_event` is still defined before `get_bracket` in the file purely for readability (grouping the read-only helper route near the other creation-adjacent logic), not because route order is load-bearing here.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_brackets_routes.py -v`
Expected: all 11 tests PASS.

- [ ] **Step 5: Run the full backend suite to check for regressions**

Run: `pytest`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/brackets.py dashboard/backend/tests/test_brackets_routes.py
git commit -m "feat: add bracket CRUD routes and event-entries preview endpoint"
```

---

### Task 4: Winner-setting route

**Files:**
- Modify: `dashboard/backend/routes/brackets.py` (add the route)
- Test: `dashboard/backend/tests/test_brackets_routes.py`

**Interfaces:**
- Consumes: `brackets.set_winner` from Task 2, `serialize_bracket_detail` from Task 3 (same file).
- Produces: `POST /api/brackets/{id}/matches/{round_index}/{match_index}/winner`.

- [ ] **Step 1: Write the failing tests**

Add to the end of `dashboard/backend/tests/test_brackets_routes.py`:

```python
@pytest.mark.asyncio
async def test_set_match_winner_advances_entry(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B", "C", "D"], None, 10)
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(f"/api/brackets/{bracket['id']}/matches/0/0/winner", json={"winner": "a"})
    assert resp.status == 200
    body = await resp.json()
    assert body["rounds"][0][0]["winner"] == "a"
    assert body["rounds"][1][0]["slot_a"] == "A"


@pytest.mark.asyncio
async def test_set_match_winner_rejects_invalid_winner_value(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B", "C", "D"], None, 10)
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(f"/api/brackets/{bracket['id']}/matches/0/0/winner", json={"winner": "c"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_set_match_winner_rejects_a_match_that_is_not_ready(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B", "C", "D"], None, 10)
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    # Round 1, match 0 (0-1) has not been decided yet, so round 2 match 0 is not ready.
    resp = await client.post(f"/api/brackets/{bracket['id']}/matches/1/0/winner", json={"winner": "a"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "match_not_ready"


@pytest.mark.asyncio
async def test_set_match_winner_404_when_bracket_missing(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/brackets/does-not-exist/matches/0/0/winner", json={"winner": "a"})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_set_match_winner_404_for_out_of_range_indices(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B", "C", "D"], None, 10)
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(f"/api/brackets/{bracket['id']}/matches/5/0/winner", json={"winner": "a"})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_set_match_winner_requires_auth(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B", "C", "D"], None, 10)
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)

    resp = await client.post(f"/api/brackets/{bracket['id']}/matches/0/0/winner", json={"winner": "a"})
    assert resp.status == 401
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_brackets_routes.py -v -k "winner"`
Expected: FAIL — 404s across the board (route doesn't exist yet).

- [ ] **Step 3: Implement the route**

Add to the end of `dashboard/backend/routes/brackets.py`:

```python
@routes.post("/api/brackets/{id}/matches/{round_index}/{match_index}/winner")
@require_dashboard_access
async def set_match_winner(request: web.Request) -> web.Response:
    data = brackets.load_brackets()
    bracket = data.get(request.match_info["id"])
    if bracket is None:
        return web.json_response({"error": "bracket_not_found"}, status=404)

    try:
        round_index = int(request.match_info["round_index"])
        match_index = int(request.match_info["match_index"])
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    winner = body.get("winner")
    if winner not in ("a", "b"):
        return web.json_response({"error": "invalid_request"}, status=400)

    rounds = bracket.get("rounds", [])
    if round_index < 0 or round_index >= len(rounds):
        return web.json_response({"error": "match_not_found"}, status=404)
    if match_index < 0 or match_index >= len(rounds[round_index]):
        return web.json_response({"error": "match_not_found"}, status=404)

    match = rounds[round_index][match_index]
    if match["slot_a"] is None or match["slot_b"] is None:
        return web.json_response({"error": "match_not_ready"}, status=400)

    brackets.set_winner(bracket, round_index, match_index, winner)
    brackets.save_brackets(data)
    return web.json_response(serialize_bracket_detail(bracket))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_brackets_routes.py -v`
Expected: all 17 tests PASS (11 from Task 3 + 6 new).

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/routes/brackets.py dashboard/backend/tests/test_brackets_routes.py
git commit -m "feat: add the bracket match-winner route"
```

---

### Task 5: Share on/off and the public route

**Files:**
- Modify: `dashboard/backend/routes/brackets.py` (add the three routes)
- Test: `dashboard/backend/tests/test_brackets_routes.py`

**Interfaces:**
- Consumes: `serialize_bracket_detail` from Task 3 (same file).
- Produces: `POST /api/brackets/{id}/share`, `DELETE /api/brackets/{id}/share`, `GET /api/public/brackets/{token}` (this last one has NO `@require_dashboard_access`).

- [ ] **Step 1: Write the failing tests**

Add to the end of `dashboard/backend/tests/test_brackets_routes.py`:

```python
@pytest.mark.asyncio
async def test_enable_share_generates_a_token(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B"], None, 10)
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(f"/api/brackets/{bracket['id']}/share")
    assert resp.status == 200
    token = (await resp.json())["share_token"]
    assert token
    assert brackets.load_brackets()[bracket["id"]]["share_token"] == token


@pytest.mark.asyncio
async def test_disable_share_clears_the_token(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B"], None, 10)
    bracket["share_token"] = "existing-token"
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete(f"/api/brackets/{bracket['id']}/share")
    assert resp.status == 200
    assert brackets.load_brackets()[bracket["id"]]["share_token"] is None


@pytest.mark.asyncio
async def test_public_bracket_returns_data_with_no_auth(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B"], None, 10)
    bracket["share_token"] = "my-token"
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    # deliberately no force_login call

    resp = await client.get("/api/public/brackets/my-token")
    assert resp.status == 200
    assert (await resp.json())["title"] == "T1"


@pytest.mark.asyncio
async def test_public_bracket_404s_on_unknown_token(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)

    resp = await client.get("/api/public/brackets/no-such-token")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_public_bracket_404s_after_share_disabled(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B"], None, 10)
    bracket["share_token"] = "my-token"
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.delete(f"/api/brackets/{bracket['id']}/share")
    resp = await client.get("/api/public/brackets/my-token")
    assert resp.status == 404
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest dashboard/backend/tests/test_brackets_routes.py -v -k "share or public_bracket"`
Expected: FAIL — 404s (routes don't exist yet).

- [ ] **Step 3: Implement the routes**

Add `import secrets` to the top of `dashboard/backend/routes/brackets.py` (alongside the existing `from aiohttp import web` import), then add these three routes at the end of the file:

```python
@routes.post("/api/brackets/{id}/share")
@require_dashboard_access
async def enable_share(request: web.Request) -> web.Response:
    data = brackets.load_brackets()
    bracket = data.get(request.match_info["id"])
    if bracket is None:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    token = secrets.token_urlsafe(32)
    bracket["share_token"] = token
    brackets.save_brackets(data)
    return web.json_response({"share_token": token})


@routes.delete("/api/brackets/{id}/share")
@require_dashboard_access
async def disable_share(request: web.Request) -> web.Response:
    data = brackets.load_brackets()
    bracket = data.get(request.match_info["id"])
    if bracket is None:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    bracket["share_token"] = None
    brackets.save_brackets(data)
    return web.json_response({"ok": True})


@routes.get("/api/public/brackets/{token}")
async def get_public_bracket(request: web.Request) -> web.Response:
    data = brackets.load_brackets()
    token = request.match_info["token"]
    bracket = next((b for b in data.values() if b.get("share_token") == token), None)
    if bracket is None:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    return web.json_response(serialize_bracket_detail(bracket))
```

Note `get_public_bracket` deliberately has NO `@require_dashboard_access` decorator — this is the one intentionally public route in the whole dashboard backend.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest dashboard/backend/tests/test_brackets_routes.py -v`
Expected: all 22 tests PASS (17 from Task 4 + 5 new).

- [ ] **Step 5: Run the full backend suite to check for regressions**

Run: `pytest`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/routes/brackets.py dashboard/backend/tests/test_brackets_routes.py
git commit -m "feat: add bracket share-link on/off and the public read-only route"
```

---

### Task 6: Frontend API client

**Files:**
- Modify: `dashboard/frontend/src/api/client.ts`
- Test: `dashboard/frontend/src/api/brackets.test.ts` (new)

**Interfaces:**
- Consumes: the routes from Tasks 3-5 (`/api/brackets`, `/api/brackets/{id}`, `/api/brackets/entries-from-event/{event_id}`, `/api/brackets/{id}/matches/{round}/{match}/winner`, `/api/brackets/{id}/share`, `/api/public/brackets/{token}`).
- Produces: `BracketSummary`, `BracketMatch`, `BracketDetail` types; `fetchBrackets`, `fetchBracketDetail`, `fetchEventEntries`, `createBracket`, `deleteBracket`, `setBracketMatchWinner`, `enableBracketShare`, `disableBracketShare`, `fetchPublicBracket` functions. Tasks 7-9 (all frontend pages) consume these.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/frontend/src/api/brackets.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createBracket,
  deleteBracket,
  disableBracketShare,
  enableBracketShare,
  fetchBrackets,
  fetchBracketDetail,
  fetchEventEntries,
  fetchPublicBracket,
  setBracketMatchWinner,
} from './client'

const okJson = (payload: unknown) => ({ ok: true, status: 200, json: async () => payload })

describe('brackets api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchBrackets unwraps the brackets array', async () => {
    const brackets = [{ id: '1', title: 'T1', source_event_id: null, entry_count: 4, created_at: '2026-07-04' }]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(okJson({ brackets })))
    const result = await fetchBrackets()
    expect(result).toEqual(brackets)
  })

  it('fetchBracketDetail calls the detail endpoint', async () => {
    const detail = { id: '1', title: 'T1', source_event_id: null, entries: ['A', 'B'], rounds: [], share_token: null }
    const fetchMock = vi.fn().mockResolvedValue(okJson(detail))
    vi.stubGlobal('fetch', fetchMock)
    const result = await fetchBracketDetail('1')
    expect(result).toEqual(detail)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/brackets/1')
  })

  it('fetchEventEntries calls the preview endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ entries: ['Alpha', 'Beta'] }))
    vi.stubGlobal('fetch', fetchMock)
    const result = await fetchEventEntries('900')
    expect(result).toEqual(['Alpha', 'Beta'])
    expect(fetchMock.mock.calls[0][0]).toBe('/api/brackets/entries-from-event/900')
  })

  it('createBracket POSTs title, entries, and source_event_id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okJson({ id: '1', title: 'T1', source_event_id: null, entries: ['A', 'B'], rounds: [], share_token: null }),
    )
    vi.stubGlobal('fetch', fetchMock)
    await createBracket('T1', ['A', 'B'], null)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/brackets',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ title: 'T1', entries: ['A', 'B'], source_event_id: null }),
      }),
    )
  })

  it('deleteBracket DELETEs the bracket', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    await deleteBracket('1')
    expect(fetchMock).toHaveBeenCalledWith('/api/brackets/1', expect.objectContaining({ method: 'DELETE' }))
  })

  it('setBracketMatchWinner POSTs the winner', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      okJson({ id: '1', title: 'T1', source_event_id: null, entries: [], rounds: [], share_token: null }),
    )
    vi.stubGlobal('fetch', fetchMock)
    await setBracketMatchWinner('1', 0, 2, 'a')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/brackets/1/matches/0/2/winner',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ winner: 'a' }) }),
    )
  })

  it('enableBracketShare returns the token', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(okJson({ share_token: 'abc' })))
    const token = await enableBracketShare('1')
    expect(token).toBe('abc')
  })

  it('disableBracketShare DELETEs the share endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    await disableBracketShare('1')
    expect(fetchMock).toHaveBeenCalledWith('/api/brackets/1/share', expect.objectContaining({ method: 'DELETE' }))
  })

  it('fetchPublicBracket calls the public endpoint', async () => {
    const detail = { id: '1', title: 'T1', source_event_id: null, entries: [], rounds: [], share_token: 'abc' }
    const fetchMock = vi.fn().mockResolvedValue(okJson(detail))
    vi.stubGlobal('fetch', fetchMock)
    const result = await fetchPublicBracket('abc')
    expect(result).toEqual(detail)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/public/brackets/abc')
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `dashboard/frontend`): `npx vitest run src/api/brackets.test.ts`
Expected: FAIL — none of these functions are exported from `./client` yet.

- [ ] **Step 3: Add the types and functions to `client.ts`**

Add to the end of `dashboard/frontend/src/api/client.ts`:

```typescript
export interface BracketMatch {
  slot_a: string | null
  slot_b: string | null
  winner: 'a' | 'b' | null
}

export interface BracketSummary {
  id: string
  title: string
  source_event_id: string | null
  entry_count: number
  created_at: string
}

export interface BracketDetail {
  id: string
  title: string
  source_event_id: string | null
  entries: string[]
  rounds: BracketMatch[][]
  share_token: string | null
}

export async function fetchBrackets(): Promise<BracketSummary[]> {
  const body = await apiFetch<{ brackets: BracketSummary[] }>('/api/brackets')
  return body.brackets
}

export function fetchBracketDetail(id: string): Promise<BracketDetail> {
  return apiFetch(`/api/brackets/${id}`)
}

export async function fetchEventEntries(eventId: string): Promise<string[]> {
  const body = await apiFetch<{ entries: string[] }>(`/api/brackets/entries-from-event/${eventId}`)
  return body.entries
}

export function createBracket(
  title: string,
  entries: string[],
  sourceEventId: string | null,
): Promise<BracketDetail> {
  return apiFetch('/api/brackets', jsonInit('POST', { title, entries, source_event_id: sourceEventId }))
}

export async function deleteBracket(id: string): Promise<void> {
  await apiFetch(`/api/brackets/${id}`, jsonInit('DELETE'))
}

export function setBracketMatchWinner(
  id: string,
  roundIndex: number,
  matchIndex: number,
  winner: 'a' | 'b',
): Promise<BracketDetail> {
  return apiFetch(`/api/brackets/${id}/matches/${roundIndex}/${matchIndex}/winner`, jsonInit('POST', { winner }))
}

export async function enableBracketShare(id: string): Promise<string> {
  const result = await apiFetch<{ share_token: string }>(`/api/brackets/${id}/share`, jsonInit('POST'))
  return result.share_token
}

export async function disableBracketShare(id: string): Promise<void> {
  await apiFetch(`/api/brackets/${id}/share`, jsonInit('DELETE'))
}

export function fetchPublicBracket(token: string): Promise<BracketDetail> {
  return apiFetch(`/api/public/brackets/${token}`)
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run (from `dashboard/frontend`): `npx vitest run src/api/brackets.test.ts`
Expected: all 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/api/client.ts dashboard/frontend/src/api/brackets.test.ts
git commit -m "feat: add bracket API client types and functions"
```

---

### Task 7: `Brackets.tsx` — list and create flow

**Files:**
- Create: `dashboard/frontend/src/pages/Brackets.tsx`
- Test: `dashboard/frontend/src/pages/Brackets.test.tsx`

**Interfaces:**
- Consumes: `fetchBrackets`, `createBracket`, `fetchEventEntries`, `fetchEvents` (existing, from Phase 5), `type BracketSummary`, `type EventSummary` from `client.ts`.
- Produces: `BracketsPage` component. Task 9 wires this into `App.tsx`/`DashboardShell.tsx`. No other task consumes exports from this file directly (navigation to a bracket's detail page happens via `react-router-dom`'s `useNavigate`, not a prop).

Note: no drag-and-drop library exists in this project (`dashboard/frontend/package.json` has no `dnd`/`sortable` dependency), and none is added here — reordering is done with per-row ↑/↓ move buttons instead of literal dragging. This achieves the approved "manual reorder before generating" requirement without a new dependency, and is far more reliable to test than simulating drag events.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/frontend/src/pages/Brackets.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { BracketsPage } from './Brackets'

describe('BracketsPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lists existing brackets', async () => {
    vi.spyOn(client, 'fetchBrackets').mockResolvedValue([
      { id: '1', title: 'Летний турнир', source_event_id: null, entry_count: 8, created_at: '2026-07-04T00:00:00Z' },
    ])
    render(<BracketsPage />)
    expect(await screen.findByText('Летний турнир')).toBeInTheDocument()
  })

  it('shows an empty state when there are no brackets', async () => {
    vi.spyOn(client, 'fetchBrackets').mockResolvedValue([])
    render(<BracketsPage />)
    expect(await screen.findByText('Сеток пока нет.')).toBeInTheDocument()
  })

  it('creates a bracket manually from typed names', async () => {
    vi.spyOn(client, 'fetchBrackets').mockResolvedValue([])
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createBracket').mockResolvedValue({
      id: '1',
      title: 'Manual',
      source_event_id: null,
      entries: ['X', 'Y'],
      rounds: [],
      share_token: null,
    })

    render(<BracketsPage />)
    fireEvent.click(await screen.findByText('Создать сетку'))
    fireEvent.click(screen.getByText('Вручную'))
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'Manual' } })
    fireEvent.change(screen.getByLabelText('Имена (по одному на строку)'), { target: { value: 'X\nY' } })
    fireEvent.click(screen.getByText('Далее'))
    fireEvent.click(screen.getByText('Сгенерировать'))

    await waitFor(() => expect(createSpy).toHaveBeenCalledWith('Manual', ['X', 'Y'], null))
  })

  it('loads entries from a selected event and allows reordering', async () => {
    vi.spyOn(client, 'fetchBrackets').mockResolvedValue([])
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([
      { message_id: '900', type: 'tournament', title: 'Кубок', status: 'closed', channel_id: '1', count: 2 },
    ])
    vi.spyOn(client, 'fetchEventEntries').mockResolvedValue(['Alpha', 'Beta'])
    const createSpy = vi.spyOn(client, 'createBracket').mockResolvedValue({
      id: '1',
      title: 'From Event',
      source_event_id: '900',
      entries: ['Beta', 'Alpha'],
      rounds: [],
      share_token: null,
    })

    render(<BracketsPage />)
    fireEvent.click(await screen.findByText('Создать сетку'))
    fireEvent.change(await screen.findByLabelText('Событие'), { target: { value: '900' } })
    await screen.findByText('Загружено участников: 2')
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'From Event' } })
    fireEvent.click(screen.getByText('Далее'))

    // The seed step (reached after "Далее") is what actually renders each entry's name.
    await screen.findByText('Alpha')

    // Move Beta above Alpha using the down-arrow on the first row.
    fireEvent.click(screen.getAllByLabelText('Переместить вниз')[0])

    fireEvent.click(screen.getByText('Сгенерировать'))
    await waitFor(() => expect(createSpy).toHaveBeenCalledWith('From Event', ['Beta', 'Alpha'], '900'))
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `dashboard/frontend`): `npx vitest run src/pages/Brackets.test.tsx`
Expected: FAIL — the module `./Brackets` doesn't exist yet.

- [ ] **Step 3: Implement `Brackets.tsx`**

Create `dashboard/frontend/src/pages/Brackets.tsx`:

```tsx
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  createBracket,
  fetchBrackets,
  fetchEventEntries,
  fetchEvents,
  type BracketSummary,
  type EventSummary,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'

type SourceTab = 'event' | 'manual'

function shuffle(items: string[]): string[] {
  const copy = [...items]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

export function BracketsPage() {
  const navigate = useNavigate()
  const [brackets, setBrackets] = useState<BracketSummary[]>([])
  const [events, setEvents] = useState<EventSummary[]>([])
  const [error, setError] = useState('')

  const [createOpen, setCreateOpen] = useState(false)
  const [tab, setTab] = useState<SourceTab>('event')
  const [selectedEventId, setSelectedEventId] = useState('')
  const [manualText, setManualText] = useState('')
  const [title, setTitle] = useState('')
  const [entries, setEntries] = useState<string[]>([])
  const [step, setStep] = useState<'source' | 'seed'>('source')
  const [createError, setCreateError] = useState('')
  const [createBusy, setCreateBusy] = useState(false)

  const reload = () => {
    fetchBrackets()
      .then(setBrackets)
      .catch(() => setError('Не удалось загрузить сетки'))
  }

  useEffect(reload, [])
  useEffect(() => {
    fetchEvents('open').then(setEvents).catch(() => {})
  }, [])

  const openCreate = () => {
    setTab('event')
    setSelectedEventId('')
    setManualText('')
    setTitle('')
    setEntries([])
    setStep('source')
    setCreateError('')
    setCreateOpen(true)
  }

  const loadEventEntries = async (eventId: string) => {
    setSelectedEventId(eventId)
    if (!eventId) {
      setEntries([])
      return
    }
    try {
      const loaded = await fetchEventEntries(eventId)
      setEntries(loaded)
    } catch {
      setCreateError('Не удалось загрузить участников события')
    }
  }

  const goToSeedStep = () => {
    if (tab === 'manual') {
      const lines = manualText
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)
      setEntries(lines)
    }
    setStep('seed')
  }

  const moveEntry = (index: number, direction: -1 | 1) => {
    setEntries((prev) => {
      const target = index + direction
      if (target < 0 || target >= prev.length) return prev
      const copy = [...prev]
      ;[copy[index], copy[target]] = [copy[target], copy[index]]
      return copy
    })
  }

  const save = async () => {
    setCreateBusy(true)
    setCreateError('')
    try {
      await createBracket(title, entries, tab === 'event' ? selectedEventId || null : null)
      setCreateOpen(false)
      reload()
    } catch {
      setCreateError('Не удалось создать сетку')
    } finally {
      setCreateBusy(false)
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <h1 className="text-lg font-semibold text-foreground">Сетки</h1>
        <Button variant="primary" onClick={openCreate} className="ml-auto">
          Создать сетку
        </Button>
      </div>

      {error && <p className="mb-4 text-sm text-danger">{error}</p>}

      <div className="flex flex-col gap-2">
        {brackets.map((b) => (
          <Card key={b.id} interactive className="!p-3" onClick={() => navigate(`/brackets/${b.id}`)}>
            <p className="text-sm text-foreground">{b.title}</p>
            <p className="text-xs text-muted">{b.entry_count} участников</p>
          </Card>
        ))}
        {brackets.length === 0 && <p className="text-sm text-muted">Сеток пока нет.</p>}
      </div>

      <Modal open={createOpen} title="Создать сетку" onClose={() => setCreateOpen(false)}>
        {step === 'source' ? (
          <div className="flex flex-col gap-3">
            <div className="flex gap-2">
              <Button variant={tab === 'event' ? 'primary' : 'secondary'} onClick={() => setTab('event')}>
                Из ивента
              </Button>
              <Button variant={tab === 'manual' ? 'primary' : 'secondary'} onClick={() => setTab('manual')}>
                Вручную
              </Button>
            </div>

            {tab === 'event' ? (
              <>
                <label className="text-sm text-muted" htmlFor="bracket-event">
                  Событие
                </label>
                <select
                  id="bracket-event"
                  value={selectedEventId}
                  onChange={(e) => loadEventEntries(e.target.value)}
                  className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
                >
                  <option value="">Выберите событие…</option>
                  {events
                    .filter((ev) => ev.type === 'tournament')
                    .map((ev) => (
                      <option key={ev.message_id} value={ev.message_id}>
                        {ev.title}
                      </option>
                    ))}
                </select>
                {entries.length > 0 && (
                  <p className="text-xs text-muted">Загружено участников: {entries.length}</p>
                )}
              </>
            ) : (
              <>
                <label className="text-sm text-muted" htmlFor="bracket-manual-names">
                  Имена (по одному на строку)
                </label>
                <textarea
                  id="bracket-manual-names"
                  value={manualText}
                  onChange={(e) => setManualText(e.target.value)}
                  rows={6}
                  className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                />
              </>
            )}

            <label className="text-sm text-muted" htmlFor="bracket-title">
              Название
            </label>
            <input
              id="bracket-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            />

            {createError && <p className="text-sm text-danger">{createError}</p>}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={() => setCreateOpen(false)}>
                Отмена
              </Button>
              <Button variant="primary" onClick={goToSeedStep}>
                Далее
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted">Порядок посева</p>
              <Button variant="secondary" onClick={() => setEntries((prev) => shuffle(prev))}>
                Перемешать
              </Button>
            </div>

            <ul className="flex flex-col gap-1">
              {entries.map((entry, index) => (
                <li
                  key={`${entry}-${index}`}
                  className="flex items-center justify-between rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
                >
                  <span>{entry}</span>
                  <span className="flex gap-1">
                    <button
                      type="button"
                      aria-label="Переместить вверх"
                      onClick={() => moveEntry(index, -1)}
                      className="cursor-pointer text-muted hover:text-foreground"
                    >
                      ↑
                    </button>
                    <button
                      type="button"
                      aria-label="Переместить вниз"
                      onClick={() => moveEntry(index, 1)}
                      className="cursor-pointer text-muted hover:text-foreground"
                    >
                      ↓
                    </button>
                  </span>
                </li>
              ))}
            </ul>

            {createError && <p className="text-sm text-danger">{createError}</p>}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={() => setStep('source')} disabled={createBusy}>
                Назад
              </Button>
              <Button variant="primary" onClick={save} disabled={createBusy || entries.length < 2}>
                {createBusy ? 'Создаём…' : 'Сгенерировать'}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run (from `dashboard/frontend`): `npx vitest run src/pages/Brackets.test.tsx`
Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/pages/Brackets.tsx dashboard/frontend/src/pages/Brackets.test.tsx
git commit -m "feat: add Brackets page with event-linked and manual creation"
```

---

### Task 8: `BracketDetail.tsx` — the interactive grid

**Files:**
- Create: `dashboard/frontend/src/pages/BracketDetail.tsx`
- Test: `dashboard/frontend/src/pages/BracketDetail.test.tsx`

**Interfaces:**
- Consumes: `fetchBracketDetail`, `setBracketMatchWinner`, `enableBracketShare`, `disableBracketShare`, `deleteBracket`, `type BracketDetail as BracketDetailType` from `client.ts`.
- Produces: `BracketDetailPage` component. Task 9 wires this into `App.tsx` at `/brackets/:id`.

Note on visual scope: rounds are rendered as side-by-side columns of bordered match boxes, without literal SVG connector lines between boxes — this keeps the implementation and its tests straightforward while still fully supporting the click-to-advance interaction, which is the functional core of this task.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/frontend/src/pages/BracketDetail.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import * as client from '../api/client'
import { BracketDetailPage } from './BracketDetail'

function renderAt(id: string) {
  return render(
    <MemoryRouter initialEntries={[`/brackets/${id}`]}>
      <Routes>
        <Route path="/brackets/:id" element={<BracketDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

const baseBracket: client.BracketDetail = {
  id: '1',
  title: 'Летний турнир',
  source_event_id: null,
  entries: ['A', 'B', 'C', 'D'],
  rounds: [
    [
      { slot_a: 'A', slot_b: 'B', winner: null },
      { slot_a: 'C', slot_b: 'D', winner: null },
    ],
    [{ slot_a: null, slot_b: null, winner: null }],
  ],
  share_token: null,
}

describe('BracketDetailPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the bracket title and matches', async () => {
    vi.spyOn(client, 'fetchBracketDetail').mockResolvedValue(baseBracket)
    renderAt('1')
    expect(await screen.findByText('Летний турнир')).toBeInTheDocument()
    expect(screen.getByText('A')).toBeInTheDocument()
    expect(screen.getByText('D')).toBeInTheDocument()
  })

  it('clicking a slot sets the winner and refreshes the bracket', async () => {
    vi.spyOn(client, 'fetchBracketDetail').mockResolvedValue(baseBracket)
    const winnerSpy = vi.spyOn(client, 'setBracketMatchWinner').mockResolvedValue({
      ...baseBracket,
      rounds: [
        [
          { slot_a: 'A', slot_b: 'B', winner: 'a' },
          { slot_a: 'C', slot_b: 'D', winner: null },
        ],
        [{ slot_a: 'A', slot_b: null, winner: null }],
      ],
    })

    renderAt('1')
    fireEvent.click(await screen.findByText('A'))
    await waitFor(() => expect(winnerSpy).toHaveBeenCalledWith('1', 0, 0, 'a'))
  })

  it('does not render a click handler for a match with a pending slot', async () => {
    vi.spyOn(client, 'fetchBracketDetail').mockResolvedValue(baseBracket)
    renderAt('1')
    await screen.findByText('Летний турнир')
    // The final round has both slots null (pending) — there is nothing clickable there yet.
    const pendingSlots = screen.getAllByText('—')
    expect(pendingSlots).toHaveLength(2)
    for (const slot of pendingSlots) {
      expect(slot.closest('button')).toBeDisabled()
    }
  })

  it('enables sharing and shows the public link', async () => {
    vi.spyOn(client, 'fetchBracketDetail').mockResolvedValue(baseBracket)
    vi.spyOn(client, 'enableBracketShare').mockResolvedValue('my-token')

    renderAt('1')
    fireEvent.click(await screen.findByText('Поделиться ссылкой'))
    expect(await screen.findByText(/my-token/)).toBeInTheDocument()
  })

  it('deletes the bracket after confirmation', async () => {
    vi.spyOn(client, 'fetchBracketDetail').mockResolvedValue(baseBracket)
    const deleteSpy = vi.spyOn(client, 'deleteBracket').mockResolvedValue()

    renderAt('1')
    fireEvent.click(await screen.findByText('Удалить'))
    fireEvent.click(screen.getByText('Подтвердить'))
    await waitFor(() => expect(deleteSpy).toHaveBeenCalledWith('1'))
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `dashboard/frontend`): `npx vitest run src/pages/BracketDetail.test.tsx`
Expected: FAIL — the module `./BracketDetail` doesn't exist yet.

- [ ] **Step 3: Implement `BracketDetail.tsx`**

Create `dashboard/frontend/src/pages/BracketDetail.tsx`:

```tsx
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  deleteBracket,
  disableBracketShare,
  enableBracketShare,
  fetchBracketDetail,
  setBracketMatchWinner,
  type BracketDetail,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'

export function BracketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [bracket, setBracket] = useState<BracketDetail | null>(null)
  const [error, setError] = useState('')
  const [shareBusy, setShareBusy] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deleteBusy, setDeleteBusy] = useState(false)

  const reload = () => {
    if (!id) return
    fetchBracketDetail(id)
      .then((b) => {
        setBracket(b)
        setError('')
      })
      .catch(() => setError('Не удалось загрузить сетку'))
  }

  useEffect(reload, [id])

  const pickWinner = async (roundIndex: number, matchIndex: number, winner: 'a' | 'b') => {
    if (!id) return
    try {
      const updated = await setBracketMatchWinner(id, roundIndex, matchIndex, winner)
      setBracket(updated)
    } catch {
      setError('Не удалось сохранить результат')
    }
  }

  const toggleShare = async () => {
    if (!id || !bracket) return
    setShareBusy(true)
    try {
      if (bracket.share_token) {
        await disableBracketShare(id)
        setBracket({ ...bracket, share_token: null })
      } else {
        const token = await enableBracketShare(id)
        setBracket({ ...bracket, share_token: token })
      }
    } catch {
      setError('Не удалось изменить доступ к ссылке')
    } finally {
      setShareBusy(false)
    }
  }

  const confirmDelete = async () => {
    if (!id) return
    setDeleteBusy(true)
    try {
      await deleteBracket(id)
      navigate('/brackets')
    } catch {
      setError('Не удалось удалить сетку')
      setDeleteBusy(false)
    }
  }

  if (!bracket) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  const shareUrl = bracket.share_token ? `${window.location.origin}/bracket/${bracket.share_token}` : null

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <h1 className="text-lg font-semibold text-foreground">{bracket.title}</h1>
        <Button variant="secondary" onClick={toggleShare} disabled={shareBusy} className="ml-auto">
          {bracket.share_token ? 'Отключить ссылку' : 'Поделиться ссылкой'}
        </Button>
        <Button variant="danger" onClick={() => setConfirmingDelete(true)}>
          Удалить
        </Button>
      </div>

      {shareUrl && (
        <p className="mb-4 text-sm text-muted">
          Публичная ссылка: <span className="text-foreground">{shareUrl}</span>
        </p>
      )}

      {error && <p className="mb-4 text-sm text-danger">{error}</p>}

      <div className="flex gap-6 overflow-x-auto">
        {bracket.rounds.map((round, roundIndex) => (
          <div key={roundIndex} className="flex flex-col justify-around gap-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted">
              {roundIndex === bracket.rounds.length - 1 ? 'Финал' : `Раунд ${roundIndex + 1}`}
            </p>
            {round.map((match, matchIndex) => {
              const ready = match.slot_a !== null && match.slot_b !== null
              return (
                <Card key={matchIndex} className="!p-2 w-48">
                  <button
                    type="button"
                    disabled={!ready}
                    onClick={() => ready && pickWinner(roundIndex, matchIndex, 'a')}
                    className={`block w-full rounded-control px-2 py-1 text-left text-sm ${
                      match.winner === 'a' ? 'font-semibold text-foreground' : 'text-muted'
                    } ${ready ? 'cursor-pointer hover:bg-surface-hover' : ''}`}
                  >
                    {match.slot_a ?? '—'}
                  </button>
                  <button
                    type="button"
                    disabled={!ready}
                    onClick={() => ready && pickWinner(roundIndex, matchIndex, 'b')}
                    className={`block w-full rounded-control px-2 py-1 text-left text-sm ${
                      match.winner === 'b' ? 'font-semibold text-foreground' : 'text-muted'
                    } ${ready ? 'cursor-pointer hover:bg-surface-hover' : ''}`}
                  >
                    {match.slot_b ?? '—'}
                  </button>
                </Card>
              )
            })}
          </div>
        ))}
      </div>

      <Modal open={confirmingDelete} title="Удалить сетку?" onClose={() => setConfirmingDelete(false)}>
        <p className="mb-4 text-sm text-muted">Это действие необратимо.</p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setConfirmingDelete(false)} disabled={deleteBusy}>
            Отмена
          </Button>
          <Button variant="danger" onClick={confirmDelete} disabled={deleteBusy}>
            {deleteBusy ? 'Удаляем…' : 'Подтвердить'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run (from `dashboard/frontend`): `npx vitest run src/pages/BracketDetail.test.tsx`
Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add dashboard/frontend/src/pages/BracketDetail.tsx dashboard/frontend/src/pages/BracketDetail.test.tsx
git commit -m "feat: add interactive bracket detail page with share and delete"
```

---

### Task 9: Public page, routing, and navigation

**Files:**
- Create: `dashboard/frontend/src/pages/PublicBracket.tsx`
- Test: `dashboard/frontend/src/pages/PublicBracket.test.tsx`
- Modify: `dashboard/frontend/src/App.tsx`
- Modify: `dashboard/frontend/src/pages/DashboardShell.tsx`

**Interfaces:**
- Consumes: `fetchPublicBracket`, `type BracketDetail` from `client.ts`; `BracketsPage` from Task 7; `BracketDetailPage` from Task 8.

- [ ] **Step 1: Write the failing tests for the public page**

Create `dashboard/frontend/src/pages/PublicBracket.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import * as client from '../api/client'
import { PublicBracketPage } from './PublicBracket'

const baseBracket: client.BracketDetail = {
  id: '1',
  title: 'Летний турнир',
  source_event_id: null,
  entries: ['A', 'B'],
  rounds: [[{ slot_a: 'A', slot_b: 'B', winner: 'a' }]],
  share_token: 'my-token',
}

function renderAt(token: string) {
  return render(
    <MemoryRouter initialEntries={[`/bracket/${token}`]}>
      <Routes>
        <Route path="/bracket/:token" element={<PublicBracketPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('PublicBracketPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the bracket read-only, with no click handlers', async () => {
    vi.spyOn(client, 'fetchPublicBracket').mockResolvedValue(baseBracket)
    renderAt('my-token')

    expect(await screen.findByText('Летний турнир')).toBeInTheDocument()
    const slotA = screen.getByText('A')
    expect(slotA.closest('button')).toBeNull()
    expect(screen.queryByText('Поделиться ссылкой')).not.toBeInTheDocument()
    expect(screen.queryByText('Удалить')).not.toBeInTheDocument()
  })

  it('shows an error state for an invalid token', async () => {
    vi.spyOn(client, 'fetchPublicBracket').mockRejectedValue(new Error('not found'))
    renderAt('bad-token')
    expect(await screen.findByText('Сетка не найдена.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `dashboard/frontend`): `npx vitest run src/pages/PublicBracket.test.tsx`
Expected: FAIL — the module `./PublicBracket` doesn't exist yet.

- [ ] **Step 3: Implement `PublicBracket.tsx`**

Create `dashboard/frontend/src/pages/PublicBracket.tsx`:

```tsx
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { fetchPublicBracket, type BracketDetail } from '../api/client'

export function PublicBracketPage() {
  const { token } = useParams<{ token: string }>()
  const [bracket, setBracket] = useState<BracketDetail | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    fetchPublicBracket(token)
      .then(setBracket)
      .catch(() => setError('Сетка не найдена.'))
  }, [token])

  if (error) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <p className="text-sm text-danger">{error}</p>
      </div>
    )
  }

  if (!bracket) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <p className="text-sm text-muted">Загрузка…</p>
      </div>
    )
  }

  return (
    <div className="min-h-dvh bg-background p-6">
      <h1 className="mb-6 text-lg font-semibold text-foreground">{bracket.title}</h1>
      <div className="flex gap-6 overflow-x-auto">
        {bracket.rounds.map((round, roundIndex) => (
          <div key={roundIndex} className="flex flex-col justify-around gap-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted">
              {roundIndex === bracket.rounds.length - 1 ? 'Финал' : `Раунд ${roundIndex + 1}`}
            </p>
            {round.map((match, matchIndex) => (
              <div
                key={matchIndex}
                className="w-48 rounded-card border border-border bg-surface p-2 shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset]"
              >
                <p className={`px-2 py-1 text-sm ${match.winner === 'a' ? 'font-semibold text-foreground' : 'text-muted'}`}>
                  {match.slot_a ?? '—'}
                </p>
                <p className={`px-2 py-1 text-sm ${match.winner === 'b' ? 'font-semibold text-foreground' : 'text-muted'}`}>
                  {match.slot_b ?? '—'}
                </p>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run (from `dashboard/frontend`): `npx vitest run src/pages/PublicBracket.test.tsx`
Expected: both tests PASS.

- [ ] **Step 5: Wire routes into `App.tsx`**

In `dashboard/frontend/src/App.tsx`, change the imports (add three new lines after the existing `ConfigPage` import):

```tsx
import { ConfigPage } from './pages/Config'
```

to:

```tsx
import { ConfigPage } from './pages/Config'
import { BracketsPage } from './pages/Brackets'
import { BracketDetailPage } from './pages/BracketDetail'
import { PublicBracketPage } from './pages/PublicBracket'
```

Then change the `<Routes>` block from:

```tsx
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/access-denied" element={<AccessDeniedPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardShell />
              </ProtectedRoute>
            }
          >
            <Route index element={<HomePage />} />
            <Route path="members" element={<MembersPage />} />
            <Route path="lockdown" element={<LockdownPage />} />
            <Route path="reaction-roles" element={<MessageBuilderPage />} />
            <Route path="feedback" element={<FeedbackPage />} />
            <Route path="events" element={<EventsPage />} />
            <Route path="config" element={<ConfigPage />} />
          </Route>
        </Routes>
```

to:

```tsx
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/access-denied" element={<AccessDeniedPage />} />
          <Route path="/bracket/:token" element={<PublicBracketPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardShell />
              </ProtectedRoute>
            }
          >
            <Route index element={<HomePage />} />
            <Route path="members" element={<MembersPage />} />
            <Route path="lockdown" element={<LockdownPage />} />
            <Route path="reaction-roles" element={<MessageBuilderPage />} />
            <Route path="feedback" element={<FeedbackPage />} />
            <Route path="events" element={<EventsPage />} />
            <Route path="brackets" element={<BracketsPage />} />
            <Route path="brackets/:id" element={<BracketDetailPage />} />
            <Route path="config" element={<ConfigPage />} />
          </Route>
        </Routes>
```

Note `/bracket/:token` (public, singular "bracket") is registered as a top-level sibling of `/login`, OUTSIDE `ProtectedRoute`/`DashboardShell` — it must never require a login redirect. `/brackets` and `/brackets/:id` (plural "brackets", the authenticated list and detail pages) are nested inside `ProtectedRoute` alongside every other dashboard page.

- [ ] **Step 6: Add the nav entry to `DashboardShell.tsx`**

In `dashboard/frontend/src/pages/DashboardShell.tsx`, change the icon import (line 1-11):

```tsx
import {
  CalendarCheck,
  ChatCircleText,
  GearSix,
  ShieldWarning,
  SignOut,
  Sparkle,
  Stack,
  UsersThree,
  type Icon,
} from '@phosphor-icons/react'
```

to:

```tsx
import {
  CalendarCheck,
  ChatCircleText,
  GearSix,
  ShieldWarning,
  SignOut,
  Sparkle,
  Stack,
  Trophy,
  UsersThree,
  type Icon,
} from '@phosphor-icons/react'
```

Then change the `SECTIONS` array to add a new entry after `'События и голосования'`:

```tsx
const SECTIONS: Section[] = [
  { label: 'Feedback и тикеты', icon: ChatCircleText, to: '/feedback' },
  { label: 'Конструктор кнопок и эмбедов', icon: Stack, to: '/reaction-roles' },
  { label: 'События и голосования', icon: CalendarCheck, to: '/events' },
  { label: 'Lockdown и модерация', icon: ShieldWarning, to: '/lockdown' },
  { label: 'Участники и роли', icon: UsersThree, to: '/members' },
  { label: 'Конфигурация', icon: GearSix, to: '/config' },
]
```

to:

```tsx
const SECTIONS: Section[] = [
  { label: 'Feedback и тикеты', icon: ChatCircleText, to: '/feedback' },
  { label: 'Конструктор кнопок и эмбедов', icon: Stack, to: '/reaction-roles' },
  { label: 'События и голосования', icon: CalendarCheck, to: '/events' },
  { label: 'Сетки', icon: Trophy, to: '/brackets' },
  { label: 'Lockdown и модерация', icon: ShieldWarning, to: '/lockdown' },
  { label: 'Участники и роли', icon: UsersThree, to: '/members' },
  { label: 'Конфигурация', icon: GearSix, to: '/config' },
]
```

- [ ] **Step 7: Run the full frontend suite to check for regressions**

Run (from `dashboard/frontend`): `npx vitest run`
Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add dashboard/frontend/src/pages/PublicBracket.tsx dashboard/frontend/src/pages/PublicBracket.test.tsx dashboard/frontend/src/App.tsx dashboard/frontend/src/pages/DashboardShell.tsx
git commit -m "feat: wire up bracket routes, public page, and nav entry"
```

---

## Final Verification

After all nine tasks are complete:

- [ ] Run the full backend suite: `pytest` (from the repo root) — all tests pass.
- [ ] Run the full frontend suite: `npx vitest run` (from `dashboard/frontend`) — all tests pass.
- [ ] Manually verify in the browser (dev servers restarted): create a bracket from a real closed tournament event, shuffle/reorder the seeding, generate it, click through a few rounds of winners (including correcting a pick to confirm downstream picks clear), enable sharing, open the public link in an incognito/logged-out browser window and confirm it renders read-only, then disable sharing and confirm the old link now 404s.
