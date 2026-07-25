import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../context/AuthContext'
import { LanguageProvider } from '../context/LanguageContext'
import { CreditsPage } from './Credits'

function renderPage() {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ id: null }) }),
  )

  return render(
    <MemoryRouter>
      <LanguageProvider>
        <AuthProvider>
          <CreditsPage />
        </AuthProvider>
      </LanguageProvider>
    </MemoryRouter>,
  )
}

describe('CreditsPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('renders hero, team, home server join, and project links', () => {
    renderPage()

    expect(screen.getByRole('heading', { level: 1, name: 'Авторы' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '404 : Server Not Found' })).toBeInTheDocument()
    expect(
      screen.getByText(/Если у Cheterin Group есть парадная дверь/i),
    ).toBeInTheDocument()
    expect(screen.getByText('Nanda')).toBeInTheDocument()
    expect(screen.getByText('nandak070')).toBeInTheDocument()
    expect(screen.getByText('Mark')).toBeInTheDocument()
    expect(screen.getByText('Основатель')).toBeInTheDocument()

    const join = screen.getByRole('link', { name: /Зайти/i })
    expect(join).toHaveAttribute('href', 'https://discord.gg/cheterin')

    expect(screen.getByRole('link', { name: /AstraBuild/i })).toHaveAttribute(
      'href',
      'https://github.com/Nanda070/AstraBuild',
    )
    expect(screen.getByRole('link', { name: /IDUS/i })).toHaveAttribute(
      'href',
      'https://github.com/Nanda070/IDUS',
    )
    expect(screen.getByRole('link', { name: /Организация ChetTeam/i })).toHaveAttribute(
      'href',
      'https://github.com/orgs/ChetTeam',
    )
  })
})
