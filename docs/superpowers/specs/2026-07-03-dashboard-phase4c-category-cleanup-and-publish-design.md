# Phase 4c: Category Deletion Fix, Default Template, Panel Publishing — Design

## Context

Phase 4b shipped full CRUD for feedback categories. Manual E2E testing surfaced a real bug and two feature requests, all scoped to the same "Категории" dashboard page and its supporting backend routes.

## 1. Bug fix: cascade-delete pending cases when their category is deleted

**Problem:** `DELETE /api/feedback-categories/{category_key}` intentionally allows deleting a category with active cases (the Phase 4b design's "graceful degradation" choice). But there is no route to delete an individual feedback case, and `feedback_core.decide_case()` now returns `category_deleted` (409) instead of crashing — so a pending case under a deleted category becomes permanently stuck: it cannot be accepted, rejected, or removed.

**Fix:** `delete_feedback_category` (`dashboard/backend/routes/feedback.py`) will, after confirming the category exists and before persisting the category removal, scan `bot.feedback_cases` for entries whose `category_key` matches the deleted category and whose `status == "pending"`, delete those entries from the dict, and call `await bot.update_file()` if any were removed. Already-decided cases (`approved`/`denied`) are left untouched — they're historical records already displayed correctly via `serialize_case_summary`/`serialize_case_detail`'s existing `config.get(category_key, {})` fallback (raw key shown when category is gone).

**Scope boundary:** existing Discord messages (the public embed and the thread with Accept/Reject buttons) for cascade-deleted cases are left as-is — not edited, archived, or locked. If a moderator clicks a stale Accept/Reject button afterward, `feedback_core.decide_case()`'s existing `case_data = bot.feedback_cases.get(case_id)` / `if not case_data: return {"ok": False, "error": "not_found"}` path already handles it cleanly (this code path already exists and is already tested — no new code needed for that side).

## 2. "Дефолтный Шаблон" button — restore default category

**Behavior:** a button on the Категории page (next to "Создать категорию") that opens the create-category modal pre-filled with a hardcoded template matching the exact content of the original env-var migration's "players" category (`feedback_categories.py`'s `migrate_from_env_if_needed`) — same key (`players`), title, button_label, case_prefix (`PR`), case_title, thread_name, modal_title, approved_text, denied_text, all 4 fields (`offender`/`complaint`/`datetime`/`proof` with their exact labels/styles/required/max_length), and `mini_summary_key` (`offender`).

`channel_id` and `review_role_ids` are deliberately left empty in the template — they're guild-specific and must be picked by the user via the existing channel dropdown / role checkboxes before saving.

**Implementation:** purely additive to the frontend. A `DEFAULT_TEMPLATE` constant in `FeedbackCategories.tsx`, and the button calls `setEditingKey(null); setSpec({ ...DEFAULT_TEMPLATE }); setFormOpen(true)`. Saving goes through the existing `POST /api/feedback-categories` create flow unchanged — including its existing `key_taken` (409) rejection if "players" already exists, which is correct (restoring only makes sense if it was actually deleted). No backend changes.

## 3. "Опубликовать" button — publish panel from dashboard

**Behavior:** a page-level button on the Категории page (next to "Создать категорию" and "Дефолтный Шаблон") — not per-category, since the feedback panel is a single Discord message containing buttons for all currently-configured categories at once (this is how `FeedbackView` in `feedback_menu.py` already works, and matches the existing `/feedback_panel send` slash command). Clicking it opens a small channel picker (reusing the already-fetched `channels` list used by the category form's channel dropdown) and, on confirm, calls a new `POST /api/feedback-panel/publish` route with `{"channel_id": string}`.

**Backend — extraction to avoid drift:** the panel-building logic currently inline in `feedback_menu.py`'s `feedback_panel_send` command (build the embed, send it with `view=FeedbackView(self.bot)`, log via `bot.send_log`) is extracted into a new shared function `publish_feedback_panel(bot, channel) -> discord.Message` in `feedback_core.py`, using a local import of `FeedbackView` from `feedback_menu` (matching `decide_case`'s existing local-import pattern to avoid a circular import). Both the slash command and the new dashboard route call this same function, so they cannot drift apart — this is the same `_core.py` extraction pattern already used for `decide_case`.

**Route validation order (binding, matches every other route in this project):** structural first (`channel_id` present and a string in the JSON body → 400 if not) → Discord-existence second (`guild.get_channel(int(channel_id))` must resolve and be a `discord.TextChannel` → 404/400 if not) → permission is implicit via `require_dashboard_access`, which already gates the route. On success, call `publish_feedback_panel(bot, channel)` and return `{"ok": True}`.

**Out of scope:** no change to the slash command's own behavior or its `channel` parameter handling; no per-category publish option; no tracking of "which channel is the panel currently published in" (this project doesn't persist that today, and neither does the slash command).

## Testing

- Backend: regression test for cascade-delete (pending case removed, decided case survives, `bot.update_file()` called once if anything removed, `not_found` on delete of unknown category unchanged); regression tests for `publish_feedback_panel` extraction (route requires auth, structural-then-existence validation order, correct channel type check) using this project's existing `FakeGuild`/`FakeChannel`/`FakeBot` fakes.
- Frontend: no new tests strictly required for the default-template button (it only sets pre-existing form state — the existing create-flow tests already cover the save path), but a small test confirming the button populates the key field can be added for parity with this project's testing conventions. A test for the publish button's channel-picker-then-POST flow, mirroring existing API-client test patterns.
- No `feedback_menu.py` interaction-driven code gets new tests, consistent with this project's standing convention (no `FakeInteraction` pattern exists).

## Global constraints (carried over from Phase 4b, still binding)

- No caching in `feedback_categories.py` or its callers.
- IDs (channel_id, role_ids) stored/serialized as strings; `int(...)`-conversion only at the exact Discord API call site.
- All new/touched routes remain gated by `require_dashboard_access`.
- Never bare `git add -A`/`git add .`.
- Validation order: structural → Discord-existence → permission, everywhere.
