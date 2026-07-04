# Dashboard: Home Overview Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the placeholder `Home.tsx` (currently a single welcome card with stale "coming in later phases" copy) with a real at-a-glance overview: five clickable cards summarizing feedback, events, moderation activity, antispam status, and member count, approved in `docs/superpowers/specs/2026-07-04-dashboard-home-overview-design.md` (commit `69fccd2`).

**Architecture:** Each card fetches its own data independently via its own `useEffect`, reusing five existing `client.ts` functions unchanged (`fetchFeedbackCases`, `fetchEvents`, `fetchModerationLog`, `fetchLockdownStatus`, `fetchMembers`) — no backend changes, no `client.ts` changes. One card's fetch failing shows only that card's own inline error, never blocking the other four.

**Tech Stack:** React + TypeScript + Vite, Vitest + Testing Library, react-router-dom.

## Global Constraints

- Only `dashboard/frontend/src/pages/Home.tsx` and its test file change. No backend changes, no `client.ts` changes, no changes to any other page.
- Every card is clickable (`Card interactive` + `onClick` via `useNavigate`), navigating to: Feedback → `/feedback`, Events → `/events`, Moderation activity → `/lockdown`, Antispam status → `/lockdown`, Members → `/members`.
- The moderation-activity card shows a mini preview of the first 3 entries from `fetchModerationLog()` (already newest-first) — not just a count.
- Each card independently shows its own loading/error/data state; a failure in one card's fetch must never prevent the other four from rendering their own data.
- The existing "Добро пожаловать, {username}" greeting (via `useAuth()`) is kept as a heading above the card grid — only the stale second paragraph ("Выберите раздел слева... остальные разделы появятся в следующих фазах") is removed, since that's the part that's actually out of date now that every section is live.

---

### Task 1: Rebuild `Home.tsx` as the overview page

**Files:**
- Modify: `dashboard/frontend/src/pages/Home.tsx` (full rewrite)
- Test: `dashboard/frontend/src/pages/Home.test.tsx` (new — this page has never had tests)

