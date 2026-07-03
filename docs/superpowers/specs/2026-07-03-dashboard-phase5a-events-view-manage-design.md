# Phase 5a: Events/Voting — Dashboard View & Management — Design

## Context

The bot already has a full-featured `events.py` cog: `/event setup` (a multi-step Discord modal builder for tournaments — solo/team-captain/team-code registration, participant limits, role rewards, ping options — and polls with single/multi-select voting and live percentage bars), plus `/event manage` (a Discord-side panel for sending a DM notification to participants, closing, or deleting an event). It stores state in `events_data.json`, keyed by the published message's id.

Phase 5 brings this to the dashboard, split into two sub-phases (matching the precedent set by Phase 3's 3a/3b and Phase 4's 4a/4b/4c):

- **Phase 5a (this spec):** view and manage existing events from the dashboard — list, participant/vote detail, close, delete, notify. No event creation yet.
- **Phase 5b (future, separate spec):** a dashboard web form for creating tournaments/polls, replacing the Discord modal builder. Deferred until 5a ships and is verified working, since it's the larger and riskier piece.

## Bundled fix: remove `events.py`'s module-level cache

`events.py` currently caches `events_data.json` in a module-level `_EVENTS_CACHE`, populated once and reused until the bot restarts. This is the same stale-until-restart pattern Phase 4b explicitly removed from `feedback_categories.py`. Left as-is, a dashboard close/delete would not be visible to the running bot (and vice versa) until a restart — breaking the live-sync promise every other dashboard-editable config in this project already has. This phase removes `_EVENTS_CACHE`/`_EVENTS_LOCK` and makes `load_events()`/`save_events()` always read/write fresh from disk, matching `feedback_categories.py`'s established pattern. `events.py`'s own callers (the builder, registration modals, vote buttons, `/event manage`) are otherwise unaffected — they already call `load_events()`/`save_events()` fresh on every interaction.

## Extraction: `events_core.py`

`load_events()`/`save_events()` are already plain async functions with no `discord.Interaction` dependency — directly reusable by dashboard routes as-is. The close/delete/notify actions, however, currently live as inline closures inside `EventManageSelect.callback()` in `events.py` — not reusable. Following this project's established `_core.py` extraction pattern (`feedback_core.py`), this phase extracts them into a new `events_core.py`:

- `async def close_event(bot, message_id: str) -> dict` — sets status to `closed`, edits the live message (disabled buttons, "🔴 Статус: Закрыто" footer). Idempotent: closing an already-closed event is a harmless no-op, matching the current Discord behavior exactly (no new validation invented).
- `async def delete_event(bot, guild, message_id: str) -> dict` — removes `role_reward` from all participants (if any), deletes the live message, removes the event from storage.
- `async def notify_participants(bot, guild, message_id: str, text: str) -> dict` — bulk-DMs all participant user ids with the given text, rate-limited identically to the existing modal's loop (`asyncio.sleep(0.1)` between sends), returns success/failure counts.

Both `EventManageSelect`'s Discord-side callbacks and the new dashboard routes call these same three functions, so the two paths cannot drift apart.

## API (`dashboard/backend/routes/events.py`, new file)

- `GET /api/events?status=open|closed` — list, filtered by status, defaults to `open` if omitted (mirrors Phase 4a's feedback-case list route). Each entry: `message_id`, `type` (`tournament`/`poll`), `title`, `status`, `channel_id` (string).
- `GET /api/events/{message_id}` — detail. For tournaments: participant list (shape depends on `mode` — solo shows ign per user, team_captain shows team name + members text + captain, team_code shows teams grouped by code with each member's ign), plus `max_limit`/`team_size`/`role_reward`. For polls: `options` with per-option vote counts and percentages (same math as `rebuild_event_embed`), `multi_select` flag. 404 if unknown.
- `POST /api/events/{message_id}/close` — calls `events_core.close_event`. 404 if unknown.
- `DELETE /api/events/{message_id}` — calls `events_core.delete_event`. 404 if unknown.
- `POST /api/events/{message_id}/notify` — body `{"message": string}`. Tournament-only in the UI (mirrors the existing Discord panel, which never shows the "📢 Рассылка" button for polls); no separate server-side type guard is added, since a poll's empty `participants` list already naturally triggers the existing "no participants" error path. 404 if unknown, 400 if `participants` is empty.

All routes gated by `require_dashboard_access`. IDs (`channel_id`, `role_reward`) serialized as strings in API responses, matching this project's established convention — the underlying `events_data.json` storage format for existing/new events is unchanged (still native ints), since migrating that shape is out of scope and every dashboard `int(...)`-conversion already happens at the exact Discord API call site.

## Frontend

- `dashboard/frontend/src/pages/Events.tsx` — list + open/closed status filter, same list+detail-panel layout convention as `FeedbackCases.tsx`.
- `dashboard/frontend/src/pages/EventDetailPanel.tsx` — participants (mode-aware rendering) or poll results, with Close/Delete/Notify actions. Notify opens a small text-input modal (mirrors `EventNotifyModal`'s single textarea), Delete requires confirmation (mirrors the existing delete-confirmation pattern used in `FeedbackCategories.tsx`/`ReactionRoles.tsx`).
- New sidebar entry "События" routed at `/events`.

## Testing

- `events_core.py`: fakes-based tests for `close_event`/`delete_event`/`notify_participants`, using `dashboard/backend/tests/fakes.py` (extending it only if a genuine gap is found, same discipline as the `FakeMessage.jump_url` gap-fill in Phase 4c).
- A dedicated regression test proving `load_events()` reads fresh from disk after an external write to `events_data.json` — proving the cache removal genuinely works, not just asserted by inspection.
- Route tests: list (with/without status filter), detail (tournament and poll shapes), close (including idempotent re-close), delete (including role removal), notify (including the empty-participants 400 path), auth-gating on all five routes, 404s on all four id-scoped routes.
- Zero new tests for `events.py`'s interaction-driven UI (`EventBuilderView`, registration modals, vote buttons, `/event setup`/`/event manage` slash commands) — this project's standing convention holds (no `FakeInteraction` pattern exists, none invented). Any change to `events.py` itself (only `EventManageSelect`'s three callbacks being reduced to thin wrappers around `events_core`, plus the cache removal) is verified by careful, minimal, line-by-line diffing against the current source.

## Global constraints (carried over, still binding)

- No caching in `events_core.py`/`events.py`'s data-access layer (this phase's whole point, for the events module).
- IDs stored/serialized as strings in API responses; `int(...)`-conversion only at the exact Discord API call site.
- All routes gated by `require_dashboard_access`.
- Validation order: structural → Discord-existence → permission, everywhere.
- Never bare `git add -A`/`git add .`.
- `events.py`'s interaction-driven code gets zero new pytest coverage; verified by diff reading only.
