# Dashboard: Tournament Bracket Generator — Design

## Context

Replicates the core functionality of lvup.gg's "easy" single-elimination bracket tool (https://lvup.gg/ru/easy/bracket), integrated with this dashboard's existing tournament-event system (Phase 5: `events.py`/`events_core.py`, `dashboard/backend/routes/events.py`, `dashboard/frontend/src/pages/Events.tsx`). Two ways to start a bracket — auto-populated from an existing tournament event's registered participants/teams, or built from scratch by typing names — plus a public, unauthenticated, read-only share link so a bracket can be watched by anyone without a dashboard account.

Scope is deliberately single-elimination only (matching the linked tool). Double-elimination, round-robin, or group stages are out of scope and would be a separate future feature.

## Data model & storage

A new root module `brackets.py`, following the project's established no-cache JSON pattern (same as `events_core.py`/`moderation_log.py`): every read/write goes straight to `brackets_data.json` on disk, no in-memory cache. No discord.py cog is needed — brackets never post to or read from Discord; this is a dashboard-only feature that happens to optionally read from `events_data.json` at creation time.

A bracket is a **snapshot**, not a live link to its source event: participant/team names are copied in at creation time and never retroactively updated if the source event's registrations change afterward. Per the approved scope, a bracket can be generated from a tournament event in any status (open or closed) — whatever has registered "as of right now."

```json
{
  "id": "<uuid4>",
  "title": "...",
  "source_event_id": "<message_id>" | null,
  "entries": ["Team A", "Team B", "Team C", null],
  "rounds": [
    [ {"slot_a": "Team A", "slot_b": "Team B", "winner": null}, {"slot_a": "Team C", "slot_b": null, "winner": "a"} ],
    [ {"slot_a": null, "slot_b": "Team C", "winner": null} ]
  ],
  "created_by": "<moderator_id>",
  "created_at": "<ISO-8601 UTC>",
  "share_token": "<random-token>" | null
}
```

- `entries` is the final, organizer-approved seeding order (after shuffle/manual reorder), padded with `null` ("bye") entries appended to the END of the list up to the next power of two (e.g. 5 real entries → 3 `null`s appended → 8 slots total). A bracket requires at least 2 entries; creation is rejected below that.
- `rounds` is an array of rounds; each round is an array of match objects (`slot_a`, `slot_b`, `winner`: `"a"` | `"b"` | `null`). Round 1 is built directly from `entries` via sequential adjacent pairing (`entries[0]` vs `entries[1]`, `entries[2]` vs `entries[3]`, ...) — no traditional seeding-chart placement, since the organizer already controls the order via shuffle/reorder.
- A match where one slot is `null` (a bye) auto-resolves its `winner` immediately at generation time — no click needed — and the real entry is pre-filled into the correct slot of the next round.
- `id`s (bracket id, `source_event_id`, `created_by`) are stored as strings, matching the project-wide convention for Discord snowflakes.

## Populating entries

**From an event**: `brackets.py` calls `events.load_events()` and maps that event's `participants` to a flat list of display-name strings, based on the event's `mode` (mirroring the grouping logic already used by `dashboard/backend/routes/events.py`'s `_serialize_participants`):

- **`solo`**: each participant → `ign` if set, else the guild member's `display_name` (resolved via `request.app["bot"]`'s guild object), else `f"User {user_id}"` as a last-resort fallback.
- **`team_captain`**: each participant row already *is* a team → `team_name`.
- **`team_code`**: participants are grouped by `team_code`; each group's captain's `team_name` becomes one entry.

**Manually**: the organizer pastes/types a newline-separated list of names in the create-bracket form — no event involved. Duplicate or blank lines are stripped.

Either path produces the same flat list of strings, which the organizer can then shuffle and drag-reorder in the UI before generating.

## Backend API surface

New `dashboard/backend/routes/brackets.py`. All routes require `require_dashboard_access` except the one explicitly public route:

