# Dashboard: Lockdown Page — Recent Moderation Activity Feed — Design

## Context

The "Lockdown и модерация" page currently shows only the antispam-mode toggle card — it's sparse. Meanwhile, three moderation flows already fire and post a Discord log embed but persist nothing the dashboard can read back: automatic anti-spam punishment (`spam.py`'s `_punish`), automatic tempban (`tempban.py`'s `_do_tempban`), and manual ban/kick from the dashboard's Members page (`dashboard/backend/routes/moderation.py`'s `ban_member`/`kick_member`, both funneled through the shared `_send_action_log` helper at lines 125-133). This adds a "Recent moderation activity" feed to the Lockdown page, scoped to exactly these four action types, confirmed with the user as: automatic spam + automatic tempban + manual ban + manual kick (manual role grants/revokes, which also call `_send_action_log`, are explicitly out of scope).

## Storage: `moderation_log.py`

New root module, following the project's established JSON-backed pattern (no in-memory cache — every call reads/writes `moderation_log.json` fresh from disk, same as `reaction_roles.json`/`events_data.json`/`config.json`):

```python
LOG_FILE = "moderation_log.json"
MAX_ENTRIES = 200

def load_events() -> list[dict]:
    """Returns events newest-first."""

def append_event(
    event_type: str,       # "spam_punish" | "tempban" | "manual_ban" | "manual_kick"
    user_id: int,
    user_display: str,
    reason: str,
    moderator_id: int | None = None,     # None = automatic
    moderator_display: str | None = None,
    extra: str = "",
) -> None:
    """Appends one event with an ISO timestamp, trims to the oldest MAX_ENTRIES, writes the file."""
```

Each stored record: `{type, timestamp (ISO-8601 UTC), user_id (str), user_display, moderator_id (str | null), moderator_display (str | null), reason, extra}`. `user_id`/`moderator_id` are stored as strings, matching the project-wide convention for Discord snowflakes. `moderator_id: null` is how the frontend distinguishes automatic events from manual ones (rendered as "Автоматически").

`moderation_log.json` is added to `.gitignore` (same class of runtime-generated file as `events_data.json`/`config.json`).

## Instrumentation (four call sites, one shared function)

- **`spam.py`'s `_punish`** (around line 214): after the timeout/purge logic, call `moderation_log.append_event("spam_punish", member.id, member.name, f"Спам массовыми тегами ({limit} одинаковых сообщений за 60 сек.)", extra=", ".join(channels_spammed))`. Called unconditionally — not gated behind `log_channel_id` being set, since this is a separate, dashboard-facing concern from the Discord embed log.
- **`tempban.py`'s `_do_tempban`** (around line 135, right before the final `await self.bot.send_log(embed)`): only on the success path (member actually banned) — call `moderation_log.append_event("tempban", member.id, member.name, TEMPBAN_REASON, extra=f"Канал: <#{message.channel.id}>; unban: {'ok' if not unban_error else unban_error}")`. The three early-return error paths (Forbidden/HTTPException/generic Exception before the ban succeeds) do NOT log an event — nothing happened to the member yet.
- **`dashboard/backend/routes/moderation.py`'s `_send_action_log`** (lines 125-133): gains one new parameter, `event_type: str | None = None`. When set, it calls `moderation_log.append_event(event_type, target.id, target.name, reason, moderator_id=moderator.id, moderator_display=moderator.name, extra=extra)` in addition to the existing Discord embed post. `ban_member` passes `event_type="manual_ban"`, `kick_member` passes `event_type="manual_kick"`. The two role-grant/revoke call sites (lines 281, 303) are left unchanged — they don't pass `event_type`, so nothing is persisted for them, matching the confirmed scope.

## API: `GET /api/moderation-log`

Added to `dashboard/backend/routes/moderation.py`, gated by the same `require_dashboard_access` decorator as every other dashboard route. Read-only — no `POST`/`PUT`/`DELETE`, since this is a feed, not an editable resource.

```python
@routes.get("/api/moderation-log")
@require_dashboard_access
async def get_moderation_log(request: web.Request) -> web.Response:
    limit = min(int(request.query.get("limit", 50)), moderation_log.MAX_ENTRIES)
    events = moderation_log.load_events()[:limit]
    return web.json_response({"events": events})
```

## Frontend

`dashboard/frontend/src/api/client.ts` gains:

```typescript
export interface ModerationLogEntry {
  type: 'spam_punish' | 'tempban' | 'manual_ban' | 'manual_kick'
  timestamp: string
  user_id: string
  user_display: string
  moderator_id: string | null
  moderator_display: string | null
  reason: string
  extra: string
}

export function fetchModerationLog(): Promise<ModerationLogEntry[]>
```

`dashboard/frontend/src/pages/Lockdown.tsx` gains a second `<Card>` below the existing antispam-toggle card, titled "Последняя активность", fetched in parallel with the existing `reload()` call on mount. Each row shows: a type icon/label (spam → warning, tempban → clock, manual ban → prohibit, manual kick → sign-out — using the already-imported `@phosphor-icons/react` package), the target user's display name, the reason, and either the moderator's name or "Автоматически" (when `moderator_id` is `null`), plus a relative timestamp. Empty state: "Активности пока нет." No pagination — the list is capped at 50 by the API and 200 in storage, which is small enough to render in full.

## Scope

New file: `moderation_log.py`. Modified: `spam.py`, `tempban.py`, `dashboard/backend/routes/moderation.py`, `dashboard/frontend/src/api/client.ts`, `dashboard/frontend/src/pages/Lockdown.tsx`, `.gitignore`. No changes to the antispam-toggle logic already on the page.

## Testing

- Backend: a unit test for `moderation_log.append_event`/`load_events` (round-trip, newest-first ordering, trimming at `MAX_ENTRIES`).
- Backend: a test that `ban_member`/`kick_member` each result in one new entry in `moderation_log.json` with the correct `event_type` and non-null `moderator_id`.
- Backend: a test for `GET /api/moderation-log` — returns entries newest-first, respects `limit`, requires dashboard access.
- Frontend: a test that `Lockdown.tsx` renders fetched entries, shows "Автоматически" when `moderator_id` is `null`, and shows the empty state when the list is empty.
- `spam.py`/`tempban.py` instrumentation is verified by manual line-by-line diff review against the pre-change source, consistent with the rest of the project (no pytest coverage exists for interaction/event-listener cog code anywhere in this project).
