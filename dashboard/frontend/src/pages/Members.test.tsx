import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { LanguageProvider } from '../context/LanguageContext'
import { MembersPage } from './Members'

const page = (members: Partial<client.MemberSummary>[], total = members.length): client.MembersPage => ({
  total,
  page: 1,
  page_size: 20,
  members: members.map((m, i) => ({
    id: String(i + 1),
    username: `user${i}`,
    display_name: `user${i}`,
    avatar: null,
    role_count: 0,
    joined_at: null,
    is_bot: false,
    ...m,
  })),
})

describe('MembersPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('loads and renders the first page of members', async () => {
    vi.spyOn(client, 'fetchMembers').mockResolvedValue(page([{ username: 'Alpha' }, { username: 'Beta' }]))
    render(
      <MemoryRouter>
        <LanguageProvider>
          <MembersPage />
        </LanguageProvider>
      </MemoryRouter>,
    )
    await waitFor(() => expect(screen.getByText('Alpha')).toBeInTheDocument())
    expect(screen.getByText('Beta')).toBeInTheDocument()
    expect(client.fetchMembers).toHaveBeenCalledWith('', 1)
  })

  it('debounces search input and refetches with the query', async () => {
    const spy = vi.spyOn(client, 'fetchMembers').mockResolvedValue(page([]))
    render(
      <MemoryRouter>
        <LanguageProvider>
          <MembersPage />
        </LanguageProvider>
      </MemoryRouter>,
    )
    await waitFor(() => expect(spy).toHaveBeenCalledWith('', 1))

    fireEvent.change(screen.getByPlaceholderText('Поиск по имени или нику…'), {
      target: { value: 'sharp' },
    })
    expect(spy).not.toHaveBeenCalledWith('sharp', 1)
    await waitFor(() => expect(spy).toHaveBeenCalledWith('sharp', 1), { timeout: 1000 })
  })

  it('opens the detail panel when a member is clicked', async () => {
    vi.spyOn(client, 'fetchMembers').mockResolvedValue(page([{ id: '42', username: 'Clicky' }]))
    vi.spyOn(client, 'fetchMemberDetail').mockResolvedValue({
      id: '42',
      username: 'Clicky',
      display_name: 'Clicky',
      avatar: null,
      joined_at: null,
      created_at: '2020-06-01T00:00:00+00:00',
      is_bot: false,
      roles: [],
      invite_stats: { joins: 0, leaves: 0, invites: 0 },
      feedback_case_count: 0,
    })
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    render(
      <MemoryRouter>
        <LanguageProvider>
          <MembersPage />
        </LanguageProvider>
      </MemoryRouter>,
    )
    await waitFor(() => screen.getByText('Clicky'))
    fireEvent.click(screen.getByText('Clicky'))
    await waitFor(() => expect(screen.getByText('Забанить')).toBeInTheDocument())
    expect(screen.getByText('Кикнуть')).toBeInTheDocument()
  })
})
