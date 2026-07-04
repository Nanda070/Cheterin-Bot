# Dashboard: Header Rename to "Cheterin" + Clickable Home Link — Design

## Context

Small follow-up to the earlier title-rename mini-fix ("Панель управления ботом" → "404 Bot Dashboard"): the user wants the title changed again, this time to "Cheterin", and wants the dashboard header's title clickable so it acts as a shortcut back to the home page — a standard "logo goes home" pattern this dashboard didn't have before.

## Changes

Two independent changes to the same header element, plus two consistency renames:

1. **Clickable header title**: `dashboard/frontend/src/pages/DashboardShell.tsx`'s header `<span className="font-semibold">404 Bot Dashboard</span>` (currently plain text) becomes a clickable link to the index route (`/`) — implemented with `react-router-dom`'s `<Link to="/">` wrapping the icon+text group, matching how every other internal navigation in this project already uses `react-router-dom` (`NavLink`/`useNavigate`), rather than a manual `onClick`+`useNavigate` handler.
2. **Text rename, three spots** (per the approved "everywhere" scope): `DashboardShell.tsx`'s header, `Login.tsx`'s heading, and `index.html`'s `<title>` all change from `"404 Bot Dashboard"` to `"Cheterin"` — the exact same three locations the prior title-rename mini-fix touched.

## Scope

Only `dashboard/frontend/src/pages/DashboardShell.tsx`, `dashboard/frontend/src/pages/Login.tsx`, `dashboard/frontend/index.html` change. No backend changes.

## Testing

- Frontend: a test confirming the header title renders as a link to `/`, and that clicking it navigates there (using the same `MemoryRouter` + marker-route pattern already established in this project's other navigation tests).
- A grep-based verification step (not a test) confirming no remaining occurrence of "404 Bot Dashboard" anywhere in `dashboard/frontend/src` or `index.html`, mirroring how the prior title-rename mini-fix verified its own rename.