**Interfaces:**
- Consumes (all pre-existing, unchanged): `fetchFeedbackCases(status?: string): Promise<FeedbackCaseSummary[]>`, `fetchEvents(status?: string): Promise<EventSummary[]>`, `fetchModerationLog(): Promise<ModerationLogEntry[]>`, `fetchLockdownStatus(): Promise<LockdownStatus>`, `fetchMembers(search: string, page: number, pageSize?: number): Promise<MembersPage>` (`MembersPage` has a `total: number` field) — all from `../api/client`.
- Produces: `HomePage` component (same export name as before, so `App.tsx`'s existing `<Route index element={<HomePage />} />` needs no change).

- [ ] **Step 1: Write the failing tests**

Create `dashboard/frontend/src/pages/Home.test.tsx`:

```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { HomePage } from './Home'

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/feedback" element={<div>Feedback Page Marker</div>} />
        <Route path="/events" element={<div>Events Page Marker</div>} />
        <Route path="/lockdown" element={<div>Lockdown Page Marker</div>} />
        <Route path="/members" element={<div>Members Page Marker</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

function defaultMocks() {
  vi.spyOn(client, 'fetchFeedbackCases').mockResolvedValue([])
  vi.spyOn(client, 'fetchEvents').mockResolvedValue([])
  vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])
  vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
  vi.spyOn(client, 'fetchMembers').mockResolvedValue({ total: 0, page: 1, page_size: 1, members: [] })
}

describe('HomePage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the feedback card with a pending count', async () => {
    defaultMocks()
    vi.spyOn(client, 'fetchFeedbackCases').mockResolvedValue([
      {
        case_id: '1',
        category_key: 'bug',
        category_title: 'Bug',
        submitter_id: '1',
        submitter_display: 'u1',
        status: 'pending',
        created_at: null,
      },
      {
        case_id: '2',
        category_key: 'bug',
        category_title: 'Bug',
        submitter_id: '2',
        submitter_display: 'u2',
        status: 'pending',
        created_at: null,
      },
    ])
    renderPage()
    expect(await screen.findByText('Ожидают решения: 2')).toBeInTheDocument()
  })

  it('shows an empty state when there are no pending feedback cases', async () => {
    defaultMocks()
    renderPage()
    expect(await screen.findByText('Нет ожидающих')).toBeInTheDocument()
  })

  it('renders the events card with an active count', async () => {
    defaultMocks()
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([
      { message_id: '900', type: 'tournament', title: 'Кубок', status: 'open', channel_id: '1', count: 4 },
    ])
    renderPage()
    expect(await screen.findByText('Активных событий: 1')).toBeInTheDocument()
  })

  it('renders the moderation activity card as a preview of only the first 3 entries', async () => {
    defaultMocks()
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([
      {
        type: 'manual_ban',
        timestamp: '2026-07-04T12:00:00+00:00',
        user_id: '1',
        user_display: 'rulebreaker',
        moderator_id: '10',
        moderator_display: 'mod',
        reason: 'спам',
        extra: '',
      },
      {
        type: 'tempban',
        timestamp: '2026-07-04T11:00:00+00:00',
        user_id: '2',
        user_display: 'userB',
        moderator_id: null,
        moderator_display: null,
        reason: 'r',
        extra: '',
      },
      {
        type: 'spam_punish',
        timestamp: '2026-07-04T10:00:00+00:00',
        user_id: '3',
        user_display: 'userC',
        moderator_id: null,
        moderator_display: null,
        reason: 'r',
        extra: '',
      },
      {
        type: 'manual_kick',
        timestamp: '2026-07-04T09:00:00+00:00',
        user_id: '4',
        user_display: 'userD',
        moderator_id: '10',
        moderator_display: 'mod',
        reason: 'r',
        extra: '',
      },
    ])
    renderPage()
    expect(await screen.findByText(/rulebreaker/)).toBeInTheDocument()
    expect(screen.getByText(/userB/)).toBeInTheDocument()
    expect(screen.getByText(/userC/)).toBeInTheDocument()
    expect(screen.queryByText(/userD/)).not.toBeInTheDocument()
  })

  it('shows an empty state when there is no moderation activity', async () => {
    defaultMocks()
    renderPage()
    expect(await screen.findByText('Активности пока нет.')).toBeInTheDocument()
  })

  it('renders an inactive antispam status', async () => {
    defaultMocks()
    renderPage()
    expect(await screen.findByText('ВЫКЛЮЧЕН')).toBeInTheDocument()
  })

  it('renders an active antispam status', async () => {
    defaultMocks()
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: true, role_count: 3 })
    renderPage()
    expect(await screen.findByText('ВКЛЮЧЁН')).toBeInTheDocument()
  })

  it('renders the member count card', async () => {
    defaultMocks()
    vi.spyOn(client, 'fetchMembers').mockResolvedValue({ total: 42, page: 1, page_size: 1, members: [] })
    renderPage()
    expect(await screen.findByText('Участников: 42')).toBeInTheDocument()
  })

  it('navigates to /feedback when the feedback card is clicked', async () => {
    defaultMocks()
    renderPage()
    fireEvent.click(await screen.findByText('Feedback'))
    expect(await screen.findByText('Feedback Page Marker')).toBeInTheDocument()
  })

  it('navigates to /events when the events card is clicked', async () => {
    defaultMocks()
    renderPage()
    fireEvent.click(await screen.findByText('События'))
    expect(await screen.findByText('Events Page Marker')).toBeInTheDocument()
  })

  it('navigates to /lockdown when the moderation activity card is clicked', async () => {
    defaultMocks()
    renderPage()
    fireEvent.click(await screen.findByText('Модерация'))
    expect(await screen.findByText('Lockdown Page Marker')).toBeInTheDocument()
  })

  it('navigates to /lockdown when the antispam status card is clicked', async () => {
    defaultMocks()
    renderPage()
    fireEvent.click(await screen.findByText('Антиспам'))
    expect(await screen.findByText('Lockdown Page Marker')).toBeInTheDocument()
  })

  it('navigates to /members when the members card is clicked', async () => {
    defaultMocks()
    renderPage()
    fireEvent.click(await screen.findByText('Участники'))
    expect(await screen.findByText('Members Page Marker')).toBeInTheDocument()
  })

  it('a failing card does not prevent the other four cards from rendering their own data', async () => {
    vi.spyOn(client, 'fetchFeedbackCases').mockRejectedValue(new Error('fail'))
    vi.spyOn(client, 'fetchEvents').mockResolvedValue([
      { message_id: '900', type: 'poll', title: 'Опрос', status: 'open', channel_id: '1', count: 2 },
    ])
    vi.spyOn(client, 'fetchModerationLog').mockResolvedValue([])
    vi.spyOn(client, 'fetchLockdownStatus').mockResolvedValue({ active: false, role_count: 0 })
    vi.spyOn(client, 'fetchMembers').mockResolvedValue({ total: 7, page: 1, page_size: 1, members: [] })

    renderPage()

    expect(await screen.findByText('Не удалось загрузить')).toBeInTheDocument()
    expect(await screen.findByText('Активных событий: 1')).toBeInTheDocument()
    expect(await screen.findByText('Активности пока нет.')).toBeInTheDocument()
    expect(await screen.findByText('ВЫКЛЮЧЕН')).toBeInTheDocument()
    expect(await screen.findByText('Участников: 7')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `dashboard/frontend`): `npx vitest run src/pages/Home.test.tsx`
Expected: FAIL — the current `HomePage` renders none of this content (it's still the old placeholder welcome card), so every assertion fails to find its target text.

- [ ] **Step 3: Rewrite `Home.tsx`**

Replace the full contents of `dashboard/frontend/src/pages/Home.tsx`:

```tsx
import { Card } from '../components/ui/Card'
import { useAuth } from '../context/AuthContext'

export function HomePage() {
  const { user } = useAuth()
  return (
    <Card className="animate-fade-in-up max-w-2xl">
      <h1 className="text-lg font-semibold text-foreground">Добро пожаловать, {user?.username}</h1>
      <p className="mt-2 text-sm text-muted">
        Выберите раздел слева. «Участники и роли» и «Lockdown и модерация» уже работают —
        остальные разделы появятся в следующих фазах.
      </p>
    </Card>
  )
}
```

with:

```tsx
import {
  CalendarCheck,
  ChatCircleText,
  Clock,
  Prohibit,
  ShieldCheck,
  ShieldWarning,
  SignOut,
  UsersThree,
  Warning,
} from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  fetchEvents,
  fetchFeedbackCases,
  fetchLockdownStatus,
  fetchMembers,
  fetchModerationLog,
  type LockdownStatus,
  type ModerationLogEntry,
} from '../api/client'
import { Card } from '../components/ui/Card'
import { useAuth } from '../context/AuthContext'

