import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../context/AuthContext'
import { ServerSelectPage } from './ServerSelect'

function jsonResponse(body: unknown, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => body }
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/servers']}>
      <AuthProvider>
        <Routes>
          <Route path="/servers" element={<ServerSelectPage />} />
          <Route path="/" element={<div>Dashboard home</div>} />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('ServerSelectPage', () => {
  afterEach(() => vi.restoreAllMocks())

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
    expect(screen.getByRole('button', { name: /Добавить бота/ })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Выбрать' }))
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith('/api/auth/select-guild', expect.objectContaining({ method: 'POST' })),
    )
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
})
