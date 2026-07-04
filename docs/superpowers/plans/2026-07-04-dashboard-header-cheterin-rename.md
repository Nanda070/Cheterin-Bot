# Dashboard: Header Cheterin Rename + Clickable Home Link Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename "404 Bot Dashboard" to "Cheterin" everywhere it appears, and make the dashboard header's title a clickable link back to the home page, per the approved spec (`docs/superpowers/specs/2026-07-04-dashboard-header-cheterin-rename-design.md`, commit `e3012cf`).

**Architecture:** Three plain text/JSX edits (`DashboardShell.tsx`, `Login.tsx`, `index.html`) plus one behavioral change: `DashboardShell.tsx`'s header title span is wrapped in a `react-router-dom` `<Link to="/">`, matching how every other internal navigation in this project already uses `react-router-dom` rather than manual click handlers.

**Tech Stack:** React + TypeScript + Vite, Vitest + Testing Library, react-router-dom.

## Global Constraints

- Text renames from "404 Bot Dashboard" to "Cheterin" in exactly three places: `dashboard/frontend/src/pages/DashboardShell.tsx`'s header, `dashboard/frontend/src/pages/Login.tsx`'s heading, `dashboard/frontend/index.html`'s `<title>`.
- The header title link uses `react-router-dom`'s `<Link to="/">`, not a manual `onClick`+`useNavigate` handler.
- No backend changes.

---

### Task 1: Rename to "Cheterin" and make the header title a home link

**Files:**
- Modify: `dashboard/frontend/src/pages/DashboardShell.tsx:14` (import), `:56-60` (header)
- Modify: `dashboard/frontend/src/pages/Login.tsx:14`
- Modify: `dashboard/frontend/index.html:7`
- Test: `dashboard/frontend/src/pages/DashboardShell.test.tsx` (new — this component has never had tests)

**Interfaces:** None — no new exports or functions, plain text/JSX edits only.

- [ ] **Step 1: Write the failing test**

Create `dashboard/frontend/src/pages/DashboardShell.test.tsx`:

```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { AuthProvider } from '../context/AuthContext'
import { DashboardShell } from './DashboardShell'

describe('DashboardShell', () => {
  it('renders the "Cheterin" header title as a link to the home page', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
    })

    render(
      <MemoryRouter initialEntries={['/members']}>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<div>Home Page Marker</div>} />
            <Route path="/members" element={<DashboardShell />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    )

    const title = await screen.findByText('Cheterin')
    expect(title.closest('a')).toHaveAttribute('href', '/')

    fireEvent.click(title)
    expect(await screen.findByText('Home Page Marker')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `dashboard/frontend`): `npx vitest run src/pages/DashboardShell.test.tsx`
Expected: FAIL — the header still renders the plain-text "404 Bot Dashboard" (not "Cheterin", not a link), so `screen.findByText('Cheterin')` finds nothing.

- [ ] **Step 3: Make the header title a clickable link and rename it**

In `dashboard/frontend/src/pages/DashboardShell.tsx`, change the import on line 14:

```tsx
import { NavLink, Outlet } from 'react-router-dom'
```

to:

```tsx
import { Link, NavLink, Outlet } from 'react-router-dom'
```

Then replace the header block (lines 56-60):

```tsx
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <div className="flex items-center gap-2 text-foreground">
          <Sparkle size={20} weight="fill" className="text-primary" />
          <span className="font-semibold">404 Bot Dashboard</span>
        </div>
```

with:

```tsx
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <Link to="/" className="flex items-center gap-2 text-foreground">
          <Sparkle size={20} weight="fill" className="text-primary" />
          <span className="font-semibold">Cheterin</span>
        </Link>
```

- [ ] **Step 4: Run the test to verify it passes**

Run (from `dashboard/frontend`): `npx vitest run src/pages/DashboardShell.test.tsx`
Expected: PASS.

- [ ] **Step 5: Rename the login screen heading**

In `dashboard/frontend/src/pages/Login.tsx`, change line 14:

```tsx
          <h1 className="text-xl font-semibold text-foreground">404 Bot Dashboard</h1>
```

to:

```tsx
          <h1 className="text-xl font-semibold text-foreground">Cheterin</h1>
```

- [ ] **Step 6: Rename the browser tab title**

In `dashboard/frontend/index.html`, change line 7:

```html
    <title>404 Bot Dashboard</title>
```

to:

```html
    <title>Cheterin</title>
```

- [ ] **Step 7: Verify no old title text remains**

Run: `grep -rn "404 Bot Dashboard" dashboard/frontend/src dashboard/frontend/index.html`
Expected: no output (no matches).

- [ ] **Step 8: Run the full frontend suite to check for regressions**

Run (from `dashboard/frontend`): `npx vitest run`
Expected: all tests PASS. No existing test file asserts on the old "404 Bot Dashboard" string (confirmed during planning — neither `DashboardShell.test.tsx` nor `Login.test.tsx` existed before this task, and no other test file references this string), so no other test file needs updating.

- [ ] **Step 9: Commit**

```bash
git add dashboard/frontend/src/pages/DashboardShell.tsx dashboard/frontend/src/pages/DashboardShell.test.tsx dashboard/frontend/src/pages/Login.tsx dashboard/frontend/index.html
git commit -m "feat: rename dashboard title to Cheterin and make the header a home link"
```

---

## Final Verification

- [ ] Run the full frontend suite: `npx vitest run` (from `dashboard/frontend`) — all tests pass.
- [ ] Manually verify in the browser (dev servers restarted): the header, login screen, and browser tab all say "Cheterin"; clicking the header title from any dashboard page returns to the home page.
