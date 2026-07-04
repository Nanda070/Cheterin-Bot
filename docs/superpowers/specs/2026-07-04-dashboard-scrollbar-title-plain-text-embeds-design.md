# Dashboard: Scrollbar Styling, Title Rename, Plain-Text Embed Messages — Design

## Context

Three small, independent UX fixes found during use of the dashboard, bundled together since they're all small frontend-only changes — not a new phase.

## Fix 1: styled scrollbar

The dashboard currently uses the browser's default scrollbar everywhere (page body, modal `overflow-y-auto` panels, etc.), which doesn't match the dark design system. A global rule in `dashboard/frontend/src/index.css` styles both WebKit browsers (`::-webkit-scrollbar`/`-track`/`-thumb`/`-thumb:hover`) and Firefox (`scrollbar-color`/`scrollbar-width: thin`), applied to `html`/`*` so it covers every scrollable element in the app with one rule — no component changes needed. Thumb color matches `--color-border` (`#232838`) with a `--color-surface-hover` (`#181d2c`) hover state, track transparent, rounded to match the design system's existing `--radius-control`.

## Fix 2: title rename

Two textual changes, no logic changes:
- `dashboard/frontend/src/pages/DashboardShell.tsx`'s header `<span className="font-semibold">Панель управления ботом</span>` → `404 Bot Dashboard`.
- `dashboard/frontend/index.html`'s `<title>frontend</title>` → `<title>404 Bot Dashboard</title>` (currently the Vite scaffold default, never localized).

## Fix 3: allow plain-text (no-embed) messages in the embed builder

The embed builder form already has a "Текст сообщения" (`content`) field that's sent alongside the embed — the only blocker is that both the frontend's `validateEmbedSpec` and the backend's `embed_builder.validate_embed_spec` unconditionally require at least one embed field (title/description/field/image/thumbnail) to be filled, even when `content` alone is provided.

**Change**: both validators gain one added condition — skip the "must have at least one embed field" check when `content` is non-empty (trimmed). The existing `empty_embed` error still fires when BOTH `content` and every embed field are empty (nothing to send). No new UI toggle — leaving every embed field blank and only filling `content` already works automatically.

**Backend behavior when the embed is empty but `content` isn't**: `create_embed_message`/`update_embed_message` (`dashboard/backend/routes/embed_builder.py`) skip calling `embed_builder.build_embed()` entirely for an empty spec, and call `channel.send(content=content, embed=None, view=view)` — a genuine plain-text message, not an embed with all-empty fields. `EmbedPreview.tsx` already renders `content` as a paragraph separate from the embed card, so a content-only preview already displays correctly with no component changes.

## Scope

Only `dashboard/frontend/src/index.css`, `dashboard/frontend/src/pages/DashboardShell.tsx`, `dashboard/frontend/index.html`, `dashboard/frontend/src/pages/EmbedBuilder.tsx`, `embed_builder.py`, `dashboard/backend/routes/embed_builder.py` change. No new files, no new routes.

## Testing

- Frontend: a test confirming `validateEmbedSpec` passes when the embed is empty but `content` is non-empty, and still fails when both are empty.
- Backend: a test confirming `create_embed_message` sends `embed=None` (no embed object) when the spec is empty and `content` is provided, and a regression test confirming the existing `empty_embed` 400 still fires when both are blank.
- Title/scrollbar changes are visual-only — verified by the assistant in the browser before handoff, not unit-tested.