- `GET /api/brackets` — list all brackets (id, title, source event title if any, entry count, created date).
- `POST /api/brackets` — create one. Body is either `{"title": "...", "source_event_id": "..."}` (server re-derives entries from the event) or `{"title": "...", "entries": ["...", "..."]}` (manual) — plus, in both cases, the client sends the final ordered list it wants seeded as `entries` (the client is the source of truth for order, since the organizer may have shuffled/reordered it; when `source_event_id` is given the server still validates the event exists and the submitted entries are a permutation of what that event's participants currently resolve to, rejecting anything else).
- `GET /api/brackets/{id}` — full detail (entries, all rounds/matches, share status).
- `DELETE /api/brackets/{id}` — delete.
- `POST /api/brackets/{id}/matches/{round_index}/{match_index}/winner` — body `{"winner": "a" | "b"}`. Records the pick, copies the winner into the correct slot of the next round's match, or marks the bracket complete if this was the final match. Picking a different winner than previously recorded overwrites the pick and clears any downstream picks that depended on it (since those advanced entries are no longer valid).
- `POST /api/brackets/{id}/share` — generates a random `share_token` via `secrets.token_urlsafe(32)`, stores it, returns it.
- `DELETE /api/brackets/{id}/share` — clears `share_token` to `null`; any previously-issued link 404s immediately. Re-sharing later generates a brand-new token — old links never come back.

Public, unauthenticated route (no `require_dashboard_access`):

- `GET /api/public/brackets/{share_token}` — read-only bracket view (title, entries, rounds, winners). Looked up only by token; unknown or unshared (cleared) token returns 404. No listing endpoint for tokens exists anywhere, so tokens cannot be enumerated, and no write path exists at or near this route.

## Frontend

- **`Brackets.tsx`** (new top-level page, "Сетки" in the sidebar nav, wired into `DashboardShell.tsx` and `App.tsx`) — lists existing brackets, with a "Создать сетку" button opening a modal with two tabs: "Из ивента" (dropdown of tournament events, entries auto-load on selection) or "Вручную" (textarea for names). Either tab then shows the resulting list as a draggable, reorderable list with a "Перемешать" (shuffle) button, before a final "Сгенерировать" button creates the bracket and navigates to its detail page.
- **`BracketDetail.tsx`** — the bracket grid itself (rounds as columns, matches as connected boxes). Each match is clickable to pick a winner, which visually advances them into the next column. Includes the "Поделиться ссылкой" toggle (shows the public URL + a copy-to-clipboard button once enabled, with an "Отключить" option to turn it back off) and a delete button with a confirmation modal (matching the project's existing danger-action confirmation pattern, e.g. Lockdown's activate/deactivate modal).
- **`PublicBracket.tsx`** — a new route mounted OUTSIDE `ProtectedRoute`/`DashboardShell` in `App.tsx` (e.g. `/bracket/:token`, alongside the existing top-level `/login` and `/access-denied` routes). Reuses the same bracket-grid rendering as `BracketDetail.tsx` but with no click handlers, no share/delete controls, and no dashboard chrome (no login redirect, no sidebar) — just the read-only grid.

## Share link security

- `share_token` is a long random string (`secrets.token_urlsafe(32)`), independent of the bracket's own `id` — knowing the internal ID gives no help guessing the token.
- The public route does a direct dict lookup by token; no match means 404. Tokens cannot be enumerated (no listing endpoint exposes them).
- Clearing the token (unshare) makes the old link 404 immediately; re-sharing always issues a fresh token.
- The public route only ever serves read data. There is no public write path anywhere in this feature.

## Scope

New files: `brackets.py`, `dashboard/backend/routes/brackets.py`, `dashboard/frontend/src/pages/Brackets.tsx`, `dashboard/frontend/src/pages/BracketDetail.tsx`, `dashboard/frontend/src/pages/PublicBracket.tsx`. Modified: `dashboard/frontend/src/pages/DashboardShell.tsx` (nav entry), `dashboard/frontend/src/App.tsx` (routes), `dashboard/frontend/src/api/client.ts` (new types + functions), `.gitignore` (new `brackets_data.json` entry). No changes to `events.py`/`events_core.py`/`Events.tsx` beyond being read from for entry-extraction — this feature does not modify how events themselves work.

## Testing

- Backend: unit tests for `brackets.py`'s entry-extraction (all three event modes, plus manual), bracket generation (power-of-two padding, bye auto-resolution, sequential pairing), and winner-advancement logic (including the final match completing the bracket, and overwriting a pick clearing downstream picks).
- Backend: route tests for full CRUD, the winner-setting route, share on/off, and a test confirming the public route works with zero auth and returns 404 on a wrong or cleared token.
- Frontend: tests for the create-bracket modal (both tabs, including the entries-from-event flow and the shuffle/reorder step), the bracket grid's click-to-advance behavior, and `PublicBracket.tsx` rendering read-only with no click handlers wired and no dashboard chrome.
