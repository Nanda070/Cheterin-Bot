import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { AuthProvider } from '../context/AuthContext'
import { HomePage } from './Home'

function renderPage() {
  const userPayload = { id: '1', username: 'tester', avatar: null, is_admin: false }
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => userPayload }),
  )

  return render(
    <MemoryRouter initialEntries={['/']}>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/feedback" element={<div>Feedback Page Marker</div>} />
          <Route path="/events" element={<div>Events Page Marker</div>} />
          <Route path="/lockdown" element={<div>Lockdown Page Marker</div>} />
          <Route path="/members" element={<div>Members Page Marker</div>} />
        </Routes>
      </AuthProvider>
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
