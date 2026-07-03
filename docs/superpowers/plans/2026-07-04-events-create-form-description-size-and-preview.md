# Events Create Form: Larger Description Field + Live Embed Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enlarge the too-small "Описание" textarea in the event creation form, and add a live Discord-embed-styled preview that updates as the form is filled in, before publishing.

**Architecture:** Reuse `dashboard/frontend/src/components/EmbedPreview.tsx` as-is (already shipped in Phase 3b). Add a pure mapping function `buildEventEmbedPreview(spec, optionsText)` in `Events.tsx` that converts the create form's current state into the `EmbedSpec` shape `EmbedPreview` expects, mirroring `events_core.publish_event`'s actual embed-building logic field-for-field.

**Tech Stack:** React + TypeScript + Vite + Vitest (frontend only — no backend changes).

## Global Constraints

- Only `dashboard/frontend/src/pages/Events.tsx` and its test file change. `EmbedPreview.tsx` and `EventDetailPanel.tsx` are reused/left untouched.
- The preview must mirror `events_core.publish_event`'s exact placeholder text/values (not approximations), since that's what a freshly-published event's real embed shows: `"Формат"` + mode label, `"Лимит"`/`"0 / {max_limit}"` or `"Участники"`/`"0"` for tournaments, `"░░░░░░░░░░ 0% (0 гол.)"` per poll option, footer `"🟢 Статус: Открыто"`.
- Colors match discord.py's real values exactly: `brand_red()` = `#ed4245` (tournament), `blurple()` = `#5865f2` (poll).
- **Test-query collision to avoid**: the form already has `<label htmlFor="event-mode">Формат</label>` for the mode `<select>`. The preview also shows a field literally named `"Формат"`. Any test asserting on preview content by plain text must be scoped with `within(screen.getByTestId('event-embed-preview'))`, never a bare `screen.getByText(...)` — otherwise it will throw "multiple elements found." This mirrors the `within(dialog)` scoping pattern already used elsewhere in this project's tests for the same reason.
- Never bare `git add -A`/`git add .`.
- Baseline before this plan: 301 backend (pytest) tests (unaffected — no backend changes), 84 frontend (Vitest) tests, `tsc` clean, build clean, at commit `efef2aa`.

---

### Task 1: Larger description field + live embed preview

**Files:**
- Modify: `dashboard/frontend/src/pages/Events.tsx`
- Modify: `dashboard/frontend/src/pages/Events.test.tsx`

**Interfaces:**
- Consumes: `EmbedPreview` (existing component, `dashboard/frontend/src/components/EmbedPreview.tsx`, props `{ content: string; embed: EmbedSpec }`), `EmbedSpec`/`EmbedFieldSpec` types (existing, `dashboard/frontend/src/api/client.ts`).
- Produces: `buildEventEmbedPreview(spec: CreateEventSpec, optionsText: string): EmbedSpec` — a local, non-exported function in `Events.tsx`. No other file consumes it.

Read `dashboard/frontend/src/pages/Events.tsx` in full first to confirm it still matches — you need its exact current content (from Phase 5b) so your edits land in the right places.

- [ ] **Step 1: Write the failing tests**

Read `dashboard/frontend/src/pages/Events.test.tsx` in full first to see its existing `describe('EventsPage create flow', ...)` block and imports. Change the `@testing-library/react` import line to also import `within` (if not already imported):

```typescript
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
```

Append these three tests inside the existing `describe('EventsPage create flow', ...)` block:

