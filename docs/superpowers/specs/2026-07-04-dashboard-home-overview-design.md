# Dashboard: Home Overview Page — Design

## Context

`dashboard/frontend/src/pages/Home.tsx` is currently a placeholder: a single welcome card with copy that's now stale ("остальные разделы появятся в следующих фазах" — every section has been live since Phase 6). Since every dashboard feature is now built, Home should become a real at-a-glance overview: five cards summarizing feedback, events, moderation activity, antispam status, and member count, each clickable through to its full section.

## Architecture

No backend changes. Every card's data already exists behind an existing, working endpoint — this keeps `HomePage` consistent with the rest of the project, where multi-source pages (Lockdown, Events) already do independent per-card fetches rather than a combined summary endpoint:

- **Pending feedback**: `GET /api/feedback-cases?status=pending` (`fetchFeedbackCases('pending')`, already exported from `client.ts`) → card shows `cases.length`.
- **Active events**: `GET /api/events?status=open` (`fetchEvents('open')`) → card shows `events.length` (tournaments + polls combined, no type split).
- **Recent moderation activity**: `GET /api/moderation-log` (`fetchModerationLog()`) → card shows the first 3 entries (already returned newest-first), reusing the same type-icon/label mapping already built for `Lockdown.tsx`'s own activity feed.
- **Antispam status**: `GET /api/lockdown/status` (`fetchLockdownStatus()`) → card shows the existing `active`/`role_count` fields, styled like Lockdown's own status badge.
- **Member count**: `GET /api/members?page_size=1` (`fetchMembers()` with a 1-item page) → card shows the `total` field — the cheapest possible call, since only the count is needed, not the member list.

Each card fetches independently, in its own `useEffect` with its own loading/error state — matching the resilience pattern `Lockdown.tsx` already uses for its two independent data sources. One card's fetch failing must not blank out or block the other four cards from rendering.

## Cards

Five `Card` components (the existing shared primitive) in a responsive grid. Per the approved design, every card is clickable (`interactive` + `onClick` navigating via `useNavigate`):

1. **Feedback** → `/feedback` — "Ожидают решения: N" (or "Нет ожидающих" when N is 0).
2. **События** → `/events` — "Активных событий: N".
3. **Модерация** → `/lockdown` — a mini preview list of the last 3 moderation-log entries (type icon + target display name + relative time), "Активности пока нет." when empty — mirrors `Lockdown.tsx`'s own feed rendering, just capped at 3 items instead of the full list.
4. **Антиспам** → `/lockdown` — "ВКЛЮЧЁН"/"ВЫКЛЮЧЕН" badge matching Lockdown's existing status card styling (danger color when active, success color when inactive).
5. **Участники** → `/members` — "Участников: N".

The old placeholder card and its stale copy are removed entirely.

## Error handling

Each card renders its own inline error message on fetch failure (e.g. "Не удалось загрузить") in place of its data, independent of the other four cards. No page-level error state.

## Scope

Only `dashboard/frontend/src/pages/Home.tsx` changes, plus its test file. No backend changes, no changes to `client.ts` (all needed functions already exist), no changes to any other page.

## Testing

Frontend only (no backend changes to test):
- One test per card verifying it renders its fetched data correctly (including the empty-state text for feedback/events/moderation-activity/members when the count is 0 or the list is empty).
- One test verifying each card navigates to the correct route on click.
- One test verifying that a failed fetch on one card (e.g. member count) still allows the other four cards to render their own data — proving the independent-fetch resilience pattern actually holds, not just that each card works in isolation.
