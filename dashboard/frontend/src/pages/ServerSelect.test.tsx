import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../context/AuthContext'
import { LanguageProvider } from '../context/LanguageContext'
import { ServerSelectPage } from './ServerSelect'

function jsonResponse(body: unknown, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => body }
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/servers']}>
      <LanguageProvider>
        <AuthProvider>
          <Routes>
            <Route path="/servers" element={<ServerSelectPage />} />
            <Route path="/about" element={<div>Landing page</div>} />
            <Route path="/" element={<div>Dashboard home</div>} />
            <Route path="/login" element={<div>Login page</div>} />
          </Routes>
        </AuthProvider>
      </LanguageProvider>
    </MemoryRouter>,
  )
}

describe('ServerSelectPage', () => {
  afterEach(() => vi.restoreAllMocks())

  it('links the Cheterin brand to the marketing landing', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/api/auth/me')) {
        return Promise.resolve(jsonResponse({ id: '1', is_super_admin: false, active_guild_id: null }))
      }
      if (url.endsWith('/api/auth/guilds')) {
        return Promise.resolve(jsonResponse({ guilds: [] }))
      }
      return Promise.resolve(jsonResponse({}, 404))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderPage()

    const brand = await screen.findByText('Cheterin')
    expect(brand.closest('a')).toHaveAttribute('href', '/about')
  })

  it('lists manageable guilds and selects one with the bot present', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/api/auth/me')) {
        return Promise.resolve(jsonResponse({ id: '1', is_super_admin: false, active_guild_id: null }))
      }
      if (url.endsWith('/api/auth/guilds')) {
        return Promise.resolve(
          jsonResponse({
            guilds: [
              { id: '10', name: 'With Bot', icon: null, has_bot: true },
              { id: '20', name: 'No Bot', icon: null, has_bot: false },
            ],
          }),
        )
      }
      if (url.endsWith('/api/auth/select-guild')) {
        expect(init?.method).toBe('POST')
        return Promise.resolve(jsonResponse({ ok: true, guild_id: '10' }))
      }
      return Promise.resolve(jsonResponse({}, 404))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderPage()

    await waitFor(() => expect(screen.getByText('With Bot')).toBeInTheDocument())
    expect(screen.getByText('No Bot')).toBeInTheDocument()
    // Сервер без бота предлагает добавить бота, с ботом — выбрать.
    expect(screen.getByRole('button', { name: 'Выбрать' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Добавить бота' })).toBeInTheDocument()
    // Плюс общая кнопка «добавить на любой другой сервер».
    expect(screen.getByRole('button', { name: 'Добавить бота на другой сервер' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Выбрать' }))
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith('/api/auth/select-guild', expect.objectContaining({ method: 'POST' })),
    )
  })

  it('opens a generic invite (no guild_id) when adding the bot to another server', async () => {
    const openMock = vi.fn()
    vi.stubGlobal('open', openMock)
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/api/auth/me')) {
        return Promise.resolve(jsonResponse({ id: '1', is_super_admin: false, active_guild_id: null }))
      }
      if (url.endsWith('/api/auth/guilds')) {
        return Promise.resolve(jsonResponse({ guilds: [] }))
      }
      if (url.endsWith('/api/auth/invite-url')) {
        return Promise.resolve(jsonResponse({ url: 'https://discord.com/invite' }))
      }
      return Promise.resolve(jsonResponse({}, 404))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderPage()

    const addButton = await screen.findByRole('button', { name: 'Добавить бота на другой сервер' })
    fireEvent.click(addButton)

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith('/api/auth/invite-url', expect.anything()),
    )
    await waitFor(() => expect(openMock).toHaveBeenCalledWith('https://discord.com/invite', '_blank', 'noopener,noreferrer'))
  })

  it('shows empty state when there are no manageable guilds', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/api/auth/me')) {
        return Promise.resolve(jsonResponse({ id: '1', is_super_admin: false, active_guild_id: null }))
      }
      if (url.endsWith('/api/auth/guilds')) {
        return Promise.resolve(jsonResponse({ guilds: [] }))
      }
      return Promise.resolve(jsonResponse({}, 404))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderPage()

    await waitFor(() =>
      expect(screen.getByText('Нет серверов, которыми вы можете управлять.')).toBeInTheDocument(),
    )
  })

  it('shows docs, terms, privacy and support server links', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/api/auth/me')) {
        return Promise.resolve(jsonResponse({ id: '1', is_super_admin: false, active_guild_id: null }))
      }
      if (url.endsWith('/api/auth/guilds')) {
        return Promise.resolve(jsonResponse({ guilds: [] }))
      }
      return Promise.resolve(jsonResponse({}, 404))
    })
    vi.stubGlobal('fetch', fetchMock)

    renderPage()

    await waitFor(() => expect(screen.getByRole('link', { name: 'Документация' })).toBeInTheDocument())
    expect(screen.getByRole('link', { name: 'Авторы' })).toHaveAttribute('href', '/credits')
    expect(screen.getByRole('link', { name: 'Условия' })).toHaveAttribute('href', '/terms')
    const support = screen.getByRole('link', { name: 'Сервер поддержки' })
    expect(support).toHaveAttribute('href', 'https://discord.gg/cheterin')
    expect(support).toHaveAttribute('target', '_blank')
  })
})
