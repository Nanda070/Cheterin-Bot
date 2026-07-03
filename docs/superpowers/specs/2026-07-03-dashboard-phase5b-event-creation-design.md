# Phase 5b: Events/Voting — Dashboard Event Creation — Design

## Context

Phase 5a shipped dashboard view/management for events (list, participant/vote detail, close, delete, notify), deliberately deferring creation to this phase. The bot already has a full Discord-side creation flow: `/event setup` opens `EventBuilderView` (`events.py`), a stateful multi-step button/modal builder covering both event types (tournament, poll) and every option (registration mode, role reward, limits, ping, banner, poll options, multi-select). This phase adds a dashboard web form that produces the exact same `events_data.json` shape, coexisting with `/event setup` rather than replacing it.

## Extraction: `events_core.py` gains `publish_event` and `validate_event_spec`

`EventBuilderView.publish()` currently does everything inline once its (minimal) validation passes: build the embed, send it to the channel, build the `event_obj` dict, save it, attach the participation view. This gets extracted into `events_core.py`, following the same `_core.py` pattern already used for `publish_feedback_panel` (Phase 4c) and `close_event`/`delete_event`/`notify_participants` (Phase 5a):

- `async def publish_event(bot, channel, spec: dict, author_id: int) -> discord.Message` — builds the announcement embed (tournament or poll shape, matching the current `publish()` method's embed exactly), sends it, constructs the `event_obj` (identical field set to what `EventBuilderView.publish()` builds today), saves via `events.save_events`, and attaches `events.create_participation_view(message_id, event_obj)`. `spec` is a plain dict shaped like `DraftEvent`'s fields: `type`, `title`, `description`, `banner_url`, `mode`, `require_info`, `max_limit`, `team_size`, `role_reward`, `ping`, `options`, `multi_select`.
- `def validate_event_spec(spec: dict) -> str | None` — returns an error string or `None`, following the exact convention of `feedback_categories.validate_category_spec`. Structural rules, matching what the Discord builder's UI can actually produce (not the unused theoretical flexibility in the data model — e.g. `ping` only ever cycles through three fixed values in the current UI, so validation only accepts those three, not an arbitrary role id):
  - `type` ∈ `{"tournament", "poll"}`
  - `title`: non-empty, ≤100 chars (matches `TextModal`'s `inp_title` `max_length=100`)
  - `description`: non-empty, ≤2000 chars (matches `inp_desc`'s `max_length=2000`)
  - `banner_url`: optional string, no format constraint (matches the Discord builder, which never validates this beyond accepting any string)
  - `ping` ∈ `{"none", "everyone", "here"}`
  - Tournament-only: `mode` ∈ `{"solo", "team_captain", "team_code"}`; `max_limit` is an int ≥ 0; `team_size` is an int ≥ 2 (only checked when `mode != "solo"`, matching `LimitsModal`'s own conditional field); `require_info` is a bool
  - Poll-only: `options` is a list of 2–10 non-empty strings (matches `OptionsModal`'s line-count bounds); `multi_select` is a bool

**The Discord builder switches to calling `validate_event_spec` too**, replacing its current ad-hoc `if not title or not description` / `if poll and not options` checks in `EventPublishSelect.callback()`. This is a small, deliberate strictness upgrade for the existing builder (adds bounds the modals already enforce per-field but the publish step never double-checked) and, more importantly, guarantees the Discord and dashboard paths can never validate differently.

## API — `POST /api/events`

Request body: `{channel_id, type, title, description, banner_url, ping, mode, require_info, max_limit, team_size, role_reward, options, multi_select}` — fields irrelevant to the chosen `type` may be omitted or ignored (mirroring how the Discord builder only shows/uses the relevant section per type).

Validation order (binding, matches every other route in this project): structural (`validate_event_spec`) → Discord-existence (`guild.get_channel(int(channel_id))` must resolve; if `role_reward` is set, `guild.get_role(int(role_reward))` must resolve) → permission (already enforced by `@require_dashboard_access` wrapping the whole handler before any body code runs). On success: `201` with `serialize_event_detail(message_id, ev)`, reusing Phase 5a's existing serializer unchanged. IDs (`channel_id`, `role_reward`) arrive as strings from the client and are `int(...)`-converted only at the exact Discord API call sites, matching the established convention.

## Frontend

A "Создать событие" button on the existing `Events.tsx` page (next to the status filter) opens one large `Modal` form. A type toggle (Турнир/Опрос) conditionally renders the relevant section:
- **Tournament section**: mode selector, "анкета" (require_info) toggle, лимиты (max_limit, team_size — team_size only shown when mode ≠ solo), role-reward picker (reusing the already-fetched `roles` list).
- **Poll section**: a single multi-line textarea for options (one per line, 2–10 lines) — matching `OptionsModal`'s exact UX rather than inventing a repeatable add/remove row widget, since the Discord builder itself uses a plain textarea here.
- **Shared fields**: title, description, banner URL (optional), ping selector (none/everyone/here), channel picker (reusing the already-fetched `channels` list, same pattern as `FeedbackCategories.tsx`).

On successful create, the modal closes and the events list reloads.

## Testing

- `events_core.validate_event_spec`: structural rejection for each rule above (invalid type, oversized title/description, bad mode/ping, poll option-count out of bounds).
- `events_core.publish_event`: fakes-based test confirming the created `event_obj`'s shape matches exactly what Phase 5a's `serialize_event_detail`/`serialize_event_summary` already expect to read (this is the critical cross-phase contract — a mismatch here would silently break the Phase 5a UI for newly-created events), and that the participation view gets attached to the sent message.
- The Discord builder's refactor to call `validate_event_spec` gets zero new tests — same standing convention (no `FakeInteraction` pattern, interaction-driven code verified by diff reading only).
- `POST /api/events` route: structural-then-existence validation order (dedicated regression test, matching this project's established pattern for this exact bug class), auth gate, success creates a fetchable event (round-trip through `GET /api/events/{message_id}`), channel/role-not-found 404s.
- Frontend: create-flow tests for both tournament and poll paths, type-toggle switching sections correctly, and the standing test-query-collision discipline (any modal-scoped button whose text could collide with page-level text gets `within(dialog)` scoping, never a copy rename).

## Global constraints (carried over, still binding)

- No caching in `events.py`'s data-access layer (already true since Phase 5a, unaffected by this phase).
- IDs stored/serialized as strings in API request/response bodies; `int(...)`-conversion only at the exact Discord API call site. Underlying `events_data.json` storage format is unchanged (still native ints), matching Phase 5a's precedent.
- The new route gated by `require_dashboard_access`.
- Validation order: structural → Discord-existence → permission, everywhere.
- Never bare `git add -A`/`git add .`.
- `events.py`'s interaction-driven code gets zero new pytest coverage beyond what's already there; any change to it is verified by careful, minimal diff reading.
