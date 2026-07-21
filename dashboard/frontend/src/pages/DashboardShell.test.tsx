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
      is_super_admin: false,
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

  it('renders the user avatar and username at the top of the sidebar', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: false,
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

    const usernameNodes = await screen.findAllByText('tester')
    expect(usernameNodes.length).toBeGreaterThanOrEqual(2)
  })

  it('lists core nav entries and omits pages merged into tabs', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: false,
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

    expect(await screen.findByText('Модерация')).toBeInTheDocument()
    expect(screen.getByText('События и голосования')).toBeInTheDocument()
    expect(screen.getByText('Ежедневная рубрика')).toBeInTheDocument()
    // Слиты в табы внутри разделов — отдельных пунктов меню больше нет.
    expect(screen.queryByText('Приветствие и прощание')).not.toBeInTheDocument()
    expect(screen.queryByText('Авто-роли')).not.toBeInTheDocument()
    expect(screen.queryByText('Гивевеи')).not.toBeInTheDocument()
    expect(screen.queryByText('Антирейд')).not.toBeInTheDocument()
    expect(screen.queryByText('Верификация')).not.toBeInTheDocument()
  })

  it('hides the super-admin nav group for a regular moderator', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: false,
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

    await screen.findByText('Модерация')
    expect(screen.queryByText('Супер-админ')).not.toBeInTheDocument()
  })

  it('shows the CTD entry only when the main guild is active', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: false,
      is_main_guild: true,
      active_guild_id: '1',
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

    expect(await screen.findByText('Тикеты CTD')).toBeInTheDocument()
  })

  it('hides the CTD entry when a non-main guild is active', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: false,
      is_main_guild: false,
      active_guild_id: '2',
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

    await screen.findByText('Модерация')
    expect(screen.queryByText('Тикеты CTD')).not.toBeInTheDocument()
  })

  it('shows the super-admin nav group for a super admin', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: true,
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

    expect(await screen.findByText('Супер-админ')).toBeInTheDocument()
    expect(screen.getByText('Серверы бота')).toBeInTheDocument()
  })
})
