import { screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { AuthProvider } from '../context/AuthContext'
import { renderWithI18n } from '../test/renderWithI18n'
import { SuperAdminPage } from './SuperAdmin'

function renderPage() {
  return renderWithI18n(
    <MemoryRouter>
      <AuthProvider>
        <SuperAdminPage />
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('SuperAdminPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('renders the list of guilds the bot is in', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'admin',
      avatar: null,
      is_admin: true,
      is_super_admin: true,
      active_guild_id: '1',
    })
    vi.spyOn(client, 'fetchSuperAdminGuilds').mockResolvedValue([
      { id: '1', name: 'Основной сервер', icon: null, member_count: 42, owner_id: '999' },
      { id: '2', name: 'Другой сервер', icon: null, member_count: 7, owner_id: null },
    ])

    renderPage()

    expect(await screen.findByText('Основной сервер')).toBeInTheDocument()
    expect(screen.getByText('Другой сервер')).toBeInTheDocument()
    expect(screen.getByText(/42 участников/)).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Открыть' })).toHaveLength(2)
  })

  it('shows an empty state when the bot is in no guilds', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'admin',
      avatar: null,
      is_admin: true,
      is_super_admin: true,
      active_guild_id: '1',
    })
    vi.spyOn(client, 'fetchSuperAdminGuilds').mockResolvedValue([])
    renderPage()
    expect(await screen.findByText('Бот пока не состоит ни на одном сервере.')).toBeInTheDocument()
  })

  it('shows an error state when access is denied', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'admin',
      avatar: null,
      is_admin: true,
      is_super_admin: true,
      active_guild_id: '1',
    })
    vi.spyOn(client, 'fetchSuperAdminGuilds').mockRejectedValue(new Error('forbidden'))
    renderPage()
    expect(await screen.findByText('Не удалось загрузить список серверов — недостаточно прав.')).toBeInTheDocument()
  })
})
