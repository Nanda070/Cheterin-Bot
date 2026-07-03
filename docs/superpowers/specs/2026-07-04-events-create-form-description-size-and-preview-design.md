# Events Create Form: Larger Description Field + Live Embed Preview — Design

## Context

Manual E2E of Phase 5b (dashboard event creation) surfaced a small UX gap: the "Описание" textarea in the create-event form (`dashboard/frontend/src/pages/Events.tsx`) is `rows={3}`, too short for a real event description. The user also asked for a live preview of what the published Discord embed will look like, while still filling in the form.

This is a small, single-file UX enhancement — not a new phase.

## Fix 1: larger description field

Change the `Описание` `<textarea>`'s `rows={3}` to `rows={6}`. No other change.

## Fix 2: live embed preview

The project already has a Discord-embed-styled preview component, `dashboard/frontend/src/components/EmbedPreview.tsx` (built in Phase 3b for the message/embed builder), which renders an `EmbedSpec` (`title`, `description`, `color`, `fields: EmbedFieldSpec[]`, `image.url`, `footer.text`, etc. — see `dashboard/frontend/src/api/client.ts`). This gets reused as-is, with no changes to `EmbedPreview.tsx` itself.

A new function in `Events.tsx`, `buildEventEmbedPreview(spec: CreateEventSpec, optionsText: string): EmbedSpec`, maps the create form's current state into that shape, mirroring `events_core.publish_event`'s actual embed-building logic field-for-field (so the preview matches exactly what gets published, not an approximation):
- `title`/`description` pass through directly from `spec`.
- `color`: Discord's brand-red hex for `type === 'tournament'`, blurple hex for `type === 'poll'` (matching `discord.Color.brand_red()`/`discord.Color.blurple()`).
- Tournament fields: `"Формат"` (localized mode label) + either `"Лимит: 0 / {max_limit}"` (if `max_limit > 0`) or `"Участники: 0"` — matching the exact placeholder values a freshly-published event's embed shows before anyone registers.
- Poll fields: one field per line of `optionsText` (trimmed, empty lines filtered — same parsing already used at submit time), each showing `"░░░░░░░░░░ 0% (0 гол.)"` — matching the exact placeholder a freshly-published poll shows before any votes.
- `footer.text`: `"🟢 Статус: Открыто"` (the real footer text `publish_event` sets).
- `image.url`: the form's `banner_url` field.
- `author`, `thumbnail`, `url`, `timestamp`: all empty/`null` (unused by event embeds).

`<EmbedPreview content="" embed={buildEventEmbedPreview(createSpec, optionsText)} />` is placed directly after the type toggle (Турнир/Опрос), at the top of the form — visible as a persistent reference while the rest of the fields are filled in below it. No new state or debouncing is needed: the preview is purely derived from `createSpec`/`optionsText`, which already update on every keystroke, so it re-renders live automatically.

## Scope

Only `dashboard/frontend/src/pages/Events.tsx` changes. `EmbedPreview.tsx` and `EventDetailPanel.tsx` are reused/left untouched.

## Testing

- A test confirming the preview shows the correct tournament fields (`Формат`, `Участники`/`Лимит`) as the relevant inputs change.
- A test confirming the preview shows one field per newline-separated poll option, live as the textarea is typed into.
- A test confirming the preview's color changes when the type toggle switches between Турнир/Опрос.