const TYPE_ICON: Record<ModerationLogEntry['type'], typeof Warning> = {
  spam_punish: Warning,
  tempban: Clock,
  manual_ban: Prohibit,
  manual_kick: SignOut,
}

const TYPE_LABEL: Record<ModerationLogEntry['type'], string> = {
  spam_punish: 'Анти-спам',
  tempban: 'Tempban',
  manual_ban: 'Бан (дашборд)',
  manual_kick: 'Кик (дашборд)',
}

export function HomePage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [feedbackCount, setFeedbackCount] = useState<number | null>(null)
  const [feedbackError, setFeedbackError] = useState('')

  const [eventsCount, setEventsCount] = useState<number | null>(null)
  const [eventsError, setEventsError] = useState('')

  const [activity, setActivity] = useState<ModerationLogEntry[] | null>(null)
  const [activityError, setActivityError] = useState('')

  const [lockdownStatus, setLockdownStatus] = useState<LockdownStatus | null>(null)
  const [lockdownError, setLockdownError] = useState('')

  const [memberCount, setMemberCount] = useState<number | null>(null)
  const [memberError, setMemberError] = useState('')

  useEffect(() => {
    fetchFeedbackCases('pending')
      .then((cases) => setFeedbackCount(cases.length))
      .catch(() => setFeedbackError('Не удалось загрузить'))
  }, [])

  useEffect(() => {
    fetchEvents('open')
      .then((events) => setEventsCount(events.length))
      .catch(() => setEventsError('Не удалось загрузить'))
  }, [])

  useEffect(() => {
    fetchModerationLog()
      .then(setActivity)
      .catch(() => setActivityError('Не удалось загрузить'))
  }, [])

  useEffect(() => {
    fetchLockdownStatus()
      .then(setLockdownStatus)
      .catch(() => setLockdownError('Не удалось загрузить'))
  }, [])

  useEffect(() => {
    fetchMembers('', 1, 1)
      .then((page) => setMemberCount(page.total))
      .catch(() => setMemberError('Не удалось загрузить'))
  }, [])

  return (
    <div>
      <h1 className="mb-4 text-lg font-semibold text-foreground">Добро пожаловать, {user?.username}</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/feedback')}>
          <div className="flex items-center gap-2 text-foreground">
            <ChatCircleText size={20} className="text-primary" />
            <h2 className="font-semibold">Feedback</h2>
          </div>
          {feedbackError && <p className="mt-2 text-sm text-danger">{feedbackError}</p>}
          {!feedbackError && feedbackCount === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
          {!feedbackError && feedbackCount !== null && (
            <p className="mt-2 text-sm text-muted">
              {feedbackCount === 0 ? 'Нет ожидающих' : `Ожидают решения: ${feedbackCount}`}
            </p>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/events')}>
          <div className="flex items-center gap-2 text-foreground">
            <CalendarCheck size={20} className="text-primary" />
            <h2 className="font-semibold">События</h2>
          </div>
          {eventsError && <p className="mt-2 text-sm text-danger">{eventsError}</p>}
          {!eventsError && eventsCount === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
          {!eventsError && eventsCount !== null && (
            <p className="mt-2 text-sm text-muted">Активных событий: {eventsCount}</p>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/lockdown')}>
          <div className="flex items-center gap-2 text-foreground">
            <ShieldWarning size={20} className="text-primary" />
            <h2 className="font-semibold">Модерация</h2>
          </div>
          {activityError && <p className="mt-2 text-sm text-danger">{activityError}</p>}
          {!activityError && activity === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
          {!activityError && activity !== null && activity.length === 0 && (
            <p className="mt-2 text-sm text-muted">Активности пока нет.</p>
          )}
          {!activityError && activity !== null && activity.length > 0 && (
            <ul className="mt-2 flex flex-col gap-1">
              {activity.slice(0, 3).map((entry, index) => {
                const Icon = TYPE_ICON[entry.type]
                return (
                  <li key={index} className="flex items-center gap-2 text-sm text-muted">
                    <Icon size={14} className="shrink-0" />
                    <span className="truncate">
                      {TYPE_LABEL[entry.type]} — {entry.user_display}
                    </span>
                  </li>
                )
              })}
            </ul>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/lockdown')}>
          <div className="flex items-center gap-2 text-foreground">
            {lockdownStatus?.active ? (
              <ShieldWarning size={20} weight="fill" className="text-danger" />
            ) : (
              <ShieldCheck size={20} weight="fill" className="text-success" />
            )}
            <h2 className="font-semibold">Антиспам</h2>
          </div>
          {lockdownError && <p className="mt-2 text-sm text-danger">{lockdownError}</p>}
          {!lockdownError && lockdownStatus === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
          {!lockdownError && lockdownStatus !== null && (
            <p className="mt-2 text-sm text-muted">{lockdownStatus.active ? 'ВКЛЮЧЁН' : 'ВЫКЛЮЧЕН'}</p>
          )}
        </Card>

        <Card interactive className="animate-fade-in-up" onClick={() => navigate('/members')}>
          <div className="flex items-center gap-2 text-foreground">
            <UsersThree size={20} className="text-primary" />
            <h2 className="font-semibold">Участники</h2>
          </div>
          {memberError && <p className="mt-2 text-sm text-danger">{memberError}</p>}
          {!memberError && memberCount === null && <p className="mt-2 text-sm text-muted">Загрузка…</p>}
          {!memberError && memberCount !== null && (
            <p className="mt-2 text-sm text-muted">Участников: {memberCount}</p>
          )}
        </Card>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run (from `dashboard/frontend`): `npx vitest run src/pages/Home.test.tsx`
Expected: all 14 tests PASS.

- [ ] **Step 5: Run the full frontend suite to check for regressions**

Run (from `dashboard/frontend`): `npx vitest run`
Expected: all tests PASS (no regressions — `HomePage` is only rendered from `App.tsx`'s index route, and no other test file imports it).

- [ ] **Step 6: Commit**

```bash
git add dashboard/frontend/src/pages/Home.tsx dashboard/frontend/src/pages/Home.test.tsx
git commit -m "feat: turn the Home page into a real overview dashboard"
```

---

## Final Verification

- [ ] Run the full frontend suite: `npx vitest run` (from `dashboard/frontend`) — all tests pass.
- [ ] Manually verify in the browser (dev servers restarted): log into the dashboard and confirm the Home page shows all 5 cards with real data (pending feedback count, active events count, a few recent moderation-log entries if any exist, antispam status, member count), and that clicking each card navigates to the right section.
