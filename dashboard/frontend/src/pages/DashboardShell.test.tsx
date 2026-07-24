import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { AuthProvider } from '../context/AuthContext'
import { LanguageProvider } from '../context/LanguageContext'
import { DashboardShell } from './DashboardShell'

function renderShell(initialPath = '/members') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <LanguageProvider>
        <AuthProvider>
          <Routes>
            <Route path="/about" element={<div>Landing Page Marker</div>} />
            <Route path="/members" element={<DashboardShell />} />
          </Routes>
        </AuthProvider>
      </LanguageProvider>
    </MemoryRouter>,
  )
}

describe('DashboardShell', () => {
  it('renders the "Cheterin" header title as a link to the marketing landing', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: false,
      active_guild_id: '1',
    })

    renderShell()

    const title = await screen.findByText('Cheterin')
    expect(title.closest('a')).toHaveAttribute('href', '/about')

    fireEvent.click(title)
    expect(await screen.findByText('Landing Page Marker')).toBeInTheDocument()
  })

  it('shows the username in the top-right header', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: false,
      active_guild_id: '1',
      active_guild_name: 'Мой Сервер',
      active_guild_icon: null,
    })

    renderShell()

    // Аккаунт (никнейм) — справа сверху в шапке.
    const username = await screen.findByText('tester')
    expect(username.closest('header')).not.toBeNull()
  })

  it('shows the active server name in the sidebar', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: false,
      active_guild_id: '1',
      active_guild_name: 'Мой Сервер',
      active_guild_icon: null,
    })

    renderShell()

    // Сервер — в сайдбаре (переключатель), а не в шапке.
    const serverName = await screen.findByText('Мой Сервер')
    expect(serverName.closest('aside')).not.toBeNull()
  })

  it('lists core nav entries and omits pages merged into tabs', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: false,
      active_guild_id: '1',
    })

    renderShell()

    expect(await screen.findByText('Модерация')).toBeInTheDocument()
    expect(screen.getByText('События и голосования')).toBeInTheDocument()
    expect(screen.getByText('Ежедневная рубрика')).toBeInTheDocument()
    // Слиты в табы внутри разделов — отдельных пунктов меню больше нет.
    expect(screen.queryByText('Приветствие и прощание')).not.toBeInTheDocument()
    expect(screen.queryByText('Авто-роли')).not.toBeInTheDocument()
    expect(screen.queryByText('Розыгрыши')).not.toBeInTheDocument()
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
      active_guild_id: '1',
    })

    renderShell()

    await screen.findByText('Модерация')
    expect(screen.queryByText('Супер-админ')).not.toBeInTheDocument()
  })

  it('shows the CTD entry only for super admins on the main guild', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: true,
      is_main_guild: true,
      active_guild_id: '1',
    })

    renderShell()

    expect(await screen.findByText('Тикеты CTD')).toBeInTheDocument()
  })

  it('hides the CTD entry for moderators without super-admin access', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: false,
      is_main_guild: true,
      active_guild_id: '1',
    })

    renderShell()

    await screen.findByText('Модерация')
    expect(screen.queryByText('Тикеты CTD')).not.toBeInTheDocument()
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

    renderShell()

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
      active_guild_id: '1',
    })

    renderShell()

    expect(await screen.findByText('Супер-админ')).toBeInTheDocument()
    expect(screen.getByText('Серверы бота')).toBeInTheDocument()
  })

  it('exposes a mobile menu toggle', async () => {
    vi.spyOn(client, 'fetchCurrentUser').mockResolvedValue({
      id: '1',
      username: 'tester',
      avatar: null,
      is_admin: true,
      is_super_admin: false,
      active_guild_id: '1',
    })

    renderShell()

    expect(await screen.findByRole('button', { name: 'Открыть меню' })).toBeInTheDocument()
  })
})