```typescript
  it('shows a live preview of the tournament embed as fields are filled in', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'tourneys' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByLabelText('Название'))
    fireEvent.change(screen.getByLabelText('Название'), { target: { value: 'Летний турнир' } })
    fireEvent.change(screen.getByLabelText('Описание'), { target: { value: 'Описание турнира' } })

    const preview = within(screen.getByTestId('event-embed-preview'))
    expect(preview.getByText('Летний турнир')).toBeInTheDocument()
    expect(preview.getByText('Описание турнира')).toBeInTheDocument()
    expect(preview.getByText('Участники')).toBeInTheDocument()
    expect(preview.getByText('0')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Макс. участников/команд (0 = безлимит)'), { target: { value: '20' } })

    expect(preview.getByText('Лимит')).toBeInTheDocument()
    expect(preview.getByText('0 / 20')).toBeInTheDocument()
  })

  it('shows a live preview of poll options as they are typed', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByText('Опрос'))
    fireEvent.click(screen.getByText('Опрос'))

    fireEvent.change(screen.getByLabelText('Варианты ответа (каждый с новой строки, 2–10)'), {
      target: { value: 'Да\nНет' },
    })

    const preview = within(screen.getByTestId('event-embed-preview'))
    expect(preview.getByText('Да')).toBeInTheDocument()
    expect(preview.getByText('Нет')).toBeInTheDocument()
    expect(preview.getAllByText('░░░░░░░░░░ 0% (0 гол.)')).toHaveLength(2)
  })

  it('preview hides tournament fields when the type is switched to poll', async () => {
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(<EventsPage />)

    await waitFor(() => screen.getByText('Создать событие'))
    fireEvent.click(screen.getByText('Создать событие'))

    await waitFor(() => screen.getByLabelText('Формат'))
    const preview = within(screen.getByTestId('event-embed-preview'))
    expect(preview.getByText('Участники')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Опрос'))

    expect(preview.queryByText('Участники')).not.toBeInTheDocument()
  })
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `dashboard/frontend/`): `npm run test -- Events`
Expected: the 3 new tests FAIL — no element with `data-testid="event-embed-preview"` exists yet.

- [ ] **Step 3: Add the imports**

Change the top of `dashboard/frontend/src/pages/Events.tsx` from:

```typescript
import { useEffect, useState } from 'react'
import {
  createEvent,
  fetchChannels,
  fetchEvents,
  fetchRoles,
  type ChannelInfo,
  type CreateEventSpec,
  type EventSummary,
  type RoleInfo,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { EventDetailPanel } from './EventDetailPanel'
```

to:

```typescript
import { useEffect, useState } from 'react'
import {
  createEvent,
  fetchChannels,
  fetchEvents,
  fetchRoles,
  type ChannelInfo,
  type CreateEventSpec,
  type EmbedFieldSpec,
  type EmbedSpec,
  type EventSummary,
  type RoleInfo,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { EmbedPreview } from '../components/EmbedPreview'
import { Modal } from '../components/ui/Modal'
import { EventDetailPanel } from './EventDetailPanel'
```

- [ ] **Step 4: Add `buildEventEmbedPreview`**

After the existing `emptyCreateSpec()` function and before `export function EventsPage()`, add:

```typescript
const MODE_LABELS: Record<CreateEventSpec['mode'], string> = {
  solo: 'Соло',
  team_captain: 'Командный',
  team_code: 'Командный (по коду)',
}

function buildEventEmbedPreview(spec: CreateEventSpec, optionsText: string): EmbedSpec {
  const fields: EmbedFieldSpec[] =
    spec.type === 'tournament'
      ? [
          { name: 'Формат', value: MODE_LABELS[spec.mode], inline: true },
          spec.max_limit > 0
            ? { name: 'Лимит', value: `0 / ${spec.max_limit}`, inline: true }
            : { name: 'Участники', value: '0', inline: true },
        ]
      : optionsText
          .split('\n')
          .map((line) => line.trim())
          .filter(Boolean)
          .map((opt) => ({ name: opt, value: '░░░░░░░░░░ 0% (0 гол.)', inline: false }))

  return {
    title: spec.title,
    description: spec.description,
    url: '',
    color: spec.type === 'tournament' ? '#ed4245' : '#5865f2',
    author: { name: '', url: '', icon_url: '' },
    footer: { text: '🟢 Статус: Открыто', icon_url: '' },
    image: { url: spec.banner_url },
    thumbnail: { url: '' },
    timestamp: null,
    fields,
  }
}
```

- [ ] **Step 5: Enlarge the description textarea**

In the create-event `Modal`, change the `Описание` `<textarea>` from:

```tsx
          <textarea
            id="event-description"
            value={createSpec.description}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, description: e.target.value }))}
            rows={3}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />
```

to:

```tsx
          <textarea
            id="event-description"
            value={createSpec.description}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, description: e.target.value }))}
            rows={6}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />
```

- [ ] **Step 6: Render the live preview**

In the create-event `Modal`, right after the type-toggle `<div className="flex gap-2">...</div>` block (Турнир/Опрос buttons) and before the `Название` label, add:

```tsx
          <div data-testid="event-embed-preview">
            <EmbedPreview content="" embed={buildEventEmbedPreview(createSpec, optionsText)} />
          </div>
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `npm run test -- Events`
Expected: all pass, including the 3 new preview tests.

- [ ] **Step 8: Run the full frontend suite, typecheck, and build**

Run: `npm run test` then `npx tsc --noEmit` then `npm run build`
Expected: `87 passed` (84 baseline + 3 new), `tsc` clean, build clean.

- [ ] **Step 9: Commit**

```bash
git add dashboard/frontend/src/pages/Events.tsx dashboard/frontend/src/pages/Events.test.tsx
git commit -m "feat(dashboard): enlarge event description field and add live embed preview to create form"
```

---

## Self-Review Notes

- **Spec coverage:** Fix 1 (textarea `rows`) is Step 5; Fix 2 (live preview, `buildEventEmbedPreview`, `EmbedPreview` reuse) is Steps 3-4 and 6; the spec's testing section (tournament fields, poll options, type-switch) maps to the 3 tests in Step 1.
- **Placeholder scan:** none found — every step has complete code.
- **Type/name consistency:** `buildEventEmbedPreview(spec: CreateEventSpec, optionsText: string): EmbedSpec` is defined once (Step 4) and consumed once (Step 6), with matching parameter names throughout. `EmbedSpec`/`EmbedFieldSpec` are the exact existing types from `client.ts`, not redefined.
- **Cross-task risk caught during planning:** the `"Формат"` text-query collision between the form's own `<label htmlFor="event-mode">` and the preview's field name is pre-empted by wrapping the preview in `data-testid="event-embed-preview"` and requiring every test assertion on preview content to go through `within(...)` — this is baked into Step 1's test code itself, not left for a reviewer to discover after the fact.
- Since this is a single small task, there is no multi-task arithmetic to double-check: 84 (baseline) + 3 (this task's new tests) = 87, the plan's only projected total.
