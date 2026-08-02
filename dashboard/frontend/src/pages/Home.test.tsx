import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { AuthProvider } from '../context/AuthContext'
import { LanguageProvider } from '../context/LanguageContext'
import { LATEST_WHATS_NEW, whatsNewDismissKey } from '../whatsNew'
import { HomePage } from './Home'

function renderPage() {
  const userPayload = { id: '1', username: 'tester', avatar: null, is_admin: false, is_super_admin: false }
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => userPayload }),
  )

  return render(
    <MemoryRouter initialEntries={['/']}>
      <LanguageProvider>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/lockdown" element={<div>Lockdown Page Marker</div>} />
            <Route path="/members" element={<div>Members Page Marker</div>} />
            <Route path="/settings" element={<div>Settings Page Marker</div>} />
          </Routes>
        </AuthProvider>
      </LanguageProvider>
    </MemoryRouter>,
  )
}

function defaultMocks() {
  vi.spyOn(client, 'fetchSetupHealth').mockResolvedValue({
    ok: true,
    missing_permissions: [],
    module_issues: [],
    guild_id: '1',
    guild_name: 'Test',
  })
}

describe('HomePage', () => {
  beforeEach(() => {
    const store: Record<string, string> = {
      [whatsNewDismissKey(LATEST_WHATS_NEW.version)]: '1',
    }
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => store[key] ?? null,
      setItem: (key: string, value: string) => {
        store[key] = value
      },
      removeItem: (key: string) => {
        delete store[key]
      },
      clear: () => {
        for (const key of Object.keys(store)) delete store[key]
      },
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('renders welcome and quick links without module cards', async () => {
    defaultMocks()
    renderPage()
    expect(await screen.findByText(/tester/)).toBeInTheDocument()
    expect(screen.getByText('Модерация и lockdown')).toBeInTheDocument()
    expect(screen.getByText('Участники и роли')).toBeInTheDocument()
    expect(screen.getByText('Настройки сервера')).toBeInTheDocument()
    expect(screen.queryByText('Feedback')).not.toBeInTheDocument()
    expect(screen.queryByText('События')).not.toBeInTheDocument()
  })

  it('shows a setup-health warning and navigates to settings', async () => {
    vi.spyOn(client, 'fetchSetupHealth').mockResolvedValue({
      ok: false,
      missing_permissions: ['Send Messages'],
      module_issues: [],
      guild_id: '1',
      guild_name: 'Test',
    })
    renderPage()
    fireEvent.click(await screen.findByText('У бота нет критических прав'))
    expect(await screen.findByText('Settings Page Marker')).toBeInTheDocument()
  })

  it('lists module issues with deep-links', async () => {
    vi.spyOn(client, 'fetchSetupHealth').mockResolvedValue({
      ok: false,
      missing_permissions: [],
      module_issues: [{ module: 'levels', kind: 'missing_channel', detail: 'xp_channel' }],
      guild_id: '1',
      guild_name: 'Test',
    })
    renderPage()
    expect(await screen.findByText(/Рейтинг участников:/)).toBeInTheDocument()
  })

  it('navigates to /lockdown from the moderation quick link', async () => {
    defaultMocks()
    renderPage()
    fireEvent.click(await screen.findByText('Модерация и lockdown'))
    expect(await screen.findByText('Lockdown Page Marker')).toBeInTheDocument()
  })

  it('navigates to /members from the members quick link', async () => {
    defaultMocks()
    renderPage()
    fireEvent.click(await screen.findByText('Участники и роли'))
    expect(await screen.findByText('Members Page Marker')).toBeInTheDocument()
  })

  it('navigates to /settings from the settings quick link', async () => {
    defaultMocks()
    renderPage()
    fireEvent.click(await screen.findByText('Настройки сервера'))
    expect(await screen.findByText('Settings Page Marker')).toBeInTheDocument()
  })
})
